"""
Modul: error_detector.py
Tanggung Jawab: Membaca logcat secara real-time dengan parameter native -e untuk mendeteksi error in-game.
"""
import subprocess
import threading
import re
from core.logger import log

# Menggunakan regex pattern untuk parameter -e pada logcat (Case-Insensitive)
LOGCAT_PATTERN = "(?i)(error code: 266|error code: 267|error code: 277|error code: 279|error code: 280|kicked by server|connection timed out|lost connection|disconnected from game)"

def _logcat_watcher(stats):
    """Worker daemon yang membaca logcat OS secara efisien dan real-time."""
    # Membersihkan buffer logcat lama
    subprocess.run(['su', '-c', 'logcat -c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # NATIVE FILTERING: Menggunakan parameter -e agar 100% real-time tanpa pipe blocking OS
    cmd = ['su', '-c', f'logcat -v brief -e "{LOGCAT_PATTERN}"']
    
    try:
        # bufsize=1 dan universal_newlines=True untuk membaca line-by-line secara instan
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, bufsize=1)
        
        for line in process.stdout:
            # Ekstrak PID dari logcat dengan Regex
            match = re.search(r'\(\s*(\d+)\)', line)
            if match:
                pid = str(match.group(1))
                
                # Cek apakah PID ini milik salah satu package Roblox kita yang sedang ONLINE
                for pkg, data in stats.items():
                    if data.get('pid') == pid and data.get('status') == 'ONLINE':
                        if not data.get('has_error'):
                            log.error(f"ERROR DETECTOR: Terdeteksi in-game error untuk {pkg} (PID: {pid}).")
                            data['has_error'] = True
                        break
    except Exception as e:
        log.error(f"ERROR DETECTOR: Logcat watcher crash - {str(e)}")

def start_error_detector(stats):
    """Fungsi hook untuk dipanggil dari monitor.py"""
    log.info("ERROR DETECTOR: Memulai OS-level pemantauan logcat di latar belakang...")
    watcher_thread = threading.Thread(target=_logcat_watcher, args=(stats,), daemon=True)
    watcher_thread.start()
    
