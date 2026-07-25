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

# Impor Layout Engine
from core.ui import console, reset_terminal, draw_header, show_transition, draw_footer
from rich.prompt import Prompt
from rich.table import Table
from rich.align import Align

def pause():
    draw_footer("Enter  Kembali ke Menu Test")
    console.input("\n[dim]Tekan Enter...[/]")

def test_root():
    console.print("\n[dim]--- TEST ROOT ---[/]", justify="center")
    try:
        uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
    except Exception:
        import os
        uid = os.geteuid()
        
    console.print(f"\n[white]Current UID:[/] [cyan]{uid}[/]", justify="center")
    if uid == 0:
        console.print("[bold green][OK] Sistem berjalan sebagai Root.[/]", justify="center")
    else:
        console.print("[bold red][FAIL] Sistem TIDAK berjalan sebagai Root.[/]", justify="center")
    pause()

def test_config():
    console.print("\n[dim]--- TEST CONFIG ---[/]", justify="center")
    config_data = load_config("config.conf")
    
    table = Table(box=None, padding=(0, 2), show_header=False, expand=False)
    for key, value in config_data.items():
        table.add_row(f"[white]{key}[/]", f"[cyan]{value}[/]")
    
    console.print("\n")
    console.print(Align.center(table))
    console.print("\n[bold green][OK] Config berhasil dibaca.[/]", justify="center")
    pause()

def test_logger():
    console.print("\n[dim]--- TEST LOGGER ---[/]", justify="center")
    console.print("\n[white]Menulis pesan test ke dalam log...[/]", justify="center")
    log.info("TESTING: Ini adalah pesan uji coba dari modul tester.py")
    log.warning("TESTING: Ini adalah pesan warning.")
    log.error("TESTING: Ini adalah pesan error.")
    console.print("\n[bold green][OK] Silakan cek file logs/latest.log untuk melihat hasilnya.[/]", justify="center")
    pause()

def test_scanner():
    console.print("\n[dim]--- TEST SCANNER ---[/]", justify="center")
    packages = get_roblox_packages()
    if packages:
        console.print("\n[bold green][OK] Scanner berfungsi dan menemukan package.[/]", justify="center")
    pause()

def test_deeplink():
    console.print("\n[dim]--- TEST DEEP LINK ---[/]", justify="center")
    config_data = load_config("config.conf")
    link = config_data.get("PRIVATE_SERVER_LINK", "")
    console.print(f"\n[white]Link Asli:[/] [cyan]{link}[/]", justify="center")
    intent_url = get_intent_url(link)
    console.print(f"[white]Intent URL:[/] [cyan]{intent_url}[/]", justify="center")
    if intent_url:
        console.print("\n[bold green][OK] Deep Link konversi berhasil.[/]", justify="center")
    pause()

def test_launcher():
    console.print("\n[dim]--- TEST LAUNCHER ---[/]", justify="center")
    packages = get_roblox_packages()
    if not packages:
        console.print("\n[bold red][!] Tidak ada package untuk dites.[/]", justify="center")
        pause()
        return
        
    pkg = packages[0]
    console.print(f"\n[white]Akan melakukan test launch pada:[/] [cyan]{pkg}[/]", justify="center")
    config_data = load_config("config.conf")
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    
    console.print("\n[dim]Mengeksekusi Launch & Smart Wait...[/]", justify="center")
    success = launch_and_wait(pkg, intent_url, config_data["TIMEOUT_SECONDS"])
    
    if success:
        console.print("\n[bold green][OK] Launcher mengembalikan nilai True (Sukses).[/]", justify="center")
    else:
        console.print("\n[bold red][FAIL] Launcher mengembalikan nilai False (Gagal).[/]", justify="center")
    pause()

def test_monitor():
    console.print("\n[dim]--- TEST MONITORING ---[/]", justify="center")
    packages = get_roblox_packages()
    if not packages:
        console.print("\n[bold red][!] Tidak ada package untuk dites.[/]", justify="center")
        pause()
        return
        
    console.print("\n[white]Mencari PID aktif untuk package yang terdeteksi:[/]", justify="center")
    for pkg in packages:
        pid = get_pid(pkg)
        if pid:
            console.print(f"[bold green][OK] {pkg} SEDANG BERJALAN (PID: {pid})[/]", justify="center")
        else:
            console.print(f"[bold red][INFO] {pkg} SEDANG MATI[/]", justify="center")
    pause()

def show_test_menu():
    show_transition("Initializing Test Environment...")
    while True:
        reset_terminal()
        draw_header("UNIT TESTING")
        
        table = Table(box=None, padding=(0, 2), show_header=False, expand=False)
        table.add_column("No", style="bold cyan", justify="right")
        table.add_column("Icon", style="white", justify="center")
        table.add_column("Test", style="white", justify="left")
        table.add_column("Chevron", style="dim white", justify="right")
        
        table.add_row("[1]", "🔑", "Test Root Access", ">")
        table.add_row("[2]", "📄", "Test Config Loader", ">")
        table.add_row("[3]", "🐛", "Test Logger System", ">")
        table.add_row("[4]", "🔎", "Test Package Scanner", ">")
        table.add_row("[5]", "🔗", "Test Deep Link Converter", ">")
        table.add_row("[6]", "🚀", "Test Launcher & Smart Wait", ">")
        table.add_row("[7]", "📊", "Test Monitor (PID Check)", ">")
        table.add_row("[8]", "↩ ", "Kembali", ">")
        
        console.print(Align.center(table))
        draw_footer("ESC / 8  Back to Menu")
        
        choice = Prompt.ask("\n[dim]Pilih test (1-8)[/]", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == '8': 
            break
            
        show_transition(f"Preparing Test {choice}...")
        reset_terminal()
        draw_header(f"TEST RUNNER: {choice}")
        
        if choice == '1': test_root()
        elif choice == '2': test_config()
        elif choice == '3': test_logger()
        elif choice == '4': test_scanner()
        elif choice == '5': test_deeplink()
        elif choice == '6': test_launcher()
        elif choice == '7': test_monitor()
            
