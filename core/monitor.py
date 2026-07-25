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
from core.ui import console, reset_terminal, LAYOUT_WIDTH
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

def draw_dashboard(stats, current_time, pkg_count):
    # 1. Header (Rata Kiri murni tanpa space terbuang)
    ascii_art = pyfiglet.figlet_format("CARRERA", font="slant")
    logo_lines = [Text.from_markup(f"[bold green]{line}[/]") for line in ascii_art.split('\n') if line.strip()]
    
    t = time.strftime("%H:%M:%S")
    info_text = f"Version 1.0.0   |   User root   |   Status Monitoring   |   Packages {pkg_count}   |   Time {t}"
    info_render = Text.from_markup(f"[dim white]{info_text}[/]")
    
    rule = Text.from_markup(f"[dim cyan]{'─' * LAYOUT_WIDTH}[/]")
    
    # 2. Summary Bar (Kepadatan Informasi)
    running = sum(1 for s in stats.values() if s['status'] == 'ONLINE')
    recover = sum(1 for s in stats.values() if s['status'] == 'RECOVERY')
    loading = sum(1 for s in stats.values() if s['status'] == 'LOADING')
    offline = sum(1 for s in stats.values() if s['status'] in ['FAILED', 'COOLDOWN'])
    
    summary_text = f"Clones {running}/{pkg_count}   |   [bold green]● Running {running}[/]   |   [bold yellow]● Recover {recover}[/]   |   [bold blue]● Loading {loading}[/]   |   [bold red]● Offline {offline}[/]"
    summary_render = Text.from_markup(summary_text)

    # 3. Tabel TUI Profesional (Tanpa kotak/border)
    table = Table(box=None, padding=(0, 1), show_header=True, header_style="dim white", width=LAYOUT_WIDTH)
    table.add_column("ID", style="bold cyan", width=4)
    table.add_column("PACKAGE", style="white", width=22)
    table.add_column("PID", style="cyan", width=6)
    table.add_column("STATUS", width=12)
    table.add_column("UPTIME", style="white", width=8)
    table.add_column("L", style="dim white", width=3, justify="right")
    table.add_column("R", style="dim white", width=3, justify="right")
    table.add_column("C", style="dim white", width=3, justify="right")
    
    for idx, (pkg, s) in enumerate(stats.items(), 1):
        uptime_str = format_uptime(s['uptime_start'], current_time) if s['status'] == 'ONLINE' else "--:--:--"
        display_pkg = pkg.replace("com.roblox.", "..") if "com.roblox." in pkg else pkg
        
        # Indikator warna solid TUI
        if s['status'] == 'ONLINE': stat_fmt = "[bold green]● Farming[/]"
        elif s['status'] == 'LOADING': stat_fmt = "[bold blue]● Loading[/]"
        elif s['status'] == 'RECOVERY': stat_fmt = "[bold yellow]● Recover[/]"
        elif s['status'] == 'FAILED': stat_fmt = "[bold red]● Offline[/]"
        elif s['status'] == 'COOLDOWN': stat_fmt = "[bold red]● Cooldown[/]"
        else: stat_fmt = f"[white]● {s['status']}[/]"
            
        table.add_row(
            f"[{idx}]", display_pkg, str(s['pid']), stat_fmt, uptime_str,
            str(s['launch_count']), str(s['recovery_count']), str(s['crash_count'])
        )
        
    # 4. Recent Logs (Pantau log real-time di bawah tabel)
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
    log_lines = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                log_lines = lines[-6:] # Ambil 6 baris terakhir
        except:
            log_lines = ["Gagal membaca log."]
    else:
        log_lines = ["Belum ada log aktif."]
        
    logs_render = [Text.from_markup("[dim white]RECENT LOGS[/]")]
    for line in log_lines:
        if "[INFO]" in line: line = line.replace("[INFO]", "[bold green]INFO[/]")
        elif "[WARNING]" in line: line = line.replace("[WARNING]", "[bold yellow]WARN[/]")
        elif "[ERROR]" in line: line = line.replace("[ERROR]", "[bold red]FAIL[/]")
        
        # Potong string jika kepanjangan agar tidak merusak layout
        if len(line) > LAYOUT_WIDTH:
            line = line[:LAYOUT_WIDTH - 3] + "..."
            
        logs_render.append(Text.from_markup(f"[dim]{line}[/]"))
        
    # 5. Footer
    footer_text = Text.from_markup("[dim white]CTRL+C Back to Menu   |   CTRL+Z Exit   |   Refresh: 1s[/]")
    
    # Render gabungan tanpa spasi vertikal berlebih
    renderables = logo_lines + [
        Text(""), info_render, rule, summary_render, rule, table, rule
    ] + logs_render + [rule, footer_text]
    
    return Group(*renderables)

def start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats=None):
    log.info("MONITORING: Semua package diproses. Memasuki mode penjagaan...")
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
    
