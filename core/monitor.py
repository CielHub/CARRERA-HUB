"""
Modul: monitor.py
Tanggung Jawab: Memantau status proses (PID), Dashboard Real-time, dan memicu Recovery Pintar.
"""
import os
import subprocess
import time
import sys

try:
    import pyfiglet
except ImportError:
    pass

from core.logger import log
from core.launcher import launch_and_wait
from core.ui import console, reset_terminal
from rich.live import Live
from rich.table import Table
from rich.console import Group
from rich.text import Text

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

def draw_static_header(pkg_count):
    ascii_art = pyfiglet.figlet_format("CARRERA", font="slant")
    for line in ascii_art.split('\n'):
        if line.strip():
            console.print(f"[bold green]{line}[/]")
    
    info_text = f"Version 1.0.0   |   Status Monitoring   |   Packages {pkg_count}"
    console.print(f"[dim white]{info_text}[/]")
    
    DASHBOARD_WIDTH = 60
    console.print(f"[dim cyan]{'─' * DASHBOARD_WIDTH}[/]")

def draw_dashboard(stats, current_time, pkg_count):
    DASHBOARD_WIDTH = 60
    rule = Text.from_markup(f"[dim cyan]{'─' * DASHBOARD_WIDTH}[/]")
    
    running = sum(1 for s in stats.values() if s['status'] == 'ONLINE')
    recover = sum(1 for s in stats.values() if s['status'] in ['RECOVERY', 'LOGIN'])
    offline = sum(1 for s in stats.values() if s['status'] in ['FAILED', 'COOLDOWN', 'LOGIN FAILED', 'CAPTCHA'])
    
    summary_text = f"Clones {running}/{pkg_count}   |   [bold yellow]● Recover {recover}[/]   |   [bold red]● Offline {offline}[/]"
    summary_render = Text.from_markup(summary_text)

    table = Table(box=None, padding=(0, 1), show_header=True, header_style="dim white", expand=False)
    table.add_column("ID", style="bold cyan", width=3, no_wrap=True)
    table.add_column("PACKAGE", style="white", width=16, no_wrap=True, overflow="ellipsis") 
    table.add_column("PID", style="cyan", width=5, no_wrap=True)
    table.add_column("STATUS", width=12, no_wrap=True) 
    table.add_column("UPTIME", style="white", width=9, no_wrap=True) 
    table.add_column("L", style="dim white", width=2, justify="right", no_wrap=True)
    table.add_column("R", style="dim white", width=2, justify="right", no_wrap=True)
    table.add_column("C", style="dim white", width=2, justify="right", no_wrap=True)
    
    for idx, (pkg, s) in enumerate(stats.items(), 1):
        uptime_str = format_uptime(s['uptime_start'], current_time) if s['status'] == 'ONLINE' else "--:--:--"
        display_pkg = pkg.replace("com.roblox.", "..") if "com.roblox." in pkg else pkg
        
        if s['status'] == 'ONLINE': stat_fmt = "[bold green]● Farming[/]"
        elif s['status'] == 'LOADING': stat_fmt = "[bold blue]● Loading[/]"
        elif s['status'] == 'RECOVERY': stat_fmt = "[bold yellow]● Recover[/]"
        elif s['status'] == 'FAILED': stat_fmt = "[bold red]● Offline[/]"
        elif s['status'] == 'COOLDOWN': stat_fmt = "[bold red]● Cooldown[/]"
        elif s['status'] == 'LOGIN': stat_fmt = "[bold magenta]● Login[/]"
        elif s['status'] == 'LOGIN FAILED': stat_fmt = "[bold red]● Log Fail[/]"
        elif s['status'] == 'CAPTCHA': stat_fmt = "[bold red]● Captcha[/]"
        else: stat_fmt = f"[white]● {s['status'][:8]}[/]"
            
        table.add_row(
            f"[{idx}]", display_pkg, str(s['pid']), stat_fmt, uptime_str,
            str(s['launch_count']), str(s['recovery_count']), str(s['crash_count'])
        )
        
    footer_text = Text.from_markup("[dim white]CTRL+C Back to Menu   |   CTRL+Z Exit   |   Refresh: 1s[/]")
    
    renderables = [summary_render, rule, table, rule, footer_text]
    return Group(*renderables)

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None, config_data=None):
    log.info("MONITORING: Semua package diproses. Memasuki mode penjagaan...")
    time.sleep(1)
    reset_terminal()

    current_time = time.time()
    pkg_count = len(packages)
    
    draw_static_header(pkg_count)
    
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

    # --- INJEKSI CACHE CLEANER SERVICE ---
    clear_cache_mins = config_data.get('CLEAR_CACHE_MINUTES', 0) if config_data else 0
    from core.cache_cleaner import start_cache_cleaner_service
    start_cache_cleaner_service(packages, stats, clear_cache_mins)
    # -------------------------------------

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
                            
                            pkg_intent = intent_url[pkg] if isinstance(intent_url, dict) else intent_url
                            success = launch_and_wait(pkg, pkg_intent, timeout_seconds)
                            
                            # --- HOOK: AUTO LOGIN FALLBACK SAAT RECOVERY ---
                            if not success:
                                try:
                                    from core.autologin import run as run_autologin
                                    stats[pkg]['status'] = 'LOGIN'
                                    live.update(draw_dashboard(stats, current_time, pkg_count))
                                    
                                    login_status = run_autologin(pkg)
                                    
                                    if login_status in ["SUCCESS", "ALREADY_LOGGED_IN"]:
                                        if login_status == "ALREADY_LOGGED_IN":
                                            log.info(f"AUTO LOGIN: {pkg} sudah login. Melanjutkan Join Private Server...")
                                        else:
                                            log.info(f"AUTO LOGIN SUCCESS: Berhasil masuk ke Home. Melanjutkan Join Private Server untuk {pkg}...")
                                            
                                        stats[pkg]['status'] = 'LOADING'
                                        live.update(draw_dashboard(stats, current_time, pkg_count))
                                        
                                        success = launch_and_wait(pkg, pkg_intent, timeout_seconds)
                                    elif login_status == "CAPTCHA":
                                        log.warning(f"AUTO LOGIN CAPTCHA: Terdeteksi Captcha untuk {pkg}.")
                                        stats[pkg]['status'] = 'CAPTCHA'
                                    else:
                                        log.warning(f"AUTO LOGIN {login_status}: Gagal memproses login untuk {pkg}.")
                                        stats[pkg]['status'] = 'LOGIN FAILED'
                                except ImportError:
                                    pass
                            # -----------------------------------------------

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
                                if config_data and config_data.get('GRID_ENABLED'):
                                    gridlayout.apply_grid_single(
                                        pkg, packages,
                                        cell_w=config_data.get('GRID_CELL_W') or None,
                                        cell_h=config_data.get('GRID_CELL_H') or None,
                                        cols=config_data.get('GRID_COLS') or None,
                                        margin=config_data.get('GRID_MARGIN', 10),
                                        offset_y=config_data.get('GRID_OFFSET_Y', 60),
                                    )
                            else:
                                if stats[pkg]['status'] not in ['LOGIN FAILED', 'CAPTCHA']:
                                    log.error(f"RECOVERY FAILED: {pkg} gagal dihidupkan.")
                                    stats[pkg]['status'] = 'FAILED'
                                
                        else:
                            stats[pkg]['pid'] = current_pid
                            if stats[pkg]['status'] in ['FAILED', 'LOGIN FAILED', 'CAPTCHA']:
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
                                        
