import os
import time
import json
import subprocess
import re
import sys
import threading
import queue
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

# --- STATE GLOBALS ---
stop_event = threading.Event()
cookie_lock = threading.Lock()
indeks_akun_aktif = 0

status_paket = {}
waktu_mulai_dict = {}

# --- SISTEM ANTREAN (QUEUE) ---
antrean_perintah = queue.Queue()

def prosesor_antrean():
    """Kasir: Satu-satunya thread yang mengeksekusi perintah shell Android."""
    while not stop_event.is_set():
        try:
            tugas = antrean_perintah.get(timeout=1)
        except queue.Empty:
            continue
            
        perintah = tugas['perintah']
        tunggu_output = tugas['tunggu']
        
        try:
            # Jika butuh output (seperti cek proses berjalan), kita tangkap hasilnya
            if tunggu_output:
                hasil = subprocess.run(perintah, shell=True, capture_output=True, text=True, stderr=subprocess.DEVNULL)
                tugas['hasil'] = hasil
            else:
                # Eksekusi lepas tangan (seperti buka aplikasi) agar tidak macet
                subprocess.Popen(perintah, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                tugas['hasil'] = None
        except Exception:
            tugas['hasil'] = None
            
        tugas['selesai'].set()
        antrean_perintah.task_done()

def eksekusi_aman(perintah_shell, tunggu=True):
    """Pelanggan: Fungsi untuk menitipkan perintah ke Kasir."""
    tugas = {
        'perintah': perintah_shell,
        'tunggu': tunggu,
        'selesai': threading.Event(),
        'hasil': None
    }
    antrean_perintah.put(tugas)
    
    if tunggu:
        tugas['selesai'].wait() 
        return tugas['hasil']
    return None

# --- FUNGSI BANTUAN DASAR ---
def bersihkan_layar_total():
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

def jeda_interupsi(durasi):
    waktu_mulai = time.time()
    while time.time() - waktu_mulai < durasi:
        if stop_event.is_set(): return True
        time.sleep(0.5)
    return False

def tanya_pengguna(pertanyaan, nilai_default=None):
    if nilai_default is not None:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan} [Default: {nilai_default}]: "
    else:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan}: "
    jawaban = input(teks_prompt).strip()
    return nilai_default if (jawaban == "" and nilai_default is not None) else jawaban

def cetak_error(teks): print(f"{WARNA_MERAH}[!]{WARNA_RESET} {teks}")
def cetak_sukses(teks): print(f"{WARNA_HIJAU}[+]{WARNA_RESET} {teks}")

def deteksi_paket_roblox():
    try:
        hasil = subprocess.check_output("pm list packages | grep roblox", shell=True, text=True)
        return [p.replace("package:", "").strip() for p in hasil.strip().split('\n') if p]
    except subprocess.CalledProcessError:
        return []

def muat_konfigurasi():
    if os.path.exists(FILE_KONFIGURASI):
        with open(FILE_KONFIGURASI, 'r') as file: return json.load(file)
    return None

def muat_cookie():
    if os.path.exists(FILE_COOKIE):
        with open(FILE_COOKIE, 'r') as file: return json.load(file)
    return []

# --- KOMPONEN WORKER (MENGGUNAKAN EKSEKUSI AMAN) ---
def bersihkan_cache(nama_paket):
    path_cache = f"/storage/emulated/0/Android/data/{nama_paket}/cache/*"
    eksekusi_aman(f"su -c 'rm -rf {path_cache}'", tunggu=False)

def cek_roblox_berjalan(nama_paket):
    hasil = eksekusi_aman(f"ps -ef | grep {nama_paket} | grep -v grep", tunggu=True)
    if hasil and hasil.stdout:
        return nama_paket in hasil.stdout
    return False

def tutup_roblox(nama_paket):
    eksekusi_aman(f"su -c 'am force-stop {nama_paket}'", tunggu=False)
    jeda_interupsi(2)

def buka_roblox(nama_paket, url_server):
    # Kembali ke "Cara 1" yang langsung menembak URL (Tanpa perlu ditunggu Kasir)
    eksekusi_aman(f'su -c \'am start -a android.intent.action.VIEW -d "{url_server}"\'', tunggu=False)

def ganti_akun_otomatis(nama_paket):
    global indeks_akun_aktif
    with cookie_lock:
        daftar_cookie = muat_cookie()
        if not daftar_cookie: return False
            
        indeks_akun_aktif += 1
        if indeks_akun_aktif >= len(daftar_cookie): indeks_akun_aktif = 0 
            
        cookie_baru = daftar_cookie[indeks_akun_aktif]
        tutup_roblox(nama_paket)
        
        path_prefs = f"/data/data/{nama_paket}/shared_prefs/{nama_paket}_preferences.xml"
        path_temp = f"/storage/emulated/0/temp_prefs_{nama_paket}.xml"
        
        eksekusi_aman(f"su -c 'cp {path_prefs} {path_temp}'", tunggu=True)
        if os.path.exists(path_temp):
            try:
                with open(path_temp, 'r', encoding='utf-8', errors='ignore') as f:
                    isi_baru = re.sub(r'_\|WARNING:-DO-NOT-SHARE-THIS.*?<', f'{cookie_baru}<', f.read())
                with open(path_temp, 'w', encoding='utf-8') as f:
                    f.write(isi_baru)
                
                eksekusi_aman(f"su -c 'cat {path_temp} > {path_prefs}'", tunggu=True)
                os.remove(path_temp)
                return True
            except Exception:
                return False
        return False

def deteksi_error_layar(nama_paket):
    path_gambar = f"/storage/emulated/0/kuro_screen_{nama_paket}.png"
    eksekusi_aman(f"su -c 'screencap -p {path_gambar}'", tunggu=True) 
    
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

# --- KOMPONEN DASHBOARD (BUFFERED RENDERING) ---
def dapatkan_statistik_ram():
    # Menghapus pengecekan CPU yang berat, fokus ke RAM saja
    stats = {"ram_free": "N/A", "ram_pct": "N/A"}
    try:
        meminfo = subprocess.check_output("cat /proc/meminfo", shell=True, text=True)
        mem_total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
        mem_free = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
        stats["ram_free"] = f"{mem_free // 1024}MB"
        stats["ram_pct"] = f"{int((mem_total - mem_free) / mem_total * 100)}%"
    except Exception:
        pass
    return stats

def thread_dashboard():
    bersihkan_layar_total()
    while not stop_event.is_set():
        sys_stats = dapatkan_statistik_ram()
        mem_teks = f"Free: {sys_stats.get('ram_free')} ({sys_stats.get('ram_pct')})"
        
        garis_batas = f"{WARNA_CYAN}+{'-'*16}+{'-'*25}+{WARNA_RESET}\n"
        buffer_layar = '\033[H' 
        
        buffer_layar += f"{WARNA_CYAN} _  __ _   _  ____   ___  \n"
        buffer_layar += f"| |/ /| | | ||  _ \\ / _ \\ \n"
        buffer_layar += f"| ' / | | | || |_) | | | |\n"
        buffer_layar += f"| . \\ | |_| ||  _ <| |_| |\n"
        buffer_layar += f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}\n"
        buffer_layar += "v4.3 (Fast Queue & Buffered)\n\n"
        
        buffer_layar += garis_batas
        buffer_layar += f"{WARNA_CYAN}|{WARNA_RESET} {'PACKAGE':<14} {WARNA_CYAN}|{WARNA_RESET} {'STATUS':<23} {WARNA_CYAN}|{WARNA_RESET}\n"
        buffer_layar += garis_batas
        buffer_layar += f"{WARNA_CYAN}|{WARNA_RESET} {'System Memory':<14} {WARNA_CYAN}|{WARNA_RESET} {mem_teks:<23} {WARNA_CYAN}|{WARNA_RESET}\n"
        buffer_layar += garis_batas
        
        for pkg, stat in status_paket.items():
            nama_pkg = pkg if len(pkg) <= 14 else f"{pkg[:11]}..."
            status_teks = stat if len(stat) <= 23 else f"{stat[:20]}..."
            buffer_layar += f"{WARNA_CYAN}|{WARNA_RESET} {nama_pkg:<14} {WARNA_CYAN}|{WARNA_RESET} {status_teks:<23} {WARNA_CYAN}|{WARNA_RESET}\n"
            
        buffer_layar += garis_batas
        buffer_layar += "\nTekan CTRL+C untuk menghentikan semua proses.\n"
        buffer_layar += '\033[J' 
        
        sys.stdout.write(buffer_layar)
        sys.stdout.flush()
        jeda_interupsi(1.5) # Sedikit diperlambat agar lebih stabil

# --- KOMPONEN WORKER (ALUR APLIKASI & RECOVERY) ---
def thread_pekerja_paket(pkg, config, jeda_awal):
    url_global = config.get("global_url", "")
    auto_rotate = config.get("auto_account_rotation", "n").lower() == 'y'
    fitur_clear_cache = config.get("auto_clear_cache", "y").lower() == 'y'
    delay_launch = int(config.get("delay_launch", 40))
    hop_waktu = int(config.get("server_hop_interval", "0").split()[0])

    status_paket[pkg] = "Idle (Queue)..."
    if jeda_interupsi(jeda_awal): return

    while not stop_event.is_set():
        status_paket[pkg] = "Preparing..."
        if fitur_clear_cache: bersihkan_cache(pkg)
            
        # Menggunakan "Cara 1" Langsung tembak URL
        status_paket[pkg] = "Launch & Join..."
        buka_roblox(pkg, url_global)
        waktu_mulai_dict[pkg] = time.time()
        
        # Menunggu proses loading aplikasi
        for i in range(delay_launch, 0, -1):
            status_paket[pkg] = f"Wait Process: {i}s"
            if jeda_interupsi(1): return
        
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

            if butuh_recovery:
                status_paket[pkg] = "Force Stop..."
                if auto_rotate: ganti_akun_otomatis(pkg)
                else: tutup_roblox(pkg)
                    
                if fitur_clear_cache:
                    status_paket[pkg] = "Clear Cache..."
                    bersihkan_cache(pkg)
                    
                status_paket[pkg] = "Launch & Join..."
                buka_roblox(pkg, url_global)
                waktu_mulai_dict[pkg] = time.time()
                
                for i in range(delay_launch, 0, -1):
                    status_paket[pkg] = f"Recovery Wait: {i}s"
                    if jeda_interupsi(1): return
                continue

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
        t_kasir = threading.Thread(target=prosesor_antrean)
        t_kasir.daemon = True
        t_kasir.start()
        threads.append(t_kasir)

        t_dash = threading.Thread(target=thread_dashboard)
        t_dash.daemon = True
        t_dash.start()
        threads.append(t_dash)

        for i, pkg in enumerate(daftar_paket_aktif):
            # Memberikan jeda 10 detik antar aplikasi agar HP tidak kaget
            jeda_stagger = i * 10 
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
        while not antrean_perintah.empty():
            try:
                antrean_perintah.get_nowait()
                antrean_perintah.task_done()
            except queue.Empty:
                break
        time.sleep(1) 

def setup_configuration():
    bersihkan_layar_total()
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
    delay_launch = tanya_pengguna("Wait Process Delay (seconds)", "40")
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
    bersihkan_layar_total()
    print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print(f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
    print("Version 4.3 (Fast Queue & Buffered)")
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
