"""
Modul: config.py
Tanggung Jawab: Membaca dan mem-parsing file config.conf.
"""
import os
import sys

def load_config(config_path="config.conf"):
    """Membaca config.conf dan mengembalikan dictionary konfigurasi."""
    if not os.path.isfile(config_path):
        print(f"[!] File {config_path} tidak ditemukan!")
        sys.exit(1)

    config = {
        "PRIVATE_SERVER_LINK": "",
        "TIMEOUT_SECONDS": 45  # Nilai default
    }

    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("PRIVATE_SERVER_LINK="):
                config["PRIVATE_SERVER_LINK"] = line.split("=", 1)[1].strip('"\'')
            elif line.startswith("TIMEOUT_SECONDS="):
                try:
                    config["TIMEOUT_SECONDS"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError:
                    pass
                    
    return config
  
