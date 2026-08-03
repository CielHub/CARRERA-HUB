# error_detector_r9x4m.py
"""
Modul : error_detector.py

Arsitektur Baru (v2)

Tujuan:
- Tidak mengganggu rich.Live
- Tidak pernah menyentuh dashboard
- Tidak pernah mengubah stats
- Tidak pernah print/log ke terminal
- Tidak memakai logcat -d
- Tidak memakai logcat -c
- Hanya membaca log Roblox
- Hanya membaca FLog::Network
- Mendukung multi clone menggunakan PID
"""

import subprocess
import threading
import queue
import re
import time

# ==========================================================
# INTERNAL EVENT QUEUE
# ==========================================================

_event_queue = queue.Queue()

# ==========================================================
# REGEX
# ==========================================================

PID_PATTERN = re.compile(r"Roblox\s+\(\s*(\d+)\)")

NETWORK_PATTERN = re.compile(r"\[FLog::Network\]")

REASON_PATTERN = re.compile(
    r"reason\s*:\s*(266|267|277|279|280)",
    re.IGNORECASE
)

# ==========================================================
# DAEMON
# ==========================================================

class ErrorDetector:

    def __init__(self):

        self.proc = None
        self.running = False

    def start(self):

        if self.running:
            return

        self.running = True

        threading.Thread(
            target=self._worker,
            daemon=True,
            name="RobloxErrorDetector"
        ).start()

    def _worker(self):

        cmd = [
            "su",
            "-c",
            "logcat -v brief -s Roblox"
        ]

        while self.running:

            try:

                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    bufsize=1,
                )

                while self.running:

                    line = self.proc.stdout.readline()

                    if not line:
                        break

                    # hanya log network roblox
                    if not NETWORK_PATTERN.search(line):
                        continue

                    # hanya reason yg kita pedulikan
                    reason_match = REASON_PATTERN.search(line)

                    if not reason_match:
                        continue

                    pid_match = PID_PATTERN.search(line)

                    if not pid_match:
                        continue

                    event = {
                        "pid": pid_match.group(1),
                        "reason": int(reason_match.group(1)),
                        "line": line.strip(),
                        "timestamp": time.time()
                    }

                    _event_queue.put(event)

            except Exception:
                time.sleep(2)

    def stop(self):

        self.running = False

        try:
            if self.proc:
                self.proc.kill()
        except Exception:
            pass


# ==========================================================
# SINGLETON
# ==========================================================

_detector = ErrorDetector()

# ==========================================================
# PUBLIC API
# ==========================================================

def start_error_detector():
    """
    Dipanggil sekali dari monitor.py
    """
    _detector.start()


def stop_error_detector():
    _detector.stop()


def has_event():

    return not _event_queue.empty()


def get_event():

    try:
        return _event_queue.get_nowait()

    except queue.Empty:
        return None
