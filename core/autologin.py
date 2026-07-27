"""
Modul: autologin.py
Tanggung Jawab: State-Based Login Engine untuk Roblox (Fallback Recovery).
"""
import os
import time
import subprocess
import re
from core.logger import log
from core.accounts import load_accounts

def get_ui_dump():
    """Mendapatkan struktur UI Android (XML) untuk deteksi state."""
    try:
        # Menggunakan /data/local/tmp/ yang pasti bisa ditulis oleh Termux Root
        os.system("su -c 'uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1'")
        dump = subprocess.check_output("su -c 'cat /data/local/tmp/uidump.xml'", shell=True, text=True)
        return dump
    except Exception:
        return ""

def analyze_state(dump):
    """Menganalisis XML dump untuk menentukan State Roblox saat ini."""
    if not dump:
        return "UNKNOWN"
    
    # 1. Deteksi Captcha / Security
    if "Verification" in dump or "Verify" in dump or "robot" in dump.lower():
        return "CAPTCHA_SCREEN"
    
    # 2. Deteksi Login Screen (Terdapat form Username & Password)
    if "Username/Email/Phone" in dump and "Password" in dump:
        return "LOGIN_SCREEN"
        
    # 3. Deteksi Welcome Screen (Terdapat tombol Sign In & Create Account)
    if "Sign In" in dump and "Create Account" in dump:
        return "WELCOME_SCREEN"
        
    # 4. Deteksi Home Screen (Sudah masuk ke dalam game/Home)
    if "Home" in dump or "Avatar" in dump or "Connect" in dump or "Chat" in dump or "Discover" in dump:
        return "HOME_SCREEN"
        
    return "UNKNOWN"

def tap_element(dump, target_text):
    """Mencari elemen berdasarkan teks dan melakukan tap menggunakan kordinat bounds dinamis."""
    # Ekstrak bounds="[x1,y1][x2,y2]" dari elemen yang memiliki teks/desc target
    matches = re.finditer(r'(?:text|content-desc)="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', dump, re.IGNORECASE)
    for match in matches:
        text_val = match.group(1)
        if target_text.lower() in text_val.lower():
            x1, y1, x2, y2 = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            os.system(f"su -c 'input tap {cx} {cy}'")
            return True
    return False

def wait_for_state(target_states, timeout=30):
    """Polling engine: Menunggu hingga UI berubah menjadi salah satu target state (tanpa hard sleep)."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        dump = get_ui_dump()
        state = analyze_state(dump)
        if state in target_states:
            return state, dump
        time.sleep(1) # Polling ringan agar CPU Termux tidak terbakar
    return "TIMEOUT", ""

def run(pkg):
    """
    API Utama Modular.
    Return values: SUCCESS, FAILED, TIMEOUT, CAPTCHA, ALREADY_LOGGED_IN.
    """
    accounts = load_accounts()
    if pkg not in accounts:
        log.warning(f"AUTO LOGIN: Akun untuk {pkg} belum dikonfigurasi di accounts.json.")
        return "FAILED"

    username = accounts[pkg]['username']
    password = accounts[pkg]['password']

    log.info(f"AUTO LOGIN: Membaca state UI untuk {pkg}...")
    
    # Wake up application (opsional, untuk memastikan Roblox berada di layar)
    os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")
    time.sleep(2)

    timeout_limit = time.time() + 90 # Hard timeout maksimal 90 detik
    
    while time.time() < timeout_limit:
        dump = get_ui_dump()
        state = analyze_state(dump)

        if state == "HOME_SCREEN":
            log.info(f"AUTO LOGIN: {pkg} terdeteksi di Home Screen (Sudah Login).")
            return "ALREADY_LOGGED_IN"

        elif state == "WELCOME_SCREEN":
            log.info(f"AUTO LOGIN: {pkg} berada di Welcome Screen. Menekan 'Sign In'...")
            tap_element(dump, "Sign In")
            
            # Polling untuk menunggu transisi UI selesai
            new_state, _ = wait_for_state(["LOGIN_SCREEN", "CAPTCHA_SCREEN"], timeout=15)
            if new_state == "TIMEOUT":
                log.warning(f"AUTO LOGIN: Timeout saat transisi ke Login Screen untuk {pkg}.")
            elif new_state == "CAPTCHA_SCREEN":
                return "CAPTCHA"

        elif state == "LOGIN_SCREEN":
            log.info(f"AUTO LOGIN: {pkg} berada di Login Screen. Mengisi kredensial...")
            
            if tap_element(dump, "Username/Email/Phone"):
                time.sleep(1) # Jeda natural untuk animasi keyboard Android
                os.system(f"su -c 'input text \"{username}\"'")
                time.sleep(1)
                
                # Pindah ke field Password menggunakan keyevent TAB
                os.system("su -c 'input keyevent 61'")
                time.sleep(1)
                
                os.system(f"su -c 'input text \"{password}\"'")
                time.sleep(1)
                
                log.info(f"AUTO LOGIN: Kredensial dimasukkan. Mengirim perintah Log In...")
                # Tekan tombol 'Log In'. Jika gagal tap, gunakan fallback Enter (66)
                if not tap_element(dump, "Log In"):
                    os.system("su -c 'input keyevent 66'")
                
                log.info(f"AUTO LOGIN: Menunggu verifikasi server ke Home Screen...")
                
                final_state, _ = wait_for_state(["HOME_SCREEN", "LOGIN_SCREEN", "WELCOME_SCREEN", "CAPTCHA_SCREEN"], timeout=30)
                
                if final_state == "HOME_SCREEN":
                    return "SUCCESS"
                elif final_state == "CAPTCHA_SCREEN":
                    log.warning(f"AUTO LOGIN: Captcha terdeteksi untuk {pkg}.")
                    return "CAPTCHA"
                elif final_state in ["LOGIN_SCREEN", "WELCOME_SCREEN"]:
                    log.warning(f"AUTO LOGIN: Gagal login untuk {pkg} (Mungkin salah password).")
                    return "FAILED"
                else:
                    return "TIMEOUT"
            else:
                log.error(f"AUTO LOGIN: Tidak dapat menemukan input field pada {pkg}.")
                return "FAILED"

        elif state == "CAPTCHA_SCREEN":
            log.warning(f"AUTO LOGIN: Captcha terdeteksi pada {pkg} saat awal identifikasi.")
            return "CAPTCHA"

        else:
            time.sleep(2) # UNKNOWN state, tunggu loading layar selesai sebelum loop ulang

    return "TIMEOUT"
    
