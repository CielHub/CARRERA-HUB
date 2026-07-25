"""
Modul: ui.py
Tanggung Jawab: Menyediakan komponen UI terminal, warna ANSI, dan Header statis.
"""
import os
import sys
import time
from rich.console import Console
from rich.text import Text

# Instance global
console = Console()

def reset_terminal():
    """Membersihkan layar terminal secara total murni (termasuk scrollback buffer)."""
    sys.stdout.write('\033c\033[2J\033[3J\033[H')
    sys.stdout.flush()
    os.system('clear' if os.name == 'posix' else 'cls')

def get_compact_header(title="CARRERA-HUB v1.0", user="root", pkg_count="-", status="Active"):
    """Header ringkas 1 baris untuk efisiensi ruang layar vertikal."""
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
    
