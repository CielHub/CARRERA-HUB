"""
Modul: error_detector.py
Tanggung Jawab: Membaca logcat secara real-time untuk mendeteksi error in-game Roblox.
"""
import subprocess
import threading
import re
from core.logger import log

# Daftar kata kunci error yang sering dilemparkan oleh engine Roblox
ERROR_KEYWORDS = [
    "error code: 266",
    "error code: 267",
    "error code: 277",
    "error code: 279",
    "error code: 280",
    "kicked by server",
    "connection timed out",
    "lost connection",
    "disconnected from game"
]

def _logcat_watcher(stats):
    """Worker daemon yang membaca logcat OS baris-demi-baris secara efisien."""
    # Membersihkan buffer logcat lama agar tidak membaca error dari sesi sebelumnya
    subprocess.run(['su', '-c', 'logcat -c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Menjalankan stream logcat. Format brief: "I/Tag( PID): Message"
    cmd = ['su', '-c', 'logcat -v brief']
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True, bufsize=1)
        
        for line in process.stdout:
            line_lower = line.lower()
            
            # Deteksi string cepat (Low CPU Cost) sebelum menggunakan Regex
            if any(kw in line_lower for kw in ERROR_KEYWORDS):
                # Ekstrak PID dari logcat dengan Regex
                match = re.search(r'\(\s*(\d+)\)', line)
                if match:
                    pid = str(match.group(1))
                    
                    # Cek apakah PID ini milik salah satu package Roblox kita yang sedang ONLINE
                    for pkg, data in stats.items():
                        if data.get('pid') == pid and data.get('status') == 'ONLINE':
                            # Jika belum ditandai error, tandai sekarang
                            if not data.get('has_error'):
                                log.error(f"ERROR DETECTOR: Terdeteksi in-game error untuk {pkg} (PID: {pid}).")
                                data['has_error'] = True
                            break
    except Exception as e:
        log.error(f"ERROR DETECTOR: Logcat watcher crash - {str(e)}")

def start_error_detector(stats):
    """Fungsi hook untuk dipanggil dari monitor.py"""
    log.info("ERROR DETECTOR: Memulai pemantauan logcat di latar belakang...")
    watcher_thread = threading.Thread(target=_logcat_watcher, args=(stats,), daemon=True)
    watcher_thread.start()
  
