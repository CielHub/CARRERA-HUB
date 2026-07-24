#!/bin/bash

# ==========================================
# 0. AUTO REQUEST ROOT & DIRECTORY SETUP
# ==========================================
# Ambil path direktori tempat script ini berada
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "$0")"

# Cek apakah script sudah berjalan sebagai root (UID 0)
if [ "$(id -u)" -ne 0 ]; then
    echo "[*] Script ini membutuhkan akses Root untuk bekerja."
    echo "[*] Meminta izin Root ke sistem..."
    
    # Ambil lokasi absolute dari binary bash Termux sebelum masuk ke environment root.
    # Jika command -v gagal, gunakan path default Termux sebagai fallback.
    TERMUX_BASH=$(command -v bash || echo "/data/data/com.termux/files/usr/bin/bash")
    
    # Eksekusi ulang script menggunakan absolute path bash Termux
    su -c "$TERMUX_BASH \"$SCRIPT_DIR/$SCRIPT_NAME\""
    
    # Menangkap exit code dari su (gagal/ditolak)
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo "------------------------------------------------"
        echo "[!] Gagal mendapatkan akses Root."
        echo "[!] Pastikan HP sudah di-root dan berikan izin (Grant) pada prompt Magisk/KernelSU."
        exit 1
    fi
    
    # Tutup instance non-root (Termux biasa) setelah eksekusi root selesai
    exit 0
fi

# Pindah ke direktori script agar file config.conf terbaca
cd "$SCRIPT_DIR" || { echo "[!] Gagal masuk ke direktori script."; exit 1; }


# ==========================================
# 1. LOAD CONFIG & PARSE URL TO DEEP LINK
# ==========================================
CONFIG_FILE="config.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "[!] File config.conf tidak ditemukan di: $SCRIPT_DIR"
    exit 1
fi
source "$CONFIG_FILE"

# Cek apakah ini format Share Link baru atau format lama
if echo "$PRIVATE_SERVER_LINK" | grep -q "/share"; then
    INTENT_URL="$PRIVATE_SERVER_LINK"
    echo "[+] Terdeteksi format Share Link baru."
else
    PLACE_ID=$(echo "$PRIVATE_SERVER_LINK" | grep -oP 'games/\K\d+')
    LINK_CODE=$(echo "$PRIVATE_SERVER_LINK" | grep -oP 'privateServerLinkCode=\K[^&]+')

    if [ -z "$PLACE_ID" ] || [ -z "$LINK_CODE" ]; then
        echo "[!] Link Private Server tidak valid di config.conf!"
        exit 1
    fi
    INTENT_URL="roblox://placeId=$PLACE_ID&linkCode=$LINK_CODE"
    echo "[+] URL Berhasil dikonversi ke Intent (Format Lama)."
fi

echo "[+] Target Intent yang akan dieksekusi:"
echo "    -> $INTENT_URL"
echo "------------------------------------------------"

# ==========================================
# 2. SCAN ROBLOX PACKAGES
# ==========================================
echo "[*] Melakukan scan package Roblox..."
PACKAGES=($(pm list packages | grep -i "roblox" | cut -d':' -f2))

if [ ${#PACKAGES[@]} -eq 0 ]; then
    echo "[!] Tidak ada package Roblox yang terdeteksi!"
    exit 1
fi

echo "[+] Ditemukan ${#PACKAGES[@]} package Roblox:"
for pkg in "${PACKAGES[@]}"; do
    echo "    - $pkg"
done
echo "------------------------------------------------"

# ==========================================
# 3. FUNGSI LAUNCH & SMART WAIT
# ==========================================
launch_and_wait() {
    local PKG_NAME=$1
    
    echo "[*] Membuka $PKG_NAME..."
    
    # Bersihkan logcat lama agar deteksi lebih akurat
    logcat -c
    
    # Eksekusi Intent spesifik ke package yang dituju
    am start -p "$PKG_NAME" -a android.intent.action.VIEW -d "$INTENT_URL" > /dev/null 2>&1
    
    echo "[*] Menunggu $PKG_NAME masuk ke server (Smart Wait: $TIMEOUT_SECONDS detik)..."
    
    # SMART WAIT: Pantau logcat di background
    logcat | grep -m 1 -iE "GameJoinUtil|DataModel initialized|successfully connected" > /dev/null &
    local LOGCAT_PID=$!
    
    local ELAPSED=0
    # DUMB WAIT FALLBACK: Loop selama proses grep masih berjalan
    while kill -0 $LOGCAT_PID 2>/dev/null; do
        if [ $ELAPSED -ge $TIMEOUT_SECONDS ]; then
            echo "[!] Logcat tidak mendeteksi koneksi dalam $TIMEOUT_SECONDS detik."
            echo "[!] Menggunakan Fallback (Dumb Wait). Menganggap $PKG_NAME sudah masuk."
            kill $LOGCAT_PID 2>/dev/null
            break
        fi
        sleep 1
        ((ELAPSED++))
    done
    
    echo "[+] $PKG_NAME selesai diproses."
    echo "------------------------------------------------"
}

# ==========================================
# 4. EKSEKUSI SEQUENTIAL (SATU PER SATU)
# ==========================================
for pkg in "${PACKAGES[@]}"; do
    launch_and_wait "$pkg"
    # Jeda ekstra 3 detik sebelum lanjut ke package berikutnya untuk stabilitas OS
    sleep 3 
done

# ==========================================
# 5. MONITORING & RECOVERY MODE
# ==========================================
echo "[+] SEMUA PACKAGE SELESAI DIPROSES."
echo "[*] Masuk ke Mode Monitoring. Tekan CTRL+C untuk berhenti."

while true; do
    echo "--- Cek Status ($(date +%H:%M:%S)) ---"
    
    for pkg in "${PACKAGES[@]}"; do
        # Simpan output pidof ke dalam variabel untuk dianalisis
        PIDS=$(pidof "$pkg")
        
        # Cek apakah string PIDS kosong
        if [ -z "$PIDS" ]; then
            echo "[DEBUG] $pkg -> MATI (Process tidak ditemukan)"
            echo "[!] CRASH DETECTED: $pkg terhenti!"
            echo "[*] Menjalankan Recovery untuk $pkg..."
            
            launch_and_wait "$pkg"
            
            echo "[*] Recovery selesai. Kembali memantau..."
        else
            # Jika tidak kosong, tampilkan angka PID yang terdeteksi
            echo "[DEBUG] $pkg -> HIDUP (PIDs: $PIDS)"
        fi
    done
    
    # Cek setiap 15 detik
    sleep 15
done
