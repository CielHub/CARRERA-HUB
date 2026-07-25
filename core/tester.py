"""
Modul: tester.py
Tanggung Jawab: Menyediakan framework pengujian (Unit Test) untuk setiap modul secara terisolasi.
"""
import os
import subprocess
import time
from core.logger import log
from core.config import load_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import get_pid

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def pause():
    input("\n[+] Tekan Enter untuk kembali ke Menu Test...")

def test_root():
    print("--- TEST ROOT ---")
    try:
        uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
    except Exception:
        import os
        uid = os.geteuid()
        
    print(f"Current UID: {uid}")
    if uid == 0:
        print("[OK] Sistem berjalan sebagai Root.")
    else:
        print("[FAIL] Sistem TIDAK berjalan sebagai Root.")
    pause()

def test_config():
    print("--- TEST CONFIG ---")
    config_data = load_config("config.conf")
    for key, value in config_data.items():
        print(f"{key}: {value}")
    print("[OK] Config berhasil dibaca.")
    pause()

def test_logger():
    print("--- TEST LOGGER ---")
    print("Menulis pesan test ke dalam log...")
    log.info("TESTING: Ini adalah pesan uji coba dari modul tester.py")
    log.warning("TESTING: Ini adalah pesan warning.")
    log.error("TESTING: Ini adalah pesan error.")
    print("[OK] Silakan cek file logs/latest.log untuk melihat hasilnya.")
    pause()

def test_scanner():
    print("--- TEST SCANNER ---")
    packages = get_roblox_packages()
    if packages:
        print("[OK] Scanner berfungsi dan menemukan package.")
    pause()

def test_deeplink():
    print("--- TEST DEEP LINK ---")
    config_data = load_config("config.conf")
    link = config_data.get("PRIVATE_SERVER_LINK", "")
    print(f"Link Asli: {link}")
    intent_url = get_intent_url(link)
    print(f"Intent URL: {intent_url}")
    if intent_url:
        print("[OK] Deep Link konversi berhasil.")
    pause()

def test_launcher():
    print("--- TEST LAUNCHER ---")
    packages = get_roblox_packages()
    if not packages:
        print("[!] Tidak ada package untuk dites.")
        pause()
        return
        
    pkg = packages[0]
    print(f"Akan melakukan test launch pada: {pkg}")
    config_data = load_config("config.conf")
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    
    print("\nMengeksekusi Launch & Smart Wait...")
    success = launch_and_wait(pkg, intent_url, config_data["TIMEOUT_SECONDS"])
    
    if success:
        print("\n[OK] Launcher mengembalikan nilai True (Sukses).")
    else:
        print("\n[FAIL] Launcher mengembalikan nilai False (Gagal).")
    pause()

def test_monitor():
    print("--- TEST MONITORING (PID CATCHER) ---")
    packages = get_roblox_packages()
    if not packages:
        print("[!] Tidak ada package untuk dites.")
        pause()
        return
        
    print("Mencari PID aktif untuk package yang terdeteksi:")
    for pkg in packages:
        pid = get_pid(pkg)
        if pid:
            print(f"[OK] {pkg} SEDANG BERJALAN (PID: {pid})")
        else:
            print(f"[INFO] {pkg} SEDANG MATI")
    pause()

def show_test_menu():
    """Menampilkan Sub-Menu Testing."""
    while True:
        clear_screen()
        print("=================================")
        print("       MENU UNIT TESTING         ")
        print("=================================")
        print("1. Test Root Access")
        print("2. Test Config Loader")
        print("3. Test Logger System")
        print("4. Test Package Scanner")
        print("5. Test Deep Link Converter")
        print("6. Test Launcher & Smart Wait")
        print("7. Test Monitor (PID Check)")
        print("8. Kembali ke Menu Utama")
        print("=================================")
        
        choice = input("Pilih test (1-8): ")
        
        clear_screen()
        if choice == '1': test_root()
        elif choice == '2': test_config()
        elif choice == '3': test_logger()
        elif choice == '4': test_scanner()
        elif choice == '5': test_deeplink()
        elif choice == '6': test_launcher()
        elif choice == '7': test_monitor()
        elif choice == '8': break
      
