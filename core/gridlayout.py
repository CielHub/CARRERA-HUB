"""
Modul: gridlayout.py
Tanggung Jawab: Deteksi resolusi layar & taskId freeform, hitung layout grid,
                dan mengatur ukuran/posisi window tiap package via `am task resize`.

CATATAN:
- Hanya berfungsi untuk window yang berjalan di Android Freeform Mode
  (developer options -> force activities to be resizable / freeform support).
- `am task resize <taskId> <left> <top> <right> <bottom>` bekerja dalam satuan
  PIXEL layar (bukan dp), jadi semua perhitungan grid di sini pakai pixel.
"""
import re
import math
import subprocess
from core.logger import log


def _sh_out(cmd, default=""):
    try:
        return subprocess.check_output(f"su -c \"{cmd}\"", shell=True, text=True)
    except Exception:
        return default


# =====================================================================
# INFO LAYAR
# =====================================================================
def get_screen_size():
    """Ambil resolusi layar fisik dalam pixel. Return (width, height) atau None."""
    raw = _sh_out("wm size")
    # Contoh output: "Physical size: 1080x2400" (atau "Override size: ..." kalau dioverride)
    m = re.search(r"(?:Override|Physical) size:\s*(\d+)x(\d+)", raw)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def get_screen_density():
    """Ambil density layar (dpi). Return int atau None."""
    raw = _sh_out("wm density")
    m = re.search(r"(?:Override|Physical) density:\s*(\d+)", raw)
    if not m:
        return None
    return int(m.group(1))


# =====================================================================
# TASK ID LOOKUP (freeform)
# =====================================================================
def get_task_id(pkg):
    """
    Cari taskId freeform milik package tertentu dari dumpsys activity.
    Best-effort parsing karena format dumpsys beda-beda tiap versi Android.
    """
    raw = _sh_out("dumpsys activity activities")
    if not raw:
        return None

    blocks = re.split(r"(?=\* Task\{)|(?=TaskRecord\{)", raw)
    for block in blocks:
        if pkg not in block:
            continue
        m_task = re.search(r"(?:\* Task\{[^}]*#(\d+)|taskId=(\d+))", block)
        if not m_task:
            continue
        task_id = m_task.group(1) or m_task.group(2)
        # pastikan blok ini memang activity milik pkg (realActivity / package field)
        if re.search(rf"realActivity={re.escape(pkg)}/", block) or re.search(rf"\b{re.escape(pkg)}\b", block):
            return task_id
    return None


def resize_task(task_id, left, top, right, bottom):
    """Resize + pindahkan task freeform ke bounds tertentu. Return True/False."""
    cmd = f"am task resize {task_id} {left} {top} {right} {bottom}"
    result = _sh_out(cmd)
    ok = "Error" not in result and "error" not in result
    return ok


# =====================================================================
# PERHITUNGAN GRID
# =====================================================================
def auto_grid_dims(n, screen_w, screen_h):
    """
    Cari kombinasi (cols, rows) yang memaksimalkan ukuran sel terkecil
    (biar window sebisa mungkin proporsional, gak ada yang kepipihin).
    """
    best = None
    for cols in range(1, n + 1):
        rows = math.ceil(n / cols)
        cell_w = screen_w // cols
        cell_h = screen_h // rows
        score = min(cell_w, cell_h)
        if best is None or score > best[0]:
            best = (score, cols, rows)
    return best[1], best[2]


def compute_grid_positions(packages, screen_w, screen_h, cell_w=None, cell_h=None,
                            cols=None, margin=10, offset_x=0, offset_y=60):
    """
    Hitung posisi (left, top, right, bottom) tiap package dalam grid.
    - cell_w/cell_h: ukuran window (px). Kalau None -> dihitung otomatis dari layar.
    - cols: jumlah kolom. Kalau None -> dihitung otomatis (auto_grid_dims).
    - offset_y: jarak dari atas layar (default 60px, biar gak ketutup status bar).
    Return: dict {pkg: (left, top, right, bottom)}
    """
    n = len(packages)
    usable_w = screen_w - offset_x
    usable_h = screen_h - offset_y

    if cols is None:
        auto_cols, auto_rows = auto_grid_dims(n, usable_w, usable_h)
        cols = auto_cols
    rows = math.ceil(n / cols)

    if cell_w is None:
        cell_w = (usable_w - margin * (cols + 1)) // cols
    if cell_h is None:
        cell_h = (usable_h - margin * (rows + 1)) // rows

    cell_w = max(cell_w, 100)   # batas minimum biar gak ke-resize jadi 0/negatif
    cell_h = max(cell_h, 100)

    positions = {}
    for idx, pkg in enumerate(packages):
        row = idx // cols
        col = idx % cols
        left = offset_x + margin + col * (cell_w + margin)
        top = offset_y + margin + row * (cell_h + margin)
        right = left + cell_w
        bottom = top + cell_h
        positions[pkg] = (left, top, right, bottom)

    return positions, cols, rows, cell_w, cell_h


# =====================================================================
# EKSEKUSI
# =====================================================================
def apply_grid(packages, cell_w=None, cell_h=None, cols=None, margin=10, offset_x=0, offset_y=60):
    """
    Terapkan grid ke semua package yang diberikan. Return dict {pkg: True/False}.
    Package yang belum punya taskId (belum jalan) otomatis dilewati.
    """
    screen = get_screen_size()
    if not screen:
        log.error("GRID: Gagal membaca resolusi layar (wm size).")
        return {}

    screen_w, screen_h = screen
    positions, cols_used, rows_used, cw, ch = compute_grid_positions(
        packages, screen_w, screen_h, cell_w, cell_h, cols, margin, offset_x, offset_y
    )
    log.info(f"GRID: Layout {cols_used}x{rows_used}, cell {cw}x{ch}px, layar {screen_w}x{screen_h}px.")

    results = {}
    for pkg, (l, t, r, b) in positions.items():
        task_id = get_task_id(pkg)
        if not task_id:
            log.warning(f"GRID: {pkg} belum punya taskId aktif (belum jalan?), dilewati.")
            results[pkg] = False
            continue
        ok = resize_task(task_id, l, t, r, b)
        if ok:
            log.info(f"GRID: {pkg} -> posisi ({l},{t})-({r},{b}) [task {task_id}]")
        else:
            log.warning(f"GRID: Gagal resize {pkg} (task {task_id}).")
        results[pkg] = ok

    return results


def apply_grid_single(pkg, packages_order, cell_w=None, cell_h=None, cols=None,
                       margin=10, offset_x=0, offset_y=60):
    """
    Terapkan posisi grid untuk SATU package saja, berdasarkan urutannya di
    packages_order (dipakai buat auto re-apply posisi tiap kali sebuah
    package selesai di-(re)launch, tanpa perlu resize ulang semua window).
    """
    screen = get_screen_size()
    if not screen:
        return False
    screen_w, screen_h = screen
    positions, _, _, _, _ = compute_grid_positions(
        packages_order, screen_w, screen_h, cell_w, cell_h, cols, margin, offset_x, offset_y
    )
    if pkg not in positions:
        return False
    l, t, r, b = positions[pkg]
    task_id = get_task_id(pkg)
    if not task_id:
        return False
    return resize_task(task_id, l, t, r, b)
