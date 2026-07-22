import os
import time
import json

# Nama file untuk menyimpan pengaturan
FILE_KONFIGURASI = "config.json"

# --- KODE WARNA UNTUK TERMUX ---
# Ini digunakan agar teks di terminal tidak monoton (hitam putih)
WARNA_CYAN = '\033[96m'
WARNA_HIJAU = '\033[92m'
WARNA_KUNING = '\033[93m'
WARNA_RESET = '\033[0m' # Untuk mengembalikan warna ke normal

def bersihkan_layar():
    os.system('cls' if os.name == 'nt' else 'clear')

def tanya_pengguna(pertanyaan, nilai_default=None):
    """
    Fungsi pembantu agar tampilan pertanyaan lebih rapi dan seragam.
    Jika pengguna hanya menekan Enter, nilai_default akan digunakan.
    """
    if nilai_default is not None:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan} [Default: {nilai_default}]: "
    else:
        teks_prompt = f"{WARNA_CYAN}[?]{WARNA_RESET} {pertanyaan}: "
        
    jawaban = input(teks_prompt).strip()
    
    # Jika jawaban kosong (cuma tekan Enter) dan ada default, gunakan default
    if jawaban == "" and nilai_default is not None:
        return nilai_default
    return jawaban

def cetak_info(teks):
    print(f"{WARNA_KUNING}[i]{WARNA_RESET} {teks}")

def cetak_sukses(teks):
    print(f"{WARNA_HIJAU}[+]{WARNA_RESET} {teks}")

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
    
    cetak_info("Auto-detecting packages...\n")
    time.sleep(1)
    
    # Simulasi menemukan aplikasi Roblox di HP
    print(f"{WARNA_CYAN}[?]{WARNA_RESET} Discovered packages:")
    print("  1) com.roblox.client")
    print("  2) com.roblox.clienu")
    print("- Press <Enter> or 'all' to select ALL packages (Default)")
    print("- Type 'none' to skip, or enter indices (e.g. '1,3')")
    paket_dipilih = tanya_pengguna("Select", "all")
    
    if paket_dipilih == '2':
        cetak_sukses("Selected:\n  - com.roblox.clienu")
    else:
        cetak_sukses(f"Selected: {paket_dipilih}")
        
    konfirmasi = tanya_pengguna("Confirm selection? [Y/n]", "y")
    
    # Memulai rentetan pertanyaan konfigurasi sesuai gambar
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
    cetak_sukses("Server Hop (Auto Rejoin) DISABLED." if server_hop.startswith("0") else "Server Hop ENABLED.")
    
    offline_timeout = tanya_pengguna("Offline Timeout (seconds)", "300")
    auto_rotate = tanya_pengguna("Enable Auto Account Rotation on ban? [y/N]", "n")
    auto_captcha = tanya_pengguna("Enable Auto Captcha Solver? [y/N]", "n")
    cetak_sukses("Auto Captcha Solver disabled." if auto_captcha.lower() == 'n' else "Auto Captcha Solver enabled.")
    
    clear_cache = tanya_pengguna("Auto-clear app cache on launch/relaunch? [Y/n]", "y")
    cetak_sukses("Auto-clear app cache enabled." if clear_cache.lower() == 'y' else "Auto-clear app cache disabled.")
    
    delta_bypass = tanya_pengguna("Enable Delta Auto Bypass (auto-solve key checkpoint)? [y/N]", "n")
    cetak_sukses("Delta Auto Bypass disabled." if delta_bypass.lower() == 'n' else "Delta Auto Bypass enabled.")
    
    inject_scripts = tanya_pengguna("Inject scripts to 'autoexecute' folder? [y/N]", "n")
    
    # Menyimpan semua data yang sudah diisi ke dalam dictionary
    data_konfigurasi = {
        "package_mode": mode_paket,
        "selected_packages": paket_dipilih,
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
        "delta_auto_bypass": delta_bypass,
        "inject_scripts": inject_scripts
    }
    
    # Menyimpan ke file JSON
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
            cetak_info("\nMenjalankan Auto Rejoiner Script...")
            time.sleep(2)
        elif pilihan == '8':
            cetak_info("\nMenjalankan proses Uninstall Kuro...")
            time.sleep(2)
        elif pilihan == '9':
            print("\nKeluar dari program. Sampai jumpa!")
            break 
        else:
            print(f"\nPilihan {pilihan} tidak valid.")
            time.sleep(1)

if __name__ == "__main__":
    main()
            
