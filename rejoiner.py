import os
import time
import json
import subprocess
import re
import sys
import threading
from datetime import datetime

try:
    from PIL import Image
    import pytesseract
    import requests
except ImportError:
    print("\n[!] Modul Pillow, pytesseract, atau requests belum terinstal.")
    print("[!] Jalankan: pip install pytesseract Pillow requests")
    sys.exit()

FILE_KONFIGURASI = "config.json"
FILE_COOKIE = "cookies.json"

WARNA_CYAN = '\033[96m'
WARNA_HIJAU = '\033[92m'
WARNA_KUNING = '\033[93m'
WARNA_MERAH = '\033[91m'
WARNA_RESET = '\033[0m'

# --- STATE GLOBALS (SHARED MEMORY) ---
stop_event = threading.Event()
ocr_lock = threading.Lock()
cookie_lock = threading.Lock()
indeks_akun_aktif = 0

# Status akan dibaca oleh Dashboard dan ditulis oleh Worker
status_paket = {}
waktu_mulai_dict = {}

def bersihkan_layar():
    print('\033[2J\033[H', end='', flush=True)

def jeda_interupsi(durasi):
    """Jeda waktu yang bisa dipotong seketika oleh Ctrl+C"""
    waktu_mulai = time.time()
    while time.time() - waktu_mulai < durasi:
        if stop_event.is_set():
            return True
        time.sleep(0.5)
    return False

def tanya_pengguna(pertanyaan, nilai_default=None):
    if nilai_default is not None:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan} [Default: {nilai_default}]: "
    else:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan}: "
        
    jawaban = input(teks_prompt).strip()
    if jawaban == "" and nilai_default is not None:
        return nilai_default
    return jawaban

def cetak_info(teks):
    print(f"{WARNA_KUNING}[i]{WARNA_RESET} {teks}")

def cetak_sukses(teks):
    print(f"{WARNA_HIJAU}[+]{WARNA_RESET} {teks}")

def cetak_error(teks):
    print(f"{WARNA_MERAH}[!]{WARNA_RESET} {teks}")

def deteksi_paket_roblox():
    try:
        hasil = subprocess.check_output("pm list packages | grep roblox", shell=True, text=True)
        paket_mentah = hasil.strip().split('\n')
        daftar_paket = []
        for paket in paket_mentah:
            if paket:
                daftar_paket.append(paket.replace("package:", "").strip())
        return daftar_paket
    except subprocess.CalledProcessError:
        return []

def muat_konfigurasi():
    if os.path.exists(FILE_KONFIGURASI):
        with open(FILE_KONFIGURASI, 'r') as file:
            return json.load(file)
    return None

def muat_cookie():
    if os.path.exists(FILE_COOKIE):
        with open(FILE_COOKIE, 'r') as file:
            return json.load(file)
    return []

# --- KOMPONEN WORKER (PERINTAH ANDROID) ---
def bersihkan_cache(nama_paket):
    path_cache = f"/storage/emulated/0/Android/data/{nama_paket}/cache/*"
    try:
        subprocess.run(f"su -c 'rm -rf {path_cache}'", shell=True, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def cek_roblox_berjalan(nama_paket):
    try:
        hasil = subprocess.check_output(f"ps -ef | grep {nama_paket} | grep -v grep", shell=True, text=True)
        return nama_paket in hasil
    except subprocess.CalledProcessError:
        return False

def tutup_roblox(nama_paket):
    subprocess.run(f"su -c 'am force-stop {nama_paket}'", shell=True, stderr=subprocess.DEVNULL)
    jeda_interupsi(2)

def buka_aplikasi_dasar(nama_paket):
    """Tahap 1: Membuka aplikasi ke menu utama (Cold Start)"""
    perintah = f"su -c 'monkey -p {nama_paket} -c android.intent.category.LAUNCHER 1'"
    subprocess.run(perintah, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def buka_private_server(url_server):
    """Tahap 2: Menembakkan URL Private Server (Warm Start)"""
    perintah = f'su -c \'am start -a android.intent.action.VIEW -d "{url_server}"\''
    subprocess.run(perintah, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def ganti_akun_otomatis(nama_paket):
    global indeks_akun_aktif
    with cookie_lock:
        daftar_cookie = muat_cookie()
        if not daftar_cookie:
            return False
            
        indeks_akun_aktif += 1
        if indeks_akun_aktif >= len(daftar_cookie):
            indeks_akun_aktif = 0 
            
        cookie_baru = daftar_cookie[indeks_akun_aktif]
        tutup_roblox(nama_paket)
        
        path_prefs = f"/data/data/{nama_paket}/shared_prefs/{nama_paket}_preferences.xml"
        path_temp = f"/storage/emulated/0/temp_prefs_{nama_paket}.xml"
        
        subprocess.run(f"su -c 'cp {path_prefs} {path_temp}'", shell=True, stderr=subprocess.DEVNULL)
        if os.path.exists(path_temp):
            try:
                with open(path_temp, 'r', encoding='utf-8', errors='ignore') as f:
                    isi_file = f.read()
                isi_baru = re.sub(r'_\|WARNING:-DO-NOT-SHARE-THIS.*?<', f'{cookie_baru}<', isi_file)
                with open(path_temp, 'w', encoding='utf-8') as f:
                    f.write(isi_baru)
                
                subprocess.run(f"su -c 'cat {path_temp} > {path_prefs}'", shell=True)
                os.remove(path_temp)
                return True
            except Exception:
                return False
        return False

def deteksi_error_layar(nama_paket):
    with ocr_lock:
        path_gambar = f"/storage/emulated/0/kuro_screen_{nama_paket}.png"
        subprocess.run(f"su -c 'screencap -p {path_gambar}'", shell=True, stderr=subprocess.DEVNULL)
        if not os.path.exists(path_gambar): return False
        try:
            gambar = Image.open(path_gambar)
            teks_di_layar = pytesseract.image_to_string(gambar).lower()
            for kata in ["disconnected", "kicked", "error code", "lost connection", "reconnect", "banned"]:
                if kata in teks_di_layar: return True 
            return False
        except Exception:
            return False
        finally:
            if os.path.exists(path_gambar): os.remove(path_gambar)

# --- KOMPONEN DASHBOARD (PEMBACAAN STATISTIK) ---
def dapatkan_statistik_sistem():
    stats = {"ram_free": "N/A", "ram_pct": "N/A", "cpu": "N/A"}
    try:
        meminfo = subprocess.check_output("cat /proc/meminfo", shell=True, text=True)
        mem_total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
        mem_free = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
        stats["ram_free"] = f"{mem_free // 1024}MB"
        stats["ram_pct"] = f"{int((mem_total - mem_free) / mem_total * 100)}%"
        
        top_out = subprocess.check_output("top -n 1 -b | head -n 5", shell=True, text=True)
        cpu_m = re.search(r"(\d+)%cpu", top_out, re.IGNORECASE)
        if cpu_m: stats["cpu"] = f"{cpu_m.group(1)}%"
    except Exception:
        pass
    return stats

def thread_dashboard():
    """Alur Dashboard: Membaca murni data lalu merender setiap 1 detik"""
    while not stop_event.is_set():
        sys_stats = dapatkan_statistik_sistem()
        mem_teks = f"Free: {sys_stats['ram_free']} ({sys_stats['ram_pct']})"
        cpu_teks = f"CPU Load: {sys_stats['cpu']}"
        
        bersihkan_layar()
        print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
        print("| |/ /| | | ||  _ \\ / _ \\ ")
        print("| ' / | | | || |_) | | | |")
        print("| . \\ | |_| ||  _ <| |_| |")
        print(f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
        print("v4.1.0 (Ultimate Multi-Thread)\n")
        
        garis_batas = f"{WARNA_CYAN}+{'-'*20}+{'-'*25}+{WARNA_RESET}"
        
        print(garis_batas)
        print(f"{WARNA_CYAN}|{WARNA_RESET} {'PACKAGE':<18} {WARNA_CYAN}|{WARNA_RESET} {'STATUS':<23} {WARNA_CYAN}|{WARNA_RESET}")
        print(garis_batas)
        print(f"{WARNA_CYAN}|{WARNA_RESET} {'System Memory':<18} {WARNA_CYAN}|{WARNA_RESET} {mem_teks:<23} {WARNA_CYAN}|{WARNA_RESET}")
        print(f"{WARNA_CYAN}|{WARNA_RESET} {'System CPU':<18} {WARNA_CYAN}|{WARNA_RESET} {cpu_teks:<23} {WARNA_CYAN}|{WARNA_RESET}")
        print(f"{WARNA_CYAN}+{'-'*20}+{'-'*25}+{WARNA_RESET}")
        
        for pkg, stat in status_paket.items():
            nama_pkg = pkg if len(pkg) <= 18 else f"{pkg[:15]}..."
            print(f"{WARNA_CYAN}|{WARNA_RESET} {nama_pkg:<18} {WARNA_CYAN}|{WARNA_RESET} {stat:<23} {WARNA_CYAN}|{WARNA_RESET}")
        print(garis_batas)
        print("\nTekan CTRL+C untuk menghentikan semua proses.")
        
        jeda_interupsi(1)

# --- KOMPONEN WORKER (ALUR APLIKASI & RECOVERY) ---
def thread_pekerja_paket(pkg, config, jeda_awal):
    url_global = config.get("global_url", "")
    auto_rotate = config.get("auto_account_rotation", "n").lower() == 'y'
    fitur_clear_cache = config.get("auto_clear_cache", "y").lower() == 'y'
    delay_launch = int(config.get("delay_launch", 40))
    hop_waktu = int(config.get("server_hop_interval", "0").split()[0])

    # 1. Idle
    status_paket[pkg] = "Idle (Queue)..."
    if jeda_interupsi(jeda_awal): return

    # Loop Besar (Hanya digunakan jika terjadi force restart penuh)
    while not stop_event.is_set():
        # 2. Preparing
        status_paket[pkg] = "Preparing..."
        if fitur_clear_cache:
            bersihkan_cache(pkg)
            
        # 3. Launch Roblox
        status_paket[pkg] = "Launch Roblox..."
        buka_aplikasi_dasar(pkg)
        
        # 4. Wait Process
        for i in range(delay_launch, 0, -1):
            status_paket[pkg] = f"Wait Process: {i}s"
            if jeda_interupsi(1): return
            
        # 5. Open Private Server
        status_paket[pkg] = "Open Private Server..."
        buka_private_server(url_global)
        
        # 6. Joining
        status_paket[pkg] = "Joining Server..."
        if jeda_interupsi(15): return 
        waktu_mulai_dict[pkg] = time.time()
        
        # 7. Running & Monitoring Loop
        dalam_sesi = True
        while dalam_sesi and not stop_event.is_set():
            status_paket[pkg] = "Running (Online)"
            is_running = cek_roblox_berjalan(pkg)
            butuh_recovery = False
            
            if is_running:
                if deteksi_error_layar(pkg):
                    status_paket[pkg] = "Error Detected!"
                    butuh_recovery = True
                elif hop_waktu > 0 and (time.time() - waktu_mulai_dict.get(pkg, time.time()) >= hop_waktu):
                    status_paket[pkg] = "Server Hop..."
                    butuh_recovery = True
            else:
                status_paket[pkg] = "Offline/Crashed!"
                butuh_recovery = True

            # --- RECOVERY FLOW ---
            if butuh_recovery:
                status_paket[pkg] = "Force Stop..."
                if auto_rotate:
                    ganti_akun_otomatis(pkg)
                else:
                    tutup_roblox(pkg)
                    
                if fitur_clear_cache:
                    status_paket[pkg] = "Clear Cache..."
                    bersihkan_cache(pkg)
                    
                status_paket[pkg] = "Launch Roblox..."
                buka_aplikasi_dasar(pkg)
                
                for i in range(delay_launch, 0, -1):
                    status_paket[pkg] = f"Recovery Wait: {i}s"
                    if jeda_interupsi(1): return
                    
                status_paket[pkg] = "Open Private Server..."
                buka_private_server(url_global)
                
                status_paket[pkg] = "Joining Server..."
                waktu_mulai_dict[pkg] = time.time()
                if jeda_interupsi(15): return 
                continue # Kembali ke siklus Running

            if jeda_interupsi(5): return

# --- MANAGER UTAMA ---
def mesin_utama_rejoiner(config):
    global status_paket, waktu_mulai_dict
    stop_event.clear() 
    
    paket_target = config.get("selected_packages", "")
    if not paket_target or paket_target == "none":
        cetak_error("Paket aplikasi belum diatur.")
        time.sleep(2)
        return

    daftar_paket_aktif = [p.strip() for p in paket_target.split(",") if p.strip()]
    status_paket = {p: "Idle" for p in daftar_paket_aktif}
    waktu_mulai_dict = {}
    threads = []
    
    try:
        t_dash = threading.Thread(target=thread_dashboard)
        t_dash.daemon = True
        t_dash.start()
        threads.append(t_dash)

        for i, pkg in enumerate(daftar_paket_aktif):
            jeda_stagger = i * 15 
            t = threading.Thread(target=thread_pekerja_paket, args=(pkg, config, jeda_stagger))
            t.daemon = True
            t.start()
            threads.append(t)
            
        while not stop_event.is_set():
            time.sleep(1)
                
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        time.sleep(1) 

def setup_configuration():
    bersihkan_layar()
    print("\n[i] Select package selection mode:")
    print("  1) Auto-detect (Recommended)")
    print("  2) Manual")
    mode_paket = tanya_pengguna("Choice", "1")
    
    paket_dipilih = "none"
    if mode_paket == '1':
        paket_ditemukan = deteksi_paket_roblox()
        if paket_ditemukan:
            for i, p in enumerate(paket_ditemukan, 1): print(f"  {i}) {p}")
            pilihan = tanya_pengguna("Select (e.g. 'all' or '1,2')", "all")
            if pilihan.lower() == 'all':
                paket_dipilih = ",".join(paket_ditemukan)
            elif ',' in pilihan:
                terpilih = [paket_ditemukan[int(i.strip())-1] for i in pilihan.split(',') if i.strip().isdigit()]
                paket_dipilih = ",".join(terpilih)
            elif pilihan.isdigit():
                paket_dipilih = paket_ditemukan[int(pilihan) - 1]
    
    url_global = tanya_pengguna("Global Private Server URL")
    delay_launch = tanya_pengguna("Wait Process Delay (seconds)", "20")
    server_hop = tanya_pengguna("Server Hop Interval (seconds)", "0")
    auto_rotate = tanya_pengguna("Enable Auto Account Rotation? [y/N]", "n")
    clear_cache = tanya_pengguna("Auto-clear cache? [Y/n]", "y")
    
    data = {
        "selected_packages": paket_dipilih,
        "global_url": url_global,
        "delay_launch": delay_launch,
        "server_hop_interval": server_hop,
        "auto_account_rotation": auto_rotate,
        "auto_clear_cache": clear_cache
    }
    with open(FILE_KONFIGURASI, 'w') as file: json.dump(data, file, indent=4)
    cetak_sukses("Configuration saved."); time.sleep(1)

def tampilkan_menu():
    bersihkan_layar()
    print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print(f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
    print("Version 4.1.0 (Ultimate Multi-Thread)")
    print("-" * 60)
    print("  1) Setup Configuration")
    print("  3) Run Script (Multi-Package Dashboard)")
    print("  9) Exit\n")

def main():
    while True:
        tampilkan_menu()
        pilihan = tanya_pengguna("Enter your choice [1-9]")
        if pilihan == '1': setup_configuration()
        elif pilihan == '3':
            c = muat_konfigurasi()
            if c: mesin_utama_rejoiner(c)
        elif pilihan == '9': break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n\n{WARNA_MERAH}[!] Program dihentikan paksa (Ctrl+C). Keluar dengan aman...{WARNA_RESET}")
        sys.exit(0)
