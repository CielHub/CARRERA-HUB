import os
import time

def bersihkan_layar():
    # Fungsi ini membersihkan layar terminal agar menu selalu tampil rapi
    os.system('cls' if os.name == 'nt' else 'clear')

def tampilkan_menu():
    bersihkan_layar()
    # Menampilkan teks judul KURO
    print(" _  __ _   _  ____   ___  ")
    print("| |/ /| | | ||  _ \\ / _ \\ ")
    print("| ' / | | | || |_) | | | |")
    print("| . \\ | |_| ||  _ <| |_| |")
    print("|_|\\_\\ \\___/ |_| \\_\\\\___/ ")
    print("Version 3.5.2")
    print("-" * 50)
    
    # Menampilkan daftar pilihan menu
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

def main():
    # Looping utama agar aplikasi tidak langsung tertutup
    while True:
        tampilkan_menu()
        pilihan = input("[?] Enter your choice [1-9]: ")
        
        if pilihan == '1':
            print("\nMenjalankan Setup Configuration...")
            time.sleep(2)
        elif pilihan == '3':
            print("\nMenjalankan Auto Rejoiner Script...")
            # Logika utama auto rejoiner akan kita masukkan ke sini nanti
            time.sleep(2)
        elif pilihan == '8':
            print("\nMenjalankan proses Uninstall Kuro...")
            time.sleep(2)
        elif pilihan == '9':
            print("\nKeluar dari program. Sampai jumpa!")
            break 
        else:
            print(f"\nPilihan {pilihan} belum dibuat kodenya atau tidak valid.")
            time.sleep(2)

if __name__ == "__main__":
    main()
  
