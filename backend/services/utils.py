# /backend/services/utils.py

import os
import time
import logging

def safe_remove(path, retries=3, delay=0.5, logger=None):
    for i in range(retries):
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
        except PermissionError:
            if i < retries - 1:
                time.sleep(delay)
            else:
                msg = f"Could not remove temp file {path}: File is locked after retries."
                (logger or print)(msg)
                return False
        except Exception as e:
            msg = f"Could not remove temp file {path}: {e}"
            (logger or print)(msg)
            return False
    return False
