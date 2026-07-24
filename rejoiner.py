import os
import time

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

def render_menu(state="STATE_STOPPED", pid="None", server_link="Not Set"):
    """Fungsi utama untuk merender dashboard menu."""
    clear_screen()
    print_divider()
    print_ascii_art()
    print_divider()
    
    # SYSTEM INFO SECTION
    print(f"\n {Colors.BOLD}[ SYSTEM INFO ]{Colors.RESET}")
    print(f" Target Package : {Colors.CYAN}com.roblox.client (Delta Lite){Colors.RESET}")
    print(f" Root Access    : {Colors.GREEN}[ OK ]{Colors.RESET}") 
    print(f" Doze/Wakelock  : {Colors.GREEN}[ ACTIVE ]{Colors.RESET}")
    
    # BOT STATUS SECTION
    print(f"\n {Colors.BOLD}[ BOT STATUS ]{Colors.RESET}")
    
    # Pewarnaan dinamis berdasarkan State
    state_color = Colors.GREEN if state == "STATE_IN_GAME" else Colors.YELLOW
    if state == "STATE_STOPPED":
        state_color = Colors.RED
        
    print(f" Current State  : {state_color}{state}{Colors.RESET}")
    print(f" Active PID     : {Colors.WHITE}{pid}{Colors.RESET}")
    
    # Potong link jika terlalu panjang agar UI tetap rapi
    display_link = server_link if len(server_link) < 45 else server_link[:42] + "..."
    link_color = Colors.WHITE if server_link == "Not Set" else Colors.GREEN
    print(f" Target Server  : {link_color}{display_link}{Colors.RESET}\n")
    
    print_divider()
    
    # MAIN MENU SECTION
    print(f" {Colors.BOLD}[ MAIN MENU ]{Colors.RESET}\n")
    print(f" {Colors.YELLOW}[ 1 ]{Colors.RESET} Set Private Server Link")
    print(f" {Colors.YELLOW}[ 2 ]{Colors.RESET} Start Auto Rejoiner (Watchdog Mode)")
    print(f" {Colors.YELLOW}[ 3 ]{Colors.RESET} Stop / Force Kill Roblox")
    print(f" {Colors.YELLOW}[ 4 ]{Colors.RESET} View System Logs")
    print(f" {Colors.RED}[ 0 ]{Colors.RESET} Exit\n")
    
    print_divider()

def main_loop():
    """Looping utama antarmuka pengguna."""
    current_link = "Not Set"
    
    while True:
        # Panggil fungsi render dengan data dummy (nantinya diganti dengan variabel real dari State Machine)
        render_menu(server_link=current_link)
        
        try:
            choice = input(f" {Colors.CYAN}Carrera-Bot@Termux:~# {Colors.RESET}")
            
            if choice == '1':
                print(f"\n {Colors.YELLOW}>>{Colors.RESET} Paste link Private Server Roblox:")
                current_link = input(f" {Colors.CYAN}Link:{Colors.RESET} ").strip()
            elif choice == '2':
                print(f"\n {Colors.GREEN}>> Memulai Watchdog...{Colors.RESET}")
                time.sleep(1)
                # Di sini nantinya memanggil modul State Machine
            elif choice == '3':
                print(f"\n {Colors.RED}>> Mengeksekusi 'am force-stop com.roblox.client'...{Colors.RESET}")
                time.sleep(1)
            elif choice == '4':
                print(f"\n {Colors.WHITE}>> Membuka Logcat...{Colors.RESET}")
                time.sleep(1)
            elif choice == '0':
                clear_screen()
                print(f"{Colors.GREEN}Terima kasih telah menggunakan Carrera Auto Rejoiner.{Colors.RESET}")
                break
            else:
                pass # Abaikan input yang tidak valid
                
        except KeyboardInterrupt:
            # Menangkap CTRL+C agar program keluar dengan rapi
            clear_screen()
            print(f"{Colors.GREEN}Program dihentikan oleh user.{Colors.RESET}")
            break

if __name__ == "__main__":
    main_loop()
