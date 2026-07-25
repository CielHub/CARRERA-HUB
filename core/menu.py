"""
Modul: menu.py
Tanggung Jawab: Menampilkan CLI interaktif dan routing eksekusi.
"""
import os
import sys
import time

from core.logger import log
from core.config import load_config, save_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import start_monitoring
from core.tester import show_test_menu   # [PHASE 6] Import menu tester

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# ... [Fungsi run_auto_rejoiner() dan show_settings() TETAP SAMA SEPERTI SEBELUMNYA] ...
# (Saya potong di sini agar tidak memakan layar, pastikan fungsi run_auto_rejoiner dan show_settings lu tidak dihapus)

def show_main_menu():
    """Menampilkan Menu Utama."""
    while True:
        clear_screen()
        print("=================================")
        print("    CARRERA-HUB Auto Rejoiner    ")
        print("=================================")
        print("1. Jalankan Auto Rejoiner")
        print("2. Settings")
        print("3. Test")
        print("4. Logs")
        print("5. About")
        print("6. Exit")
        print("=================================")
        
        choice = input("Pilih menu (1-6): ")
        
        if choice == '1':
            run_auto_rejoiner()
        elif choice == '2':
            show_settings()
        elif choice == '3':
            # [PHASE 6] Arahkan ke modul tester
            show_test_menu()
        elif choice == '4':
            clear_screen()
            print("=================================")
            print("        LOG TERAKHIR (20 Baris)  ")
            print("=================================")
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
            if os.path.exists(log_path):
                os.system(f"tail -n 20 {log_path}")
            else:
                print("File log belum tersedia.")
            print("=================================")
            input("Tekan Enter untuk kembali...")
        elif choice == '5':
            print("\n=================================")
            print("CARRERA-HUB Auto Rejoiner")
            print("Versi: Python Modular Edition")
            print("Status: Stabil & Termux Root Ready")
            print("=================================")
            input("Tekan Enter untuk kembali...")
        elif choice == '6':
            log.info("SHUTDOWN: Script dihentikan oleh user via Menu.")
            clear_screen()
            sys.exit(0)
            
