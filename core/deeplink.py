"""
Modul: deeplink.py
Tanggung Jawab: Mengonversi Share Link Roblox menjadi Android Intent Deep Link.
"""
import re
import sys

def get_intent_url(private_server_link):
    """Mengekstrak dan mengonversi URL menjadi format yang bisa dieksekusi 'am start'."""
    if "/share" in private_server_link:
        print("[+] Terdeteksi format Share Link baru.")
        return private_server_link
    
    # Format lama
    place_id_match = re.search(r'games/(\d+)', private_server_link)
    link_code_match = re.search(r'privateServerLinkCode=([^&]+)', private_server_link)

    if not place_id_match or not link_code_match:
        print("[!] Link Private Server tidak valid di config!")
        sys.exit(1)

    place_id = place_id_match.group(1)
    link_code = link_code_match.group(1)
    
    print("[+] URL Berhasil dikonversi ke Intent (Format Lama).")
    return f"roblox://placeId={place_id}&linkCode={link_code}"
  
