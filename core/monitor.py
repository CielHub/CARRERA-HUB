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

# [PHASE 7 OPTIMIZATION]
# Variabel statis: hitung operasi 'clear' satu kali saja (tidak diulang tiap detik)
CLEAR_CMD = 'clear' if os.name == 'posix' else 'cls'

def get_pid(pkg_name):
    # [PHASE 7 OPTIMIZATION] shell=False
    try:
        result = subprocess.run(['pidof', pkg_name], capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return ""

def format_uptime(start_time, current_time):
    # [PHASE 7 OPTIMIZATION] Gunakan current_time parameter, gunakan divmod
    if start_time == 0:
        return "00:00:00"
    elapsed = int(current_time - start_time)
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def draw_dashboard(stats, current_time):
    # [PHASE 7 OPTIMIZATION]
    # Buffered I/O: Menyatukan semua output ke dalam satu List lalu di print sekali.
    # Sangat mengurangi CPU time terminal dan mencegah layar berkedip (flickering).
    output = []
    output.append("===============================================================================")
    output.append("                      CARRERA-HUB REAL-TIME DASHBOARD                          ")
    output.append("===============================================================================")
    output.append(f"{'PACKAGE':<25} | {'PID':<7} | {'STATUS':<10} | {'UPTIME':<8} | {'L':<3} | {'R':<3} | {'C':<3}")
    output.append("-" * 79)
    
    for pkg, s in stats.items():
        uptime_str = format_uptime(s['uptime_start'], current_time) if s['status'] == 'ONLINE' else "--:--:--"
        output.append(f"{pkg:<25} | {s['pid']:<7} | {s['status']:<10} | {uptime_str:<8} | {s['launch_count']:<3} | {s['recovery_count']:<3} | {s['crash_count']:<3}")
        
    output.append("===============================================================================")
    output.append(" Keterangan: L = Launch Count, R = Recovery Count, C = Crash Count")
    output.append(" Tekan CTRL+C untuk menghentikan monitoring dan kembali ke Menu Utama.")
    output.append("===============================================================================")
    
    os.system(CLEAR_CMD)
    print('\n'.join(output))

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None):
    log.info("MONITORING: Semua package diproses. Masuk ke mode penjagaan...")

    current_time = time.time()
    
    if stats is None:
        stats = {pkg: {
            'pid': '-', 'status': 'ONLINE', 'uptime_start': current_time, 
            'launch_count': 1, 'recovery_count': 0, 'crash_count': 0,
            'consecutive_crashes': 0, 'last_recovery_time': current_time, 'cooldown_until': 0
        } for pkg in packages}

    tracked_pids = {}
    for pkg in packages:
        pid = get_pid(pkg)
        tracked_pids[pkg] = pid
        stats[pkg]['pid'] = pid if pid else '-'

    check_interval = 15
    last_check_time = current_time
    STABILITY_THRESHOLD = 300 

    try:
        while True:
            # [PHASE 7 OPTIMIZATION] Panggil time.time() cukup 1 kali di awal loop
            current_time = time.time()
            
            if current_time - last_check_time >= check_interval:
                for pkg in packages:
                    if stats[pkg]['cooldown_until'] > current_time:
                        stats[pkg]['status'] = 'COOLDOWN'
                        stats[pkg]['pid'] = '-'
                        continue
                        
                    current_pid = get_pid(pkg)
                    
                    if not current_pid or current_pid != tracked_pids[pkg]:
                        stats[pkg]['crash_count'] += 1
                        stats[pkg]['consecutive_crashes'] += 1
                        
                        if stats[pkg]['consecutive_crashes'] > max_retries:
                            log.error(f"COOLDOWN: {pkg} crash {max_retries} kali berturut-turut! Cooldown {cooldown_secs} detik.")
                            stats[pkg]['cooldown_until'] = current_time + cooldown_secs
                            stats[pkg]['status'] = 'COOLDOWN'
                            stats[pkg]['pid'] = '-'
                            draw_dashboard(stats, current_time)
                            continue

                        stats[pkg]['status'] = 'RECOVERY'
                        stats[pkg]['pid'] = '-'
                        draw_dashboard(stats, current_time)
                        
                        log.error(f"CRASH DETECTED: {pkg} terhenti!")
                        log.info(f"RECOVERY: Percobaan pemulihan {stats[pkg]['consecutive_crashes']}/{max_retries} untuk {pkg}...")
                        
                        success = launch_and_wait(pkg, intent_url, timeout_seconds)
                        # Re-sync waktu setelah operasi blocking panjang
                        current_time = time.time() 
                        
                        if success:
                            new_pid = get_pid(pkg)
                            tracked_pids[pkg] = new_pid
                            stats[pkg]['pid'] = new_pid if new_pid else '-'
                            stats[pkg]['recovery_count'] += 1
                            stats[pkg]['status'] = 'ONLINE'
                            stats[pkg]['uptime_start'] = current_time
                            stats[pkg]['last_recovery_time'] = current_time
                            log.info(f"RECOVERY SUCCESS: PID baru dicatat.")
                        else:
                            log.error(f"RECOVERY FAILED: {pkg} gagal dihidupkan.")
                            stats[pkg]['status'] = 'FAILED'
                            
                    else:
                        stats[pkg]['pid'] = current_pid
                        if stats[pkg]['status'] == 'FAILED':
                            stats[pkg]['status'] = 'ONLINE'
                            
                        if stats[pkg]['consecutive_crashes'] > 0:
                            if current_time - stats[pkg]['last_recovery_time'] > STABILITY_THRESHOLD:
                                log.info(f"STABILITY ACHIEVED: {pkg} stabil selama 5 menit. Reset counter crash.")
                                stats[pkg]['consecutive_crashes'] = 0
                
                last_check_time = current_time

            # Kirim current_time ke fungsi dashboard
            draw_dashboard(stats, current_time)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Keluar dari mode monitoring...")
        time.sleep(1)
                            
