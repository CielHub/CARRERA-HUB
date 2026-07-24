"""
Modul: launcher.py
Tanggung Jawab: Membuka package Roblox dan menjalankan fungsi Smart Wait.
"""
import subprocess
import time

def launch_and_wait(pkg_name, intent_url, timeout_seconds):
    """Mengeksekusi intent via am start dan menunggu log koneksi dari logcat."""
    print(f"[*] Membuka {pkg_name}...")
    
    # Bersihkan logcat lama
    subprocess.run("logcat -c", shell=True)
    
    # Eksekusi Intent
    am_cmd = f"am start -p '{pkg_name}' -a android.intent.action.VIEW -d '{intent_url}'"
    subprocess.run(am_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"[*] Menunggu {pkg_name} masuk ke server (Smart Wait: {timeout_seconds} detik)...")
    
    # SMART WAIT
    grep_cmd = "logcat | grep -m 1 -iE 'GameJoinUtil|DataModel initialized|successfully connected'"
    logcat_proc = subprocess.Popen(grep_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    elapsed = 0
    # DUMB WAIT FALLBACK
    while logcat_proc.poll() is None:
        if elapsed >= timeout_seconds:
            print(f"[!] Logcat tidak mendeteksi koneksi dalam {timeout_seconds} detik.")
            print(f"[!] Menggunakan Fallback (Dumb Wait). Menganggap {pkg_name} sudah masuk.")
            logcat_proc.kill()
            break
        time.sleep(1)
        elapsed += 1
        
    print(f"[+] {pkg_name} selesai diproses.")
    print("-" * 48)
  
