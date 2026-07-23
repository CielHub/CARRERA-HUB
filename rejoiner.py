import os
import time
import json
import subprocess
import re
import sys 
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

indeks_akun_aktif = 0

def bersihkan_layar():
    # Menggunakan ANSI escape code: lebih kuat & bersih untuk Termux
    print('\033[2J\033[H', end='', flush=True)

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
                nama_bersih = paket.replace("package:", "").strip()
                daftar_paket.append(nama_bersih)
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

def simpan_cookie(daftar_cookie):
    with open(FILE_COOKIE, 'w') as file:
        json.dump(daftar_cookie, file, indent=4)

def sensor_cookie(cookie_teks):
    if len(cookie_teks) > 30:
        return f"{cookie_teks[:15]}...[DISENSOR]...{cookie_teks[-10:]}"
    return cookie_teks

def bersihkan_cache(nama_paket, silent=False):
    if not silent: cetak_info(f"Mencoba membersihkan cache untuk {nama_paket}...")
    path_cache = f"/storage/emulated/0/Android/data/{nama_paket}/cache/*"
    try:
        subprocess.run(f"su -c 'rm -rf {path_cache}'", shell=True, stderr=subprocess.DEVNULL)
        if not silent: cetak_sukses(f"Cache untuk {nama_paket} berhasil dibersihkan.")
    except Exception as e:
        if not silent: cetak_error(f"Terjadi kesalahan saat menghapus cache: {e}")

def cek_roblox_berjalan(nama_paket):
    try:
        hasil = subprocess.check_output(f"ps -ef | grep {nama_paket} | grep -v grep", shell=True, text=True)
        return nama_paket in hasil
    except subprocess.CalledProcessError:
        return False

def tutup_roblox(nama_paket, silent=False):
    if not silent: cetak_info(f"Menutup paksa {nama_paket} (Termasuk Delta Lite)...")
    subprocess.run(f"su -c 'am force-stop {nama_paket}'", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(2)

def buka_roblox(nama_paket, url_server, silent=False):
    if not silent: cetak_info(f"Membuka Roblox: {nama_paket}")
    perintah = f'su -c \'am start -a android.intent.action.VIEW -d "{url_server}"\''
    subprocess.run(perintah, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def ganti_akun_otomatis(nama_paket, silent=False):
    global indeks_akun_aktif
    daftar_cookie = muat_cookie()
    
    if not daftar_cookie:
        if not silent: cetak_error("Tidak ada Cookie di Menu 4. Rotasi akun dibatalkan.")
        return False
        
    indeks_akun_aktif += 1
    if indeks_akun_aktif >= len(daftar_cookie):
        indeks_akun_aktif = 0 
        
    cookie_baru = daftar_cookie[indeks_akun_aktif]
    if not silent: cetak_info(f"Memulai Rotasi: Beralih ke Akun {indeks_akun_aktif + 1}...")
    
    tutup_roblox(nama_paket, silent=True)
    
    path_prefs = f"/data/data/{nama_paket}/shared_prefs/{nama_paket}_preferences.xml"
    path_temp = "/storage/emulated/0/temp_roblox_prefs.xml"
    
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
            
            if not silent: cetak_sukses(f"Berhasil menyuntikkan Cookie untuk Akun {indeks_akun_aktif + 1}!")
            return True
        except Exception:
            return False
    return False

def deteksi_error_layar():
    path_gambar = "/storage/emulated/0/kuro_screen.png"
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

def dapatkan_statistik_sistem():
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

# --- FUNGSI RENDER DASHBOARD ---
def render_dashboard(sys_stat, app_stats):
    bersihkan_layar()
    print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print(f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
    print("v3.5.2\n")
    
    mem_data = dapatkan_statistik_sistem()
    mem_stat = f"Free: {mem_data['ram_free']} ({mem_data['ram_pct']})"
    
    garis_batas = f"{WARNA_CYAN}+{'-'*20}+{'-'*25}+{WARNA_RESET}"
    
    print(garis_batas)
    print(f"{WARNA_CYAN}|{WARNA_RESET} {'PACKAGE':<18} {WARNA_CYAN}|{WARNA_RESET} {'STATUS':<23} {WARNA_CYAN}|{WARNA_RESET}")
    print(garis_batas)
    
    print(f"{WARNA_CYAN}|{WARNA_RESET} {'System':<18} {WARNA_CYAN}|{WARNA_RESET} {sys_stat:<23} {WARNA_CYAN}|{WARNA_RESET}")
    print(f"{WARNA_CYAN}|{WARNA_RESET} {'Memory':<18} {WARNA_CYAN}|{WARNA_RESET} {mem_stat:<23} {WARNA_CYAN}|{WARNA_RESET}")
    print(f"{WARNA_CYAN}+{'-'*20}+{'-'*25}+{WARNA_RESET}")
    
    for pkg, stat in app_stats.items():
        nama_pkg = pkg if len(pkg) <= 18 else f"{pkg[:15]}..."
        print(f"{WARNA_CYAN}|{WARNA_RESET} {nama_pkg:<18} {WARNA_CYAN}|{WARNA_RESET} {stat:<23} {WARNA_CYAN}|{WARNA_RESET}")
    print(garis_batas)
    print("\nTekan CTRL+C untuk berhenti dan kembali ke menu.")

# --- MESIN UTAMA ---
def mesin_utama_rejoiner(config):
    paket_target = config.get("selected_packages", "")
    url_global = config.get("global_url", "")
    auto_rotate_aktif = config.get("auto_account_rotation", "n").lower() == 'y'
    
    if not paket_target or paket_target == "none" or not url_global:
        cetak_error("Paket aplikasi belum diatur. Silakan jalankan Menu 1 kembali.")
        time.sleep(2)
        return

    try:
        delay_launch = int(config.get("delay_launch", 40))
        delay_relaunch = int(config.get("delay_relaunch", 40))
        server_hop_interval = config.get("server_hop_interval", "0")
        hop_waktu = int(server_hop_interval.split()[0]) 
    except ValueError:
        delay_launch = 40
        delay_relaunch = 40
        hop_waktu = 0

    fitur_clear_cache = config.get("auto_clear_cache", "y").lower() == 'y'
    
    # Memisahkan paket jika menjalankan multi-akun
    daftar_paket_aktif = [p.strip() for p in paket_target.split(",") if p.strip()]
    
    app_stats = {p: "Idle" for p in daftar_paket_aktif}
    waktu_mulai_dict = {}

    try:
        sys_stat = "Optimizing (1)"
        render_dashboard(sys_stat, app_stats)
        time.sleep(1)
        
        sys_stat = "Boosting"
        for p in daftar_paket_aktif: app_stats[p] = "Keep-Alive"
        render_dashboard(sys_stat, app_stats)
        time.sleep(1)
        
        sys_stat = "Resetting apps"
        for p in daftar_paket_aktif: 
            app_stats[p] = "Resetting"
            if fitur_clear_cache: bersihkan_cache(p, silent=True)
        render_dashboard(sys_stat, app_stats)
        time.sleep(1)
        
        sys_stat = "Ready"
        for p in daftar_paket_aktif: app_stats[p] = "Apps Ready"
        render_dashboard(sys_stat, app_stats)
        time.sleep(1)
        
        for i in range(delay_launch, 0, -1):
            for p in daftar_paket_aktif: app_stats[p] = f"Launch Delay: {i}s"
            render_dashboard(sys_stat, app_stats)
            time.sleep(1)
            
        for p in daftar_paket_aktif:
            app_stats[p] = "Launching"
            render_dashboard(sys_stat, app_stats)
            buka_roblox(p, url_global, silent=True)
            waktu_mulai_dict[p] = time.time()
            time.sleep(3)
            app_stats[p] = "Launched"
            
        render_dashboard(sys_stat, app_stats)
        
        while True:
            for p in daftar_paket_aktif:
                if cek_roblox_berjalan(p):
                    app_stats[p] = "Running (Online)"
                    if deteksi_error_layar():
                        app_stats[p] = "Error Detected!"
                        render_dashboard(sys_stat, app_stats)
                        if auto_rotate_aktif: ganti_akun_otomatis(p, silent=True)
                        else: tutup_roblox(p, silent=True)
                        for i in range(delay_relaunch, 0, -1):
                            app_stats[p] = f"Relaunch: {i}s"
                            render_dashboard(sys_stat, app_stats)
                            time.sleep(1)
                        if fitur_clear_cache: bersihkan_cache(p, silent=True)
                        buka_roblox(p, url_global, silent=True)
                        waktu_mulai_dict[p] = time.time()
                        app_stats[p] = "Launched"
                    
                    elif hop_waktu > 0:
                        if time.time() - waktu_mulai_dict.get(p, time.time()) >= hop_waktu:
                            app_stats[p] = "Server Hop..."
                            render_dashboard(sys_stat, app_stats)
                            tutup_roblox(p, silent=True)
                            time.sleep(2)
                            if fitur_clear_cache: bersihkan_cache(p, silent=True)
                            buka_roblox(p, url_global, silent=True)
                            waktu_mulai_dict[p] = time.time()
                            app_stats[p] = "Launched"
                else:
                    app_stats[p] = "Offline/Crashed!"
                    render_dashboard(sys_stat, app_stats)
                    if auto_rotate_aktif: ganti_akun_otomatis(p, silent=True)
                    for i in range(delay_relaunch, 0, -1):
                        app_stats[p] = f"Relaunch: {i}s"
                        render_dashboard(sys_stat, app_stats)
                        time.sleep(1)
                    if fitur_clear_cache: bersihkan_cache(p, silent=True)
                    buka_roblox(p, url_global, silent=True)
                    waktu_mulai_dict[p] = time.time()
                    app_stats[p] = "Launched"
                    
            render_dashboard(sys_stat, app_stats)
            time.sleep(2)

    except KeyboardInterrupt:
        return

def setup_configuration():
    bersihkan_layar()
    cetak_info("Reset detected. Removing old config...")
    time.sleep(1)
    
    print("\n[i] Select package selection mode:")
    print("  1) Auto-detect (Recommended)")
    print("  2) Use package pattern (e.g., 'com.roblox.*')")
    print("  3) Enter manual package names")
    mode_paket = tanya_pengguna("Choice", "1")
    
    paket_dipilih = "none"
    if mode_paket == '1':
        cetak_info("Auto-detecting packages...\n")
        time.sleep(1)
        paket_ditemukan = deteksi_paket_roblox()
        
        if not paket_ditemukan:
            cetak_error("Tidak ada aplikasi Roblox yang ditemukan di sistem.")
        else:
            print(f"{WARNA_CYAN}[?]{WARNA_RESET} Discovered packages:")
            for index, paket in enumerate(paket_ditemukan, start=1):
                print(f"  {index}) {paket}")
            print("- Press <Enter> or 'all' to select ALL packages (Default)")
            print("- Type 'none' to skip, or enter indices (e.g. '1,3')")
            
            pilihan_indeks = tanya_pengguna("Select", "all")
            
            # --- PARSING KOMA (1,2) DAN ALL ---
            if pilihan_indeks.lower() == 'all':
                paket_dipilih = ",".join(paket_ditemukan)
                cetak_sukses(f"Selected ALL packages:\n{paket_dipilih}")
            elif ',' in pilihan_indeks:
                terpilih = []
                for i in pilihan_indeks.split(','):
                    i = i.strip()
                    if i.isdigit() and 1 <= int(i) <= len(paket_ditemukan):
                        terpilih.append(paket_ditemukan[int(i)-1])
                paket_dipilih = ",".join(terpilih) if terpilih else "none"
                cetak_sukses(f"Selected:\n{paket_dipilih}")
            elif pilihan_indeks.isdigit() and 1 <= int(pilihan_indeks) <= len(paket_ditemukan):
                paket_dipilih = paket_ditemukan[int(pilihan_indeks) - 1]
                cetak_sukses(f"Selected:\n  - {paket_dipilih}")
            else:
                paket_dipilih = pilihan_indeks
                cetak_sukses(f"Selected: {paket_dipilih}")
                
        tanya_pengguna("Confirm selection? [Y/n]", "y")
    
    url_sama = tanya_pengguna("Use same Private Server URL for all packages? [Y/n]", "y")
    url_global = tanya_pengguna("Global Private Server URL (or Game URL)")
    cetak_sukses("Global URL set.")
    mask_user = tanya_pengguna("Mask username in status table? (e.g. naxxxie) [y/N]", "n")
    delay_launch = tanya_pengguna("Delay between launching apps (seconds)", "40")
    delay_relaunch = tanya_pengguna("Delay before relaunching crashed/disconnected apps (seconds)", "40")
    webhook = tanya_pengguna("Discord Webhook URL (for critical alerts) [Enter to skip]", "")
    screenshot = tanya_pengguna("Capture screenshot on critical alerts? [y/N]", "n")
    status_update = tanya_pengguna("Status Update Interval (minutes)", "0 (Disabled)")
    server_hop = tanya_pengguna("Server Hop Interval (seconds)", "0 (Disabled)")
    offline_timeout = tanya_pengguna("Offline Timeout (seconds)", "300")
    auto_rotate = tanya_pengguna("Enable Auto Account Rotation on ban/disconnect? [y/N]", "n")
    auto_captcha = tanya_pengguna("Enable Auto Captcha Solver? [y/N]", "n")
    clear_cache = tanya_pengguna("Auto-clear app cache on launch/relaunch? [Y/n]", "y")
    inject_scripts = tanya_pengguna("Inject scripts to 'autoexecute' folder? [y/N]", "n")
    
    data_konfigurasi = {
        "package_mode": mode_paket,
        "selected_packages": paket_dipilih,
        "use_same_url": url_sama,
        "global_url": url_global,
        "mask_username": mask_user,
        "delay_launch": delay_launch,
        "delay_relaunch": delay_relaunch,
        "webhook_url": webhook,
        "capture_screenshot": screenshot,
        "status_update_interval": status_update,
        "server_hop_interval": server_hop,
        "offline_timeout": offline_timeout,
        "auto_account_rotation": auto_rotate,
        "auto_captcha": auto_captcha,
        "auto_clear_cache": clear_cache,
        "inject_scripts": inject_scripts
    }
    
    with open(FILE_KONFIGURASI, 'w') as file:
        json.dump(data_konfigurasi, file, indent=4)
        
    cetak_sukses("Configuration saved.\n")
    input("Press Enter to return to menu...")

def tampilkan_menu():
    bersihkan_layar()
    print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print(f"|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
    print("Version 3.5.2")
    print("-" * 60)
    print("What would you like to do?")
    print("  1) Setup Configuration (First Run)")
    print("  2) Edit Configuration (WIP)")
    print("  3) Run Script (Launch apps + optimizations)")
    print("  4) Cookie Management")
    print("  5) Clear All App Caches")
    print("  9) Exit\n")

def main():
    while True:
        tampilkan_menu()
        pilihan = tanya_pengguna("Enter your choice [1-9]")
        
        if pilihan == '1':
            setup_configuration()
        elif pilihan == '3':
            config = muat_konfigurasi()
            if not config:
                cetak_error("Konfigurasi belum dibuat. Silakan pilih Menu 1 terlebih dahulu.")
                time.sleep(2)
                continue
            mesin_utama_rejoiner(config)
            print(f"\n{WARNA_KUNING}[i] Kembali ke menu utama...{WARNA_RESET}")
            time.sleep(1.5)
        elif pilihan == '5':
            config = muat_konfigurasi()
            if config:
                paket_target = config.get("selected_packages", "")
                if paket_target:
                    for p in paket_target.split(","):
                        if p.strip(): bersihkan_cache(p.strip())
            time.sleep(2)
        elif pilihan == '9':
            break

if __name__ == "__main__":
    try:
        main()
        print(f"\n{WARNA_HIJAU}Program selesai. Sampai jumpa!{WARNA_RESET}")
    except KeyboardInterrupt:
        print(f"\n\n{WARNA_MERAH}[!] Program dihentikan paksa (Ctrl+C). Keluar...{WARNA_RESET}")
        sys.exit(0)
