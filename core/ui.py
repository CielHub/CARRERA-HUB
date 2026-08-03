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
LAYOUT_WIDTH = 60 # Dipertahankan sebagai fallback/kompatibilitas untuk modul lama

def reset_terminal():
    """Membersihkan layar terminal secara aman tanpa merusak history (scrollback)."""
    # BUG FIX: Menggunakan fitur native dari rich console yang kompatibel dengan Termux OS
    console.clear()

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
    """Membangun Header responsif yang mendeteksi ukuran kolom Terminal secara dinamis."""
    current_width = console.width
    
    # 1. Fallback cerdas untuk layar sempit (Zoom in maksimal)
    if current_width < 45:
        console.print("[bold green]CARRERA-HUB[/]")
    else:
        try:
            ascii_art = pyfiglet.figlet_format("CARRERA", font="small")
        except Exception:
            ascii_art = pyfiglet.figlet_format("CARRERA")
            
        for line in ascii_art.split('\n'):
            if line.strip():
                console.print(f"[bold green]{line}[/]")
    
    # 2. Info Bar Padat
    console.print(f"[bold cyan]{subtitle}[/] [dim white]| Version 1.0.0 | User root[/]")
    
    # 3. Garis Pemisah Dinamis
    line_width = min(current_width, 60)
    console.print("[dim cyan]" + "─" * line_width + "[/]")

def show_transition(message="Loading..."):
    """Menampilkan transisi spinner modern sebelum berpindah halaman."""
    with console.status(f"[dim cyan]{message}[/]", spinner="dots"):
        time.sleep(0.4) 
    reset_terminal()

def draw_footer(text="CTRL+C  Dashboard    CTRL+Z  Exit"):
    """Mencetak Footer minimalis di bagian bawah (Rata Kiri)."""
    console.print(f"\n[dim white]{text}[/]")
    
