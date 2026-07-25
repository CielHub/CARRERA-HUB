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

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def run_auto_rejoiner():
    clear_screen()
    print("=================================")
    print("    MENJALANKAN AUTO REJOINER    ")
    print("=================================\n")
    
    config_data = load_config("config.conf")
    timeout_seconds = config_data.get("TIMEOUT_SECONDS", 45)
    delay_seconds = config_data.get("DELAY_SECONDS", 3)
    max_retries = config_data.get("MAX_RETRIES", 3)
    cooldown_secs = config_data.get("COOLDOWN_SECONDS", 300)
    
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    packages = get_roblox_packages()
    
    # [PHASE 5] Penambahan kunci stats baru
    stats = {}
    for pkg in packages:
        stats[pkg] = {
            'pid': '-', 'status': 'OFFLINE', 'uptime_start': 0,
            'launch_count': 0, 'recovery_count': 0, 'crash_count': 0,
            'consecutive_crashes': 0, 'last_recovery_time': time.time(), 'cooldown_until': 0
        }
    
    for pkg in packages:
        stats[pkg]['status'] = 'LOADING'
        stats[pkg]['launch_count'] += 1
        
        success = launch_and_wait(pkg, intent_url, timeout_seconds)
        if success:
            stats[pkg]['status'] = 'ONLINE'
            stats[pkg]['uptime_start'] = time.time()
        else:
            stats[pkg]['status'] = 'FAILED'
            
        time.sleep(delay_seconds)
        
    start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats)

def show_settings():
    config_data = load_config("config.conf")
    
    while True:
        clear_screen()
        print("=================================")
        print("          MENU SETTINGS          ")
        print("=================================")
        
        link = config_data.get('PRIVATE_SERVER_LINK', '')
        display_link = link[:25] + "..." if len(link) > 25 else link
        
        print(f"1. Edit Private Server Link [{display_link}]")
        print(f"2. Edit Timeout Smart Wait  [{config_data.get('TIMEOUT_SECONDS', 45)}s]")
        print(f"3. Edit Delay Antar Package [{config_data.get('DELAY_SECONDS', 3)}s]")
        print(f"4. Edit Max Retries         [{config_data.get('MAX_RETRIES', 3)} kali]")
        print(f"5. Edit Cooldown Recovery   [{config_data.get('COOLDOWN_SECONDS', 300)}s]")
        print("6. Simpan Config")
        print("7. Kembali")
        print("=================================")
        
        choice = input("Pilih menu (1-7): ")
        
        if choice == '1':
            new_link = input("Masukkan Private Server Link baru: ")
            if new_link.strip(): config_data['PRIVATE_SERVER_LINK'] = new_link.strip()
        elif choice == '2':
            new_timeout = input("Masukkan Timeout (detik): ")
            if new_timeout.isdigit(): config_data['TIMEOUT_SECONDS'] = int(new_timeout)
        elif choice == '3':
            new_delay = input("Masukkan Delay (detik): ")
            if new_delay.isdigit(): config_data['DELAY_SECONDS'] = int(new_delay)
        elif choice == '4':
            new_retries = input("Masukkan Max Retries: ")
            if new_retries.isdigit(): config_data['MAX_RETRIES'] = int(new_retries)
        elif choice == '5':
            new_cooldown = input("Masukkan Cooldown (detik): ")
            if new_cooldown.isdigit(): config_data['COOLDOWN_SECONDS'] = int(new_cooldown)
        elif choice == '6':
            save_config(config_data, "config.conf")
            input("\n[+] Config berhasil disimpan! Tekan Enter untuk lanjut...")
        elif choice == '7':
            break

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
            print("\n[INFO] Menu Test akan diimplementasikan pada Phase 6.")
            input("Tekan Enter untuk kembali...")
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
            
