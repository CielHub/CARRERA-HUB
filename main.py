"""
Modul: main.py
Tanggung Jawab: Entry point utama, menangani Auto Root, dan Orkestrasi Modul.
"""
import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from core.logger import log  # Import logger
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
            print("[!] Gagal mendapatkan akses Root. Pastikan HP sudah di-root.")
            sys.exit(1)
            
        sys.exit(0)

def main():
    """Fungsi Orkestrasi Utama."""
    os.chdir(SCRIPT_DIR)
    ensure_root()
    
    # [LOG STARTUP]
    log.info("STARTUP: Menginisialisasi CARRERA-HUB Auto Rejoiner...")
    
    config_data = load_config("config.conf")
    timeout_seconds = config_data["TIMEOUT_SECONDS"]
    
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    log.info(f"Target Intent: {intent_url}")
    
    packages = get_roblox_packages()
    
    for pkg in packages:
        launch_and_wait(pkg, intent_url, timeout_seconds)
        time.sleep(3)
        
    start_monitoring(packages, intent_url, timeout_seconds)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("") # Jarak enter
        # [LOG SHUTDOWN]
        log.info("SHUTDOWN: Script dihentikan oleh user (CTRL+C).")
        sys.exit(0)
        
