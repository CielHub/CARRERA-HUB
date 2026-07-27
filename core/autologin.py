"""
Modul: autologin.py
Tanggung Jawab: State-Based Login Engine (Hybrid: UI Detection + Coordinate Fallback).
"""
import os
import time
import subprocess
import re
from core.logger import log
from core.accounts import load_accounts

# =====================================================================
# COORDINATE CONFIGURATION (FALLBACK)
# Sesuaikan resolusi X dan Y ini dengan layar Termux/Emulator lu.
# Nilai di bawah ini adalah estimasi generik untuk layar rasio standar.
# =====================================================================
COORDS = {
    "WELCOME_SIGNIN": "360 1100",  # Posisi tombol Sign In di layar Welcome
    "USERNAME": "360 450",         # Posisi kolom Username di layar Login
    "PASSWORD": "360 600",         # Posisi kolom Password di layar Login
    "LOGIN_BUTTON": "360 800"      # Posisi tombol Log In di layar Login
}

def log_hybrid_step(pkg, state, search_target, ui_success, fallback_used, next_action):
    """Fungsi pembantu untuk mencetak log berjenjang yang detail sesuai standar."""
    ui_res = "SUCCESS" if ui_success else "FAILED"
    fallback_msg = f"Coordinate Tap ({fallback_used})" if not ui_success else "None"
    
    msg = (
        f"\n[LOGIN]\n"
        f"Package: {pkg}\n"
        f"↓\n"
        f"State: {state}\n"
        f"↓\n"
        f"Searching: {search_target}\n"
        f"↓\n"
        f"UI Result: {ui_res}\n"
        f"↓\n"
        f"Fallback: {fallback_msg}\n"
        f"↓\n"
        f"Tap Success\n"
        f"↓\n"
        f"Waiting: {next_action}\n"
    )
    log.info(msg)

def log_input_step(state, field_name, success_msg, next_action):
    """Fungsi pembantu untuk log proses pengisian teks."""
    msg = (
        f"\nState: {state}\n"
        f"↓\n"
        f"Input {field_name}\n"
        f"↓\n"
        f"{success_msg}\n"
        f"↓\n"
        f"Waiting: {next_action}\n"
    )
    log.info(msg)

def get_ui_dump():
    """Mendapatkan struktur UI Android (XML) untuk deteksi state."""
    try:
        os.system("su -c 'uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1'")
        dump = subprocess.check_output("su -c 'cat /data/local/tmp/uidump.xml'", shell=True, text=True)
        return dump
    except Exception:
        return ""

def analyze_state(dump):
    """Mendeteksi State Roblox berdasarkan isi XML."""
    if not dump:
        return "UNKNOWN"
    
    dump_lower = dump.lower()
    
    if "verification" in dump_lower or "verify" in dump_lower or "robot" in dump_lower:
        return "CAPTCHA"
    
    if "username/email/phone" in dump_lower or "password" in dump_lower:
        return "LOGIN"
        
    if "sign in" in dump_lower and "create account" in dump_lower:
        return "WELCOME"
        
    if "home" in dump_lower or "avatar" in dump_lower or "discover" in dump_lower:
        return "HOME"
        
    if "leave" in dump_lower or "resume" in dump_lower or "roblox player" in dump_lower:
        return "INGAME"
        
    return "UNKNOWN"

def hybrid_tap(pkg, state, dump, target_text, coord_key, next_action_msg):
    """
    Engine Hybrid: Mencoba deteksi UI terlebih dahulu. 
    Jika gagal, gunakan Coordinate Fallback.
    """
    ui_success = False
    
    # 1. Try UI Detection
    matches = re.finditer(r'(?:text|content-desc)="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', dump, re.IGNORECASE)
    for match in matches:
        text_val = match.group(1)
        if target_text.lower() in text_val.lower():
            x1, y1, x2, y2 = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            os.system(f"su -c 'input tap {cx} {cy}'")
            ui_success = True
            break
            
    # 2. Coordinate Fallback jika UI Detection gagal (Unity Obfuscation)
    if not ui_success:
        coords = COORDS.get(coord_key, "0 0")
        os.system(f"su -c 'input tap {coords}'")
        
    log_hybrid_step(pkg, state, target_text, ui_success, coord_key, next_action_msg)
    time.sleep(2) # Jeda natural agar animasi UI selesai

def run(pkg):
    """
    API Utama Modular (State-Based Engine).
    Return: SUCCESS, FAILED, TIMEOUT, CAPTCHA, ALREADY_LOGGED_IN.
    """
    accounts = load_accounts()
    if pkg not in accounts:
        log.warning(f"AUTO LOGIN: Akun untuk {pkg} belum dikonfigurasi.")
        return "FAILED"

    username = accounts[pkg]['username']
    password = accounts[pkg]['password']
    
    # Wake up application (opsional untuk memastikan app di depan)
    os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")
    time.sleep(2)

    timeout_limit = time.time() + 60  # Global timeout per percobaan (60 detik)
    login_attempted = False

    while time.time() < timeout_limit:
        dump = get_ui_dump()
        state = analyze_state(dump)

        # STATE 1: HOME / INGAME
        if state in ["HOME", "INGAME"]:
            if login_attempted:
                return "SUCCESS"
            else:
                return "ALREADY_LOGGED_IN"

        # STATE 2: CAPTCHA
        elif state == "CAPTCHA":
            return "CAPTCHA"

        # STATE 3: WELCOME SCREEN
        elif state == "WELCOME":
            hybrid_tap(pkg, "WELCOME", dump, "Sign In", "WELCOME_SIGNIN", "Login Screen")
            # Loop akan kembali berjalan untuk mendeteksi state baru (LOGIN)
            continue

        # STATE 4: LOGIN SCREEN
        elif state == "LOGIN":
            # 1. Username
            hybrid_tap(pkg, "LOGIN", dump, "Username", "USERNAME", "Inputting Username")
            os.system(f"su -c 'input text \"{username}\"'")
            log_input_step("LOGIN", "Username", "SUCCESS", "Password Field")
            
            # 2. Password (TIDAK menggunakan TAB, langsung Tap)
            hybrid_tap(pkg, "LOGIN", dump, "Password", "PASSWORD", "Inputting Password")
            os.system(f"su -c 'input text \"{password}\"'")
            log_input_step("LOGIN", "Password", "SUCCESS", "Log In Button")
            
            # 3. Log In Button
            hybrid_tap(pkg, "LOGIN", dump, "Log In", "LOGIN_BUTTON", "Home Screen")
            
            login_attempted = True
            
            # Jeda agar server merespon sebelum loop membaca state lagi
            time.sleep(5)
            continue

        # STATE 5: UNKNOWN
        else:
            time.sleep(2) # Tunggu UI loading
            continue

    # Jika loop selesai dan melebihi timeout_limit
    log.warning(f"\nState: {state}\n↓\nTimeout\n↓\nLOGIN FAILED\n")
    return "TIMEOUT"
    
