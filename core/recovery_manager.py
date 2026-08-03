"""
Modul : recovery_manager.py

Tahap 1

Tanggung Jawab:
- Menjalankan thread Recovery Manager.
- Menerima event dari Error Detector.
- Belum melakukan kill.
- Belum melakukan recovery.
- Belum melakukan launch.

Tahap ini hanya membangun fondasi arsitektur baru.
"""

import threading
import time

from core.error_detector import (
    has_event,
    get_event,
)


class RecoveryManager:

    def __init__(self):

        self._running = False
        self._thread = None

    def start(self):

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="RecoveryManager"
        )

        self._thread.start()

    def stop(self):
        self._running = False

    def _worker(self):

        while self._running:

            while has_event():

                event = get_event()

                if event is None:
                    break

                # ==================================================
                # Tahap 1
                #
                # Event diterima.
                # Belum melakukan apapun.
                # ==================================================

                pass

            time.sleep(0.1)


_manager = RecoveryManager()


def start_recovery_manager():
    _manager.start()


def stop_recovery_manager():
    _manager.stop()
