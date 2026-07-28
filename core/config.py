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
        "MAX_RETRIES": 3,
        "COOLDOWN_SECONDS": 300,
        "GRID_ENABLED": 0,        # 1 = auto-terapkan grid tiap kali package (re)launch
        "GRID_COLS": 0,           # 0 = otomatis dihitung dari jumlah package
        "GRID_CELL_W": 0,         # 0 = otomatis dihitung dari layar
        "GRID_CELL_H": 0,         # 0 = otomatis dihitung dari layar
        "GRID_MARGIN": 10,
        "GRID_OFFSET_Y": 60,
        "CLEAR_CACHE_MINUTES": 30,
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
            elif line.startswith("GRID_ENABLED="):
                try: config["GRID_ENABLED"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("GRID_COLS="):
                try: config["GRID_COLS"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("GRID_CELL_W="):
                try: config["GRID_CELL_W"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("GRID_CELL_H="):
                try: config["GRID_CELL_H"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("GRID_MARGIN="):
                try: config["GRID_MARGIN"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("GRID_OFFSET_Y="):
                try: config["GRID_OFFSET_Y"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            elif line.startswith("CLEAR_CACHE_MINUTES="):
                try: config["CLEAR_CACHE_MINUTES"] = int(line.split("=", 1)[1].strip('"\''))
                except ValueError: pass
            # --- PENAMBAHAN FITUR: Dynamic Package Link Parser ---
            elif line.startswith("PKG_"):
                try:
                    key, val = line.split("=", 1)
                    config[key] = val.strip('"\'')
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
    
