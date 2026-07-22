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
    """
    Fungsi pembantu agar tampilan pertanyaan lebih rapi dan seragam.
    Jika pengguna hanya menekan Enter, nilai_default akan digunakan.
    """
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
    """
    Fungsi ini menjalankan perintah di sistem Android (Termux) 
    untuk mencari aplikasi dengan kata 'roblox'.
    """
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
    
    # Bagian input data lainnya
    url_global = tanya_pengguna("Global Private Server URL (or Game URL)")
    cetak_sukses("Global URL set.")
    
    # Menyimpan data ke dalam dictionary
    data_konfigurasi = {
        "package_mode": mode_paket,
        "selected_packages": paket_dipilih,
        "global_url": url_global
    }
    
    # Menulis ke file JSON
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
