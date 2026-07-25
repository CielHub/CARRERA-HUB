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

from core.ui import console, get_compact_header, reset_terminal
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
    """Membangun layout Tabel Fixed-Width yang sangat compact."""
    header = get_compact_header(pkg_count=str(pkg_count), status="Monitoring")
    
    # expand=False agar tabel tidak melebar mengikuti terminal, mengunci layout
    table = Table(box=box.SIMPLE_HEAD, expand=False, show_edge=False, pad_edge=False)
    
    # Menetapkan lebar pasti (fixed width) setiap kolom
    table.add_column("PACKAGE", width=18, justify="left", style="white")
    table.add_column("PID", width=7, justify="right", style="cyan")
    table.add_column("STATUS", width=12, justify="left")
    table.add_column("UPTIME", width=8, justify="right", style="white")
    table.add_column("L", width=3, justify="right", style="dim white")
    table.add_column("R", width=3, justify="right", style="dim white")
    table.add_column("C", width=3, justify="right", style="dim white")

    for pkg, s in stats.items():
        uptime_str = format_uptime(s['uptime_start'], current_time) if s['status'] == 'ONLINE' else "--:--:--"
        
        # Potong 'com.roblox.' agar tampilan lebih bersih
        display_pkg = pkg.replace("com.roblox.", "..") if "com.roblox." in pkg else pkg
        
        # Logika warna dan highlight baris
        row_style = ""
        if s['status'] == 'ONLINE':
            stat_fmt = "[bold green]● ONLINE[/]"
        elif s['status'] == 'LOADING':
            stat_fmt = "[bold yellow]● LOADING[/]"
            row_style = "dim"
        elif s['status'] == 'RECOVERY':
            stat_fmt = "[bold blue]● RECOVERY[/]"
            row_style = "blue"
        elif s['status'] == 'FAILED':
            stat_fmt = "[bold red]● FAILED[/]"
            row_style = "red"
        elif s['status'] == 'COOLDOWN':
            stat_fmt = "[bold magenta]● COOLDOWN[/]"
            row_style = "magenta"
        else:
            stat_fmt = f"[white]● {s['status']}[/]"

        table.add_row(
            display_pkg, str(s['pid']), stat_fmt, uptime_str,
            str(s['launch_count']), str(s['recovery_count']), str(s['crash_count']),
            style=row_style
        )
        
    footer = Text.from_markup(
        "\n[dim white]L=Launch  R=Recovery  C=Crash   |   [bold yellow]CTRL+C: Menu Utama[/][/]", 
        justify="center"
    )
    
    return Group(header, Text(""), table, footer)

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None):
    log.info("MONITORING: Semua package selesai diproses. Memasuki mode penjagaan...")
    time.sleep(1)
    reset_terminal()

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
                            live.update(draw_dashboard(stats, current_time, pkg_count))
                            
                            log.error(f"CRASH DETECTED: {pkg} terhenti!")
                            log.info(f"RECOVERY: Percobaan pemulihan {stats[pkg]['consecutive_crashes']}/{max_retries} untuk {pkg}...")
                            
                            success = launch_and_wait(pkg, intent_url, timeout_seconds)
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

                live.update(draw_dashboard(stats, current_time, pkg_count))
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
                                
