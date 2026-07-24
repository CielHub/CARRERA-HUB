"""
Modul: monitor.py
Tanggung Jawab: Memantau status proses (PID) dan memicu Recovery jika terjadi crash/hantu.
"""
import subprocess
import time
import sys
from core.launcher import launch_and_wait

def get_pid(pkg_name):
    """Mengambil PID dari package menggunakan pidof Android."""
    result = subprocess.run(f"pidof '{pkg_name}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def start_monitoring(packages, intent_url, timeout_seconds):
    """Sistem stateful monitoring untuk mencegah false positive dan proses hantu."""
    print("[+] SEMUA PACKAGE SELESAI DIPROSES.")
    print("[*] Masuk ke Mode Monitoring. Tekan CTRL+C untuk berhenti.")

    tracked_pids = {}

    # Catat PID masing-masing package sebelum masuk ke loop
    for pkg in packages:
        tracked_pids[pkg] = get_pid(pkg)

    try:
        while True:
            for pkg in packages:
                current_pid = get_pid(pkg)
                
                # Kondisi 1: Kosong (Mati), Kondisi 2: Berubah (Hantu)
                if not current_pid or current_pid != tracked_pids[pkg]:
                    print("")
                    print(f"[!] CRASH DETECTED: {pkg} terhenti atau berubah jadi proses hantu!")
                    print(f"[*] Menjalankan Recovery untuk {pkg}...")
                    
                    # Panggil recovery
                    launch_and_wait(pkg, intent_url, timeout_seconds)
                    
                    # Update array dengan PID baru setelah recovery
                    tracked_pids[pkg] = get_pid(pkg)
                    
                    print("[*] Recovery selesai. PID baru dicatat. Kembali memantau...")
                    
            print(".", end="", flush=True)
            time.sleep(15)
            
    except KeyboardInterrupt:
        print("\n[*] Script dihentikan oleh user.")
        sys.exit(0)
      
