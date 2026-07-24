import os
import sys
import subprocess
import time
import re

# ==========================================
# 0. AUTO REQUEST ROOT & DIRECTORY SETUP
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAME = os.path.basename(__file__)

# Cek apakah script sudah berjalan sebagai root (UID 0)
try:
    uid = int(subprocess.check_output(['id', '-u']).decode('utf-8').strip())
except Exception:
    uid = os.geteuid() # Fallback

if uid != 0:
    print("[*] Script ini membutuhkan akses Root untuk bekerja.")
    print("[*] Meminta izin Root ke sistem...")
    
    # Ambil lokasi absolute dari binary python Termux saat ini
    python_bin = sys.executable
    
    # Eksekusi ulang script menggunakan absolute path python
    cmd = f"su -c \"{python_bin} '{os.path.join(SCRIPT_DIR, SCRIPT_NAME)}'\""
    exit_code = subprocess.call(cmd, shell=True)
    
    if exit_code != 0:
        print("-" * 48)
        print("[!] Gagal mendapatkan akses Root.")
        print("[!] Pastikan HP sudah di-root dan berikan izin (Grant) pada prompt Magisk/KernelSU.")
        sys.exit(1)
        
    # Tutup instance non-root
    sys.exit(0)

# Pindah ke direktori script agar file config.conf terbaca
os.chdir(SCRIPT_DIR)


# ==========================================
# 1. LOAD CONFIG & PARSE URL TO DEEP LINK
# ==========================================
CONFIG_FILE = "config.conf"

if not os.path.isfile(CONFIG_FILE):
    print(f"[!] File {CONFIG_FILE} tidak ditemukan di: {SCRIPT_DIR}")
    sys.exit(1)

# Manual parser untuk menggantikan perintah 'source' di Bash
PRIVATE_SERVER_LINK = ""
TIMEOUT_SECONDS = 45 # Default

with open(CONFIG_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith("PRIVATE_SERVER_LINK="):
            PRIVATE_SERVER_LINK = line.split("=", 1)[1].strip('"\'')
        elif line.startswith("TIMEOUT_SECONDS="):
            try:
                TIMEOUT_SECONDS = int(line.split("=", 1)[1].strip('"\''))
            except ValueError:
                pass

# Cek apakah ini format Share Link baru atau format lama
if "/share" in PRIVATE_SERVER_LINK:
    INTENT_URL = PRIVATE_SERVER_LINK
    print("[+] Terdeteksi format Share Link baru.")
else:
    # Extract Place ID dan Link Code pakai Regex sebagai pengganti grep -oP
    place_id_match = re.search(r'games/(\d+)', PRIVATE_SERVER_LINK)
    link_code_match = re.search(r'privateServerLinkCode=([^&]+)', PRIVATE_SERVER_LINK)

    if not place_id_match or not link_code_match:
        print("[!] Link Private Server tidak valid di config.conf!")
        sys.exit(1)

    PLACE_ID = place_id_match.group(1)
    LINK_CODE = link_code_match.group(1)
    
    INTENT_URL = f"roblox://placeId={PLACE_ID}&linkCode={LINK_CODE}"
    print("[+] URL Berhasil dikonversi ke Intent (Format Lama).")

print("[+] Target Intent yang akan dieksekusi:")
print(f"    -> {INTENT_URL}")
print("-" * 48)


# ==========================================
# 2. SCAN ROBLOX PACKAGES
# ==========================================
print("[*] Melakukan scan package Roblox...")
try:
    # Mempertahankan pipeline subprocess yang persis sama dengan Bash
    raw_packages = subprocess.check_output(
        "pm list packages | grep -i 'roblox' | cut -d':' -f2", 
        shell=True, text=True
    )
    PACKAGES = [pkg.strip() for pkg in raw_packages.strip().split('\n') if pkg.strip()]
except subprocess.CalledProcessError:
    PACKAGES = []

if len(PACKAGES) == 0:
    print("[!] Tidak ada package Roblox yang terdeteksi!")
    sys.exit(1)

print(f"[+] Ditemukan {len(PACKAGES)} package Roblox:")
for pkg in PACKAGES:
    print(f"    - {pkg}")
print("-" * 48)


# ==========================================
# 3. FUNGSI LAUNCH & SMART WAIT
# ==========================================
def launch_and_wait(pkg_name):
    print(f"[*] Membuka {pkg_name}...")
    
    # Bersihkan logcat lama agar deteksi lebih akurat
    subprocess.run("logcat -c", shell=True)
    
    # Eksekusi Intent
    am_cmd = f"am start -p '{pkg_name}' -a android.intent.action.VIEW -d '{INTENT_URL}'"
    subprocess.run(am_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"[*] Menunggu {pkg_name} masuk ke server (Smart Wait: {TIMEOUT_SECONDS} detik)...")
    
    # SMART WAIT: Pantau logcat di background
    grep_cmd = "logcat | grep -m 1 -iE 'GameJoinUtil|DataModel initialized|successfully connected'"
    logcat_proc = subprocess.Popen(grep_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    elapsed = 0
    # DUMB WAIT FALLBACK: Loop selama proses subprocess (grep) masih berjalan
    while logcat_proc.poll() is None:
        if elapsed >= TIMEOUT_SECONDS:
            print(f"[!] Logcat tidak mendeteksi koneksi dalam {TIMEOUT_SECONDS} detik.")
            print(f"[!] Menggunakan Fallback (Dumb Wait). Menganggap {pkg_name} sudah masuk.")
            logcat_proc.kill()
            break
        time.sleep(1)
        elapsed += 1
        
    print(f"[+] {pkg_name} selesai diproses.")
    print("-" * 48)


# ==========================================
# 4. EKSEKUSI SEQUENTIAL (SATU PER SATU)
# ==========================================
for pkg in PACKAGES:
    launch_and_wait(pkg)
    # Jeda ekstra 3 detik sebelum lanjut
    time.sleep(3)


# ==========================================
# 5. MONITORING & RECOVERY MODE (PID TRACKING)
# ==========================================
print("[+] SEMUA PACKAGE SELESAI DIPROSES.")
print("[*] Masuk ke Mode Monitoring. Tekan CTRL+C untuk berhenti.")

def get_pid(pkg_name):
    """Fungsi helper untuk mengeksekusi pidof dengan aman di Python"""
    result = subprocess.run(f"pidof '{pkg_name}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# Dictionary (Associative Array) untuk menyimpan PID awal
TRACKED_PIDS = {}

# Catat PID masing-masing package sebelum masuk ke loop monitoring
for pkg in PACKAGES:
    TRACKED_PIDS[pkg] = get_pid(pkg)

try:
    while True:
        for pkg in PACKAGES:
            # Ambil PID yang sedang berjalan saat ini
            CURRENT_PID = get_pid(pkg)
            
            # Kondisi 1: CURRENT_PID kosong (Proses benar-benar mati)
            # Kondisi 2: CURRENT_PID tidak sama dengan TRACKED_PIDS (Diganti Hantu)
            if not CURRENT_PID or CURRENT_PID != TRACKED_PIDS[pkg]:
                print("")
                print(f"[!] CRASH DETECTED: {pkg} terhenti atau berubah jadi proses hantu!")
                print(f"[*] Menjalankan Recovery untuk {pkg}...")
                
                launch_and_wait(pkg)
                
                # Update array dengan PID yang baru setelah recovery
                TRACKED_PIDS[pkg] = get_pid(pkg)
                
                print("[*] Recovery selesai. PID baru dicatat. Kembali memantau...")
                
        # Flush output agar titik indikator langsung muncul di terminal
        print(".", end="", flush=True)
        time.sleep(15)
        
except KeyboardInterrupt:
    print("\n[*] Script dihentikan oleh user.")
    sys.exit(0)
    
