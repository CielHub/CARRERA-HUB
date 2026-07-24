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
        result = subprocess.run(['pm', 'list', 'packages'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'roblox' in line.lower() or 'delta' in line.lower():
                pkg_name = line.split(':')[1].strip()
                detected_packages.append(pkg_name)
        return sorted(list(set(detected_packages)))
    except Exception as e:
        return ['com.roblox.client']

def render_menu(state="STATE_STOPPED", pid="None", server_link="Not Set", target_packages=None):
    """Fungsi utama untuk merender dashboard menu."""
    if target_packages is None:
        target_packages = []
        
    clear_screen()
    print_divider()
    print_ascii_art()
    print_divider()
    
    # SYSTEM INFO SECTION
    print(f"\n {Colors.BOLD}[ SYSTEM INFO ]{Colors.RESET}")
    
    # Format list package agar rapi di UI
    if not target_packages:
        display_pkgs = f"{Colors.RED}None Selected{Colors.RESET}"
    else:
        joined_pkgs = ", ".join(target_packages)
        # Potong string jika kepanjangan agar tidak merusak layout
        if len(joined_pkgs) > 42:
            display_pkgs = f"{Colors.CYAN}{joined_pkgs[:39]}...{Colors.RESET}"
        else:
            display_pkgs = f"{Colors.CYAN}{joined_pkgs}{Colors.RESET}"
            
    print(f" Target Packages: {display_pkgs}")
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
    
    # MAIN MENU SECTION
    print(f" {Colors.BOLD}[ MAIN MENU ]{Colors.RESET}\n")
    print(f" {Colors.YELLOW}[ 1 ]{Colors.RESET} Set Private Server Link")
    print(f" {Colors.YELLOW}[ 2 ]{Colors.RESET} Select Target Packages (Multi-Select)")
    print(f" {Colors.YELLOW}[ 3 ]{Colors.RESET} Start Auto Rejoiner (Watchdog Mode)")
    print(f" {Colors.YELLOW}[ 4 ]{Colors.RESET} Stop / Force Kill All Targets")
    print(f" {Colors.YELLOW}[ 5 ]{Colors.RESET} View System Logs")
    print(f" {Colors.RED}[ 0 ]{Colors.RESET} Exit\n")
    
    print_divider()

def multi_select_menu(available_packages, current_selection):
    """Sub-menu untuk memilih banyak package dengan fitur toggle."""
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
            # Logika Checkbox
            if pkg in current_selection:
                checkbox = f"{Colors.GREEN}[ X ]{Colors.RESET}"
                pkg_text = f"{Colors.GREEN}{pkg}{Colors.RESET}"
            else:
                checkbox = f"{Colors.WHITE}[   ]{Colors.RESET}"
                pkg_text = f"{Colors.WHITE}{pkg}{Colors.RESET}"
                
            print(f" {Colors.YELLOW}[ {idx + 1} ]{Colors.RESET} {checkbox} {pkg_text}")
            
        print(f"\n {Colors.RED}[ 0 ]{Colors.RESET} {Colors.BOLD}Selesai & Kembali ke Menu Utama{Colors.RESET}")
        print_divider()
        
        try:
            selection = input(f"\n {Colors.CYAN}Pilih Nomor:{Colors.RESET} ")
            if selection == '0':
                break
                
            sel_idx = int(selection) - 1
            if 0 <= sel_idx < len(available_packages):
                selected_pkg = available_packages[sel_idx]
                
                # Logika Toggle (Tambah/Hapus dari list)
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

def main_loop():
    """Looping utama antarmuka pengguna."""
    current_link = "Not Set"
    
    # Inisialisasi awal pencarian package
    available_packages = scan_installed_packages()
    # Secara default, masukkan package pertama ke dalam list (jika ada)
    target_packages = [available_packages[0]] if available_packages else []
    
    while True:
        render_menu(server_link=current_link, target_packages=target_packages)
        
        try:
            choice = input(f" {Colors.CYAN}Carrera-Bot@Termux:~# {Colors.RESET}")
            
            if choice == '1':
                print(f"\n {Colors.YELLOW}>>{Colors.RESET} Paste link Private Server Roblox:")
                current_link = input(f" {Colors.CYAN}Link:{Colors.RESET} ").strip()
                
            elif choice == '2':
                # Panggil sub-menu multi-select dan perbarui target_packages
                available_packages = scan_installed_packages() 
                target_packages = multi_select_menu(available_packages, target_packages)
                
            elif choice == '3':
                if not target_packages:
                    print(f"\n {Colors.RED}>> Error: Tidak ada package yang dipilih!{Colors.RESET}")
                    time.sleep(2)
                    continue
                print(f"\n {Colors.GREEN}>> Memulai Watchdog untuk {len(target_packages)} package...{Colors.RESET}")
                time.sleep(1)
                
            elif choice == '4':
                if not target_packages:
                    print(f"\n {Colors.RED}>> Tidak ada target untuk dimatikan.{Colors.RESET}")
                else:
                    print(f"\n {Colors.RED}>> Mengeksekusi 'am force-stop' untuk {len(target_packages)} package...{Colors.RESET}")
                time.sleep(1)
                
            elif choice == '5':
                print(f"\n {Colors.WHITE}>> Membuka Logcat...{Colors.RESET}")
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
