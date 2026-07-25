"""
Modul: menu.py
Tanggung Jawab: Menampilkan CLI interaktif dan routing eksekusi.
"""
import os
import sys
import time

from core.logger import log
from core.config import load_config, save_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import start_monitoring
from core.tester import show_test_menu

# Impor Layout Engine terbaru
from core.ui import console, reset_terminal, get_compact_header, draw_header, show_transition, draw_footer
from rich.prompt import Prompt
from rich.table import Table
from rich.align import Align

def run_auto_rejoiner():
    # Tetap memanggil fungsi Dashboard, tidak ada perubahan logika
    reset_terminal()
    console.print(get_compact_header(status="Initializing"))
    console.print("\n[bold yellow]==== MENJALANKAN AUTO REJOINER ====[/]\n", justify="center")
    
    config_data = load_config("config.conf")
    timeout_seconds = config_data.get("TIMEOUT_SECONDS", 45)
    delay_seconds = config_data.get("DELAY_SECONDS", 3)
    max_retries = config_data.get("MAX_RETRIES", 3)
    cooldown_secs = config_data.get("COOLDOWN_SECONDS", 300)
    
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    packages = get_roblox_packages()
    
    current_time = time.time()
    stats = {}
    for pkg in packages:
        stats[pkg] = {
            'pid': '-', 'status': 'OFFLINE', 'uptime_start': 0,
            'launch_count': 0, 'recovery_count': 0, 'crash_count': 0,
            'consecutive_crashes': 0, 'last_recovery_time': current_time, 'cooldown_until': 0
        }
    
    for pkg in packages:
        stats[pkg]['status'] = 'LOADING'
        stats[pkg]['launch_count'] += 1
        
        success = launch_and_wait(pkg, intent_url, timeout_seconds)
        if success:
            stats[pkg]['status'] = 'ONLINE'
            stats[pkg]['uptime_start'] = time.time()
        else:
            stats[pkg]['status'] = 'FAILED'
            
        time.sleep(delay_seconds)
        
    start_monitoring(packages, intent_url, timeout_seconds, max_retries, cooldown_secs, stats)

def show_settings():
    show_transition("Opening Settings...")
    config_data = load_config("config.conf")
    
    while True:
        reset_terminal()
        draw_header("SETTINGS")
        
        link = config_data.get('PRIVATE_SERVER_LINK', '')
        display_link = link[:20] + "..." if len(link) > 20 else link
        
        table = Table(box=None, padding=(0, 2), show_header=False, expand=False)
        table.add_column("No", style="bold cyan", justify="right")
        table.add_column("Icon", style="white", justify="center")
        table.add_column("Config", style="white", justify="left")
        table.add_column("Value", style="dim white", justify="right")
        
        table.add_row("[1]", "🔗", "Server Link", f"[cyan]{display_link}[/]")
        table.add_row("[2]", "⏱ ", "Timeout Wait", f"[cyan]{config_data.get('TIMEOUT_SECONDS', 45)}s[/]")
        table.add_row("[3]", "⏳", "Delay Package", f"[cyan]{config_data.get('DELAY_SECONDS', 3)}s[/]")
        table.add_row("[4]", "🔄", "Max Retries", f"[cyan]{config_data.get('MAX_RETRIES', 3)}x[/]")
        table.add_row("[5]", "❄ ", "Cooldown", f"[cyan]{config_data.get('COOLDOWN_SECONDS', 300)}s[/]")
        table.add_row("[6]", "💾", "Simpan Config", ">")
        table.add_row("[7]", "↩ ", "Kembali", ">")
        
        console.print(Align.center(table))
        draw_footer("ESC / 7  Back to Menu")
        
        choice = Prompt.ask("\n[dim]Pilih (1-7)[/]", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == '1':
            new_link = console.input("\n[dim]Masukkan Server Link baru:[/] ")
            if new_link.strip(): config_data['PRIVATE_SERVER_LINK'] = new_link.strip()
        elif choice == '2':
            new_timeout = console.input("\n[dim]Masukkan Timeout (detik):[/] ")
            if new_timeout.isdigit(): config_data['TIMEOUT_SECONDS'] = int(new_timeout)
        elif choice == '3':
            new_delay = console.input("\n[dim]Masukkan Delay (detik):[/] ")
            if new_delay.isdigit(): config_data['DELAY_SECONDS'] = int(new_delay)
        elif choice == '4':
            new_retries = console.input("\n[dim]Masukkan Max Retries:[/] ")
            if new_retries.isdigit(): config_data['MAX_RETRIES'] = int(new_retries)
        elif choice == '5':
            new_cooldown = console.input("\n[dim]Masukkan Cooldown (detik):[/] ")
            if new_cooldown.isdigit(): config_data['COOLDOWN_SECONDS'] = int(new_cooldown)
        elif choice == '6':
            show_transition("Menyimpan Config...")
            save_config(config_data, "config.conf")
        elif choice == '7':
            break

def show_main_menu():
    while True:
        reset_terminal()
        draw_header("MENU UTAMA")
        
        table = Table(box=None, padding=(0, 2), show_header=False, expand=False)
        table.add_column("No", style="bold cyan", justify="right")
        table.add_column("Icon", style="white", justify="center")
        table.add_column("Menu", style="white", justify="left")
        table.add_column("Chevron", style="dim white", justify="right")
        
        table.add_row("[1]", "▶", "Auto Rejoiner", ">")
        table.add_row("[2]", "⚙", "Settings", ">")
        table.add_row("[3]", "🧪", "Test (Unit Testing)", ">")
        table.add_row("[4]", "📝", "Logs (Lihat Log)", ">")
        table.add_row("[5]", "ⓘ", "About", ">")
        table.add_row("[bold red][6][/]", "[red]⏻[/]", "[red]Exit[/]", "[red]>[/]")
        
        console.print(Align.center(table))
        draw_footer("CTRL+C  Dashboard    CTRL+Z  Exit")
        
        choice = Prompt.ask("\n[dim]Pilih menu (1-6)[/]", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            show_transition("Starting Engine...")
            run_auto_rejoiner()
        elif choice == '2':
            show_settings()
            show_transition("Loading Menu...")
        elif choice == '3':
            show_test_menu()
            show_transition("Loading Menu...")
        elif choice == '4':
            show_transition("Fetching Logs...")
            reset_terminal()
            draw_header("LOGS VIEWER")
            
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
            if os.path.exists(log_path):
                console.print("[dim]Menampilkan 20 baris terakhir...[/]", justify="center")
                console.print("")
                os.system(f"tail -n 20 {log_path}")
            else:
                console.print("[dim]File log belum tersedia.[/]", justify="center")
            
            draw_footer("Enter  Back to Menu")
            console.input("\n[dim]Tekan Enter...[/]")
        elif choice == '5':
            show_transition("Opening About...")
            reset_terminal()
            draw_header("ABOUT")
            
            table = Table(box=None, padding=(0, 3), show_header=False, expand=False)
            table.add_row("[dim]Aplikasi[/]", "[bold white]CARRERA-HUB Auto Rejoiner[/]")
            table.add_row("[dim]Versi[/]", "[bold cyan]Python Modular Edition[/]")
            table.add_row("[dim]Status[/]", "[bold green]Stabil & Termux Root Ready[/]")
            table.add_row("[dim]Developer[/]", "[bold magenta]Carrera-Hub Team[/]")
            
            console.print(Align.center(table))
            draw_footer("Enter  Back to Menu")
            console.input("\n[dim]Tekan Enter...[/]")
        elif choice == '6':
            show_transition("Shutting Down...")
            log.info("SHUTDOWN: Script dihentikan oleh user via Menu.")
            reset_terminal()
            sys.exit(0)
            
