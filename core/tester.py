"""
Modul: tester.py
Tanggung Jawab: Menyediakan framework pengujian (Unit Test) untuk setiap modul secara terisolasi.
"""
import os
import subprocess
from core.logger import log
from core.config import load_config
from core.deeplink import get_intent_url
from core.scanner import get_roblox_packages
from core.launcher import launch_and_wait
from core.monitor import get_pid

# [UX UPGRADE] Gunakan reset_terminal
from core.ui import console, reset_terminal, get_header
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

def pause():
    console.input("\n[bold green]Tekan Enter untuk kembali ke Menu Test...[/]")

def test_root():
    console.print(Panel("[bold yellow]--- TEST ROOT ---[/]", box=box.ASCII))
    try:
        uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
    except Exception:
        import os
        uid = os.geteuid()
        
    console.print(f"[white]Current UID:[/] [cyan]{uid}[/]")
    if uid == 0:
        console.print("[bold green][OK] Sistem berjalan sebagai Root.[/]")
    else:
        console.print("[bold red][FAIL] Sistem TIDAK berjalan sebagai Root.[/]")
    pause()

def test_config():
    console.print(Panel("[bold yellow]--- TEST CONFIG ---[/]", box=box.ASCII))
    config_data = load_config("config.conf")
    for key, value in config_data.items():
        console.print(f"[white]{key}:[/] [cyan]{value}[/]")
    console.print("\n[bold green][OK] Config berhasil dibaca.[/]")
    pause()

def test_logger():
    console.print(Panel("[bold yellow]--- TEST LOGGER ---[/]", box=box.ASCII))
    console.print("[white]Menulis pesan test ke dalam log...[/]")
    log.info("TESTING: Ini adalah pesan uji coba dari modul tester.py")
    log.warning("TESTING: Ini adalah pesan warning.")
    log.error("TESTING: Ini adalah pesan error.")
    console.print("[bold green][OK] Silakan cek file logs/latest.log untuk melihat hasilnya.[/]")
    pause()

def test_scanner():
    console.print(Panel("[bold yellow]--- TEST SCANNER ---[/]", box=box.ASCII))
    packages = get_roblox_packages()
    if packages:
        console.print("\n[bold green][OK] Scanner berfungsi dan menemukan package.[/]")
    pause()

def test_deeplink():
    console.print(Panel("[bold yellow]--- TEST DEEP LINK ---[/]", box=box.ASCII))
    config_data = load_config("config.conf")
    link = config_data.get("PRIVATE_SERVER_LINK", "")
    console.print(f"[white]Link Asli:[/] [cyan]{link}[/]")
    intent_url = get_intent_url(link)
    console.print(f"[white]Intent URL:[/] [cyan]{intent_url}[/]")
    if intent_url:
        console.print("\n[bold green][OK] Deep Link konversi berhasil.[/]")
    pause()

def test_launcher():
    console.print(Panel("[bold yellow]--- TEST LAUNCHER ---[/]", box=box.ASCII))
    packages = get_roblox_packages()
    if not packages:
        console.print("[bold red][!] Tidak ada package untuk dites.[/]")
        pause()
        return
        
    pkg = packages[0]
    console.print(f"[white]Akan melakukan test launch pada:[/] [cyan]{pkg}[/]")
    config_data = load_config("config.conf")
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    
    console.print("\n[dim]Mengeksekusi Launch & Smart Wait...[/]")
    success = launch_and_wait(pkg, intent_url, config_data["TIMEOUT_SECONDS"])
    
    if success:
        console.print("\n[bold green][OK] Launcher mengembalikan nilai True (Sukses).[/]")
    else:
        console.print("\n[bold red][FAIL] Launcher mengembalikan nilai False (Gagal).[/]")
    pause()

def test_monitor():
    console.print(Panel("[bold yellow]--- TEST MONITORING (PID CATCHER) ---[/]", box=box.ASCII))
    packages = get_roblox_packages()
    if not packages:
        console.print("[bold red][!] Tidak ada package untuk dites.[/]")
        pause()
        return
        
    console.print("[white]Mencari PID aktif untuk package yang terdeteksi:[/]")
    for pkg in packages:
        pid = get_pid(pkg)
        if pid:
            console.print(f"[bold green][OK] {pkg} SEDANG BERJALAN (PID: {pid})[/]")
        else:
            console.print(f"[bold red][INFO] {pkg} SEDANG MATI[/]")
    pause()

def show_test_menu():
    """Menampilkan Sub-Menu Testing."""
    while True:
        reset_terminal()
        console.print(get_header(status="Testing"))
        console.print("\n[bold yellow]==================== MENU TESTING ====================[/]\n", justify="center")
        
        console.print("[bold green][ 1 ][/] [white]Test Root Access[/]")
        console.print("[bold green][ 2 ][/] [white]Test Config Loader[/]")
        console.print("[bold green][ 3 ][/] [white]Test Logger System[/]")
        console.print("[bold green][ 4 ][/] [white]Test Package Scanner[/]")
        console.print("[bold green][ 5 ][/] [white]Test Deep Link Converter[/]")
        console.print("[bold green][ 6 ][/] [white]Test Launcher & Smart Wait[/]")
        console.print("[bold green][ 7 ][/] [white]Test Monitor (PID Check)[/]")
        console.print("[bold green][ 8 ][/] [white]Kembali ke Menu Utama[/]\n")
        
        choice = Prompt.ask("Pilih test (1-8)", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == '8': 
            break
            
        # Bersihkan terminal sebelum merender hasil test spesifik
        reset_terminal()
        
        if choice == '1': test_root()
        elif choice == '2': test_config()
        elif choice == '3': test_logger()
        elif choice == '4': test_scanner()
        elif choice == '5': test_deeplink()
        elif choice == '6': test_launcher()
        elif choice == '7': test_monitor()
            
