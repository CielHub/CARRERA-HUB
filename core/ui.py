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
from rich.rule import Rule
from rich.align import Align

# Instance global
console = Console()

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
    """Membangun Header Utama dengan identitas visual yang konsisten."""
    # 1. Logo Pyfiglet (Font: Slant agar terlihat modern/tech)
    ascii_art = pyfiglet.figlet_format("CARRERA", font="slant")
    # Hapus spasi kosong berlebihan dari output pyfiglet
    ascii_lines = [line for line in ascii_art.split('\n') if line.strip()]
    console.print(Align.center(f"[bold green]{chr(10).join(ascii_lines)}[/]"))
    
    # 2. Subtitle Halaman
    console.print(Align.center(f"[bold cyan]{subtitle}[/]"))
    console.print("") # Whitespace
    
    # 3. Info Bar
    info_text = Text.from_markup(
        "[dim white]Version[/] [bold white]1.0.0[/]  [dim]|[/]  "
        "[dim white]User[/] [bold white]root[/]  [dim]|[/]  "
        "[dim white]Status[/] [bold white]Ready[/]",
        justify="center"
    )
    console.print(info_text)
    
    # 4. Garis Pemisah Tipis
    console.print(Rule(style="dim cyan"))
    console.print("") # Whitespace

def show_transition(message="Loading..."):
    """Menampilkan transisi spinner modern sebelum berpindah halaman."""
    with console.status(f"[dim cyan]{message}[/]", spinner="dots"):
        time.sleep(0.4) # Jeda natural
    reset_terminal()

def draw_footer(text="CTRL+C  Dashboard    CTRL+Z  Exit"):
    """Mencetak Footer minimalis di bagian bawah."""
    console.print("") # Whitespace
    console.print(Text(text, style="dim white", justify="center"))
    
