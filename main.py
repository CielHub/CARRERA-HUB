"""
Modul: main.py
Tanggung Jawab: Entry point utama, menangani Auto Root, dan Orkestrasi Modul.
"""
import os
import sys
import subprocess
import time

# Tambahkan absolute path project ke system path agar import core/ berfungsi
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from core.config import load_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import start_monitoring

def ensure_root():
    """Memastikan script berjalan di bawah environment Root."""
    try:
        uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
    except Exception:
        uid = os.geteuid()

    if uid != 0:
        print("[*] Script ini membutuhkan akses Root untuk bekerja.")
        print("[*] Meminta izin Root ke sistem...")
        
        python_bin = sys.executable
        cmd = f"su -c \"{python_bin} '{os.path.join(SCRIPT_DIR, 'main.py')}'\""
        exit_code = subprocess.call(cmd, shell=True)
        
        if exit_code != 0:
            print("-" * 48)
            print("[!] Gagal mendapatkan akses Root.")
            sys.exit(1)
            
        sys.exit(0)

def main():
    """Fungsi Orkestrasi Utama."""
    # 0. Set direktori & Auto Root
    os.chdir(SCRIPT_DIR)
    ensure_root()
    
    # 1. Load Config
    config_data = load_config("config.conf")
    timeout_seconds = config_data["TIMEOUT_SECONDS"]
    
    # 2. Parse Deep Link
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    print("[+] Target Intent yang akan dieksekusi:")
    print(f"    -> {intent_url}")
    print("-" * 48)
    
    # 3. Scan Packages
    packages = get_roblox_packages()
    
    # 4. Eksekusi Sequential
    for pkg in packages:
        launch_and_wait(pkg, intent_url, timeout_seconds)
        time.sleep(3)
        
    # 5. Mulai Monitoring
    start_monitoring(packages, intent_url, timeout_seconds)

if __name__ == "__main__":
    main()
  
