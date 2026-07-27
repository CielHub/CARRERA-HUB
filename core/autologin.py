"""
Modul: autologin.py
Tanggung Jawab: Action-Based Login Engine (Brute-Force Action Queue).
"""
import os
import time
import subprocess
import re
from core.logger import log
from core.accounts import load_accounts

# =====================================================================
# DYNAMIC COORDINATE PERCENTAGES
# Format: (X_Percentage, Y_Percentage)
# =====================================================================
COORD_PCT = {
    "WELCOME_SIGNIN": (0.50, 0.85),
    "USERNAME": (0.50, 0.35),
    "PASSWORD": (0.50, 0.45),
    "LOGIN_BUTTON": (0.50, 0.55)
}

class ActionBasedEngine:
    def __init__(self, pkg, username, password):
        self.pkg = pkg
        self.username = username
        self.password = password
        self.screen_w, self.screen_h = self._get_screen_size()
        
    def _get_screen_size(self):
        """Mendapatkan resolusi layar device saat ini secara dinamis."""
        try:
            out = subprocess.check_output("su -c 'wm size'", shell=True, text=True)
            matches = re.findall(r'(\d+)x(\d+)', out)
            if matches:
                w, h = int(matches[-1][0]), int(matches[-1][1])
                return (min(w, h), max(w, h)) # Asumsi format Portrait
        except Exception:
            pass
        return (720, 1280) # Fallback standar

    def _get_coord(self, key):
        """Menghitung pixel absolut berdasarkan persentase resolusi."""
        pct_x, pct_y = COORD_PCT.get(key, (0.5, 0.5))
        return int(self.screen_w * pct_x), int(self.screen_h * pct_y)

    def _log_action(self, action_name):
        log.info(f"\n[ACTION]\n{action_name}\nSUCCESS\n")

    def _execute_tap(self, action_name, coord_key, delay=1.5):
        x, y = self._get_coord(coord_key)
        os.system(f"su -c 'input tap {x} {y}'")
        self._log_action(action_name)
        time.sleep(delay)

    def _execute_input(self, action_name, text, delay=1.5):
        # Escape string untuk shell
        safe_text = str(text).replace('"', '\\"')
        os.system(f"su -c 'input text \"{safe_text}\"'")
        self._log_action(action_name)
        time.sleep(delay)

    def _check_home_or_captcha(self):
        """
        HANYA mencari target utama (HOME) atau intervensi manual (CAPTCHA).
        Menggunakan kombinasi UI Dump, Dumpsys, dan Logcat.
        """
        # 1. Cek UI Dump
        try:
            os.system("su -c 'uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1'")
            xml = subprocess.check_output("su -c 'cat /data/local/tmp/uidump.xml'", shell=True, text=True).lower()
        except Exception:
            xml = ""
            
        # 2. Cek Logcat
        try:
            logcat = subprocess.check_output(f"su -c 'logcat -d -t 50 | grep -i {self.pkg}'", shell=True, text=True).lower()
        except Exception:
            logcat = ""
            
        # 3. Cek Dumpsys Focus
        try:
            window = subprocess.check_output("su -c 'dumpsys window windows | grep -E \"mCurrentFocus|mFocusedApp\"'", shell=True, text=True).lower()
        except Exception:
            window = ""

        # Deteksi CAPTCHA
        if "verification" in xml or "robot" in xml or "challenge" in logcat or "captcha" in logcat or "webview" in window:
            return "CAPTCHA"

        # Deteksi HOME
        if "home" in xml or "discover" in xml or "avatar" in xml or "homescreen" in logcat or "gamejoin" in logcat or "resume" in xml:
            return "HOME"

        return "UNKNOWN"

    def execute_queue(self):
        # WAKE UP APP
        os.system(f"su -c 'monkey -p {self.pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")
        time.sleep(3)

        # INITIAL CHECK: Apakah sudah di HOME sejak awal?
        log.info("\nChecking HOME (Initial)...")
        initial_state = self._check_home_or_captcha()
        if initial_state == "HOME":
            log.info("\nHOME FOUND\nSUCCESS (ALREADY LOGGED IN)\n")
            return "ALREADY_LOGGED_IN"
        elif initial_state == "CAPTCHA":
            log.warning("\nCAPTCHA FOUND\n")
            return "CAPTCHA"

        # ACTION QUEUE LOOP
        timeout_limit = time.time() + 90 # Global timeout 90 detik
        queue_count = 1
        
        while time.time() < timeout_limit:
            log.info(f"\n--- STARTING ACTION QUEUE {queue_count} ---")
            
            # Action 1: Tap Sign In (Berjaga-jaga jika ada di Welcome Screen)
            self._execute_tap("Tap Sign In", "WELCOME_SIGNIN", delay=3)
            
            # Action 2 & 3: Tap Username & Input Username
            self._execute_tap("Tap Username", "USERNAME", delay=1.5)
            self._execute_input("Input Username", self.username, delay=1.5)
            
            # Action 4 & 5: Tap Password & Input Password
            self._execute_tap("Tap Password", "PASSWORD", delay=1.5)
            self._execute_input("Input Password", self.password, delay=1.5)
            
            # Action Tambahan: Hide Keyboard agar tidak menghalangi tombol Login
            os.system("su -c 'input keyevent 4'")
            self._log_action("Hide Keyboard")
            time.sleep(1)
            
            # Action 6: Tap Log In
            self._execute_tap("Tap Login", "LOGIN_BUTTON", delay=10) # Delay panjang untuk loading otentikasi
            
            # CEK TARGET (HOME / CAPTCHA)
            log.info("\nChecking HOME...")
            current_state = self._check_home_or_captcha()
            
            if current_state == "HOME":
                log.info("\nHOME FOUND\nSUCCESS\n")
                return "SUCCESS"
            elif current_state == "CAPTCHA":
                log.warning("\nCAPTCHA FOUND\nFAILED\n")
                return "CAPTCHA"
            else:
                log.info("\nHOME NOT FOUND\nRepeating Queue...\n")
                queue_count += 1
                time.sleep(2) # Jeda nafas sebelum loop kembali

        # JIKA TIMEOUT
        log.warning("\nTIMEOUT\nFAILED\n")
        return "TIMEOUT"


# =====================================================================
# API CALL FROM RECOVERY (MONITOR.PY)
# =====================================================================
def run(pkg):
    accounts = load_accounts()
    if pkg not in accounts:
        log.warning(f"AUTO LOGIN: Akun untuk {pkg} belum dikonfigurasi.")
        return "FAILED"

    engine = ActionBasedEngine(pkg, accounts[pkg]['username'], accounts[pkg]['password'])
    result = engine.execute_queue()
    
    return result
    
