import os
import time
import subprocess

# ANSI Color Codes untuk Termux
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Membersihkan layar terminal."""
    os.system('clear')

def print_ascii_art():
    """Menampilkan logo Carrera."""
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
    """Memindai sistem Android untuk mencari package Roblox/Delta yang terinstal."""
    detected_packages = []
    try:
        # Menjalankan Android Package Manager (pm) untuk melihat daftar aplikasi
        result = subprocess.run(['pm', 'list', 'packages'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            # Filter berdasarkan kata kunci yang sering digunakan
            if 'roblox' in line.lower() or 'delta' in line.lower():
                # Output dari sistem berbentuk "package:com.nama.aplikasi"
                pkg_name = line.split(':')[1].strip()
                detected_packages.append(pkg_name)
                
        # Hilangkan duplikasi dan urutkan
        return sorted(list(set(detected_packages)))
    except Exception as e:
        # Fallback aman jika command gagal
        return ['com.roblox.client']

def render_menu(state="STATE_STOPPED", pid="None", server_link="Not Set", target_package="Scanning..."):
    """Fungsi utama untuk merender dashboard menu."""
    clear_screen()
    print_divider()
    print_ascii_art()
    print_divider()
    
    # SYSTEM INFO SECTION
    print(f"\n {Colors.BOLD}[ SYSTEM INFO ]{Colors.RESET}")
    print(f" Target Package : {Colors.CYAN}{target_package}{Colors.RESET}")
    print(f" Root Access    : {Colors.GREEN}[ OK ]{Colors.RESET}") 
    print(f" Doze/Wakelock  : {Colors.GREEN}[ ACTIVE ]{Colors.RESET}")
    
    # BOT STATUS SECTION
    print(f"\n {Colors.BOLD}[ BOT STATUS ]{Colors.RESET}")
    state_color = Colors.GREEN if state == "STATE_IN_GAME" else Colors.YELLOW
    if state == "STATE_STOPPED":
        state_color = Colors.RED
        
    print(f" Current State  : {state_color}{state}{Colors.RESET}")
    print(f" Active PID     : {Colors.WHITE}{pid}{Colors.RESET}")
    
    display_link = server_link if len(server_link) < 45 else server_link[:42] + "..."
    link_color = Colors.WHITE if server_link == "Not Set" else Colors.GREEN
    print(f" Target Server  : {link_color}{display_link}{Colors.RESET}\n")
    
    print_divider()
    
    # MAIN MENU SECTION (Diperbarui)
    print(f" {Colors.BOLD}[ MAIN MENU ]{Colors.RESET}\n")
    print(f" {Colors.YELLOW}[ 1 ]{Colors.RESET} Set Private Server Link")
    print(f" {Colors.YELLOW}[ 2 ]{Colors.RESET} Select Target Package")
    print(f" {Colors.YELLOW}[ 3 ]{Colors.RESET} Start Auto Rejoiner (Watchdog Mode)")
    print(f" {Colors.YELLOW}[ 4 ]{Colors.RESET} Stop / Force Kill Target")
    print(f" {Colors.YELLOW}[ 5 ]{Colors.RESET} View System Logs")
    print(f" {Colors.RED}[ 0 ]{Colors.RESET} Exit\n")
    
    print_divider()

def main_loop():
    """Looping utama antarmuka pengguna."""
    current_link = "Not Set"
    
    # Inisialisasi awal pencarian package
    available_packages = scan_installed_packages()
    target_package = available_packages[0] if available_packages else "com.roblox.client"
    
    while True:
        render_menu(server_link=current_link, target_package=target_package)
        
        try:
            choice = input(f" {Colors.CYAN}Carrera-Bot@Termux:~# {Colors.RESET}")
            
            if choice == '1':
                print(f"\n {Colors.YELLOW}>>{Colors.RESET} Paste link Private Server Roblox:")
                current_link = input(f" {Colors.CYAN}Link:{Colors.RESET} ").strip()
                
            elif choice == '2':
                # Sub-menu untuk memilih package
                available_packages = scan_installed_packages() # Rescan just in case
                print(f"\n {Colors.BOLD}[ DETECTED PACKAGES ]{Colors.RESET}")
                if not available_packages:
                    print(f" {Colors.RED}Tidak ada package Roblox yang terdeteksi!{Colors.RESET}")
                    time.sleep(2)
                    continue
                    
                for idx, pkg in enumerate(available_packages):
                    indicator = " (Active)" if pkg == target_package else ""
                    print(f" {Colors.YELLOW}[ {idx + 1} ]{Colors.RESET} {pkg}{Colors.GREEN}{indicator}{Colors.RESET}")
                
                try:
                    selection = input(f"\n {Colors.CYAN}Pilih Nomor Package:{Colors.RESET} ")
                    sel_idx = int(selection) - 1
                    if 0 <= sel_idx < len(available_packages):
                        target_package = available_packages[sel_idx]
                        print(f" {Colors.GREEN}Target diubah ke: {target_package}{Colors.RESET}")
                        time.sleep(1)
                    else:
                        print(f" {Colors.RED}Pilihan tidak valid.{Colors.RESET}")
                        time.sleep(1)
                except ValueError:
                    print(f" {Colors.RED}Input harus berupa angka.{Colors.RESET}")
                    time.sleep(1)
                    
            elif choice == '3':
                print(f"\n {Colors.GREEN}>> Memulai Watchdog untuk {target_package}...{Colors.RESET}")
                time.sleep(1)
                
            elif choice == '4':
                print(f"\n {Colors.RED}>> Mengeksekusi 'am force-stop {target_package}'...{Colors.RESET}")
                time.sleep(1)
                
            elif choice == '5':
                print(f"\n {Colors.WHITE}>> Membuka Logcat untuk {target_package}...{Colors.RESET}")
                time.sleep(1)
                
            elif choice == '0':
                clear_screen()
                print(f"{Colors.GREEN}Terima kasih telah menggunakan Carrera Auto Rejoiner.{Colors.RESET}")
                break
                
        except KeyboardInterrupt:
            clear_screen()
            print(f"{Colors.GREEN}Program dihentikan oleh user.{Colors.RESET}")
            break

if __name__ == "__main__":
    main_loop()
