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

class RootExecutor:
    """Eksekusi perintah Android via akses Root."""
    @staticmethod
    def run(cmd, timeout=15):
        try:
            result = subprocess.run(
                ['su', '-c', cmd], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return "", "Timeout expired"
        except Exception as e:
            return "", str(e)

    @staticmethod
    def enable_wakelock():
        """Mencegah Android mematikan Termux (Doze Mode)."""
        stdout, _ = RootExecutor.run("dumpsys deviceidle whitelist +com.termux")
        return "Added" in stdout or stdout == ""

class URLParser:
    """Memparsing link Private Server Roblox."""
    @staticmethod
    def convert_to_deeplink(url):
        url = url.strip()
        if url.startswith("roblox://"):
            return url
        match_code = re.search(r'code=([a-zA-Z0-9]+)', url, re.IGNORECASE)
        if match_code:
            return f"roblox://navigation/share_links?code={match_code.group(1)}&type=Server"
        return None 

# ==========================================
# 2. APP MONITOR & ACTION EXECUTOR
# ==========================================

class AppMonitor:
    """Sensor untuk mendeteksi status aplikasi."""
    @staticmethod
    def is_process_running(package_name):
        stdout, _ = RootExecutor.run(f"pidof {package_name}")
        return bool(stdout)

    @staticmethod
    def is_window_visible(package_name):
        stdout, _ = RootExecutor.run("dumpsys window windows")
        return package_name in stdout

    @staticmethod
    def get_current_state(package_name):
        has_pid = AppMonitor.is_process_running(package_name)
        has_window = AppMonitor.is_window_visible(package_name)
        
        if not has_pid: return "STATE_STOPPED"
        if has_pid and not has_window: return "STATE_GHOST_PROCESS"
        if has_pid and has_window: return "STATE_RUNNING"
        return "STATE_UNKNOWN"

class ActionExecutor:
    """Mengeksekusi tindakan ke aplikasi Android."""
    @staticmethod
    def force_stop(package_name):
        RootExecutor.run(f"am force-stop {package_name}")

    @staticmethod
    def start_app(package_name):
        # Gunakan monkey agar activity utama otomatis terdeteksi untuk hasil clone APK
        RootExecutor.run(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")

    @staticmethod
    def join_server(package_name, deep_link):
        safe_link = f'"{deep_link}"'
        cmd = f"am start -W -f 0x14000000 -a android.intent.action.VIEW -d {safe_link} {package_name}"
        RootExecutor.run(cmd)

# ==========================================
# 3. WATCHDOG STATE MACHINE
# ==========================================

class Watchdog:
    """Mesin pengontrol utama sekuensial."""
    def __init__(self, target_packages, server_link, startup_delay=40):
        self.packages = target_packages
        self.server_link = URLParser.convert_to_deeplink(server_link)
        self.startup_delay = startup_delay
        
        self.package_states = {pkg: "INITIALIZING" for pkg in self.packages}
        self.startup_timestamps = {}
        
    def process_single_package(self, pkg):
        current_condition = AppMonitor.get_current_state(pkg)
        
        if current_condition in ["STATE_STOPPED", "STATE_GHOST_PROCESS"]:
            ActionExecutor.force_stop(pkg)
            ActionExecutor.start_app(pkg)
            self.startup_timestamps[pkg] = time.time()
            self.package_states[pkg] = "STATE_STARTING"
            
        elif current_condition == "STATE_RUNNING":
            if pkg in self.startup_timestamps:
                elapsed_time = time.time() - self.startup_timestamps[pkg]
                if elapsed_time < self.startup_delay:
                    time_left = int(self.startup_delay - elapsed_time)
                    self.package_states[pkg] = f"STATE_STARTING ({time_left}s left)"
                else:
                    ActionExecutor.join_server(pkg, self.server_link)
                    del self.startup_timestamps[pkg]
                    self.package_states[pkg] = "STATE_JOINING_SERVER"
            else:
                self.package_states[pkg] = "STATE_IN_GAME / MONITORING"
                
        return self.package_states[pkg]

    def run_cycle(self):
        for pkg in self.packages:
            self.process_single_package(pkg)
            time.sleep(0.5) # Jeda nafas CPU Android

# ==========================================
# 4. USER INTERFACE (UI)
# ==========================================

def clear_screen():
    os.system('clear')

def print_ascii_art():
    logo = f"""{Colors.CYAN}{Colors.BOLD}
    ______                                     
   / ____/___ ______________  _________ _      
  / /   / __ `/ ___/ ___/ _ \/ ___/ __ `/      
 / /___/ /_/ / /  / /  /  __/ /  / /_/ /       
 \____/\__,_/_/  /_/   \___/_/   \__,_/        
                                               
 {Colors.WHITE}[ Auto Rejoiner - Delta Lite Termux Edition ]{Colors.RESET}
    """
    print(logo)

def print_divider():
    print(f"{Colors.WHITE}================================================================={Colors.RESET}")

def scan_installed_packages():
    detected_packages = []
    try:
        result = subprocess.run(['pm', 'list', 'packages'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'roblox' in line.lower() or 'delta' in line.lower():
                pkg_name = line.split(':')[1].strip()
                detected_packages.append(pkg_name)
        return sorted(list(set(detected_packages)))
    except Exception:
        return ['com.roblox.client']

def render_main_menu(server_link="Not Set", target_packages=None):
    if target_packages is None:
        target_packages = []
        
    clear_screen()
    print_divider()
    print_ascii_art()
    print_divider()
    
    print(f"\n {Colors.BOLD}[ SYSTEM INFO ]{Colors.RESET}")
    
    if not target_packages:
        display_pkgs = f"{Colors.RED}None Selected{Colors.RESET}"
    else:
        joined_pkgs = ", ".join(target_packages)
        display_pkgs = f"{Colors.CYAN}{joined_pkgs[:39]}...{Colors.RESET}" if len(joined_pkgs) > 42 else f"{Colors.CYAN}{joined_pkgs}{Colors.RESET}"
            
    print(f" Target Packages: {display_pkgs}")
    print(f" Root Access    : {Colors.GREEN}[ OK ]{Colors.RESET}") 
    print(f" Doze/Wakelock  : {Colors.GREEN}[ READY ]{Colors.RESET}")
    
    print(f"\n {Colors.BOLD}[ BOT STATUS ]{Colors.RESET}")
    display_link = server_link if len(server_link) < 45 else server_link[:42] + "..."
    link_color = Colors.WHITE if server_link == "Not Set" else Colors.GREEN
    print(f" Current State  : {Colors.YELLOW}IDLE (Waiting for command){Colors.RESET}")
    print(f" Target Server  : {link_color}{display_link}{Colors.RESET}\n")
    
    print_divider()
    print(f" {Colors.BOLD}[ MAIN MENU ]{Colors.RESET}\n")
    print(f" {Colors.YELLOW}[ 1 ]{Colors.RESET} Set Private Server Link")
    print(f" {Colors.YELLOW}[ 2 ]{Colors.RESET} Select Target Packages (Multi-Select)")
    print(f" {Colors.YELLOW}[ 3 ]{Colors.RESET} Start Auto Rejoiner (Watchdog Mode)")
    print(f" {Colors.YELLOW}[ 4 ]{Colors.RESET} Stop / Force Kill All Selected")
    print(f" {Colors.RED}[ 0 ]{Colors.RESET} Exit\n")
    print_divider()

def multi_select_menu(available_packages, current_selection):
    while True:
        clear_screen()
        print_divider()
        print(f" {Colors.CYAN}{Colors.BOLD}[ MULTI-SELECT PACKAGES ]{Colors.RESET}")
        print(f" {Colors.WHITE}Pilih angka untuk menandai/menghapus ceklis.{Colors.RESET}")
        print_divider()
        print("")
        
        if not available_packages:
            print(f" {Colors.RED}Tidak ada package Roblox yang terdeteksi!{Colors.RESET}")
            time.sleep(2)
            return current_selection
            
        for idx, pkg in enumerate(available_packages):
            if pkg in current_selection:
                checkbox = f"{Colors.GREEN}[ X ]{Colors.RESET}"
                pkg_text = f"{Colors.GREEN}{pkg}{Colors.RESET}"
            else:
                checkbox = f"{Colors.WHITE}[   ]{Colors.RESET}"
                pkg_text = f"{Colors.WHITE}{pkg}{Colors.RESET}"
            print(f" {Colors.YELLOW}[ {idx + 1} ]{Colors.RESET} {checkbox} {pkg_text}")
            
        print(f"\n {Colors.RED}[ 0 ]{Colors.RESET} {Colors.BOLD}Selesai & Kembali{Colors.RESET}")
        print_divider()
        
        try:
            selection = input(f"\n {Colors.CYAN}Pilih Nomor:{Colors.RESET} ")
            if selection == '0': break
                
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < len(available_packages):
                selected_pkg = available_packages[sel_idx]
                if selected_pkg in current_selection:
                    current_selection.remove(selected_pkg)
                else:
                    current_selection.append(selected_pkg)
            else:
                print(f" {Colors.RED}Pilihan tidak valid.{Colors.RESET}")
                time.sleep(0.5)
        except ValueError:
            print(f" {Colors.RED}Input harus berupa angka.{Colors.RESET}")
            time.sleep(0.5)
            
    return current_selection

def live_watchdog_dashboard(watchdog):
    """Merender dashboard real-time tanpa berkedip parah."""
    clear_screen()
    print_divider()
    print(f" {Colors.CYAN}{Colors.BOLD}[ WATCHDOG MODE - ACTIVE ]{Colors.RESET}")
    print(f" {Colors.RED}>> Tekan CTRL + C untuk menghentikan & kembali ke menu.{Colors.RESET}")
    print_divider()
    
    for pkg in watchdog.packages:
        state = watchdog.package_states[pkg]
        if "IN_GAME" in state:
            color = Colors.GREEN
        elif "STARTING" in state or "JOINING" in state:
            color = Colors.YELLOW
        else:
            color = Colors.RED
            
        print(f" {Colors.WHITE}[ {pkg} ]{Colors.RESET}")
        print(f" Status : {color}{state}{Colors.RESET}\n")
    print_divider()

# ==========================================
# 5. MAIN APPLICATION LOOP
# ==========================================

def main_loop():
    current_link = "Not Set"
    available_packages = scan_installed_packages()
    target_packages = [available_packages[0]] if available_packages else []
    
    while True:
        render_main_menu(server_link=current_link, target_packages=target_packages)
        
        try:
            choice = input(f" {Colors.CYAN}Carrera-Bot@Termux:~# {Colors.RESET}")
            
            if choice == '1':
                print(f"\n {Colors.YELLOW}>>{Colors.RESET} Paste link Private Server Roblox:")
                current_link = input(f" {Colors.CYAN}Link:{Colors.RESET} ").strip()
                
            elif choice == '2':
                available_packages = scan_installed_packages() 
                target_packages = multi_select_menu(available_packages, target_packages)
                
            elif choice == '3':
                if not target_packages:
                    print(f"\n {Colors.RED}>> Error: Tidak ada package yang dipilih!{Colors.RESET}")
                    time.sleep(2)
                    continue
                if current_link == "Not Set" or URLParser.convert_to_deeplink(current_link) is None:
                    print(f"\n {Colors.RED}>> Error: Link Private Server tidak valid!{Colors.RESET}")
                    time.sleep(2)
                    continue
                    
                print(f"\n {Colors.GREEN}>> Mengaktifkan Wakelock...{Colors.RESET}")
                RootExecutor.enable_wakelock()
                time.sleep(1)
                
                # Inisialisasi State Machine
                watchdog = Watchdog(target_packages, current_link, startup_delay=40)
                
                try:
                    # Looping Utama Watchdog (Sequential)
                    while True:
                        watchdog.run_cycle()
                        live_watchdog_dashboard(watchdog)
                        time.sleep(2) # Refresh UI setiap 2 detik
                except KeyboardInterrupt:
                    print(f"\n {Colors.YELLOW}>> Watchdog dihentikan oleh user. Kembali ke menu utama...{Colors.RESET}")
                    time.sleep(1.5)
                
            elif choice == '4':
                if not target_packages:
                    print(f"\n {Colors.RED}>> Tidak ada target untuk dimatikan.{Colors.RESET}")
                else:
                    print(f"\n {Colors.RED}>> Mengeksekusi 'am force-stop' untuk {len(target_packages)} package...{Colors.RESET}")
                    for pkg in target_packages:
                        ActionExecutor.force_stop(pkg)
                time.sleep(1.5)
                
            elif choice == '0':
                clear_screen()
                print(f"{Colors.GREEN}Terima kasih telah menggunakan Carrera Auto Rejoiner.{Colors.RESET}")
                sys.exit(0)
                
        except KeyboardInterrupt:
            clear_screen()
            print(f"{Colors.GREEN}Program dihentikan oleh user.{Colors.RESET}")
            sys.exit(0)

if __name__ == "__main__":
    # Pastikan script dijalankan di environment Termux/Root
    main_loop()
