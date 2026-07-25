"""
Modul: monitor.py
Tanggung Jawab: Memantau status proses (PID), Dashboard Real-time, dan memicu Recovery.
"""
import os
import subprocess
import time
import sys
from core.logger import log
from core.launcher import launch_and_wait

def get_pid(pkg_name):
    """Mengambil PID dari package menggunakan pidof Android."""
    result = subprocess.run(f"pidof '{pkg_name}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def format_uptime(start_time):
    """Mengonversi detik menjadi format HH:MM:SS."""
    if start_time == 0:
        return "00:00:00"
    elapsed = int(time.time() - start_time)
    h = elapsed // 3600
    m = (elapsed % 3600) // 60
    s = elapsed % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def draw_dashboard(stats):
    """Merender antarmuka dashboard ke layar terminal."""
    os.system('clear' if os.name == 'posix' else 'cls')
    print("===============================================================================")
    print("                      CARRERA-HUB REAL-TIME DASHBOARD                          ")
    print("===============================================================================")
    print(f"{'PACKAGE':<25} | {'PID':<7} | {'STATUS':<10} | {'UPTIME':<8} | {'L':<3} | {'R':<3} | {'C':<3}")
    print("-" * 79)
    
    for pkg, s in stats.items():
        uptime_str = format_uptime(s['uptime_start']) if s['status'] == 'ONLINE' else "--:--:--"
        print(f"{pkg:<25} | {s['pid']:<7} | {s['status']:<10} | {uptime_str:<8} | {s['launch_count']:<3} | {s['recovery_count']:<3} | {s['crash_count']:<3}")
        
    print("===============================================================================")
    print(" Keterangan: L = Launch Count, R = Recovery Count, C = Crash Count")
    print(" Tekan CTRL+C untuk menghentikan monitoring dan kembali ke Menu Utama.")
    print("===============================================================================")

def start_monitoring(packages, intent_url, timeout_seconds, stats=None):
    """Sistem stateful monitoring dengan UI Dashboard Real-time."""
    log.info("MONITORING: Semua package diproses. Masuk ke mode penjagaan...")

    # Jika dipanggil tanpa stats (fallback), buat instance baru
    if stats is None:
        stats = {pkg: {'pid': '-', 'status': 'ONLINE', 'uptime_start': time.time(), 'launch_count': 1, 'recovery_count': 0, 'crash_count': 0} for pkg in packages}

    tracked_pids = {}
    for pkg in packages:
        pid = get_pid(pkg)
        tracked_pids[pkg] = pid
        stats[pkg]['pid'] = pid if pid else '-'

    check_interval = 15  # Cek PID setiap 15 detik
    last_check_time = time.time()

    try:
        while True:
            current_time = time.time()
            
            # [LOGIKA MONITORING UTAMA] Hanya dieksekusi setiap 15 detik
            if current_time - last_check_time >= check_interval:
                for pkg in packages:
                    current_pid = get_pid(pkg)
                    
                    if not current_pid or current_pid != tracked_pids[pkg]:
                        # Update status dashboard sebelum melakukan recovery (blocking)
                        stats[pkg]['crash_count'] += 1
                        stats[pkg]['status'] = 'RECOVERY'
                        stats[pkg]['pid'] = '-'
                        draw_dashboard(stats)
                        
                        log.error(f"CRASH DETECTED: {pkg} terhenti atau berubah jadi proses hantu!")
                        log.info(f"RECOVERY: Menjalankan pemulihan untuk {pkg}...")
                        
                        # Eksekusi recovery (Proses ini menahan loop sampai selesai)
                        launch_and_wait(pkg, intent_url, timeout_seconds)
                        
                        # Setel ulang state setelah recovery berhasil
                        new_pid = get_pid(pkg)
                        tracked_pids[pkg] = new_pid
                        stats[pkg]['pid'] = new_pid if new_pid else '-'
                        stats[pkg]['recovery_count'] += 1
                        stats[pkg]['status'] = 'ONLINE'
                        stats[pkg]['uptime_start'] = time.time()
                        
                        log.info(f"RECOVERY SUCCESS: PID baru dicatat. Kembali memantau...")
                    else:
                        # Jaga-jaga update PID kalau sempat tidak sinkron
                        stats[pkg]['pid'] = current_pid
                
                last_check_time = time.time()

            # [UI REFRESH] Render layar setiap 1 detik
            draw_dashboard(stats)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Keluar dari mode monitoring...")
        # Tidak sys.exit agar kembali ke Menu Utama
        time.sleep(1)
                        
