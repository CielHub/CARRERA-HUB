"""
Modul: monitor.py
Tanggung Jawab: Memantau status proses (PID), Dashboard Real-time, dan memicu Recovery Pintar.
"""
import os
import subprocess
import time
import sys
from core.logger import log
from core.launcher import launch_and_wait

def get_pid(pkg_name):
    result = subprocess.run(f"pidof '{pkg_name}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def format_uptime(start_time):
    if start_time == 0:
        return "00:00:00"
    elapsed = int(time.time() - start_time)
    h = elapsed // 3600
    m = (elapsed % 3600) // 60
    s = elapsed % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def draw_dashboard(stats):
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

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None):
    log.info("MONITORING: Semua package diproses. Masuk ke mode penjagaan...")

    if stats is None:
        stats = {pkg: {
            'pid': '-', 'status': 'ONLINE', 'uptime_start': time.time(), 
            'launch_count': 1, 'recovery_count': 0, 'crash_count': 0,
            'consecutive_crashes': 0, 'last_recovery_time': time.time(), 'cooldown_until': 0
        } for pkg in packages}

    tracked_pids = {}
    for pkg in packages:
        pid = get_pid(pkg)
        tracked_pids[pkg] = pid
        stats[pkg]['pid'] = pid if pid else '-'

    check_interval = 15
    last_check_time = time.time()
    
    # Threshold kestabilan (5 menit tanpa crash = reset konter)
    STABILITY_THRESHOLD = 300 

    try:
        while True:
            current_time = time.time()
            
            if current_time - last_check_time >= check_interval:
                for pkg in packages:
                    # [PHASE 5] Cek masa Cooldown
                    if stats[pkg]['cooldown_until'] > current_time:
                        stats[pkg]['status'] = 'COOLDOWN'
                        stats[pkg]['pid'] = '-'
                        continue
                        
                    current_pid = get_pid(pkg)
                    
                    if not current_pid or current_pid != tracked_pids[pkg]:
                        stats[pkg]['crash_count'] += 1
                        stats[pkg]['consecutive_crashes'] += 1
                        
                        # [PHASE 5] Logika Max Retry dan Cooldown
                        if stats[pkg]['consecutive_crashes'] > max_retries:
                            log.error(f"COOLDOWN: {pkg} crash {max_retries} kali berturut-turut! Cooldown {cooldown_secs} detik.")
                            stats[pkg]['cooldown_until'] = current_time + cooldown_secs
                            stats[pkg]['status'] = 'COOLDOWN'
                            stats[pkg]['pid'] = '-'
                            draw_dashboard(stats)
                            continue

                        stats[pkg]['status'] = 'RECOVERY'
                        stats[pkg]['pid'] = '-'
                        draw_dashboard(stats)
                        
                        log.error(f"CRASH DETECTED: {pkg} terhenti!")
                        log.info(f"RECOVERY: Percobaan pemulihan {stats[pkg]['consecutive_crashes']}/{max_retries} untuk {pkg}...")
                        
                        # Eksekusi recovery dan tangkap return valuenya
                        success = launch_and_wait(pkg, intent_url, timeout_seconds)
                        
                        if success:
                            new_pid = get_pid(pkg)
                            tracked_pids[pkg] = new_pid
                            stats[pkg]['pid'] = new_pid if new_pid else '-'
                            stats[pkg]['recovery_count'] += 1
                            stats[pkg]['status'] = 'ONLINE'
                            stats[pkg]['uptime_start'] = time.time()
                            stats[pkg]['last_recovery_time'] = time.time()
                            log.info(f"RECOVERY SUCCESS: PID baru dicatat.")
                        else:
                            log.error(f"RECOVERY FAILED: {pkg} gagal dihidupkan.")
                            stats[pkg]['status'] = 'FAILED'
                            # Biarkan PID '-' dan akan dicoba lagi pada siklus berikutnya
                            
                    else:
                        stats[pkg]['pid'] = current_pid
                        if stats[pkg]['status'] == 'FAILED':
                            stats[pkg]['status'] = 'ONLINE'
                            
                        # [PHASE 5] Auto Reset Counter Kestabilan
                        if stats[pkg]['consecutive_crashes'] > 0:
                            if current_time - stats[pkg]['last_recovery_time'] > STABILITY_THRESHOLD:
                                log.info(f"STABILITY ACHIEVED: {pkg} stabil selama 5 menit. Reset counter crash.")
                                stats[pkg]['consecutive_crashes'] = 0
                
                last_check_time = time.time()

            draw_dashboard(stats)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Keluar dari mode monitoring...")
        time.sleep(1)
                        
