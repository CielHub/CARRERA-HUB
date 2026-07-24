#!/bin/bash

CONFIG_FILE="config.conf"

# ==========================================
# 1. LOAD CONFIG & PARSE URL TO DEEP LINK
# ==========================================
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[!] File config.conf tidak ditemukan!"
    exit 1
fi
source "$CONFIG_FILE"

# Cek apakah ini format Share Link baru atau format lama
if echo "$PRIVATE_SERVER_LINK" | grep -q "/share"; then
    # Format Baru: Tidak ada Place ID di URL
    # Kita langsung jadikan URL aslinya sebagai Intent, Roblox akan otomatis membacanya
    INTENT_URL="$PRIVATE_SERVER_LINK"
    echo "[+] Terdeteksi format Share Link baru."
else
    # Format Lama: Extract Place ID dan Link Code pakai Regex
    PLACE_ID=$(echo "$PRIVATE_SERVER_LINK" | grep -oP 'games/\K\d+')
    LINK_CODE=$(echo "$PRIVATE_SERVER_LINK" | grep -oP 'privateServerLinkCode=\K[^&]+')

    if [ -z "$PLACE_ID" ] || [ -z "$LINK_CODE" ]; then
        echo "[!] Link Private Server tidak valid di config.conf!"
        exit 1
    fi

    # Bentuk Roblox Intent URL format lama
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
# Cari semua package yang mengandung kata "roblox"
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
    # Note: "GameJoinUtil" atau "DataModel" biasanya muncul saat Roblox berhasil connect.
    # Lo bisa ganti keyword ini sesuai hasil riset logcat lo nanti.
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
    for pkg in "${PACKAGES[@]}"; do
        # Cek apakah PID dari package tersebut masih ada
        # Menggunakan 'pidof' bawaan Android
        if ! pidof "$pkg" > /dev/null; then
            echo "[!] CRASH DETECTED: $pkg terhenti (PID hilang)!"
            echo "[*] Menjalankan Recovery untuk $pkg..."
            
            # Panggil ulang fungsi launch untuk package yang crash
            launch_and_wait "$pkg"
            
            echo "[*] Recovery selesai. Kembali memantau..."
        fi
    done
    
    # Cek setiap 15 detik agar tidak membebani CPU (Bisa lo sesuaikan)
    sleep 15
done
