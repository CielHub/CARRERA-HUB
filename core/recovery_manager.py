"""
Modul : recovery_manager.py
Tanggung Jawab:
- Menjalankan thread Recovery Manager secara independen.
- Menerima event dari Error Detector.
- Mengeksekusi kill pada target.
- Mengatur keseluruhan alur recovery Error267 dan Watchdog.
"""

import threading
import time

from core.error_detector import has_event, get_event
from core.process_manager import graceful_kill, get_pid
from core.cache_cleaner import clean_package_cache
from core.launcher import launch_and_wait
from core.logger import log

class RecoveryManager:

    def __init__(self):
        self._running = False
        self._thread = None
        
        self.packages = []
        self.stats = {}
        self.tracked_pids = {}
        self.intent_url = None
        self.timeout_seconds = 60
        self.config_data = {}

    def configure(self, packages, stats, tracked_pids, intent_url, timeout_seconds, config_data):
        self.packages = packages
        self.stats = stats
        self.tracked_pids = tracked_pids
        self.intent_url = intent_url
        self.timeout_seconds = timeout_seconds
        self.config_data = config_data

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

                pid = event["pid"]

                for pkg in self.packages:
                    if self.stats[pkg]["pid"] != pid:
                        continue

                    # Jangan proses dua kali
                    if self.stats[pkg]["status"] == "RECOVERY":
                        break

                    success = graceful_kill(pid, pkg)

                    if not success:
                        break

                    self.stats[pkg]["status"] = "RECOVERY"
                    self.stats[pkg]["pid"] = "-"
                    self.tracked_pids[pkg] = ""

                    threading.Thread(
                        target=self.recovery_worker,
                        args=(pkg,),
                        daemon=True
                    ).start()

                    break

            time.sleep(0.1)

    def recovery_worker(self, pkg):
        try:
            log.info(f"RECOVERY: Menunggu 15 detik untuk {pkg} agar server Roblox melepas data...")
            time.sleep(15)

            clean_package_cache(pkg)
            self.stats[pkg]['status'] = 'LOADING'
            
            pkg_intent = self.intent_url[pkg] if isinstance(self.intent_url, dict) else self.intent_url
            success = launch_and_wait(pkg, pkg_intent, self.timeout_seconds)
            
            if not success:
                try:
                    from core.autologin import run as run_autologin
                    self.stats[pkg]['status'] = 'LOGIN'
                    
                    login_status = run_autologin(pkg)
                    
                    if login_status in ["SUCCESS", "ALREADY_LOGGED_IN"]:
                        self.stats[pkg]['status'] = 'LOADING'
                        success = launch_and_wait(pkg, pkg_intent, self.timeout_seconds)
                    elif login_status == "CAPTCHA":
                        self.stats[pkg]['status'] = 'CAPTCHA'
                        return
                    else:
                        self.stats[pkg]['status'] = 'LOGIN FAILED'
                        return
                except ImportError:
                    pass

            current_time = time.time()
            
            if success:
                new_pid = get_pid(pkg)
                self.tracked_pids[pkg] = new_pid
                self.stats[pkg]['pid'] = new_pid if new_pid else '-'
                self.stats[pkg]['recovery_count'] += 1
                self.stats[pkg]['status'] = 'ONLINE'
                self.stats[pkg]['uptime_start'] = current_time
                self.stats[pkg]['last_recovery_time'] = current_time
                
                if self.config_data and self.config_data.get('GRID_ENABLED'):
                    try:
                        from core import gridlayout
                        gridlayout.apply_grid_single(
                            pkg, self.packages,
                            cell_w=self.config_data.get('GRID_CELL_W') or None,
                            cell_h=self.config_data.get('GRID_CELL_H') or None,
                            cols=self.config_data.get('GRID_COLS') or None,
                            margin=self.config_data.get('GRID_MARGIN', 10),
                            offset_y=self.config_data.get('GRID_OFFSET_Y', 60),
                        )
                    except ImportError:
                        pass
            else:
                if self.stats[pkg]['status'] not in ['LOGIN FAILED', 'CAPTCHA']:
                    self.stats[pkg]['status'] = 'FAILED'
        except Exception as e:
            log.error(f"RECOVERY FATAL: {str(e)}")
            self.stats[pkg]['status'] = 'FAILED'

_manager = RecoveryManager()

def start_recovery_manager(packages, stats, tracked_pids, intent_url, timeout_seconds, config_data):
    _manager.configure(packages, stats, tracked_pids, intent_url, timeout_seconds, config_data)
    _manager.start()

def stop_recovery_manager():
    _manager.stop()

def trigger_recovery(pkg):
    threading.Thread(
        target=_manager.recovery_worker,
        args=(pkg,),
        daemon=True
    ).start()
            
