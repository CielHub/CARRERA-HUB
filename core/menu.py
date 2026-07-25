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

from core.ui import console, reset_terminal, get_compact_header
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

def run_auto_rejoiner():
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
    config_data = load_config("config.conf")
    while True:
        reset_terminal()
        console.print(get_compact_header(status="Settings"))
        
        link = config_data.get('PRIVATE_SERVER_LINK', '')
        display_link = link[:20] + "..." if len(link) > 20 else link
        
        menu_text = (
            f"[bold green]1.[/] Edit Server Link     [bold cyan][{display_link}][/]\n"
            f"[bold green]2.[/] Edit Timeout         [bold cyan][{config_data.get('TIMEOUT_SECONDS', 45)}s][/]\n"
            f"[bold green]3.[/] Edit Delay Package   [bold cyan][{config_data.get('DELAY_SECONDS', 3)}s][/]\n"
            f"[bold green]4.[/] Edit Max Retries     [bold cyan][{config_data.get('MAX_RETRIES', 3)}x][/]\n"
            f"[bold green]5.[/] Edit Cooldown        [bold cyan][{config_data.get('COOLDOWN_SECONDS', 300)}s][/]\n"
            f"[bold green]6.[/] Simpan Config\n"
            f"[bold green]7.[/] Kembali"
        )
        
        panel = Panel(menu_text, title="[bold white]SETTINGS[/]", box=box.ROUNDED, expand=False, padding=(1, 4))
        console.print("\n")
        console.print(Align.center(panel))
        console.print("\n")
        
        choice = Prompt.ask("Pilih (1-7)", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == '1':
            new_link = console.input("\n[bold white]Masukkan Private Server Link baru:[/] ")
            if new_link.strip(): config_data['PRIVATE_SERVER_LINK'] = new_link.strip()
        elif choice == '2':
            new_timeout = console.input("\n[bold white]Masukkan Timeout (detik):[/] ")
            if new_timeout.isdigit(): config_data['TIMEOUT_SECONDS'] = int(new_timeout)
        elif choice == '3':
            new_delay = console.input("\n[bold white]Masukkan Delay (detik):[/] ")
            if new_delay.isdigit(): config_data['DELAY_SECONDS'] = int(new_delay)
        elif choice == '4':
            new_retries = console.input("\n[bold white]Masukkan Max Retries:[/] ")
            if new_retries.isdigit(): config_data['MAX_RETRIES'] = int(new_retries)
        elif choice == '5':
            new_cooldown = console.input("\n[bold white]Masukkan Cooldown (detik):[/] ")
            if new_cooldown.isdigit(): config_data['COOLDOWN_SECONDS'] = int(new_cooldown)
        elif choice == '6':
            save_config(config_data, "config.conf")
            console.input("\n[bold green][+][/] Config disimpan! Enter untuk lanjut...")
        elif choice == '7':
            break

def show_main_menu():
    while True:
        reset_terminal()
        console.print(get_compact_header(status="Main Menu"))
        
        menu_text = (
            "[bold green]1.[/] [bold white]Auto Rejoiner[/]\n"
            "[bold green]2.[/] [white]Settings[/]\n"
            "[bold green]3.[/] [white]Test[/]\n"
            "[bold green]4.[/] [white]Logs[/]\n"
            "[bold green]5.[/] [white]About[/]\n"
            "[bold green]6.[/] [white]Exit[/]"
        )
        
        # expand=False membuat menu terpusat dan berukuran pas kontennya
        panel = Panel(menu_text, title="[bold green]MAIN MENU[/]", box=box.ROUNDED, expand=False, padding=(1, 10))
        
        console.print("\n")
        console.print(Align.center(panel))
        console.print("\n")
        
        choice = Prompt.ask("Pilih (1-6)", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            run_auto_rejoiner()
        elif choice == '2':
            show_settings()
        elif choice == '3':
            show_test_menu()
        elif choice == '4':
            reset_terminal()
            console.print(get_compact_header(status="Logs"))
            console.print("\n[bold yellow]=========== LOG TERAKHIR (20 Baris) ===========[/]\n", justify="center")
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
            if os.path.exists(log_path):
                os.system(f"tail -n 20 {log_path}")
            else:
                console.print("[dim]File log belum tersedia.[/]", justify="center")
            console.print("\n[bold yellow]===============================================[/]", justify="center")
            console.input("\n[bold green]Tekan Enter untuk kembali...[/]")
        elif choice == '5':
            reset_terminal()
            about_text = (
                "[bold white]Versi:[/] Python Modular Edition\n"
                "[bold white]Status:[/] Stabil & Termux Root Ready\n"
                "[bold white]Developer:[/] Carrera-Hub Team"
            )
            console.print("\n")
            console.print(Align.center(Panel(about_text, title="[bold green]ABOUT[/]", box=box.ROUNDED)))
            console.input("\n[bold green]Tekan Enter untuk kembali...[/]")
        elif choice == '6':
            log.info("SHUTDOWN: Script dihentikan oleh user via Menu.")
            reset_terminal()
            sys.exit(0)
            
