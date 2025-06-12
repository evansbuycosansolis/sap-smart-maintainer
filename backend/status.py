# backend/status.py

import datetime
from typing import Optional, Dict, Any

indexing_status: Dict[str, Any] = {}

def reset_indexing_status():
    """Reset the indexing status to initial state."""
    global indexing_status
    indexing_status = {
        "current": 0,
        "total": 0,
        "running": False,
        "current_file": None,
        "last_error": None,
        "start_time": None,
        "end_time": None,
        "success_count": 0,
        "fail_count": 0
    }

reset_indexing_status()  # Initialize on import

def set_indexing_status(updates: dict):
    """Update the global indexing status with new values."""
    global indexing_status
    indexing_status.update(updates)
    # If "running" changes to False, set end_time
    if "running" in updates and not updates["running"]:
        indexing_status["end_time"] = datetime.datetime.utcnow().isoformat()

def update_indexing_status(**kwargs):
    """
    Update any part of the status.
    Usage: update_indexing_status(current=5) or update_indexing_status(current=3, running=True)
    """
    set_indexing_status(kwargs)

def start_indexing(total: int):
    set_indexing_status({
        "running": True,
        "current": 0,
        "total": total,
        "start_time": datetime.datetime.utcnow().isoformat(),
        "end_time": None,
        "success_count": 0,
        "fail_count": 0,
        "last_error": None,
        "current_file": None
    })

def finish_indexing():
    set_indexing_status({
        "running": False,
        "end_time": datetime.datetime.utcnow().isoformat()
    })

def get_indexing_status() -> dict:
    return indexing_status

def is_indexing_running() -> bool:
    return indexing_status.get("running", False)

def set_indexing_running(running: bool):
    update_indexing_status(running=running)
    if running:
        indexing_status["start_time"] = datetime.datetime.utcnow().isoformat()
        indexing_status["end_time"] = None
    else:
        indexing_status["end_time"] = datetime.datetime.utcnow().isoformat()

def set_indexing_current_file(filename: str):
    update_indexing_status(current_file=filename)

def set_indexing_total(total: int):
    update_indexing_status(total=total)

def increment_indexing_current():
    indexing_status["current"] += 1

def increment_indexing_success():
    indexing_status["success_count"] += 1

def increment_indexing_fail():
    indexing_status["fail_count"] += 1

def set_indexing_error(error: str):
    update_indexing_status(last_error=error, running=False, end_time=datetime.datetime.utcnow().isoformat())

def get_indexing_summary() -> dict:
    return {
        "total_files": indexing_status["total"],
        "indexed_files": indexing_status["success_count"],
        "failed_files": indexing_status["fail_count"],
        "current_file": indexing_status["current_file"],
        "last_error": indexing_status["last_error"],
        "start_time": indexing_status["start_time"],
        "end_time": indexing_status["end_time"]
    }
