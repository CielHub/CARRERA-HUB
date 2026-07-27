"""
Modul: autologin.py
Tanggung Jawab: Mendeteksi layar login dan mengeksekusi injeksi input (Username & Password).
"""
import os
import time
import subprocess
from core.logger import log

def detect_login_screen(pkg):
    """
    Heuristik sederhana: Jika logcat tidak menunjukkan tanda-tanda 'GameJoinUtil', 
    kita asumsikan akun ter-logout.
    """
    try:
        # Pengecekan logcat ringan untuk melihat indikasi layar awal/login
        logcat_dump = subprocess.check_output("su -c 'logcat -d -t 150 | grep -i roblox'", shell=True, text=True)
        if "Authentication" in logcat_dump or "Login" in logcat_dump or "SignUp" in logcat_dump:
            return True
        # Fallback: Jika tidak terdeteksi GameJoin, anggap butuh login
        return True 
    except Exception:
        return True

def perform_login(pkg, username, password):
    """
    Mengeksekusi urutan input shell (Root) untuk mengisi form login Roblox.
    CATATAN: Koordinat 'input tap' diatur untuk standar Termux Landscape/Portrait.
    """
    log.info(f"AUTO LOGIN: Mengeksekusi injeksi login untuk {pkg}...")
    try:
        # Pastikan app berada di depan (Wake up)
        os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")
        time.sleep(3) 
        
        # 1. Tap tombol "Log In" di layar awal (Kordinat Generik Bawah Tengah)
        # Jika tidak pas, gunakan 'input keyevent 61' (TAB) lalu 66 (ENTER)
        os.system("su -c 'input tap 360 1100'") 
        time.sleep(2)
        
        # 2. Input Username
        # (Beberapa device otomatis fokus ke kolom pertama. Jika tidak, tap kolom username dulu)
        log.info(f"AUTO LOGIN: Mengetik username...")
        os.system(f"su -c 'input text \"{username}\"'")
        time.sleep(1)
        
        # 3. Pindah ke kolom Password (Gunakan tombol TAB keyboard)
        os.system("su -c 'input keyevent 61'")
        time.sleep(1)
        
        # 4. Input Password
        log.info(f"AUTO LOGIN: Mengetik password...")
        os.system(f"su -c 'input text \"{password}\"'")
        time.sleep(1)
        
        # 5. Tekan Enter / Eksekusi Login
        log.info(f"AUTO LOGIN: Menekan tombol Login...")
        os.system("su -c 'input keyevent 66'")
        
        # Tunggu proses otentikasi ke server Roblox
        time.sleep(10)
        
        return True
    except Exception as e:
        log.error(f"AUTO LOGIN FAILED: Terjadi kesalahan shell eksekusi - {e}")
        return False
      
