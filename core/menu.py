"""
Modul: menu.py
Tanggung Jawab: Menampilkan CLI interaktif dan routing eksekusi.
"""
import os
import sys
import time
import logging

from core.logger import log
from core.config import load_config, save_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import start_monitoring, draw_static_header, draw_dashboard
from core.tester import show_test_menu
try:
    from core.sniper import sniper_agent
except ImportError:
    pass

from core.ui import console, reset_terminal, draw_header, show_transition, draw_footer, LAYOUT_WIDTH
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live

def show_link_manager(config_data):
    all_packages = get_roblox_packages()
    if not all_packages:
        console.print("\n[bold red][!] Tidak ada package Roblox terdeteksi.[/]")
        console.input("\n[dim]Tekan Enter untuk kembali...[/]")
        return

    while True:
        reset_terminal()
        draw_header("LINK PER PACKAGE")
        
        table = Table(box=None, padding=(0, 0), show_header=True, header_style="dim white", width=LAYOUT_WIDTH)
        table.add_column("ID", style="bold cyan", width=4, no_wrap=True)
        table.add_column("PACKAGE NAME", style="white", width=20, no_wrap=True)
        table.add_column("DEEP LINK", style="cyan", width=30, no_wrap=True, overflow="ellipsis")
        
        for idx, pkg in enumerate(all_packages, 1):
            pkg_key = f"PKG_{pkg}"
            link = config_data.get(pkg_key, "")
            display_link = link if link else "[dim white]<Global Link>[/]"
            table.add_row(f"[{idx}]", pkg, display_link)
            
        console.print(table)
        # UI FIX: Menghapus label 'Simpan &' karena sudah Auto Save
        draw_footer("[1,2,3..] Pilih ID untuk edit   |   [0] Kembali")
        
        choice = console.input("\n[dim]Pilih ID (0 untuk keluar):[/] ").strip()
        
        if choice == '0':
            break
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(all_packages):
                selected_pkg = all_packages[idx-1]
                pkg_key = f"PKG_{selected_pkg}"
                console.print(f"\n[dim]Kosongkan lalu Enter untuk menggunakan Global Link.[/]")
                new_link = console.input(f"[dim]Link baru untuk [white]{selected_pkg}[/]:[/] ")
                
                if new_link.strip():
                    config_data[pkg_key] = new_link.strip()
                else:
                    if pkg_key in config_data:
                        del config_data[pkg_key]
                        
                # AUTO SAVE: Langsung simpan setelah modifikasi Link Package
                save_config(config_data, "config.conf")
            else:
                console.print("[bold red][!] ID tidak valid.[/]")
                time.sleep(1)

def run_auto_rejoiner():
    reset_terminal()
    draw_header("INITIALIZING AUTO REJOINER")
    
    config_data = load_config("config.conf")
    timeout_seconds = config_data.get("TIMEOUT_SECONDS", 45)
    delay_seconds = config_data.get("DELAY_SECONDS", 3)
    max_retries = config_data.get("MAX_RETRIES", 3)
    cooldown_secs = config_data.get("COOLDOWN_SECONDS", 300)
    
    all_packages = get_roblox_packages()
    if not all_packages:
        console.print("\n[bold red][!] Tidak ada package Roblox terdeteksi.[/]")
        console.input("\n[dim]Tekan Enter untuk kembali...[/]")
        return
        
    console.print("\n[bold cyan]Detected Packages:[/]")
    for idx, pkg in enumerate(all_packages, 1):
        console.print(f"[{idx}] {pkg}")
    console.print("\n[bold cyan][A][/] All Packages")
    
    packages = []
    while True:
        choice = console.input("\n[dim]Input (A / 1,2,3...):[/] ").strip().upper()
        if choice == '':
            console.print("[bold red][!] Input tidak boleh kosong. Silakan coba lagi.[/]")
            continue
        elif choice == 'A':
            packages = all_packages
            break
        else:
            parts = choice.split(',')
            new_active = []
            invalid_nums = []
            seen = set()
            for p in parts:
                p = p.strip()
                if p.isdigit():
                    idx = int(p)
                    if 1 <= idx <= len(all_packages):
                        pkg_name = all_packages[idx-1]
                        if pkg_name not in seen:
                            seen.add(pkg_name)
                            new_active.append(pkg_name)
                    else:
                        invalid_nums.append(p)
                else:
                    invalid_nums.append(p)
                    
            if invalid_nums:
                console.print(f"[bold red][!] Input tidak valid/tidak ditemukan: {', '.join(invalid_nums)}[/]")
                continue
            else:
                packages = new_active
                break

    intent_dict = {}
    global_intent = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    for pkg in packages:
        pkg_link = config_data.get(f"PKG_{pkg}")
        if pkg_link:
            intent_dict[pkg] = get_intent_url(pkg_link)
        else:
            intent_dict[pkg] = global_intent
    
    current_time = time.time()
    stats = {}
    for pkg in packages:
        stats[pkg] = {
            'pid': '-', 'status': 'OFFLINE', 'uptime_start': 0,
            'launch_count': 0, 'recovery_count': 0, 'crash_count': 0,
            'consecutive_crashes': 0, 'last_recovery_time': current_time, 'cooldown_until': 0
        }
    
    for handler in log.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            log.removeHandler(handler)
            
    reset_terminal()
    draw_static_header(len(packages))
    
    with Live(draw_dashboard(stats, current_time, len(packages)), console=console, refresh_per_second=1) as live:
        for pkg in packages:
            stats[pkg]['status'] = 'LOADING'
            stats[pkg]['launch_count'] += 1
            live.update(draw_dashboard(stats, time.time(), len(packages)))
            
            success = launch_and_wait(pkg, intent_dict[pkg], timeout_seconds)
            if success:
                stats[pkg]['status'] = 'ONLINE'
                stats[pkg]['uptime_start'] = time.time()
            else:
                stats[pkg]['status'] = 'FAILED'
                
            time.sleep(delay_seconds)
            live.update(draw_dashboard(stats, time.time(), len(packages)))
        
    try:
        sniper_agent.start()
    except NameError:
        pass
        
    start_monitoring(packages, intent_dict, timeout_seconds, max_retries, cooldown_secs, stats)

def show_settings():
    config_data = load_config("config.conf")
    
    while True:
        reset_terminal()
        draw_header("SETTINGS")
        
        link = config_data.get('PRIVATE_SERVER_LINK', '')
        display_link = link[:25] + "..." if len(link) > 25 else link
        
        table = Table(box=None, padding=(0, 0), show_header=False, width=LAYOUT_WIDTH)
        table.add_column("No", style="bold cyan", width=5, no_wrap=True)
        table.add_column("Icon", style="white", width=3, no_wrap=True)
        table.add_column("Config", style="white", width=25, no_wrap=True)
        table.add_column("Value", style="dim white", justify="right", width=23, no_wrap=True)
        
        # UI FIX: Menghapus opsi [7] Simpan Config dan menyesuaikan urutan
        table.add_row("[1]", "🔗", "Global Server Link", f"[cyan]{display_link}[/]")
        table.add_row("[2]", "⏱", "Timeout Wait", f"[cyan]{config_data.get('TIMEOUT_SECONDS', 45)}s[/]")
        table.add_row("[3]", "⏳", "Delay Package", f"[cyan]{config_data.get('DELAY_SECONDS', 3)}s[/]")
        table.add_row("[4]", "🔄", "Max Retries", f"[cyan]{config_data.get('MAX_RETRIES', 3)}x[/]")
        table.add_row("[5]", "❄", "Cooldown", f"[cyan]{config_data.get('COOLDOWN_SECONDS', 300)}s[/]")
        table.add_row("[6]", "📦", "Atur Link per Package", ">")
        table.add_row("[7]", "↩", "Kembali", ">")
        
        console.print(table)
        draw_footer("ESC / 7  Back to Menu")
        
        choice = Prompt.ask("\n[dim]Pilih (1-7)[/]", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        # AUTO SAVE: Memanggil save_config setelah setiap perubahan value yang valid
        if choice == '1':
            new_link = console.input("\n[dim]Masukkan Server Link baru:[/] ")
            if new_link.strip(): 
                config_data['PRIVATE_SERVER_LINK'] = new_link.strip()
                save_config(config_data, "config.conf")
        elif choice == '2':
            new_timeout = console.input("\n[dim]Masukkan Timeout (detik):[/] ")
            if new_timeout.isdigit(): 
                config_data['TIMEOUT_SECONDS'] = int(new_timeout)
                save_config(config_data, "config.conf")
        elif choice == '3':
            new_delay = console.input("\n[dim]Masukkan Delay (detik):[/] ")
            if new_delay.isdigit(): 
                config_data['DELAY_SECONDS'] = int(new_delay)
                save_config(config_data, "config.conf")
        elif choice == '4':
            new_retries = console.input("\n[dim]Masukkan Max Retries:[/] ")
            if new_retries.isdigit(): 
                config_data['MAX_RETRIES'] = int(new_retries)
                save_config(config_data, "config.conf")
        elif choice == '5':
            new_cooldown = console.input("\n[dim]Masukkan Cooldown (detik):[/] ")
            if new_cooldown.isdigit(): 
                config_data['COOLDOWN_SECONDS'] = int(new_cooldown)
                save_config(config_data, "config.conf")
        elif choice == '6':
            show_link_manager(config_data)
        elif choice == '7':
            break

def show_main_menu():
    while True:
        reset_terminal()
        draw_header("MENU UTAMA")
        
        table = Table(box=None, padding=(0, 0), show_header=False, width=LAYOUT_WIDTH)
        table.add_column("No", style="bold cyan", width=5, no_wrap=True)
        table.add_column("Icon", style="white", width=3, no_wrap=True)
        table.add_column("Menu", style="white", width=45, no_wrap=True)
        table.add_column("Chevron", style="dim white", justify="right", width=3, no_wrap=True)
        
        table.add_row("[1]", "▶", "Auto Rejoiner", ">")
        table.add_row("[2]", "⚙", "Settings", ">")
        table.add_row("[3]", "🧪", "Test (Unit Testing)", ">")
        table.add_row("[4]", "📝", "Logs (Lihat Log)", ">")
        table.add_row("[5]", "ⓘ", "About", ">")
        table.add_row("[bold red][6][/]", "[red]⏻[/]", "[red]Exit[/]", "[red]>[/]")
        
        console.print(table)
        draw_footer("CTRL+C  Dashboard    CTRL+Z  Exit")
        
        choice = Prompt.ask("\n[dim]Pilih menu (1-6)[/]", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            show_transition("Starting Engine...")
            run_auto_rejoiner()
        elif choice == '2':
            show_transition("Loading Menu...")
            show_settings()
        elif choice == '3':
            show_test_menu()
            show_transition("Loading Menu...")
        elif choice == '4':
            show_transition("Fetching Logs...")
            reset_terminal()
            draw_header("LOGS VIEWER")
            
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
            if os.path.exists(log_path):
                console.print("[dim]Menampilkan 20 baris terakhir...[/]")
                console.print("")
                os.system(f"tail -n 20 {log_path}")
            else:
                console.print("[dim]File log belum tersedia.[/]")
            
            draw_footer("Enter  Back to Menu")
            console.input("\n[dim]Tekan Enter...[/]")
        elif choice == '5':
            show_transition("Opening About...")
            reset_terminal()
            draw_header("ABOUT")
            
            table = Table(box=None, padding=(0, 0), show_header=False, width=LAYOUT_WIDTH)
            table.add_column("Key", style="dim white", width=20)
            table.add_column("Value", style="bold white", width=35)
            
            table.add_row("Aplikasi", "CARRERA-HUB Auto Rejoiner")
            table.add_row("Versi", "[cyan]Python Modular Edition[/]")
            table.add_row("Status", "[green]Stabil & Termux Root Ready[/]")
            table.add_row("Developer", "[magenta]Carrera-Hub Team[/]")
            
            console.print(table)
            draw_footer("Enter  Back to Menu")
            console.input("\n[dim]Tekan Enter...[/]")
        elif choice == '6':
            show_transition("Shutting Down...")
            try:
                sniper_agent.stop()
            except Exception:
                pass
            reset_terminal()
            sys.exit(0)
                    
