"""
Modul: ui.py
Tanggung Jawab: Menyediakan komponen UI terminal, warna ANSI, dan Header statis.
"""
import os
import time
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Instance global untuk mencetak output berwarna
console = Console()

def clear_screen():
    """Membersihkan layar terminal."""
    os.system('clear' if os.name == 'posix' else 'cls')

def get_header(package_count="-", status="Online"):
    """Menghasilkan kotak Header ANSI yang konsisten untuk semua halaman."""
    t = time.strftime("%H:%M:%S")
    
    info_table = Table(show_header=False, box=None, expand=True, padding=(0, 2))
    info_table.add_row(
        "[bold cyan]Version[/] : [white]1.0.0[/]",
        "[bold cyan]Platform[/] : [white]Termux[/]",
        "[bold cyan]User[/]   : [white]root[/]"
    )
    info_table.add_row(
        f"[bold cyan]Time[/]    : [white]{t}[/]",
        f"[bold cyan]Packages[/] : [white]{package_count}[/]",
        f"[bold cyan]Status[/] : [white]{status}[/]"
    )
    
    title_text = Text.from_markup(
        "[bold green]CARRERA-HUB Auto Rejoiner[/]\n[white]Roblox Auto Rejoiner for Termux (Python Edition)[/]", 
        justify="center"
    )
    
    header_group = Group(
        title_text,
        Text(""), # Jeda kosong 1 baris
        info_table
    )
    
    # Menggunakan box.ASCII agar kompatibel sempurna dengan font Android
    return Panel(header_group, box=box.ASCII, border_style="bold green")
  
