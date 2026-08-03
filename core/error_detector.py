# error_detector_x7k9q.py
"""
Modul: error_detector.py

Tanggung Jawab:
- Menjalankan SATU proses logcat daemon di background.
- Tidak pernah melakukan print / console.print / log.info.
- Tidak pernah menyentuh rich.Live.
- Tidak pernah mengubah stats.
- Hanya mengirim event ke Queue.
- Aman untuk multi clone.
"""

import subprocess
import threading
import queue
import re

# ============================================================
# EVENT QUEUE
# ============================================================

_event_queue = queue.Queue()

# ============================================================
# ROBLOX NETWORK PATTERN
# ============================================================

LOGCAT_PATTERN = re.compile(
    r"(?i)(requests player disconnect|reason:\s*266|reason:\s*267|reason:\s*277|reason:\s*279|reason:\s*280)"
)

PID_PATTERN = re.compile(r"\(\s*(\d+)\)")

# ============================================================
# DAEMON WORKER
# ============================================================

def _logcat_daemon():
    """
    Membuka SATU proses logcat permanen.

    Tidak ada:
        - polling
        - sleep
        - logcat -d
        - logcat -c
    """

    cmd = [
        "su",
        "-c",
        "logcat -v brief"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

    except Exception:
        return

    while True:

        line = proc.stdout.readline()

        if not line:
            break

        if not LOGCAT_PATTERN.search(line):
            continue

        pid_match = PID_PATTERN.search(line)

        if not pid_match:
            continue

        pid = pid_match.group(1)

        event = {
            "pid": pid,
            "line": line.strip()
        }

        _event_queue.put(event)

# ============================================================
# PUBLIC API
# ============================================================

def start_error_detector():
    """
    Memulai daemon sekali saja.
    """

    thread = threading.Thread(
        target=_logcat_daemon,
        daemon=True,
        name="ErrorDetector"
    )

    thread.start()

# ============================================================
# EVENT API
# ============================================================

def has_event():
    return not _event_queue.empty()


def get_event():

    try:
        return _event_queue.get_nowait()

    except queue.Empty:
        return None
