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
from core.accounts import load_accounts, save_accounts
from core import gridlayout

try:
    from core.sniper import sniper_agent
except ImportError:
    pass

from core.ui import console, reset_terminal, draw_header, show_transition, draw_footer, LAYOUT_WIDTH
from rich.prompt import Prompt
from rich.table import Table
from rich.live import Live

def show_auto_login_menu():
    while True:
        reset_terminal()
        draw_header("AUTO LOGIN ROBLOX")
        
        all_packages = get_roblox_packages()
        if not all_packages:
            console.print("\n[bold red][!] Tidak ada package Roblox terdeteksi.[/]")
            console.input("\n[dim]Tekan Enter untuk kembali...[/]")
            return
            
        accounts = load_accounts()
        
        table = Table(box=None, padding=(0, 0), show_header=True, header_style="dim white", width=LAYOUT_WIDTH)
        table.add_column("No", style="bold cyan", width=4, no_wrap=True)
        table.add_column("PACKAGE NAME", style="white", width=25, no_wrap=True)
        table.add_column("STATUS AKUN", style="green", width=30, no_wrap=True)
        
        for idx, pkg in enumerate(all_packages, 1):
            status = accounts.get(pkg, {}).get("username", "[dim red]Belum Dikonfigurasi[/]")
            table.add_row(f"[{idx}]", pkg, status)
            
        console.print(table)
        draw_footer("[1,2,3..] Pilih ID Package   |   [0] Kembali ke Menu")
        
        choice = console.input("\n[dim]Select Package (0 untuk keluar):[/] ").strip()
        
        if choice == '0':
            break
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(all_packages):
                selected_pkg = all_packages[idx-1]
                
                console.print(f"\n[bold cyan]Konfigurasi Auto Login: {selected_pkg}[/]")
                username = console.input("[white]Username:[/] ").strip()
                if not username:
                    console.print("[red]Dibatalkan.[/]")
                    time.sleep(1)
                    continue
                    
                password = Prompt.ask("[white]Password[/]", password=True)
                
                if selected_pkg not in accounts:
                    accounts[selected_pkg] = {}
                accounts[selected_pkg]["username"] = username
                accounts[selected_pkg]["password"] = password
                
                save_accounts(accounts)
                
                console.print("\n[bold green]Saved Successfully.[/]")
                again = console.input("\n[dim]Configure another package? [Y/N]:[/] ").strip().upper()
                if again != 'Y':
                    break
            else:
                console.print("[bold red][!] ID tidak valid.[/]")
                time.sleep(1)

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
            
            # --- HOOK: AUTO LOGIN FALLBACK SAAT AWAL START ---
            if not success:
                try:
                    from core.autologin import run as run_autologin
                    stats[pkg]['status'] = 'LOGIN'
                    live.update(draw_dashboard(stats, time.time(), len(packages)))
                    
                    login_status = run_autologin(pkg)
                    
                    if login_status in ["SUCCESS", "ALREADY_LOGGED_IN"]:
                        stats[pkg]['status'] = 'LOADING'
                        live.update(draw_dashboard(stats, time.time(), len(packages)))
                        success = launch_and_wait(pkg, intent_dict[pkg], timeout_seconds)
                    elif login_status == "CAPTCHA":
                        stats[pkg]['status'] = 'CAPTCHA'
                    else:
                        stats[pkg]['status'] = 'LOGIN FAILED'
                except ImportError:
                    pass
            # -------------------------------------------------
            
            if success:
                stats[pkg]['status'] = 'ONLINE'
                stats[pkg]['uptime_start'] = time.time()
                if config_data.get('GRID_ENABLED'):
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
                    stats[pkg]['status'] = 'FAILED'
                
            time.sleep(delay_seconds)
            live.update(draw_dashboard(stats, time.time(), len(packages)))
        
    try:
        sniper_agent.start()
    except NameError:
        pass
        
    start_monitoring(packages, intent_dict, timeout_seconds, max_retries, cooldown_secs, stats, config_data)


def show_grid_menu(config_data):
    while True:
        reset_terminal()
        draw_header("GRID LAYOUT (FREEFORM)")

        # Deteksi resolusi layar
        screen = gridlayout.get_screen_size()
        density = gridlayout.get_screen_density()
        screen_str = f"{screen[0]}x{screen[1]}px" if screen else "Gagal deteksi"
        density_str = f"{density} dpi" if density else "-"

        console.print(f"[dim]Layar terdeteksi:[/] [cyan]{screen_str}[/] [dim]({density_str})[/]\n")

        # Mengambil dan memformat value dari config
        val_enabled = "ON" if config_data.get('GRID_ENABLED') else "OFF"
        val_cols = str(config_data.get('GRID_COLS', 0)) if config_data.get('GRID_COLS', 0) != 0 else "Auto"
        val_cw = str(config_data.get('GRID_CELL_W', 0)) if config_data.get('GRID_CELL_W', 0) != 0 else "Auto"
        val_ch = str(config_data.get('GRID_CELL_H', 0)) if config_data.get('GRID_CELL_H', 0) != 0 else "Auto"
        val_margin = str(config_data.get('GRID_MARGIN', 10))
        val_offset = str(config_data.get('GRID_OFFSET_Y', 60))

        # RENDERER BARU (Plain ASCII Text dengan ljust untuk alignment statis yang kebal overflow)
        # 16 adalah jumlah karakter spacing agar titik dua (:) sejajar rapi.
        console.print(f"[bold cyan][1][/] [white]{'Auto Apply Grid'.ljust(16)} :[/] [cyan]{val_enabled}[/]")
        console.print(f"[bold cyan][2][/] [white]{'Kolom'.ljust(16)} :[/] [cyan]{val_cols}[/]")
        console.print(f"[bold cyan][3][/] [white]{'Lebar Window'.ljust(16)} :[/] [cyan]{val_cw}[/]")
        console.print(f"[bold cyan][4][/] [white]{'Tinggi Window'.ljust(16)} :[/] [cyan]{val_ch}[/]")
        console.print(f"[bold cyan][5][/] [white]{'Margin Window'.ljust(16)} :[/] [cyan]{val_margin}[/]")
        console.print(f"[bold cyan][6][/] [white]{'Offset Atas'.ljust(16)} :[/] [cyan]{val_offset}[/]")
        
        console.print(f"\n[dim]{'-' * 40}[/]\n")
        
        console.print(f"[bold cyan][7][/] [white]Terapkan Sekarang[/]")
        console.print(f"[bold cyan][8][/] [white]Kembali[/]")

        console.print("\n[dim]0 = otomatis dihitung dari resolusi layar & jumlah package[/]")
        draw_footer("ESC / 8  Back to Menu")

        choice = Prompt.ask("\n[dim]Pilih (1-8)[/]", choices=["1", "2", "3", "4", "5", "6", "7", "8"])

        if choice == '1':
            config_data['GRID_ENABLED'] = 0 if config_data.get('GRID_ENABLED') else 1
            save_config(config_data, "config.conf")
        elif choice == '2':
            val = console.input("\n[dim]Jumlah kolom (0 = auto):[/] ")
            if val.isdigit():
                config_data['GRID_COLS'] = int(val)
                save_config(config_data, "config.conf")
        elif choice == '3':
            val = console.input("\n[dim]Lebar window dalam px (0 = auto):[/] ")
            if val.isdigit():
                config_data['GRID_CELL_W'] = int(val)
                save_config(config_data, "config.conf")
        elif choice == '4':
            val = console.input("\n[dim]Tinggi window dalam px (0 = auto):[/] ")
            if val.isdigit():
                config_data['GRID_CELL_H'] = int(val)
                save_config(config_data, "config.conf")
        elif choice == '5':
            val = console.input("\n[dim]Margin antar window dalam px:[/] ")
            if val.isdigit():
                config_data['GRID_MARGIN'] = int(val)
                save_config(config_data, "config.conf")
        elif choice == '6':
            val = console.input("\n[dim]Offset dari atas layar dalam px:[/] ")
            if val.isdigit():
                config_data['GRID_OFFSET_Y'] = int(val)
                save_config(config_data, "config.conf")
        elif choice == '7':
            all_packages = get_roblox_packages()
            if not all_packages:
                console.print("\n[bold red][!] Tidak ada package Roblox terdeteksi.[/]")
            else:
                console.print(f"\n[dim]Menerapkan grid ke {len(all_packages)} package (yang sedang berjalan)...[/]")
                results = gridlayout.apply_grid(
                    all_packages,
                    cell_w=config_data.get('GRID_CELL_W') or None,
                    cell_h=config_data.get('GRID_CELL_H') or None,
                    cols=config_data.get('GRID_COLS') or None,
                    margin=config_data.get('GRID_MARGIN', 10),
                    offset_y=config_data.get('GRID_OFFSET_Y', 60),
                )
                ok_count = sum(1 for v in results.values() if v)
                console.print(f"[bold green]Selesai: {ok_count}/{len(all_packages)} window berhasil diatur.[/]")
                console.print("[dim](Package yang belum jalan otomatis dilewati.)[/]")
            console.input("\n[dim]Tekan Enter untuk kembali...[/]")
        elif choice == '8':
            break

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
        
        table.add_row("[1]", "🔗", "Global Server Link", f"[cyan]{display_link}[/]")
        table.add_row("[2]", "⏱", "Timeout Wait", f"[cyan]{config_data.get('TIMEOUT_SECONDS', 45)}s[/]")
        table.add_row("[3]", "⏳", "Delay Package", f"[cyan]{config_data.get('DELAY_SECONDS', 3)}s[/]")
        table.add_row("[4]", "🔄", "Max Retries", f"[cyan]{config_data.get('MAX_RETRIES', 3)}x[/]")
        table.add_row("[5]", "❄", "Cooldown", f"[cyan]{config_data.get('COOLDOWN_SECONDS', 300)}s[/]")
        table.add_row("[6]", "📦", "Atur Link per Package", ">")
        table.add_row("[7]", "▦", "Grid Layout (Freeform)", ">")
        table.add_row("[8]", "↩", "Kembali", ">")
        
        console.print(table)
        draw_footer("ESC / 8  Back to Menu")
        
        choice = Prompt.ask("\n[dim]Pilih (1-8)[/]", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
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
            show_grid_menu(config_data)
        elif choice == '8':
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
        table.add_row("[3]", "🔑", "Auto Login Roblox", ">")
        table.add_row("[4]", "🧪", "Test (Unit Testing)", ">")
        table.add_row("[5]", "📝", "Logs (Lihat Log)", ">")
        table.add_row("[6]", "ⓘ", "About", ">")
        table.add_row("[bold red][7][/]", "[red]⏻[/]", "[red]Exit[/]", "[red]>[/]")
        
        console.print(table)
        draw_footer("CTRL+C  Dashboard    CTRL+Z  Exit")
        
        choice = Prompt.ask("\n[dim]Pilih menu (1-7)[/]", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == '1':
            show_transition("Starting Engine...")
            run_auto_rejoiner()
        elif choice == '2':
            show_transition("Loading Menu...")
            show_settings()
        elif choice == '3':
            show_transition("Loading Auto Login...")
            show_auto_login_menu()
        elif choice == '4':
            show_test_menu()
            show_transition("Loading Menu...")
        elif choice == '5':
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
        elif choice == '6':
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
        elif choice == '7':
            show_transition("Shutting Down...")
            try:
                sniper_agent.stop()
            except Exception:
                pass
            reset_terminal()
            sys.exit(0)
