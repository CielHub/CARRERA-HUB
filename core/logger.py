"""
Modul: logger.py
Tanggung Jawab: Menyediakan sistem logging terpusat dengan rotasi file.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

# Menentukan letak folder logs di root project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "latest.log")

def setup_logger():
    logger = logging.getLogger("CARRERA_HUB")
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format Log: [2023-10-25 14:30:00] [INFO] Pesan log...
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # 1. File Handler dengan Rotasi (Max 5MB per file, max 3 backup: latest.log.1, latest.log.2)
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
        file_handler.setFormatter(formatter)
        
        # 2. Console Handler (Untuk tampil di Terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

# Inisialisasi object log global agar mudah dipanggil modul lain
log = setup_logger()
