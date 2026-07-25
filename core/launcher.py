"""
Modul: launcher.py
Tanggung Jawab: Membuka package Roblox dan menjalankan fungsi Smart Wait.
"""
import subprocess
import time
from core.logger import log

def get_pid_quick(pkg_name):
    """Fungsi helper internal untuk mengecek PID secara instan."""
    result = subprocess.run(f"pidof '{pkg_name}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def launch_and_wait(pkg_name, intent_url, timeout_seconds):
    """Mengeksekusi intent, menunggu log koneksi, dan mereturn True/False berdasarkan keberhasilan."""
    log.info(f"LAUNCH: Membuka {pkg_name}...")
    
    subprocess.run("logcat -c", shell=True)
    am_cmd = f"am start -p '{pkg_name}' -a android.intent.action.VIEW -d '{intent_url}'"
    subprocess.run(am_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    log.info(f"Smart Wait: Menunggu {pkg_name} terhubung ({timeout_seconds} detik)...")
    
    grep_cmd = "logcat | grep -m 1 -iE 'GameJoinUtil|DataModel initialized|successfully connected'"
    logcat_proc = subprocess.Popen(grep_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    elapsed = 0
    while logcat_proc.poll() is None:
        if elapsed >= timeout_seconds:
            log.warning(f"FALLBACK: Logcat timeout. Menggunakan Dumb Wait untuk {pkg_name}.")
            logcat_proc.kill()
            break
        time.sleep(1)
        elapsed += 1
        
    # [PHASE 5] Deteksi Recovery Gagal
    final_pid = get_pid_quick(pkg_name)
    if not final_pid:
        log.error(f"LAUNCH FAILED: {pkg_name} gagal diluncurkan (Proses mati secara prematur).")
        return False
        
    log.info(f"SUCCESS: {pkg_name} selesai diproses.")
    return True
    
