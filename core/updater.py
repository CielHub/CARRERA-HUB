"""
Modul: updater.py
Tanggung Jawab: Core logika Auto Updater dengan arsitektur modular, 
                mendukung abstraksi Provider dan persiapan Event-Driven.
"""
import os
import subprocess
from enum import Enum
from typing import Tuple
from core.logger import log

# ==========================================
# 1. ENUMS (STATE & EVENT)
# ==========================================
class UpdaterState(Enum):
    IDLE = "IDLE"
    CHECKING = "CHECKING"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    DOWNLOADING = "DOWNLOADING"
    INSTALLING = "INSTALLING"
    RESTARTING = "RESTARTING"
    ERROR = "ERROR"

class UpdaterEvent(Enum):
    # Persiapan untuk Phase Event-Driven (Discord / Dashboard)
    UPDATE_CHECK_STARTED = "UPDATE_CHECK_STARTED"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    DOWNLOAD_STARTED = "DOWNLOAD_STARTED"
    DOWNLOAD_FINISHED = "DOWNLOAD_FINISHED"
    UPDATE_FAILED = "UPDATE_FAILED"
    UPDATE_COMPLETED = "UPDATE_COMPLETED"

# ==========================================
# 2. PROVIDER ABSTRACTION (STRATEGY PATTERN)
# ==========================================
class UpdateProvider:
    """Base class untuk semua metode update di masa depan."""
    def get_latest_version(self) -> str:
        raise NotImplementedError
        
    def execute_download_and_install(self) -> bool:
        raise NotImplementedError

class GitProvider(UpdateProvider):
    """Implementasi konkrit untuk Phase 2 (menggunakan Git)."""
    def get_latest_version(self) -> str:
        # TODO: Logika hit API GitHub Raw untuk baca version.py
        pass

    def execute_download_and_install(self) -> bool:
        # TODO: Logika git status --porcelain, git pull, dan rollback mechanism
        pass

# ==========================================
# 3. CORE UPDATER MANAGER
# ==========================================
class AutoUpdater:
    def __init__(self, provider: UpdateProvider):
        # State di-encapsulate agar tidak diubah sembarangan dari luar
        self._state = UpdaterState.IDLE
        self.provider = provider
        
    def set_state(self, new_state: UpdaterState):
        """Satu pintu untuk mengubah state (Persiapan Observer Pattern)"""
        self._state = new_state
        # Nanti di sini kita bisa tambahkan: event_manager.emit(Event, new_state)
        log.debug(f"UPDATER STATE BERUBAH -> {self._state.name}")
        
    def get_state(self) -> UpdaterState:
        return self._state

    def is_safe_to_update(self) -> Tuple[bool, str]:
        """Validasi tersentralisasi dengan pesan balasan."""
        # TODO: Cek monitor.py, cache_cleaner.py, dll
        # Contoh simulasi:
        # return False, "Sistem Monitoring masih aktif menjaga package."
        return True, "Sistem dalam keadaan aman untuk update."

    def check_for_updates(self, current_version: str):
        self.set_state(UpdaterState.CHECKING)
        try:
            latest_version = self.provider.get_latest_version()
            # Logika komparasi akan masuk sini
        except Exception as e:
            self.set_state(UpdaterState.ERROR)
            
    def execute_update(self) -> bool:
        safe, reason = self.is_safe_to_update()
        if not safe:
            log.warning(f"UPDATER DITOLAK: {reason}")
            self.set_state(UpdaterState.ERROR)
            return False

        self.set_state(UpdaterState.DOWNLOADING)
        
        # Eksekusi diserahkan ke Provider (Git)
        success = self.provider.execute_download_and_install()
        
        if success:
            self.set_state(UpdaterState.RESTARTING)
            return True
        else:
            log.error("UPDATER: Gagal melakukan update. Mengembalikan ke versi sebelumnya.")
            self.set_state(UpdaterState.IDLE) # Kembali ke idle tanpa restart (Rollback)
            return False

    def restart_program(self):
        """Hard restart menggunakan os.execv()"""
        pass
      
