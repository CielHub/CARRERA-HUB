"""
Modul: autologin.py
Tanggung Jawab: State-Based Login Engine v3 (Multi-Detection + Dynamic Coordinate).
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
# Bekerja di semua resolusi (720p, 1080p, dll). Asumsi layar Portrait.
# =====================================================================
COORD_PCT = {
    "WELCOME_SIGNIN": (0.50, 0.85), # Tengah bawah
    "USERNAME": (0.50, 0.35),       # Tengah atas
    "PASSWORD": (0.50, 0.45),       # Tengah sedikit ke bawah
    "LOGIN_BUTTON": (0.50, 0.55),   # Tengah
    "SAFE_SPACE": (0.50, 0.10)      # Area kosong di atas untuk tap neutral
}

class AutoLoginEngine:
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
                # Ambil match terakhir (mengantisipasi 'Override size')
                w, h = int(matches[-1][0]), int(matches[-1][1])
                # Pastikan format Portrait (W < H)
                return (min(w, h), max(w, h))
        except Exception:
            pass
        return (720, 1280) # Fallback standar

    def _get_coord(self, key):
        """Menghitung pixel absolut berdasarkan persentase resolusi."""
        pct_x, pct_y = COORD_PCT.get(key, (0.5, 0.5))
        return int(self.screen_w * pct_x), int(self.screen_h * pct_y)

    def _get_ui_dump(self):
        try:
            os.system("su -c 'uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1'")
            return subprocess.check_output("su -c 'cat /data/local/tmp/uidump.xml'", shell=True, text=True).lower()
        except Exception:
            return ""

    def _get_logcat_dump(self):
        """Membaca logcat internal Roblox untuk mendeteksi pergerakan Lua App/UI."""
        try:
            return subprocess.check_output(f"su -c 'logcat -d -t 50 | grep -i {self.pkg}'", shell=True, text=True).lower()
        except Exception:
            return ""

    def _get_dumpsys_window(self):
        """Memeriksa window yang sedang fokus (Berguna untuk Captcha WebView)."""
        try:
            return subprocess.check_output("su -c 'dumpsys window windows | grep -E \"mCurrentFocus|mFocusedApp\"'", shell=True, text=True).lower()
        except Exception:
            return ""

    def detect_state(self):
        """
        MULTI DETECTION STRATEGY
        Prioritas: XML Dump -> Dumpsys Focus -> Logcat Routing
        """
        # 1. METODE XML UI
        xml = self._get_ui_dump()
        if xml and len(xml) > 100:
            if "verification" in xml or "robot" in xml:
                return "CAPTCHA", "XML"
            if "username/email/phone" in xml or "password" in xml:
                return "LOGIN", "XML"
            if "sign in" in xml and "create account" in xml:
                return "WELCOME", "XML"
            if "home" in xml or "discover" in xml or "avatar" in xml:
                return "HOME", "XML"
            if "resume" in xml or "leave" in xml:
                return "INGAME", "XML"
                
        # 2. METODE DUMPSYS (Pendeteksi Captcha WebView / Eksternal App)
        window = self._get_dumpsys_window()
        if window:
            if "webview" in window or "browser" in window:
                return "CAPTCHA", "DUMPSYS"
                
        # 3. METODE LOGCAT (Pendeteksi state via internal Lua Routing)
        logcat = self._get_logcat_dump()
        if logcat:
            if "loginscreen" in logcat or "authentication" in logcat:
                return "LOGIN", "LOGCAT"
            if "landingscreen" in logcat or "welcomescreen" in logcat:
                return "WELCOME", "LOGCAT"
            if "homescreen" in logcat or "gamejoin" in logcat:
                return "HOME", "LOGCAT"
            if "challenge" in logcat or "captcha" in logcat:
                return "CAPTCHA", "LOGCAT"

        return "UNKNOWN", "Active Investigation (No Matches)"

    def wait_for_states(self, target_states, timeout_sec):
        """Menunggu transisi state dengan observasi aktif, bukan sleep buta."""
        start = time.time()
        attempt = 0
        
        while time.time() - start < timeout_sec:
            attempt += 1
            state, method = self.detect_state()
            
            if state in target_states:
                return state
                
            log.info(
                f"\nWaiting {target_states}\n"
                f"Attempt {attempt}\n"
                f"Current State:\n"
                f"{state} (Method: {method})\n"
            )
            time.sleep(2)
            
        return "TIMEOUT"

    def hybrid_tap(self, state, target_text, coord_key):
        """Tap kombinasi: Coba cari di XML, jika gagal gunakan Dynamic Coordinate."""
        xml = self._get_ui_dump()
        ui_success = False
        
        if xml:
            # Mencari kordinat spesifik dari target_text di dalam XML
            matches = re.finditer(r'(?:text|content-desc)="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml, re.IGNORECASE)
            for match in matches:
                text_val = match.group(1)
                if target_text.lower() in text_val.lower():
                    x1, y1, x2, y2 = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    os.system(f"su -c 'input tap {cx} {cy}'")
                    ui_success = True
                    break
        
        if ui_success:
            log.info(
                f"\n[LOGIN]\n"
                f"Package: {self.pkg}\n"
                f"↓\n"
                f"State: {state}\n"
                f"↓\n"
                f"Searching: {target_text}\n"
                f"↓\n"
                f"UI Result: SUCCESS\n"
            )
        else:
            x, y = self._get_coord(coord_key)
            os.system(f"su -c 'input tap {x} {y}'")
            log.info(
                f"\n[LOGIN]\n"
                f"Package: {self.pkg}\n"
                f"↓\n"
                f"State: {state}\n"
                f"↓\n"
                f"Searching: {target_text}\n"
                f"↓\n"
                f"UI Result: FAILED\n"
                f"↓\n"
                f"Fallback Method:\n"
                f"Coordinate Tap ({x}, {y})\n"
                f"↓\n"
                f"SUCCESS\n"
            )

    def execute_flow(self):
        # 1. Start Detection
        state, method = self.detect_state()
        
        log.info(
            f"\n[STATE]\n"
            f"Detected:\n"
            f"{state}\n"
            f"Method:\n"
            f"{method}\n"
        )
        
        # ACTIVE UNKNOWN HANDLING
        if state == "UNKNOWN":
            log.info("\nDetected:\nUNKNOWN\nReason:\nNo UI Node or Logcat Match\nTrying Alternative Detection...\n")
            # Beri sedikit waktu untuk memuat engine Unity lalu detect ulang
            time.sleep(3)
            state, method = self.detect_state()
            if state == "UNKNOWN":
                return "FAILED" # Jika tetap UNKNOWN, serahkan ke Retry Mechanism Monitor

        # -------------------------------------------------------------
        # STATE ROUTING
        # -------------------------------------------------------------
        if state in ["HOME", "INGAME"]:
            return "ALREADY_LOGGED_IN"
            
        elif state == "CAPTCHA":
            return "CAPTCHA"
            
        elif state == "WELCOME":
            self.hybrid_tap("WELCOME", "Sign In", "WELCOME_SIGNIN")
            
            next_state = self.wait_for_states(["LOGIN", "CAPTCHA"], timeout_sec=30)
            if next_state == "TIMEOUT":
                log.info("\nState:\nWELCOME\n↓\nTimeout\n↓\nLOGIN FAILED\n")
                return "FAILED"
            elif next_state == "CAPTCHA":
                return "CAPTCHA"
                
            # Jika berhasil ke LOGIN, update state dan biarkan lanjut ke blok LOGIN di bawah
            state = "LOGIN" 

        if state == "LOGIN":
            # 1. Tap Username
            self.hybrid_tap("LOGIN", "Username", "USERNAME")
            time.sleep(1) # Tunggu keyboard virtual naik
            
            # 2. Input Username
            os.system(f"su -c 'input text \"{self.username}\"'")
            log.info(f"\nState:\nLOGIN\n↓\nInput Username\n↓\nSUCCESS\n")
            
            # Detect apakah field pindah (Active Detection)
            # Karena input shell sangat cepat, kita bisa langsung lanjut Tap Password
            
            # 3. Tap Password
            self.hybrid_tap("LOGIN", "Password", "PASSWORD")
            time.sleep(1)
            
            # 4. Input Password
            os.system(f"su -c 'input text \"{self.password}\"'")
            log.info(f"\nState:\nLOGIN\n↓\nInput Password\n↓\nSUCCESS\n")
            
            # Trik Android: Sembunyikan keyboard agar tidak menutupi tombol Log In
            os.system("su -c 'input keyevent 4'")
            time.sleep(1)
            
            # 5. Tap Log In Button
            self.hybrid_tap("LOGIN", "Log In", "LOGIN_BUTTON")
            log.info(f"\nState:\nLOGIN\n↓\nTap Login\n↓\nWaiting Home (Timeout: 40s)\n")
            
            # 6. Observasi Hasil Login
            final_state = self.wait_for_states(["HOME", "INGAME", "CAPTCHA"], timeout_sec=40)
            
            if final_state in ["HOME", "INGAME"]:
                return "SUCCESS"
            elif final_state == "CAPTCHA":
                return "CAPTCHA"
            elif final_state == "TIMEOUT":
                log.info("\nState:\nLOGIN\n↓\nTimeout (No Home Screen)\n↓\nLOGIN FAILED\n")
                return "TIMEOUT"
            else:
                return "FAILED"

        return "FAILED"

# =====================================================================
# API CALL FROM RECOVERY (MONITOR.PY)
# =====================================================================
def run(pkg):
    accounts = load_accounts()
    if pkg not in accounts:
        log.warning(f"AUTO LOGIN: Akun untuk {pkg} belum dikonfigurasi.")
        return "FAILED"

    # Pastikan aplikasi di depan sebelum memulai
    os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")
    time.sleep(3) # Initial wait untuk Unity App loading

    engine = AutoLoginEngine(pkg, accounts[pkg]['username'], accounts[pkg]['password'])
    result = engine.execute_flow()
    
    return result
            
