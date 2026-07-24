import os
import time
import subprocess
import re
import sys

# ==========================================
# 1. CORE UTILITIES & ANSI COLORS
# ==========================================

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==========================================
# 1. ROOT EXECUTOR
# ==========================================

class RootExecutor:
    """Eksekusi perintah Android menggunakan akses Root."""

    @staticmethod
    def run(cmd, timeout=20, silent=True):
        try:
            result = subprocess.run(
                ["su", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if not silent:
                print(f"\n[CMD] {cmd}")
                print(f"[STDOUT] {stdout}")
                print(f"[STDERR] {stderr}")

            return stdout, stderr

        except subprocess.TimeoutExpired:
            return "", "Command Timeout"

        except Exception as e:
            return "", str(e)

    @staticmethod
    def check_root():
        stdout, _ = RootExecutor.run("id")
        return "uid=0" in stdout

    @staticmethod
    def enable_wakelock():
        cmds = [
            "dumpsys deviceidle whitelist +com.termux",
            "svc power stayon true"
        ]

        success = True

        for cmd in cmds:
            _, stderr = RootExecutor.run(cmd)
            if stderr:
                success = False

        return success

# ==========================================
# 2. URL PARSER
# ==========================================

class URLParser:
    """Parser Link Private Server Roblox."""

    @staticmethod
    def convert_to_deeplink(url):

        if not url:
            return None

        url = url.strip()

        # Sudah berupa deeplink
        if url.startswith("roblox://"):
            return url

        # Link share terbaru
        match = re.search(
            r"code=([A-Za-z0-9]+).*?type=Server",
            url,
            re.IGNORECASE
        )

        if match:
            code = match.group(1)

            return (
                "roblox://navigation/share_links"
                f"?code={code}&type=Server"
            )

        # Link lama private server
        match = re.search(
            r"privateServerLinkCode=([A-Za-z0-9]+)",
            url,
            re.IGNORECASE
        )

        if match:
            code = match.group(1)

            return (
                "roblox://navigation/share_links"
                f"?code={code}&type=Server"
            )

        return None

    @staticmethod
    def validate(url):
        return URLParser.convert_to_deeplink(url) is not None


# ==========================================
# 2. APP MONITOR
# ==========================================

class AppMonitor:
    """Monitor status aplikasi Roblox."""

    @staticmethod
    def is_process_running(package_name):
        stdout, _ = RootExecutor.run(
            f"pidof {package_name}"
        )
        return bool(stdout.strip())

    @staticmethod
    def is_window_visible(package_name):
        stdout, _ = RootExecutor.run(
            "dumpsys window windows"
        )

        return package_name in stdout

    @staticmethod
    def is_foreground(package_name):
        stdout, _ = RootExecutor.run(
            "dumpsys activity activities | grep mResumedActivity"
        )

        return package_name in stdout

    @staticmethod
    def get_focus():
        stdout, _ = RootExecutor.run(
            "dumpsys window | grep mCurrentFocus"
        )

        return stdout

    @staticmethod
    def get_pid(package_name):
        stdout, _ = RootExecutor.run(
            f"pidof {package_name}"
        )

        return stdout.strip()

    @staticmethod
    def is_alive(package_name):

        return (
            AppMonitor.is_process_running(package_name)
            and
            AppMonitor.is_window_visible(package_name)
        )

    @staticmethod
    def get_current_state(package_name):

        if not AppMonitor.is_process_running(package_name):
            return "STATE_STOPPED"

        if not AppMonitor.is_window_visible(package_name):
            return "STATE_GHOST_PROCESS"

        if not AppMonitor.is_foreground(package_name):
            return "STATE_BACKGROUND"

        return "STATE_RUNNING"

    @staticmethod
    def wait_until_ready(package_name,
                         timeout=60,
                         interval=2):
        """
        Menunggu Roblox benar-benar tampil di foreground.
        """

        start = time.time()

        while time.time() - start < timeout:

            state = AppMonitor.get_current_state(package_name)

            if state == "STATE_RUNNING":
                return True

            time.sleep(interval)

        return False

    @staticmethod
    def print_debug(package_name):

        print()

        print("=" * 40)
        print(package_name)
        print("=" * 40)

        print(
            "PID        :",
            AppMonitor.get_pid(package_name)
        )

        print(
            "Running    :",
            AppMonitor.is_process_running(package_name)
        )

        print(
            "Visible    :",
            AppMonitor.is_window_visible(package_name)
        )

        print(
            "Foreground :",
            AppMonitor.is_foreground(package_name)
        )

        print(
            "State      :",
            AppMonitor.get_current_state(package_name)
        )

        print(
            "Focus      :",
            AppMonitor.get_focus()
        )

        print()

# ==========================================
# 3. ACTION EXECUTOR
# ==========================================

class ActionExecutor:
    """Eksekusi aksi terhadap aplikasi Roblox."""

    @staticmethod
    def force_stop(package_name):

        print(f"[STOP] {package_name}")

        RootExecutor.run(
            f"am force-stop {package_name}",
            silent=True
        )

        time.sleep(2)

    @staticmethod
    def start_app(package_name):

        print(f"[START] {package_name}")

        RootExecutor.run(
            f"monkey -p {package_name} "
            "-c android.intent.category.LAUNCHER 1",
            silent=True
        )

        return AppMonitor.wait_until_ready(
            package_name,
            timeout=60
        )

    @staticmethod
    def join_server(package_name,
                    deep_link,
                    retry=3):

        print(f"[JOIN] {package_name}")

        if not deep_link:
            print("Deep Link kosong.")
            return False

        for attempt in range(1, retry + 1):

            cmd = (
                'am start '
                '-a android.intent.action.VIEW '
                f'-d "{deep_link}" '
                f'{package_name}'
            )

            stdout, stderr = RootExecutor.run(
                cmd,
                timeout=20,
                silent=False
            )

            if "Error" not in stderr:

                print(
                    f"[OK] Join command terkirim "
                    f"(Attempt {attempt})"
                )

                return True

            print(
                f"[Retry {attempt}/{retry}]"
            )

            time.sleep(3)

        print("[FAILED] Tidak dapat mengirim Deep Link.")

        return False

    @staticmethod
    def restart(package_name):

        ActionExecutor.force_stop(package_name)

        return ActionExecutor.start_app(package_name)

    @staticmethod
    def recover(package_name,
                deep_link):

        print(f"[RECOVER] {package_name}")

        if not ActionExecutor.restart(package_name):
            return False

        time.sleep(5)

        return ActionExecutor.join_server(
            package_name,
            deep_link
        )


# ==========================================
# 4. WATCHDOG STATE MACHINE
# ==========================================

class Watchdog:
    """Watchdog Sequential untuk Delta Lite Multi Package."""

    def __init__(
        self,
        target_packages,
        server_link,
        startup_delay=40,
        retry_limit=3
    ):

        self.packages = target_packages

        self.server_link = URLParser.convert_to_deeplink(
            server_link
        )

        self.startup_delay = startup_delay
        self.retry_limit = retry_limit

        # ===============================
        # STATUS TIAP PACKAGE
        # ===============================

        self.package_states = {}

        # Waktu mulai launch Roblox
        self.startup_timestamps = {}

        # Waktu terakhir join
        self.last_join_time = {}

        # Jumlah retry join
        self.retry_counter = {}

        # Cooldown recovery
        self.recovery_timer = {}

        # Apakah package sudah pernah join
        self.joined = {}

        # ===============================
        # INISIALISASI
        # ===============================

        now = time.time()

        for pkg in self.packages:

            self.package_states[pkg] = "STATE_INITIALIZING"

            self.startup_timestamps[pkg] = 0

            self.last_join_time[pkg] = 0

            self.retry_counter[pkg] = 0

            self.recovery_timer[pkg] = now

            self.joined[pkg] = False

def process_single_package(self, item):

    state = self.package_states[item]

    if state == "STATE_INITIALIZING":
        # siapkan resource
        self.package_states[item] = "STATE_STARTING"
        return

    elif state == "STATE_STARTING":
        # cek apakah aplikasi sudah siap
        if self.is_ready(item):
            self.package_states[item] = "STATE_READY"
        return

    elif state == "STATE_READY":
        # jalankan aksi utama
        success = self.perform_action(item)

        if success:
            self.package_states[item] = "STATE_MONITORING"
        else:
            self.package_states[item] = "STATE_RECOVERING"

        return

    elif state == "STATE_MONITORING":
        # pantau kondisi
        if self.needs_recovery(item):
            self.package_states[item] = "STATE_RECOVERING"

        return

    elif state == "STATE_RECOVERING":
        ok = self.recover(item)

        if ok:
            self.package_states[item] = "STATE_STARTING"
        else:
            self.package_states[item] = "STATE_FAILED"

        return

    elif state == "STATE_FAILED":
        # menunggu retry manual atau timer
        return
