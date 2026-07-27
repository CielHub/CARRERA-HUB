"""
Modul: autologin.py
Tanggung Jawab: UI-Based Login Engine (Element Detection, BUKAN koordinat statis).

PERUBAHAN UTAMA DARI VERSI SEBELUMNYA:
- Tidak ada lagi koordinat absolut hasil kalibrasi manual (COORDS). Semua tap
  dihitung dari bounds elemen UI hasil parsing `uiautomator dump`, sehingga
  otomatis benar walau Roblox berjalan di Floating Window pada posisi/ukuran
  berapa pun (bounds dari dump selalu berupa koordinat layar absolut sesuai
  posisi window saat itu).
- Ada state machine eksplisit (SIGNUP / LOGIN_FORM / HOME / CAPTCHA / UNKNOWN)
  sehingga setiap aksi hanya dijalankan kalau state layar memang sesuai,
  bukan menembak buta dalam satu queue tetap.
- Setiap aksi (tap Sign In, isi username, isi password, tap Login) diverifikasi
  hasilnya via dump ulang sebelum lanjut ke langkah berikutnya, dengan retry
  per-langkah.
"""
import os
import re
import time
import subprocess
from core.logger import log
from core.accounts import load_accounts

# =====================================================================
# KONFIGURASI
# =====================================================================
GLOBAL_TIMEOUT = 120          # detik, batas total proses auto login
STEP_RETRIES = 4              # retry maksimum per langkah (tap sign in / isi field / dst)
STEP_POLL_INTERVAL = 1.5      # jeda antar polling dump saat menunggu transisi state
STEP_POLL_TIMEOUT = 9         # detik, batas menunggu transisi state setelah satu aksi
UNKNOWN_STATE_MAX_LOOPS = 6   # kalau state tetap UNKNOWN terus-menerus, anggap gagal


# =====================================================================
# PARSER UI DUMP
# =====================================================================
_NODE_RE = re.compile(r"<node[^>]*?/>")
_ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
_BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


class UIElement:
    __slots__ = ("text", "desc", "resid", "clazz", "clickable", "focused", "bounds")

    def __init__(self, text, desc, resid, clazz, clickable, focused, bounds):
        self.text = text
        self.desc = desc
        self.resid = resid
        self.clazz = clazz
        self.clickable = clickable
        self.focused = focused
        self.bounds = bounds  # (x1, y1, x2, y2)

    @property
    def center(self):
        x1, y1, x2, y2 = self.bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def label(self):
        return f"{self.text} {self.desc}".strip().lower()

    def __repr__(self):
        return f"<UIElement text={self.text!r} desc={self.desc!r} class={self.clazz!r} bounds={self.bounds}>"


def _parse_nodes(xml):
    nodes = []
    for m in _NODE_RE.finditer(xml):
        attrs = dict(_ATTR_RE.findall(m.group(0)))
        bm = _BOUNDS_RE.match(attrs.get("bounds", ""))
        if not bm:
            continue
        bounds = tuple(int(v) for v in bm.groups())
        if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
            continue  # elemen tak terlihat / ukuran nol
        nodes.append(UIElement(
            text=attrs.get("text", ""),
            desc=attrs.get("content-desc", ""),
            resid=attrs.get("resource-id", ""),
            clazz=attrs.get("class", ""),
            clickable=attrs.get("clickable", "false") == "true",
            focused=attrs.get("focused", "false") == "true",
            bounds=bounds,
        ))
    return nodes


class ActionBasedEngine:
    def __init__(self, pkg, username, password):
        self.pkg = pkg
        self.username = username
        self.password = password
        self._window_region = None  # (x1,y1,x2,y2) cache frame floating window

    # -----------------------------------------------------------------
    # SHELL HELPERS
    # -----------------------------------------------------------------
    def _sh(self, cmd):
        return os.system(f"su -c '{cmd}'")

    def _sh_out(self, cmd, default=""):
        try:
            return subprocess.check_output(f"su -c \"{cmd}\"", shell=True, text=True)
        except Exception:
            return default

    def _log_action(self, action_name, ok=True):
        status = "SUCCESS" if ok else "FAILED"
        log.info(f"\n[ACTION]\n{action_name}\n{status}\n")

    # -----------------------------------------------------------------
    # WINDOW / FOCUS DETECTION (untuk floating window)
    # -----------------------------------------------------------------
    def _get_window_region(self):
        """
        Ambil frame (posisi & ukuran) window milik pkg dari dumpsys window,
        supaya pencarian elemen UI bisa dibatasi ke window ini saja
        (berguna kalau ada beberapa clone Roblox berjalan floating bersamaan).
        Best-effort: kalau gagal, return None (artinya tidak difilter).
        """
        raw = self._sh_out(f"dumpsys window windows | grep -A4 '{self.pkg}'")
        if not raw:
            return None
        m = re.search(r"Frame:\s*\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", raw)
        if not m:
            m = re.search(r"mFrame=\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]", raw)
        if not m:
            return None
        return tuple(int(v) for v in m.groups())

    def _is_focused(self):
        window = self._sh_out(
            "dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
        ).lower()
        return self.pkg.lower() in window

    def _bring_to_focus(self):
        """Coba bawa window pkg ke foreground. Dipanggil kalau focus meleset."""
        if self._is_focused():
            return True
        # coba tap di tengah frame window (kalau kita tahu frame-nya) untuk fokus
        region = self._get_window_region()
        if region:
            x1, y1, x2, y2 = region
            self._tap((x1 + x2) // 2, (y1 + y2) // 2)
            time.sleep(1)
        # fallback: bawa lagi lewat launcher intent
        self._sh(f"monkey -p {self.pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(2)
        return self._is_focused()

    # -----------------------------------------------------------------
    # UI DUMP
    # -----------------------------------------------------------------
    def _dump_nodes(self):
        self._sh("uiautomator dump /data/local/tmp/uidump.xml > /dev/null 2>&1")
        xml = self._sh_out("cat /data/local/tmp/uidump.xml")
        if not xml:
            return []
        nodes = _parse_nodes(xml)
        region = self._window_region
        if region:
            x1, y1, x2, y2 = region
            nodes = [n for n in nodes if x1 <= n.center[0] <= x2 and y1 <= n.center[1] <= y2]
        return nodes

    # -----------------------------------------------------------------
    # INPUT PRIMITIVES
    # -----------------------------------------------------------------
    def _tap(self, x, y):
        self._sh(f"input tap {x} {y}")

    def _tap_node(self, node, label):
        x, y = node.center
        self._tap(x, y)
        self._log_action(f"{label} @ ({x},{y}) [text={node.text!r} desc={node.desc!r}]")
        time.sleep(1.2)

    def _clear_field(self, node):
        x, y = node.center
        self._tap(x, y)
        time.sleep(0.4)
        self._sh("input keyevent 123")  # MOVE_END, best-effort
        # hapus isi lama (kalau ada autofill / sisa ketikan)
        self._sh("for i in $(seq 1 60); do input keyevent 67; done")
        time.sleep(0.3)

    def _type_text(self, text):
        safe_text = str(text).replace('"', '\\"').replace(" ", "%s")
        self._sh(f'input text "{safe_text}"')

    def _hide_keyboard(self):
        self._sh("input keyevent 4")
        time.sleep(0.5)

    # -----------------------------------------------------------------
    # STATE DETECTION
    # -----------------------------------------------------------------
    def _classify(self, nodes):
        labels = " | ".join(n.label for n in nodes)

        if any(k in labels for k in ("verification", "robot", "i'm not a robot", "captcha", "security check", "press and hold")):
            return "CAPTCHA"

        has_signup_cue = any(k in labels for k in ("create account", "sign up", "date of birth", "birthday"))
        edit_fields = [n for n in nodes if "edittext" in n.clazz.lower()]
        has_password_field = any("password" in n.label for n in nodes)
        has_login_submit = any(
            re.search(r"\blog\s*in\b", n.label) and n.clickable and "sign up" not in n.label
            for n in nodes
        )

        if len(edit_fields) >= 2 and (has_password_field or has_login_submit) and not has_signup_cue:
            return "LOGIN_FORM"

        if has_signup_cue or (len(edit_fields) == 0 and any(
            re.search(r"\b(log\s*in|sign\s*in)\b", n.label) for n in nodes
        )):
            return "SIGNUP"

        if any(k in labels for k in ("home", "discover", "avatar", "resume", "leave game", "robux")):
            return "HOME"

        return "UNKNOWN"

    def _find_clickable(self, nodes, include_pattern, exclude_pattern=None):
        for n in nodes:
            if not n.clickable:
                continue
            if not re.search(include_pattern, n.label):
                continue
            if exclude_pattern and re.search(exclude_pattern, n.label):
                continue
            return n
        return None

    # -----------------------------------------------------------------
    # STEP EXECUTION (dengan verifikasi + retry per langkah)
    # -----------------------------------------------------------------
    def _wait_for_state(self, target_states, timeout=STEP_POLL_TIMEOUT):
        deadline = time.time() + timeout
        while time.time() < deadline:
            nodes = self._dump_nodes()
            state = self._classify(nodes)
            if state in target_states:
                return state, nodes
            time.sleep(STEP_POLL_INTERVAL)
        return None, nodes if 'nodes' in dir() else []

    def _step_tap_sign_in(self):
        """Dari layar SIGNUP/Welcome, cari & tekan tombol Sign In/Log In."""
        for attempt in range(1, STEP_RETRIES + 1):
            nodes = self._dump_nodes()
            btn = self._find_clickable(
                nodes,
                include_pattern=r"\b(log\s*in|sign\s*in)\b",
                exclude_pattern=r"\b(sign\s*up|create)\b",
            )
            if not btn:
                log.info(f"\nTap Sign In: elemen belum ditemukan (percobaan {attempt}/{STEP_RETRIES})")
                time.sleep(1.5)
                continue

            self._tap_node(btn, "Tap Sign In")
            state, _ = self._wait_for_state({"LOGIN_FORM", "HOME", "CAPTCHA"})
            if state:
                return state
            log.info(f"\nTap Sign In: belum pindah ke Login Form (percobaan {attempt}/{STEP_RETRIES})")
        return None

    def _step_fill_login_form(self, nodes):
        """Isi username & password lalu tekan tombol Login. Return True kalau semua field terisi & submit ditekan."""
        for attempt in range(1, STEP_RETRIES + 1):
            nodes = self._dump_nodes()
            edit_fields = sorted(
                (n for n in nodes if "edittext" in n.clazz.lower()),
                key=lambda n: n.bounds[1],  # urutkan dari atas ke bawah
            )
            if len(edit_fields) < 2:
                log.info(f"\nIsi Form Login: field belum lengkap (percobaan {attempt}/{STEP_RETRIES})")
                time.sleep(1.5)
                continue

            username_field, password_field = edit_fields[0], edit_fields[1]

            self._clear_field(username_field)
            self._type_text(self.username)
            self._log_action("Input Username")
            time.sleep(0.8)

            self._clear_field(password_field)
            self._type_text(self.password)
            self._log_action("Input Password")
            time.sleep(0.8)

            self._hide_keyboard()

            # verifikasi field benar-benar terisi
            check_nodes = self._dump_nodes()
            check_fields = sorted(
                (n for n in check_nodes if "edittext" in n.clazz.lower()),
                key=lambda n: n.bounds[1],
            )
            filled_ok = len(check_fields) >= 2 and all(
                len(f.text.strip()) > 0 for f in check_fields[:2]
            )
            if not filled_ok:
                log.info(f"\nIsi Form Login: verifikasi field gagal, mengulang (percobaan {attempt}/{STEP_RETRIES})")
                continue

            submit = self._find_clickable(
                check_nodes,
                include_pattern=r"\blog\s*in\b",
            )
            if not submit:
                log.info(f"\nTombol Login tidak ditemukan (percobaan {attempt}/{STEP_RETRIES})")
                continue

            self._tap_node(submit, "Tap Login")
            state, _ = self._wait_for_state({"HOME", "CAPTCHA"}, timeout=15)
            if state:
                return state
            log.info(f"\nSetelah tap Login belum sampai HOME (percobaan {attempt}/{STEP_RETRIES})")

        return None

    # -----------------------------------------------------------------
    # MAIN LOOP
    # -----------------------------------------------------------------
    def execute_queue(self):
        self._sh(f"monkey -p {self.pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
        time.sleep(3)

        if not self._is_focused():
            log.info("\nWindow belum fokus, mencoba membawa ke foreground...")
            self._bring_to_focus()

        self._window_region = self._get_window_region()
        if self._window_region:
            log.info(f"\nFloating window region terdeteksi: {self._window_region}")
        else:
            log.info("\nFloating window region tidak terdeteksi, deteksi UI akan memakai seluruh layar.")

        log.info("\nChecking state (Initial)...")
        nodes = self._dump_nodes()
        state = self._classify(nodes)

        if state == "HOME":
            log.info("\nHOME FOUND\nSUCCESS (ALREADY LOGGED IN)\n")
            return "ALREADY_LOGGED_IN"
        if state == "CAPTCHA":
            log.warning("\nCAPTCHA FOUND\n")
            return "CAPTCHA"

        deadline = time.time() + GLOBAL_TIMEOUT
        unknown_loops = 0

        while time.time() < deadline:
            nodes = self._dump_nodes()
            state = self._classify(nodes)
            log.info(f"\nState terdeteksi: {state}")

            if state == "HOME":
                log.info("\nHOME FOUND\nSUCCESS\n")
                return "SUCCESS"

            if state == "CAPTCHA":
                log.warning("\nCAPTCHA FOUND\nFAILED\n")
                return "CAPTCHA"

            if state == "SIGNUP":
                unknown_loops = 0
                result_state = self._step_tap_sign_in()
                if result_state == "HOME":
                    log.info("\nHOME FOUND\nSUCCESS\n")
                    return "SUCCESS"
                if result_state == "CAPTCHA":
                    log.warning("\nCAPTCHA FOUND\nFAILED\n")
                    return "CAPTCHA"
                if result_state != "LOGIN_FORM":
                    log.warning("\nGagal berpindah dari layar Sign Up ke Login Form setelah beberapa percobaan.\n")
                    return "FAILED"
                continue  # lanjut ke iterasi berikut, state sudah LOGIN_FORM

            if state == "LOGIN_FORM":
                unknown_loops = 0
                result_state = self._step_fill_login_form(nodes)
                if result_state == "HOME":
                    log.info("\nHOME FOUND\nSUCCESS\n")
                    return "SUCCESS"
                if result_state == "CAPTCHA":
                    log.warning("\nCAPTCHA FOUND\nFAILED\n")
                    return "CAPTCHA"
                log.warning("\nGagal menyelesaikan Login Form setelah beberapa percobaan.\n")
                return "FAILED"

            # state == UNKNOWN (misal masih loading / transisi)
            unknown_loops += 1
            if unknown_loops >= UNKNOWN_STATE_MAX_LOOPS:
                log.warning("\nState tidak dikenali berulang kali. Menghentikan proses.\n")
                return "FAILED"
            time.sleep(2)

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
