"""
Modul: config.py
Tanggung Jawab: Membaca, mem-parsing, dan menyimpan file config.conf.
"""
import os
import sys
from core.logger import log

def load_config(config_path="config.conf"):
    if not os.path.isfile(config_path):
        log.error(f"CONFIG: File {config_path} tidak ditemukan!")
        sys.exit(1)

    config = {
        "PRIVATE_SERVER_LINK": "",
        "TIMEOUT_SECONDS": 45,
        "DELAY_SECONDS": 3,
        "MAX_RETRIES": 3,           # [PHASE 5] Batas recovery berturut-turut
        "COOLDOWN_SECONDS": 300     # [PHASE 5] Waktu tunggu jika melebihi batas (5 menit)
    }

    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("PRIVATE_SERVER_LINK="):
                config["PRIVATE_SERVER_LINK"] = line.split("=", 1)[1].strip('"\'')
            elif line.startswith("TIMEOUT_SECONDS="):
                try: config["TIMEOUT_SECONDS"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("DELAY_SECONDS="):
                try: config["DELAY_SECONDS"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("MAX_RETRIES="):
                try: config["MAX_RETRIES"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("COOLDOWN_SECONDS="):
                try: config["COOLDOWN_SECONDS"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
                    
    log.info("CONFIG: Konfigurasi berhasil dimuat.")
    return config

def save_config(config_data, config_path="config.conf"):
    with open(config_path, 'w') as f:
        for key, value in config_data.items():
            if isinstance(value, str):
                f.write(f'{key}="{value}"\n')
            else:
                f.write(f'{key}={value}\n')
    log.info("CONFIG: Konfigurasi berhasil disimpan.")
    
