"""
Modul: accounts.py
Tanggung Jawab: Menyimpan dan memuat kredensial akun per-package (Auto Login).
"""
import os
import json
from core.logger import log

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"ACCOUNTS: Gagal membaca {ACCOUNTS_FILE} - {e}")
        return {}

def save_accounts(data):
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log.error(f"ACCOUNTS: Gagal menyimpan {ACCOUNTS_FILE} - {e}")
      
