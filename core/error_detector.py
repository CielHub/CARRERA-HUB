"""
Modul: error_detector.py
Tanggung Jawab: Membaca logcat secara real-time dengan parameter native -e untuk mendeteksi error in-game yang akurat.
"""
import subprocess
import threading
import re
import time
import os

# Disesuaikan setelah debugging: Menghapus string HTTP cURL umum seperti "connection timed out" 
# dan "lost connection" untuk mencegah False Positive. Hanya fokus ke Error Code Roblox asli.
LOGCAT_PATTERN = "(?i)(error code: 266|error code: 267|error code: 277|error code: 279|error code: 280|kicked by server|disconnected from game)"
DEBUG_LOG_FILE = "logs/error_debug.log"

def write_debug(msg):
    """Menulis log debugging ke file terpisah secara aman tanpa mengganggu stdout terminal."""
    os.makedirs("logs", exist_ok=True)
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def _logcat_watcher(stats):
    """Worker daemon yang membaca logcat OS secara efisien dan real-time."""
    subprocess.run(['su', '-c', 'logcat -c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cmd = ['su', '-c', f'logcat -v brief -e "{LOGCAT_PATTERN}"']
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, bufsize=1)
        
        for line in process.stdout:
            match = re.search(r'\(\s*(\d+)\)', line)
            if match:
                pid = str(match.group(1))
                
                for pkg, data in stats.items():
                    if data.get('pid') == pid and data.get('status') == 'ONLINE':
                        matched_str = re.search(LOGCAT_PATTERN, line)
                        match_val = matched_str.group(0) if matched_str else "UNKNOWN"
                        
                        # Catat bukti event yang valid ke file debug
                        write_debug(f"VALID EVENT DETECTED | PKG: {pkg} | PID: {pid} | MATCHED: '{match_val}' | LOG ASLI: {line.strip()}")
                        
                        if not data.get('has_error'):
                            data['has_error'] = True
                        break
    except Exception as e:
        write_debug(f"WATCHER CRASH: {str(e)}")

def start_error_detector(stats):
    """Fungsi hook untuk dipanggil dari monitor.py"""
    write_debug("=== ERROR DETECTOR SENSOR STARTED (PRODUCTION MODE) ===")
    watcher_thread = threading.Thread(target=_logcat_watcher, args=(stats,), daemon=True)
    watcher_thread.start()
    
