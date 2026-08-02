"""
Modul: launcher.py
Tanggung Jawab: Membuka package Roblox dan menjalankan fungsi Smart Wait dengan aman.
"""
import subprocess
import time
import datetime
import select
from core.logger import log

def get_pid_quick(pkg_name):
    # [OPTIMISASI - PID Fix]
    # Mencegah False Crash jika pidof mengembalikan multi-PID dari proses anak (misal: "1234 1235")
    try:
        result = subprocess.run(['pidof', pkg_name], capture_output=True, text=True)
        pids = result.stdout.strip().split()
        return pids[0] if pids else ""
    except Exception:
        return ""

def launch_and_wait(pkg_name, intent_url, timeout_seconds):
    log.info(f"LAUNCH: Membuka {pkg_name}...")
    
    # 1. Ambil timestamp saat ini sebelum membuka aplikasi (Format: MM-DD HH:MM:SS.000)
    # Ini MENGGANTIKAN 'logcat -c' yang brutal menghapus buffer logcat seluruh sistem
    start_time_str = datetime.datetime.now().strftime('%m-%d %H:%M:%S.000')
    
    # 2. Buka aplikasi via am start
    subprocess.run(
        ['am', 'start', '-p', pkg_name, '-a', 'android.intent.action.VIEW', '-d', intent_url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    
    log.info(f"Smart Wait: Menunggu {pkg_name} terhubung ({timeout_seconds} detik)...")
    
    # 3. Eksekusi logcat HANYA menampilkan log baru sejak timestamp tadi
    # TANPA shell=True untuk mencegah Pipeline/Zombie Process dari grep
    logcat_cmd = ['logcat', '-T', start_time_str, '-v', 'time']
    process = subprocess.Popen(
        logcat_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1 # Line buffered
    )
    
    keywords = ["gamejoinutil", "datamodel initialized", "successfully connected"]
    found_success = False
    start_time = time.time()
    
    try:
        # 4. Loop non-blocking menggunakan mekanisme select Linux
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                log.warning(f"FALLBACK: Logcat timeout. Menggunakan Dumb Wait untuk {pkg_name}.")
                break
                
            # Tunggu maksimal 1 detik apakah ada output logcat yang bisa dibaca di memory buffer
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            
            if ready:
                line = process.stdout.readline()
                if not line:
                    break # Stream proses mati atau End Of File
                
                line_lower = line.lower()
                if any(kw in line_lower for kw in keywords):
                    found_success = True
                    break
    finally:
        # 5. PENTING: Selalu bersihkan file descriptor dan memory process setelah selesai
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill() # Eksekusi paksa SIGKILL jika membandel
        
    final_pid = get_pid_quick(pkg_name)
    if not final_pid:
        log.error(f"LAUNCH FAILED: {pkg_name} gagal diluncurkan (Proses mati secara prematur).")
        return False
        
    log.info(f"SUCCESS: {pkg_name} selesai diproses.")
    return True

