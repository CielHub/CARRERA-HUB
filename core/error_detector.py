"""
Modul: error_detector.py
Tanggung Jawab: Membaca logcat menggunakan metode Periodic Snapshot (Polling) agar tidak merusak UI Terminal.
"""
import subprocess
import threading
import re
import time

# REGEX BARU: Menggunakan kata kunci emas langsung dari Network Engine C++ Roblox
LOGCAT_PATTERN = "(?i)(reason: 266|reason: 267|reason: 277|reason: 279|reason: 280|requests player disconnect)"

def _logcat_watcher(stats):
    """Worker daemon yang bangun setiap 5 detik untuk mengecek log, lalu tidur kembali."""
    # 1. Bersihkan sisa logcat OS di awal
    subprocess.run(['su', '-c', 'logcat -c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    while True:
        # 2. Fase Tidur: Biarkan UI rich.live merender dengan tenang tanpa interupsi
        time.sleep(5) 
        
        # 3. Fase Snapshot: Ambil dump logcat saat ini lalu langsung tutup (parameter -d)
        cmd = ['su', '-c', f'logcat -d -v brief -e "{LOGCAT_PATTERN}"']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
            
            # 4. Fase Analisis: Jika ada teks log yang tertangkap
            if output and output.strip():
                lines = output.strip().split('\n')
                for line in lines:
                    # Ekstrak PID
                    match = re.search(r'\(\s*(\d+)\)', line)
                    if match:
                        pid = str(match.group(1))
                        
                        # Cocokkan dengan package kita yang sedang ONLINE
                        for pkg, data in stats.items():
                            if data.get('pid') == pid and data.get('status') == 'ONLINE':
                                if not data.get('has_error'):
                                    
                                    # Tandai error secara silent (tanpa print/log ke terminal)
                                    data['has_error'] = True
                                    
                                    # Segera bersihkan logcat agar error ini tidak terbaca dobel di siklus berikutnya
                                    subprocess.run(['su', '-c', 'logcat -c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                break
        except Exception:
            # Silent fail: abaikan error Python agar tidak mencetak apapun ke terminal
            pass

def start_error_detector(stats):
    """Fungsi hook untuk dihidupkan dari monitor.py"""
    watcher_thread = threading.Thread(target=_logcat_watcher, args=(stats,), daemon=True)
    watcher_thread.start()
    
