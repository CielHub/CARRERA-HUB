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

# [UI UPGRADE] Import UI Engine
from core.ui import console, clear_screen, get_header
from rich.prompt import Prompt

def run_auto_rejoiner():
    """Mengeksekusi logika utama Auto Rejoiner (Engine)."""
    clear_screen()
    console.print(get_header(status="Initializing"))
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
    """Menampilkan dan mengelola Menu Settings."""
    config_data = load_config("config.conf")
    
    while True:
        clear_screen()
        console.print(get_header(status="Settings"))
        console.print("\n[bold yellow]==================== MENU SETTINGS ====================[/]\n", justify="center")
        
        link = config_data.get('PRIVATE_SERVER_LINK', '')
        display_link = link[:25] + "..." if len(link) > 25 else link
        
        console.print(f"[bold green][ 1 ][/] Edit Private Server Link [bold cyan][{display_link}][/]")
        console.print(f"[bold green][ 2 ][/] Edit Timeout Smart Wait  [bold cyan][{config_data.get('TIMEOUT_SECONDS', 45)}s][/]")
        console.print(f"[bold green][ 3 ][/] Edit Delay Antar Package [bold cyan][{config_data.get('DELAY_SECONDS', 3)}s][/]")
        console.print(f"[bold green][ 4 ][/] Edit Max Retries         [bold cyan][{config_data.get('MAX_RETRIES', 3)} kali][/]")
        console.print(f"[bold green][ 5 ][/] Edit Cooldown Recovery   [bold cyan][{config_data.get('COOLDOWN_SECONDS', 300)}s][/]")
        console.print(f"[bold green][ 6 ][/] Simpan Config")
        console.print(f"[bold green][ 7 ][/] Kembali\n")
        
        choice = Prompt.ask("Pilih menu (1-7)", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == '1':
            new_link = console.input("[bold white]Masukkan Private Server Link baru:[/] ")
            if new_link.strip(): config_data['PRIVATE_SERVER_LINK'] = new_link.strip()
        elif choice == '2':
            new_timeout = console.input("[bold white]Masukkan Timeout (detik):[/] ")
            if new_timeout.isdigit(): config_data['TIMEOUT_SECONDS'] = int(new_timeout)
        elif choice == '3':
            new_delay = console.input("[bold white]Masukkan Delay (detik):[/] ")
            if new_delay.isdigit(): config_data['DELAY_SECONDS'] = int(new_delay)
        elif choice == '4':
            new_retries = console.input("[bold white]Masukkan Max Retries:[/] ")
            if new_retries.isdigit(): config_data['MAX_RETRIES'] = int(new_retries)
        elif choice == '5':
            new_cooldown = console.input("[bold white]Masukkan Cooldown (detik):[/] ")
            if new_cooldown.isdigit(): config_data['COOLDOWN_SECONDS'] = int(new_cooldown)
        elif choice == '6':
            save_config(config_data, "config.conf")
            console.input("\n[bold green][+][/] Config berhasil disimpan! Tekan Enter untuk lanjut...")
        elif choice == '7':
            break

def show_main_menu():
    """Menampilkan Menu Utama."""
    while True:
        clear_screen()
        console.print(get_header(status="Main Menu"))
        console.print("\n[bold yellow]====================== MAIN MENU ======================[/]\n", justify="center")
        
        console.print("[bold green][ 1 ][/] [bold white]Jalankan Auto Rejoiner[/]")
        console.print("      [dim]Mulai menjalankan semua package dan monitoring.[/]\n")
        
        console.print("[bold green][ 2 ][/] [bold white]Settings[/]")
        console.print("      [dim]Ubah konfigurasi link, timeout, delay, retries, dll.[/]\n")
        
        console.print("[bold green][ 3 ][/] [bold white]Test[/]")
        console.print("      [dim]Jalankan unit test untuk semua modul sistem.[/]\n")
        
        console.print("[bold green][ 4 ][/] [bold white]Logs[/]")
        console.print("      [dim]Lihat log terbaru dan riwayat aktivitas.[/]\n")
        
        console.print("[bold green][ 5 ][/] [bold white]About[/]")
        console.print("      [dim]Informasi tentang CARRERA-HUB Auto Rejoiner.[/]\n")
        
        console.print("[bold green][ 6 ][/] [bold white]Exit[/]")
        console.print("      [dim]Keluar dari program.[/]\n")
        
        console.print("[bold yellow]" + "=" * 55 + "[/]\n", justify="center")
        
        choice = Prompt.ask("Pilih menu (1-6)", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == '1':
            run_auto_rejoiner()
        elif choice == '2':
            show_settings()
        elif choice == '3':
            show_test_menu()
        elif choice == '4':
            clear_screen()
            console.print(get_header(status="Logs Viewer"))
            console.print("\n[bold yellow]================ LOG TERAKHIR (20 Baris) ================[/]\n", justify="center")
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "latest.log")
            if os.path.exists(log_path):
                os.system(f"tail -n 20 {log_path}")
            else:
                console.print("[dim]File log belum tersedia.[/]")
            console.print("\n[bold yellow]" + "=" * 57 + "[/]", justify="center")
            console.input("\n[bold green]Tekan Enter untuk kembali...[/]")
        elif choice == '5':
            clear_screen()
            console.print(get_header(status="About"))
            console.print("\n[bold white]Versi:[/] Python Modular Edition")
            console.print("[bold white]Status:[/] Stabil & Termux Root Ready")
            console.print("[bold white]Developer:[/] Carrera-Hub Team\n")
            console.input("[bold green]Tekan Enter untuk kembali...[/]")
        elif choice == '6':
            log.info("SHUTDOWN: Script dihentikan oleh user via Menu.")
            clear_screen()
            sys.exit(0)
            
