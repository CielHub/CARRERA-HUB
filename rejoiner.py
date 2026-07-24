#!/bin/bash

# ================= KONFIGURASI =================
# Ganti dengan link private server Roblox lu
LINK="https://www.roblox.com/share?code=1709789b4cec9a45a6cba297c4f7d783&type=Server"

CHECK_INTERVAL=15      # Waktu (detik) untuk ngecek apakah Roblox masih jalan
WAIT_AFTER_JOIN=20     # Waktu (detik) untuk nunggu Roblox loading
# ===============================================

# Fungsi untuk ngecek apakah Roblox sedang berjalan
is_roblox_running() {
    # Menggunakan 'su -c' untuk mengecek PID menggunakan akses root.
    # Jika lu pakai Wireless ADB (tanpa root), ganti 'su -c' jadi 'adb shell'
    PID=$(su -c 'pidof com.roblox.clienu' 2>/dev/null)
    
    if [ -z "$PID" ]; then
        return 1 # False (PID kosong = Crash / Tidak jalan)
    else
        return 0 # True (PID ada = Jalan)
    fi
}

# Fungsi untuk join atau recovery
join_server() {
    echo -e "\n[!] Menjalankan Roblox / Join ke Private Server..."
    
    # termux-open-url akan melempar link ke OS Android, 
    # yang otomatis akan ditangkap oleh aplikasi Roblox lu
    termux-open-url "$LINK"
    
    echo "[-] Menunggu $WAIT_AFTER_JOIN detik agar loading selesai..."
    sleep $WAIT_AFTER_JOIN
}

echo "=== Termux Auto Rejoiner Roblox Aktif ==="

# Cek saat pertama kali jalan
if ! is_roblox_running; then
    echo "[!] Roblox belum berjalan. Memulai join awal..."
    join_server
else
    echo "[+] Roblox sudah berjalan. Mulai memantau proses..."
fi

# Main Loop (mantau terus)
while true; do
    if ! is_roblox_running; then
        echo -e "\n[X] Crash atau PID hilang terdeteksi! Memanggil fungsi Recovery..."
        join_server
    fi
    
    # Jeda sebelum loop ngecek lagi
    sleep $CHECK_INTERVAL
done
