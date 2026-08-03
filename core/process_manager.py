"""
Modul : process_manager.py

Phase 2

Tanggung Jawab:
- Graceful terminate berdasarkan PID.
- Tidak melakukan Launch.
- Tidak melakukan Recovery.
- Tidak menyentuh Dashboard.
"""

import subprocess
import time


def pid_exists(pid):

    result = subprocess.run(
        ["su", "-c", f"kill -0 {pid}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def graceful_kill(pid, package=None):

    if not pid:
        return True

    # ====================================================
    # STEP 1
    # SIGTERM
    # ====================================================

    subprocess.run(
        ["su", "-c", f"kill -15 {pid}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(10):

        if not pid_exists(pid):
            return True

        time.sleep(0.2)

    # ====================================================
    # STEP 2
    # SIGKILL
    # ====================================================

    subprocess.run(
        ["su", "-c", f"kill -9 {pid}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(10):

        if not pid_exists(pid):
            return True

        time.sleep(0.2)

    # ====================================================
    # STEP 3
    # Fallback
    # ====================================================

    if package:

        subprocess.run(
            ["su", "-c", f"am force-stop {package}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(1)

    return not pid_exists(pid)
