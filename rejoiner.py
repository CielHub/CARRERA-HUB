import subprocess
import time
import sys

# ==========================================
# KONFIGURASI PENGGUNA
# ==========================================
# Anda sekarang bisa menggunakan format HTTPS atau roblox://
DEEP_LINK = "https://www.roblox.com/share?code=1709789b4cec9a45a6cba297c4f7d783&type=Server"
CHECK_INTERVAL = 10 # Waktu jeda (dalam detik) antar pengecekan status

def run_su(command):
    """Menjalankan perintah shell dengan akses root di Android."""
    try:
        result = subprocess.run(
            ['su', '-c', command], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"[-] Error eksekusi sistem: {e}")
        return ""

def find_roblox_package():
    """Memindai sistem Android untuk menemukan nama package Roblox secara otomatis."""
    print("[*] Memindai package Roblox di sistem Android...")
    try:
        output = run_su("pm list packages | grep roblox")
        if output:
            packages = [line.replace("package:", "").strip() for line in output.split('\n') if line]
            if packages:
                detected_pkg = packages[0] 
                print(f"[+] Package Roblox ditemukan: {detected_pkg}")
                return detected_pkg
                
        print("[-] Package Roblox tidak ditemukan! Pastikan Delta Lite sudah terinstal.")
        return None
    except Exception as e:
        print(f"[-] Error saat memindai package: {e}")
        return None

def is_app_running(package_name):
    """Mengecek apakah proses aplikasi ada di memori."""
    output = run_su(f"pidof {package_name}")
    return len(output) > 0

def check_screen_state():
    """Membaca teks di layar Android untuk mengetahui kondisi UI aplikasi."""
    run_su("uiautomator dump /data/local/tmp/uidump.xml")
    ui_xml = run_su("cat /data/local/tmp/uidump.xml").lower()
    
    if any(keyword in ui_xml for keyword in ["disconnected", "error", "kicked", "check your internet"]):
        return "ERROR"
    
    if "home" in ui_xml and "avatar" in ui_xml: 
        return "READY"
    
    return "UNKNOWN_OR_INGAME"

def recover_and_join(package_name):
    """Menutup paksa, membuka ulang, dan memasukkan akun ke private server."""
    print(f"[*] Memulai prosedur Recovery untuk {package_name}...")
    
    # 1. Force Stop
    run_su(f"am force-stop {package_name}")
    time.sleep(3) 
    
    # 2. Buka aplikasi ke Menu Utama
    print("[*] Membuka ulang aplikasi...")
    run_su(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
    
    # 3. Tunggu hingga loading selesai
    wait_time = 0
    max_wait = 90
    is_ready = False
    
    while wait_time < max_wait:
        state = check_screen_state()
        if state == "READY":
            print("[+] Aplikasi sudah siap di Menu Utama!")
            is_ready = True
            break
        
        print(f"[*] Menunggu loading... ({wait_time}s)")
        time.sleep(5)
        wait_time += 5
        
    if not is_ready:
        print("[-] Waktu tunggu habis saat loading. Akan dicoba ulang pada siklus berikutnya.")
        return False 
        
    # 4. Eksekusi Link Private Server secara Spesifik ke Package
    # Penambahan {package_name} di akhir akan mencegah link terbuka di browser
    print("[+] Menembakkan link Private Server...")
    run_su(f"am start -a android.intent.action.VIEW -d '{DEEP_LINK}' {package_name}")
    time.sleep(15)
    return True

def main():
    print("=== Auto Rejoiner Delta Lite Started ===")
    
    package_name = find_roblox_package()
    if not package_name:
        print("[-] Program dihentikan karena package tidak ditemukan.")
        sys.exit(1)

    while True:
        try:
            if not is_app_running(package_name):
                print("[!] Aplikasi tidak berjalan. Melakukan recovery...")
                recover_and_join(package_name)
            else:
                state = check_screen_state()
                if state == "ERROR":
                    print("[!] Terdeteksi layar Disconnect/Error. Melakukan recovery...")
                    recover_and_join(package_name)
                elif state == "READY":
                    print("[!] Aplikasi berada di Menu Utama. Memasukkan ke server...")
                    run_su(f"am start -a android.intent.action.VIEW -d '{DEEP_LINK}' {package_name}")
                    time.sleep(15)
                else:
                    print("[*] Status Aman: Aplikasi sedang berjalan.")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[+] Program dihentikan oleh pengguna (Ctrl+C).")
            break
        except Exception as e:
            print(f"[-] Terjadi kesalahan tidak terduga: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
