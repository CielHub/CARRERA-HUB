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

from core.ui import console, reset_terminal, draw_header, show_transition, draw_footer
from rich.prompt import Prompt
from rich.table import Table
from rich.padding import Padding

def pause():
    draw_footer("Enter  Kembali ke Menu Test")
    console.input("\n[dim]Tekan Enter...[/]")

def test_root():
    console.print(Padding("\n[dim]--- TEST ROOT ---[/]", (0, 0, 0, 4)))
    try:
        uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
    except Exception:
        import os
        uid = os.geteuid()
        
    console.print(Padding(f"\n[white]Current UID:[/] [cyan]{uid}[/]", (0, 0, 0, 4)))
    if uid == 0:
        console.print(Padding("[bold green][OK] Sistem berjalan sebagai Root.[/]", (0, 0, 0, 4)))
    else:
        console.print(Padding("[bold red][FAIL] Sistem TIDAK berjalan sebagai Root.[/]", (0, 0, 0, 4)))
    pause()

def test_config():
    console.print(Padding("\n[dim]--- TEST CONFIG ---[/]", (0, 0, 0, 4)))
    config_data = load_config("config.conf")
    
    table = Table(box=None, padding=(0, 2), show_header=False, expand=False)
    for key, value in config_data.items():
        table.add_row(f"[white]{key}[/]", f"[cyan]{value}[/]")
    
    console.print("\n")
    console.print(Padding(table, (0, 0, 0, 4)))
    console.print(Padding("\n[bold green][OK] Config berhasil dibaca.[/]", (0, 0, 0, 4)))
    pause()

def test_logger():
    console.print(Padding("\n[dim]--- TEST LOGGER ---[/]", (0, 0, 0, 4)))
    console.print(Padding("\n[white]Menulis pesan test ke dalam log...[/]", (0, 0, 0, 4)))
    log.info("TESTING: Ini adalah pesan uji coba dari modul tester.py")
    log.warning("TESTING: Ini adalah pesan warning.")
    log.error("TESTING: Ini adalah pesan error.")
    console.print(Padding("\n[bold green][OK] Silakan cek file logs/latest.log untuk melihat hasilnya.[/]", (0, 0, 0, 4)))
    pause()

def test_scanner():
    console.print(Padding("\n[dim]--- TEST SCANNER ---[/]", (0, 0, 0, 4)))
    packages = get_roblox_packages()
    if packages:
        console.print(Padding("\n[bold green][OK] Scanner berfungsi dan menemukan package.[/]", (0, 0, 0, 4)))
    pause()

def test_deeplink():
    console.print(Padding("\n[dim]--- TEST DEEP LINK ---[/]", (0, 0, 0, 4)))
    config_data = load_config("config.conf")
    link = config_data.get("PRIVATE_SERVER_LINK", "")
    console.print(Padding(f"\n[white]Link Asli:[/] [cyan]{link}[/]", (0, 0, 0, 4)))
    intent_url = get_intent_url(link)
    console.print(Padding(f"[white]Intent URL:[/] [cyan]{intent_url}[/]", (0, 0, 0, 4)))
    if intent_url:
        console.print(Padding("\n[bold green][OK] Deep Link konversi berhasil.[/]", (0, 0, 0, 4)))
    pause()

def test_launcher():
    console.print(Padding("\n[dim]--- TEST LAUNCHER ---[/]", (0, 0, 0, 4)))
    packages = get_roblox_packages()
    if not packages:
        console.print(Padding("\n[bold red][!] Tidak ada package untuk dites.[/]", (0, 0, 0, 4)))
        pause()
        return
        
    pkg = packages[0]
    console.print(Padding(f"\n[white]Akan melakukan test launch pada:[/] [cyan]{pkg}[/]", (0, 0, 0, 4)))
    config_data = load_config("config.conf")
    intent_url = get_intent_url(config_data["PRIVATE_SERVER_LINK"])
    
    console.print(Padding("\n[dim]Mengeksekusi Launch & Smart Wait...[/]", (0, 0, 0, 4)))
    success = launch_and_wait(pkg, intent_url, config_data["TIMEOUT_SECONDS"])
    
    if success:
        console.print(Padding("\n[bold green][OK] Launcher mengembalikan nilai True (Sukses).[/]", (0, 0, 0, 4)))
    else:
        console.print(Padding("\n[bold red][FAIL] Launcher mengembalikan nilai False (Gagal).[/]", (0, 0, 0, 4)))
    pause()

def test_monitor():
    console.print(Padding("\n[dim]--- TEST MONITOR ---[/]", (0, 0, 0, 4)))
    packages = get_roblox_packages()
    if not packages:
        console.print(Padding("\n[bold red][!] Tidak ada package untuk dites.[/]", (0, 0, 0, 4)))
        pause()
        return
        
    console.print(Padding("\n[white]Mencari PID aktif untuk package yang terdeteksi:[/]", (0, 0, 0, 4)))
    for pkg in packages:
        pid = get_pid(pkg)
        if pid:
            console.print(Padding(f"[bold green][OK] {pkg} SEDANG BERJALAN (PID: {pid})[/]", (0, 0, 0, 4)))
        else:
            console.print(Padding(f"[bold red][INFO] {pkg} SEDANG MATI[/]", (0, 0, 0, 4)))
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
        
        # Diubah menjadi Rata Kiri dengan padding 4 spasi
        console.print(Padding(table, (0, 0, 0, 4)))
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
        
