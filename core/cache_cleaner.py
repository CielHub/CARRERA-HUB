"""
Modul: cache_cleaner.py
Tanggung Jawab: Membersihkan cache package di background sebagai daemon service, 
                tanpa mengganggu arsitektur Monitoring atau UI Dashboard.
"""
import time
import subprocess
import threading
from core.logger import log

def cache_cleaner_worker(packages, stats, interval_minutes):
    interval_seconds = interval_minutes * 60
    log.info(f"CACHE CLEANER: Service berjalan di background (Interval: {interval_minutes} menit).")
    
    while True:
        # 1. Tidur dulu sesuai interval sebelum pembersihan pertama
        time.sleep(interval_seconds)
        
        log.info("CACHE CLEANER: Memulai siklus pembersihan cache...")
        for pkg in packages:
            # 2. Skip jika package sedang sibuk (LOADING, RECOVERY, COOLDOWN, dll)
            if stats.get(pkg, {}).get('status') != 'ONLINE':
                log.info(f"CACHE CLEANER: Melewati {pkg} (Status bukan ONLINE).")
                continue
                
            # 3. Eksekusi pembersihan secara silent (output dialihkan ke DEVNULL)
            try:
                cmd = f"su -c 'rm -rf /data/data/{pkg}/cache/* && rm -rf /data/data/{pkg}/code_cache/*'"
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log.info(f"CACHE CLEANER: Berhasil membersihkan memori untuk {pkg}.")
            except Exception as e:
                log.error(f"CACHE CLEANER: Gagal membersihkan memori untuk {pkg} - {str(e)}")
            
            # 4. Beri delay antar package agar storage I/O tidak melonjak (spike)
            time.sleep(2)

def start_cache_cleaner_service(packages, stats, interval_minutes):
    """
    Fungsi trigger untuk meluncurkan worker thread. 
    Akan mati secara otomatis ketika script utama dihentikan (daemon=True).
    """
    if interval_minutes <= 0:
        log.info("CACHE CLEANER: Service dinonaktifkan karena interval diatur ke 0.")
        return

    thread = threading.Thread(
        target=cache_cleaner_worker,
        args=(packages, stats, interval_minutes),
        daemon=True
    )
    thread.start()
  
