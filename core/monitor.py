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

# [UI UPGRADE]
from core.ui import console, get_header
from rich.live import Live
from rich.table import Table
from rich.console import Group
from rich.text import Text
from rich import box

def get_pid(pkg_name):
    try:
        result = subprocess.run(['pidof', pkg_name], capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return ""

def format_uptime(start_time, current_time):
    if start_time == 0: return "00:00:00"
    elapsed = int(current_time - start_time)
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def draw_dashboard(stats, current_time, pkg_count):
    """Membangun layout Tabel dan Header untuk Live Dashboard."""
    header = get_header(package_count=str(pkg_count), status="Monitoring")
    
    table = Table(box=box.ASCII, expand=True, border_style="bold white")
    table.add_column("PACKAGE", justify="left", style="white")
    table.add_column("PID", justify="center", style="cyan")
    table.add_column("STATUS", justify="center", style="bold")
    table.add_column("UPTIME", justify="center", style="white")
    table.add_column("L", justify="center", style="dim white")
    table.add_column("R", justify="center", style="dim white")
    table.add_column("C", justify="center", style="dim white")

    for pkg, s in stats.items():
        uptime_str = format_uptime(s['uptime_start'], current_time) if s['status'] == 'ONLINE' else "--:--:--"
        
        # Color mapping berdasarkan ketentuan
        status_color = "green"
        if s['status'] == 'LOADING': status_color = "yellow"
        elif s['status'] == 'RECOVERY': status_color = "blue"
        elif s['status'] == 'FAILED': status_color = "red"
        elif s['status'] == 'COOLDOWN': status_color = "magenta"
        
        status_formatted = f"[{status_color}]{s['status']}[/]"
        
        table.add_row(
            pkg,
            str(s['pid']),
            status_formatted,
            uptime_str,
            str(s['launch_count']),
            str(s['recovery_count']),
            str(s['crash_count'])
        )
        
    footer = Text.from_markup(
        "\n[dim]Keterangan: L = Launch Count, R = Recovery Count, C = Crash Count[/]\n"
        "[bold yellow]Tekan CTRL+C untuk menghentikan monitoring dan kembali ke Menu Utama.[/]", 
        justify="center"
    )
    
    return Group(header, table, footer)

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None):
    log.info("MONITORING: Semua package diproses. Masuk ke mode penjagaan...")

    current_time = time.time()
    pkg_count = len(packages)
    
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

    # [UI UPGRADE] Membungkus loop dengan Live renderer
    with Live(draw_dashboard(stats, current_time, pkg_count), console=console, refresh_per_second=1, transient=False) as live:
        try:
            while True:
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
                                continue

                            stats[pkg]['status'] = 'RECOVERY'
                            stats[pkg]['pid'] = '-'
                            # Update UI sebelum memanggil fungsi blocking launch_and_wait
                            live.update(draw_dashboard(stats, current_time, pkg_count))
                            
                            log.error(f"CRASH DETECTED: {pkg} terhenti!")
                            log.info(f"RECOVERY: Percobaan pemulihan {stats[pkg]['consecutive_crashes']}/{max_retries} untuk {pkg}...")
                            
                            success = launch_and_wait(pkg, intent_url, timeout_seconds)
                            current_time = time.time() # Resync waktu 
                            
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

                # Refresh UI per detik
                live.update(draw_dashboard(stats, current_time, pkg_count))
                time.sleep(1)
                
        except KeyboardInterrupt:
            # Tidak mencetak error, langsung kembali ke menu
            pass
            
