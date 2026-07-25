"""
Modul: launcher.py
Tanggung Jawab: Membuka package Roblox dan menjalankan fungsi Smart Wait.
"""
import subprocess
import time
from core.logger import log

def get_pid_quick(pkg_name):
    # [PHASE 7 OPTIMIZATION]
    # Menghilangkan shell=True, langsung eksekusi binary 'pidof'
    try:
        result = subprocess.run(['pidof', pkg_name], capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return ""

def launch_and_wait(pkg_name, intent_url, timeout_seconds):
    log.info(f"LAUNCH: Membuka {pkg_name}...")
    
    # [PHASE 7 OPTIMIZATION]
    # Hindari overhead shell bash, eksekusi langsung ke sistem operasi Android
    subprocess.run(['logcat', '-c'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['am', 'start', '-p', pkg_name, '-a', 'android.intent.action.VIEW', '-d', intent_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
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
        
    final_pid = get_pid_quick(pkg_name)
    if not final_pid:
        log.error(f"LAUNCH FAILED: {pkg_name} gagal diluncurkan (Proses mati secara prematur).")
        return False
        
    log.info(f"SUCCESS: {pkg_name} selesai diproses.")
    return True
    
