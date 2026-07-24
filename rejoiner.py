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
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==========================================
# 2. ROOT EXECUTOR
# ==========================================

class RootExecutor:
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
                print(f"[{Colors.CYAN}CMD{Colors.RESET}] {cmd}")
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
# 3. URL PARSER
# ==========================================

class URLParser:
    @staticmethod
    def convert_to_deeplink(url):
        if not url:
            return None
        url = url.strip()
        if url.startswith("roblox://"):
            return url
            
        match = re.search(r"code=([A-Za-z0-9]+).*?type=Server", url, re.IGNORECASE)
        if match:
            code = match.group(1)
            return f"roblox://navigation/share_links?code={code}&type=Server"
            
        match = re.search(r"privateServerLinkCode=([A-Za-z0-9]+)", url, re.IGNORECASE)
        if match:
            code = match.group(1)
            return f"roblox://navigation/share_links?code={code}&type=Server"
            
        return None

    @staticmethod
    def validate(url):
        return URLParser.convert_to_deeplink(url) is not None

# ==========================================
# 4. APP MONITOR
# ==========================================

class AppMonitor:
    @staticmethod
    def is_process_running(package_name):
        stdout, _ = RootExecutor.run(f"pidof {package_name}")
        return bool(stdout.strip())

    @staticmethod
    def is_window_visible(package_name):
        stdout, _ = RootExecutor.run("dumpsys window windows")
        return package_name in stdout

    @staticmethod
    def is_foreground(package_name):
        stdout, _ = RootExecutor.run("dumpsys activity activities | grep mResumedActivity")
        return package_name in stdout

    @staticmethod
    def get_focus():
        stdout, _ = RootExecutor.run("dumpsys window | grep mCurrentFocus")
        return stdout

    @staticmethod
    def get_pid(package_name):
        stdout, _ = RootExecutor.run(f"pidof {package_name}")
        return stdout.strip()

    @staticmethod
    def is_alive(package_name):
        return (AppMonitor.is_process_running(package_name) and 
                AppMonitor.is_window_visible(package_name))

    @staticmethod
    def get_current_state(package_name):
        if not AppMonitor.is_process_running(package_name):
            return "STATE_STOPPED"
        if not AppMonitor.is_window_visible(package_name):
            return "STATE_GHOST_PROCESS"
        if not AppMonitor.is_foreground(package_name):
            return "STATE_BACKGROUND"
        return "STATE_RUNNING"

# ==========================================
# 5. ACTION EXECUTOR
# ==========================================

class ActionExecutor:
    @staticmethod
    def force_stop(package_name):
        RootExecutor.run(f"am force-stop {package_name}", silent=True)

    @staticmethod
    def start_app(package_name):
        RootExecutor.run(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1", silent=True)

    @staticmethod
    def join_server(package_name, deep_link):
        if not deep_link:
            return False
        cmd = f'am start -a android.intent.action.VIEW -d "{deep_link}" {package_name}'
        _, stderr = RootExecutor.run(cmd, timeout=20, silent=True)
        return "Error" not in stderr

    @staticmethod
    def restart(package_name):
        ActionExecutor.force_stop(package_name)
        ActionExecutor.start_app(package_name)

# ==========================================
# 6. WATCHDOG STATE MACHINE
# ==========================================

class Watchdog:
    def __init__(self, target_packages, server_link, retry_limit=3):
        self.packages = target_packages
        self.server_link = URLParser.convert_to_deeplink(server_link)
        self.retry_limit = retry_limit

        self.state = {}
        self.retry = {}
        self.timer = {}
        self.recovery = {}
        self.startup_timer = {}
        self.join_timer = {}
        self.uptime = {}

        now = time.time()
        for pkg in self.packages:
            self.state[pkg] = "STATE_INITIALIZING"
            self.retry[pkg] = 0
            self.timer[pkg] = now
            self.recovery[pkg] = 0
            self.startup_timer[pkg] = 0
            self.join_timer[pkg] = 0
            self.uptime[pkg] = 0

    def run_cycle(self):
        for pkg in self.packages:
            try:
                self._process_single_package(pkg)
            except Exception as e:
                self.state[pkg] = "STATE_FAILED"
                print(f"[{Colors.RED}ERROR{Colors.RESET}] {pkg}: {str(e)}")

    def _process_single_package(self, pkg):
        current_state = self.state[pkg]
        now = time.time()

        if current_state == "STATE_INITIALIZING":
            self._handle_initializing(pkg, now)
        elif current_state == "STATE_STARTING":
            self._handle_starting(pkg, now)
        elif current_state == "STATE_WAIT_READY":
            self._handle_wait_ready(pkg, now)
        elif current_state == "STATE_RUNNING":
            self._handle_running(pkg, now)
        elif current_state == "STATE_RECOVERING":
            self._handle_recovering(pkg, now)
        elif current_state == "STATE_FAILED" or current_state == "STATE_STOPPED":
            return 

    def _handle_initializing(self, pkg, now):
        ActionExecutor.force_stop(pkg)
        self.state[pkg] = "STATE_STARTING"
        self.timer[pkg] = now

    def _handle_starting(self, pkg, now):
        ActionExecutor.start_app(pkg)
        self.startup_timer[pkg] = now
        self.state[pkg] = "STATE_WAIT_READY"
        self.timer[pkg] = now

    def _handle_wait_ready(self, pkg, now):
        if AppMonitor.is_foreground(pkg):
            if ActionExecutor.join_server(pkg, self.server_link):
                self.join_timer[pkg] = now
                self.state[pkg] = "STATE_RUNNING"
                self.timer[pkg] = now
                self.retry[pkg] = 0 
            else:
                self.state[pkg] = "STATE_RECOVERING"
                self.timer[pkg] = now
            return

        if now - self.startup_timer[pkg] > 45:
            self.state[pkg] = "STATE_RECOVERING"
            self.timer[pkg] = now

    def _handle_running(self, pkg, now):
        if not AppMonitor.is_alive(pkg):
            self.state[pkg] = "STATE_RECOVERING"
            self.timer[pkg] = now
            return
            
        self.uptime[pkg] = int(now - self.join_timer[pkg])

    def _handle_recovering(self, pkg, now):
        if self.retry[pkg] >= self.retry_limit:
            self.state[pkg] = "STATE_FAILED"
            self.timer[pkg] = now
            return

        if now - self.timer[pkg] > 5: 
            self.retry[pkg] += 1
            self.recovery[pkg] = now
            ActionExecutor.force_stop(pkg)
            self.state[pkg] = "STATE_STARTING"
            self.timer[pkg] = now

# ==========================================
# 7. UI FUNCTIONS
# ==========================================

def clear_screen():
    # Menggunakan \033c untuk Reset Initial State (memperbaiki terminal glitch)
    print('\033c', end='')
    sys.stdout.flush()

def print_ascii_art():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=============================================")
    print("         DELTA LITE MULTI PACKAGE V2         ")
    print("=============================================")
    print(f"{Colors.RESET}")

def print_divider():
    print(f"{Colors.WHITE}{'-' * 45}{Colors.RESET}")

def scan_installed_packages():
    stdout, _ = RootExecutor.run("pm list packages | grep roblox")
    if not stdout:
        return []
    
    packages = []
    for line in stdout.splitlines():
        pkg = line.replace("package:", "").strip()
        if pkg:
            packages.append(pkg)
    return packages

def render_main_menu():
    print(f"{Colors.BOLD}MAIN MENU{Colors.RESET}")
    print_divider()
    print(f"{Colors.GREEN}[1]{Colors.RESET} Start Watchdog")
    print(f"{Colors.YELLOW}[2]{Colors.RESET} Select Packages")
    print(f"{Colors.CYAN}[3]{Colors.RESET} Set Deep Link")
    print(f"{Colors.RED}[4]{Colors.RESET} Exit")
    print_divider()

def multi_select_menu(available, selected):
    while True:
        clear_screen()
        print_ascii_art()
        print(f"{Colors.BOLD}SELECT PACKAGES{Colors.RESET}")
        print_divider()
        
        for i, pkg in enumerate(available, 1):
            status = f"{Colors.GREEN}[X]{Colors.RESET}" if pkg in selected else f"{Colors.RED}[ ]{Colors.RESET}"
            print(f"{status} {i}. {pkg}")
            
        print_divider()
        print(f"{Colors.YELLOW}[A]{Colors.RESET} Select All  | {Colors.YELLOW}[C]{Colors.RESET} Clear All | {Colors.YELLOW}[0]{Colors.RESET} Back")
        
        choice = input(f"\n{Colors.BOLD}Choice:{Colors.RESET} ").strip().lower()
        
        if choice == '0':
            break
        elif choice == 'a':
            selected.clear()
            selected.extend(available)
        elif choice == 'c':
            selected.clear()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(available):
                target = available[idx]
                if target in selected:
                    selected.remove(target)
                else:
                    selected.append(target)

def live_watchdog_dashboard(watchdog):
    clear_screen()
    
    # Kumpulkan semua teks dalam satu buffer string untuk mencegah layar kedip/acak-acakan
    buffer = []
    buffer.append(f"{Colors.CYAN}{Colors.BOLD}")
    buffer.append("=============================================")
    buffer.append("         DELTA LITE MULTI PACKAGE V2         ")
    buffer.append("=============================================")
    buffer.append(f"{Colors.RESET}")
    buffer.append(f"{Colors.WHITE}{'-' * 45}{Colors.RESET}")
    buffer.append(f"{Colors.BOLD}{'PACKAGE':<25} | {'STATE':<18} | {'RTY':<3} | {'UPTIME'}{Colors.RESET}")
    buffer.append(f"{Colors.WHITE}{'-' * 45}{Colors.RESET}")
    
    for pkg in watchdog.packages:
        state = watchdog.state[pkg]
        retry = watchdog.retry[pkg]
        uptime = watchdog.uptime[pkg]
        
        if state == "STATE_RUNNING":
            color = Colors.GREEN
            state_str = "RUNNING"
        elif state == "STATE_WAIT_READY" or state == "STATE_STARTING":
            color = Colors.YELLOW
            state_str = "WAITING" if state == "STATE_WAIT_READY" else "STARTING"
        elif state == "STATE_FAILED":
            color = Colors.RED
            state_str = "FAILED"
        elif state == "STATE_RECOVERING":
            color = Colors.YELLOW
            state_str = "RECOVERING"
        else:
            color = Colors.BLUE
            state_str = state.replace("STATE_", "")

        mins, secs = divmod(uptime, 60)
        time_str = f"{mins}m {secs}s" if uptime > 0 else "-"
        
        pkg_short = pkg.replace("com.", "")[:24]
        
        buffer.append(f"{color}{pkg_short:<25} | {state_str:<18} | {retry:<3} | {time_str}{Colors.RESET}")
        
    buffer.append(f"{Colors.WHITE}{'-' * 45}{Colors.RESET}")
    buffer.append(f"{Colors.YELLOW}Press CTRL+C to stop and return to menu.{Colors.RESET}")
    
    # Cetak sekaligus
    print('\n'.join(buffer))

# ==========================================
# 8. MAIN LOOP
# ==========================================

def main_loop():
    if not RootExecutor.check_root():
        print(f"{Colors.RED}Root access not found! Please grant su permissions.{Colors.RESET}")
        sys.exit(1)

    RootExecutor.enable_wakelock()
    
    installed_packages = scan_installed_packages()
    selected_packages = installed_packages.copy()
    deep_link = ""

    while True:
        try:
            clear_screen()
            print_ascii_art()
            render_main_menu()
            
            print(f"{Colors.CYAN}Total Packages:{Colors.RESET} {len(selected_packages)}")
            link_display = deep_link[:30] + "..." if len(deep_link) > 30 else (deep_link or "Not Set")
            print(f"{Colors.CYAN}Current Link:{Colors.RESET} {link_display}\n")
            
            choice = input(f"{Colors.BOLD}Select menu (1-4):{Colors.RESET} ").strip()

            if choice == '1':
                if not selected_packages:
                    print(f"\n{Colors.RED}Error: No packages selected!{Colors.RESET}")
                    time.sleep(2)
                    continue
                    
                if not URLParser.validate(deep_link):
                    print(f"\n{Colors.RED}Error: Invalid or empty Deep Link!{Colors.RESET}")
                    time.sleep(2)
                    continue

                watchdog = Watchdog(selected_packages, deep_link)
                clear_screen()
                
                try:
                    while True:
                        watchdog.run_cycle()
                        live_watchdog_dashboard(watchdog)
                        time.sleep(2)
                except KeyboardInterrupt:
                    clear_screen()
                    print(f"{Colors.YELLOW}Stopping all processes...{Colors.RESET}")
                    for pkg in selected_packages:
                        try:
                            ActionExecutor.force_stop(pkg)
                            print(f"{Colors.GREEN}Stopped {pkg}{Colors.RESET}")
                        except Exception:
                            pass
                    time.sleep(2)

            elif choice == '2':
                multi_select_menu(installed_packages, selected_packages)

            elif choice == '3':
                print(f"\n{Colors.BOLD}Paste your Roblox Private Server / Share link:{Colors.RESET}")
                link_input = input("> ").strip()
                if URLParser.validate(link_input):
                    deep_link = link_input
                    print(f"{Colors.GREEN}Link saved successfully!{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Invalid link format!{Colors.RESET}")
                time.sleep(2)

            elif choice == '4':
                clear_screen()
                print(f"{Colors.GREEN}Thank you for using Delta Lite Multi Package! Goodbye.{Colors.RESET}\n")
                sys.exit(0)

        except KeyboardInterrupt:
            clear_screen()
            print(f"\n{Colors.GREEN}Exiting program safely... Goodbye!{Colors.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.RESET}")
            time.sleep(3)

if __name__ == "__main__":
    main_loop()
