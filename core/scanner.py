"""
Modul: scanner.py
Tanggung Jawab: Memindai seluruh package Roblox yang terinstal di sistem.
"""
import subprocess
import sys
from core.logger import log

def get_roblox_packages():
    """Menjalankan pm list packages dan memfilter nama yang mengandung 'roblox'."""
    log.info("SCANNER: Melakukan scan package Roblox...")
    try:
        raw_packages = subprocess.check_output(
            "pm list packages | grep -i 'roblox' | cut -d':' -f2", 
            shell=True, text=True
        )
        packages = [pkg.strip() for pkg in raw_packages.strip().split('\n') if pkg.strip()]
    except subprocess.CalledProcessError:
        packages = []

    if not packages:
        log.error("SCANNER: Tidak ada package Roblox yang terdeteksi!")
        sys.exit(1)

    log.info(f"SCANNER: Ditemukan {len(packages)} package Roblox:")
    for pkg in packages:
        log.info(f" -> {pkg}")
    
    return packages
    
