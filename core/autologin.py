"""
Modul: autologin.py
Tanggung Jawab: Action-Based Login Engine (Absolute Coordinates + UI-Only Home Detection).
"""
import os
import time
import subprocess
from core.logger import log
from core.accounts import load_accounts

# =====================================================================
# ABSOLUTE COORDINATE CONFIGURATION (MANUAL CALIBRATION)
# Nyalakan "Pointer Location" di Developer Options Android.
# Ganti angka X dan Y di bawah ini sesuai kordinat layar HP lu!
# Format: (X, Y)
# =====================================================================
COORDS = {
    "WELCOME_SIGNIN": (200, 600),   # <--- GANTI KORDINAT TOMBOL SIGN IN
    "USERNAME": (200, 300),         # <--- GANTI KORDINAT KOLOM USERNAME
    "PASSWORD": (200, 400),         # <--- GANTI KORDINAT KOLOM PASSWORD
    "LOGIN_BUTTON": (200, 500)      # <--- GANTI KORDINAT TOMBOL LOG IN
}

class ActionBasedEngine:
    def __init__(self, pkg, username, password):
        self.pkg = pkg
        self.username = username
        self.password = password

    def _log_action(self, action_name):
        log.info(f"\n[ACTION]\n{action_name}\nSUCCESS\n")

    def _execute_tap(self, action_name, coord_key, delay=1.5):
        # Mengambil kordinat absolut mentah (bukan persentase lagi)
        x, y = COORDS.get(coord_key, (0, 0))
        os.system(f"su -c 'input tap {x} {y}'")
        self._log_action(f"{action_name} ({x}, {y})")
        time.sleep(delay)

    def _execute_input(self, action_name, text, delay=1.5):
        # Escape string untuk shell Android
        safe_text = str(text).replace('"', '\\"')
        os.system(f"su -c 'input text \"{safe_text}\"'")
        self._log_action(action_name)
        time.sleep(delay)

    def _check_home_or_captcha(self):
        """
        HANYA menggunakan UI Dump & Dumpsys Window.
        Deteksi Logcat DIHAPUS SEPENUHNYA agar terhindar dari false positive.
        """
        try:
            os.system("su -c 'uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1'")
            xml = subprocess.check_output("su -c 'cat /data/local/tmp/uidump.xml'", shell=True, text=True).lower()
        except Exception:
            xml = ""
            
        try:
            window = subprocess.check_output("su -c 'dumpsys window windows | grep -E \"mCurrentFocus|mFocusedApp\"'", shell=True, text=True).lower()
        except Exception:
            window = ""

        # Deteksi CAPTCHA (Intervensi manual)
        if "verification" in xml or "robot" in xml or "webview" in window:
            return "CAPTCHA"

        # Deteksi HOME MURNI DARI UI (Teks yang dipastikan merender jika sudah login)
        if "home" in xml or "discover" in xml or "avatar" in xml or "resume" in xml or "leave" in xml:
            return "HOME"

        # Jika XML kosong atau tidak ada tanda-tanda Home
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

        # ACTION QUEUE LOOP (Brute-Force Mesin Ketik Buta)
        timeout_limit = time.time() + 90 # Global timeout 90 detik
        queue_count = 1
        
        while time.time() < timeout_limit:
            log.info(f"\n--- STARTING ACTION QUEUE {queue_count} ---")
            
            # Action 1: Tap Sign In
            self._execute_tap("Tap Sign In", "WELCOME_SIGNIN", delay=3)
            
            # Action 2 & 3: Tap Username & Input
            self._execute_tap("Tap Username", "USERNAME", delay=1.5)
            self._execute_input("Input Username", self.username, delay=1.5)
            
            # Action 4 & 5: Tap Password & Input
            self._execute_tap("Tap Password", "PASSWORD", delay=1.5)
            self._execute_input("Input Password", self.password, delay=1.5)
            
            # Action Tambahan: Hide Keyboard (Penting buat Termux!)
            os.system("su -c 'input keyevent 4'")
            self._log_action("Hide Keyboard")
            time.sleep(1)
            
            # Action 6: Tap Log In
            self._execute_tap("Tap Login", "LOGIN_BUTTON", delay=10)
            
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
                time.sleep(2)

        # JIKA TIMEOUT MELEBIHI 90 DETIK
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
    
