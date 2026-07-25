"""
Modul: ui.py
Tanggung Jawab: Menyediakan komponen UI terminal, warna ANSI, dan Header statis.
"""
import os
import sys
import time

try:
    import pyfiglet
except ImportError:
    os.system("pip install pyfiglet")
    import pyfiglet

from rich.console import Console
from rich.text import Text

console = Console()
LAYOUT_WIDTH = 60

def reset_terminal():
    """Membersihkan layar terminal secara total murni."""
    sys.stdout.write('\033c\033[2J\033[3J\033[H')
    sys.stdout.flush()
    os.system('clear' if os.name == 'posix' else 'cls')

def get_compact_header(title="CARRERA-HUB v1.0", user="root", pkg_count="-", status="Active"):
    """DIPERTAHANKAN KHUSUS UNTUK DASHBOARD."""
    t = time.strftime("%H:%M:%S")
    header_text = Text.from_markup(
        f"[bold green]{title}[/]  |  "
        f"[dim white]User:[/] [cyan]{user}[/]  |  "
        f"[dim white]Pkg:[/] [cyan]{pkg_count}[/]  |  "
        f"[dim white]Status:[/] [cyan]{status}[/]  |  "
        f"[dim white]Time:[/] [cyan]{t}[/]",
        justify="center"
    )
    return header_text

def draw_header(subtitle="MENU"):
    """Membangun Header Rata Kiri dengan Lebar Tetap (60 Karakter)."""
    # 1. Logo Pyfiglet (Rata Kiri)
    ascii_art = pyfiglet.figlet_format("CARRERA", font="slant")
    for line in ascii_art.split('\n'):
        if line.strip():
            console.print(f"[bold green]{line}[/]")
    
    # 2. Subtitle Halaman
    console.print(f"[bold cyan]{subtitle}[/]")
    console.print("")
    
    # 3. Info Bar (Teks diatur agar persis berjumlah 60 karakter, berhenti di 'y')
    info_text = "Version 1.0.0      |      User root      |      Status Ready"
    console.print(f"[dim white]{info_text}[/]")
    
    # 4. Garis Pemisah Tipis (Hanya sepanjang 60 karakter)
    console.print("[dim cyan]" + "─" * LAYOUT_WIDTH + "[/]")
    console.print("")

def show_transition(message="Loading..."):
    """Menampilkan transisi spinner modern sebelum berpindah halaman."""
    with console.status(f"[dim cyan]{message}[/]", spinner="dots"):
        time.sleep(0.4) 
    reset_terminal()

def draw_footer(text="CTRL+C  Dashboard    CTRL+Z  Exit"):
    """Mencetak Footer minimalis di bagian bawah (Rata Kiri)."""
    console.print("") 
    console.print(f"[dim white]{text}[/]")
    
