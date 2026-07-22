import os
import time
import json
import subprocess

# Nama file untuk menyimpan pengaturan
FILE_KONFIGURASI = "config.json"

# --- KODE WARNA UNTUK TERMUX ---
WARNA_CYAN = '\033[96m'
WARNA_HIJAU = '\033[92m'
WARNA_KUNING = '\033[93m'
WARNA_RESET = '\033[0m'

def bersihkan_layar():
    os.system('cls' if os.name == 'nt' else 'clear')

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
    """Membaca data dari file config.json jika file tersebut ada."""
    if os.path.exists(FILE_KONFIGURASI):
        with open(FILE_KONFIGURASI, 'r') as file:
            return json.load(file)
    return None

def bersihkan_cache(nama_paket):
    """
    Fungsi ini menghapus file cache aplikasi di Android.
    Membutuhkan izin storage di Termux (termux-setup-storage).
    """
    cetak_info(f"Mencoba membersihkan cache untuk {nama_paket}...")
    
    # Path folder cache di penyimpanan eksternal Android
    path_cache = f"/storage/emulated/0/Android/data/{nama_paket}/cache/*"
    
    try:
        # Menjalankan perintah hapus paksa (rm -rf) melalui shell Termux
        subprocess.run(f"rm -rf {path_cache}", shell=True, stderr=subprocess.DEVNULL)
        cetak_sukses(f"Cache untuk {nama_paket} berhasil dibersihkan.")
    except Exception as e:
        print(f"{WARNA_KUNING}[!] Terjadi kesalahan saat menghapus cache: {e}{WARNA_RESET}")

def tampilkan_menu():
    bersihkan_layar()
    print(f"{WARNA_CYAN} _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print("|_|\\_\\ \\___/ |_| \\_\\\\___/ {WARNA_RESET}")
    print("Version 3.5.2")
    print("-" * 60)
    
    print("What would you like to do?")
    print("  1) Setup Configuration (First Run)")
    print("  2) Edit Configuration")
    print("  3) Run Script (Launch apps + optimizations)")
    print("  4) Cookie Management")
    print("  5) Clear All App Caches")
    print("  6) Package Manager (Install/Uninstall apps)")
    print("  7) Executor Key Manager")
    print("  8) Uninstall Kuro")
    print("  9) Exit")
    print()

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
            print(f"{WARNA_KUNING}[!] Tidak ada aplikasi Roblox yang ditemukan di sistem.{WARNA_RESET}")
        else:
            print(f"{WARNA_CYAN}[?]{WARNA_RESET} Discovered packages:")
            for index, paket in enumerate(paket_ditemukan, start=1):
                print(f"  {index}) {paket}")
            
            print("- Press <Enter> or 'all' to select ALL packages (Default)")
            print("- Type 'none' to skip, or enter indices (e.g. '1,3')")
            pilihan_indeks = tanya_pengguna("Select", "all")
            
            if pilihan_indeks.lower() == 'all':
                paket_dipilih = ", ".join(paket_ditemukan)
                cetak_sukses("Selected ALL packages.")
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
    if server_hop.startswith("0"):
        cetak_sukses("Server Hop (Auto Rejoin) DISABLED.")
    else:
        cetak_sukses("Server Hop ENABLED.")
        
    offline_timeout = tanya_pengguna("Offline Timeout (seconds)", "300")
    auto_rotate = tanya_pengguna("Enable Auto Account Rotation on ban? [y/N]", "n")
    
    auto_captcha = tanya_pengguna("Enable Auto Captcha Solver? [y/N]", "n")
    if auto_captcha.lower() == 'n':
        cetak_sukses("Auto Captcha Solver disabled.")
    else:
        cetak_sukses("Auto Captcha Solver enabled.")
        
    clear_cache = tanya_pengguna("Auto-clear app cache on launch/relaunch? [Y/n]", "y")
    if clear_cache.lower() == 'y':
        cetak_sukses("Auto-clear app cache enabled.")
    else:
        cetak_sukses("Auto-clear app cache disabled.")
        
    # Fitur Delta Bypass telah dihapus dari sini sesuai permintaanmu
        
    inject_scripts = tanya_pengguna("Inject scripts to 'autoexecute' folder? [y/N]", "n")
    
    # Menyimpan data tanpa variabel delta_bypass
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

def main():
    while True:
        tampilkan_menu()
        pilihan = tanya_pengguna("Enter your choice [1-9]")
        
        if pilihan == '1':
            setup_configuration()
            
        elif pilihan == '3':
            # Logika eksekusi awal (Run Script)
            print()
            config = muat_konfigurasi()
            if not config:
                print(f"{WARNA_KUNING}[!] Konfigurasi belum dibuat. Silakan pilih Menu 1 terlebih dahulu.{WARNA_RESET}")
                time.sleep(2)
                continue
            
            paket_target = config.get("selected_packages", "")
            hapus_cache_otomatis = config.get("auto_clear_cache", "y")
            
            # Jika user memilih 'y' pada pengaturan, cache akan dibersihkan sebelum buka game
            if hapus_cache_otomatis.lower() == 'y':
                bersihkan_cache(paket_target)
                
            cetak_info("Menjalankan Auto Rejoiner Script...")
            # Nanti kita tambahkan logika untuk membuka aplikasi Roblox di sini
            input("\n[Tekan Enter untuk kembali ke menu]")
            
        elif pilihan == '5':
            # Logika pembersihan cache manual
            print()
            config = muat_konfigurasi()
            if not config:
                print(f"{WARNA_KUNING}[!] Konfigurasi belum dibuat. Skrip tidak tahu aplikasi mana yang harus dibersihkan.{WARNA_RESET}")
                time.sleep(2)
                continue
                
            paket_target = config.get("selected_packages", "")
            if paket_target and paket_target != "none":
                bersihkan_cache(paket_target)
            else:
                print(f"{WARNA_KUNING}[!] Tidak ada aplikasi yang dipilih dalam konfigurasi.{WARNA_RESET}")
            
            time.sleep(2)
            
        elif pilihan == '8':
            cetak_info("\nMenjalankan proses Uninstall Kuro...")
            time.sleep(2)
            
        elif pilihan == '9':
            print("\nKeluar dari program. Sampai jumpa!")
            break 
            
        elif pilihan in ['2', '4', '6', '7']:
            print(f"\n{WARNA_KUNING}[i] Menu {pilihan} sedang dalam tahap pengembangan.{WARNA_RESET}")
            time.sleep(1)
            
        else:
            print(f"\nPilihan {pilihan} tidak valid.")
            time.sleep(1)

if __name__ == "__main__":
    main()
