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

from core.ui import console, reset_terminal, get_compact_header
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
from rich import box

def pause():
    console.input("\n[bold green]Tekan Enter untuk kembali ke Menu Test...[/]")

def test_root():
    console.print(Panel("[bold yellow]--- TEST ROOT ---[/]", box=box.ROUNDED, expand=False))
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
    console.print(Panel("[bold yellow]--- TEST CONFIG ---[/]", box=box.ROUNDED, expand=False))
    config_data = load_config("config.conf")
    for key, value in config_data.items():
        console.print(f"[white]{key}:[/] [cyan]{value}[/]")
    console.print("\n[bold green][OK] Config berhasil dibaca.[/]")
    pause()

def test_logger():
    console.print(Panel("[bold yellow]--- TEST LOGGER ---[/]", box=box.ROUNDED, expand=False))
    console.print("[white]Menulis pesan test ke dalam log...[/]")
    log.info("TESTING: Ini adalah pesan uji coba dari modul tester.py")
    log.warning("TESTING: Ini adalah pesan warning.")
    log.error("TESTING: Ini adalah pesan error.")
    console.print("[bold green][OK] Silakan cek file logs/latest.log untuk melihat hasilnya.[/]")
    pause()

def test_scanner():
    console.print(Panel("[bold yellow]--- TEST SCANNER ---[/]", box=box.ROUNDED, expand=False))
    packages = get_roblox_packages()
    if packages:
        console.print("\n[bold green][OK] Scanner berfungsi dan menemukan package.[/]")
    pause()

def test_deeplink():
    console.print(Panel("[bold yellow]--- TEST DEEP LINK ---[/]", box=box.ROUNDED, expand=False))
    config_data = load_config("config.conf")
    link = config_data.get("PRIVATE_SERVER_LINK", "")
    console.print(f"[white]Link Asli:[/] [cyan]{link}[/]")
    intent_url = get_intent_url(link)
    console.print(f"[white]Intent URL:[/] [cyan]{intent_url}[/]")
    if intent_url:
        console.print("\n[bold green][OK] Deep Link konversi berhasil.[/]")
    pause()

def test_launcher():
    console.print(Panel("[bold yellow]--- TEST LAUNCHER ---[/]", box=box.ROUNDED, expand=False))
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
    console.print(Panel("[bold yellow]--- TEST MONITORING ---[/]", box=box.ROUNDED, expand=False))
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
    while True:
        reset_terminal()
        console.print(get_compact_header(status="Testing"))
        
        menu_text = (
            "[bold green]1.[/] Test Root Access\n"
            "[bold green]2.[/] Test Config Loader\n"
            "[bold green]3.[/] Test Logger System\n"
            "[bold green]4.[/] Test Package Scanner\n"
            "[bold green]5.[/] Test Deep Link Converter\n"
            "[bold green]6.[/] Test Launcher & Smart Wait\n"
            "[bold green]7.[/] Test Monitor (PID Check)\n"
            "[bold green]8.[/] Kembali"
        )
        
        panel = Panel(menu_text, title="[bold white]TEST MENU[/]", box=box.ROUNDED, expand=False, padding=(1, 4))
        console.print("\n")
        console.print(Align.center(panel))
        console.print("\n")
        
        choice = Prompt.ask("Pilih (1-8)", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == '8': 
            break
            
        reset_terminal()
        
        if choice == '1': test_root()
        elif choice == '2': test_config()
        elif choice == '3': test_logger()
        elif choice == '4': test_scanner()
        elif choice == '5': test_deeplink()
        elif choice == '6': test_launcher()
        elif choice == '7': test_monitor()
            
