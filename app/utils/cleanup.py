from pathlib import Path
from threading import Lock
from time import time

_CLEANUP_LOCK = Lock()
_last_cleanup_ts = 0.0


def cleanup_old_files(folders, max_age_seconds: int, min_interval_seconds: int = 60) -> None:
    global _last_cleanup_ts

    now = time()
    if now - _last_cleanup_ts < min_interval_seconds:
        return

    with _CLEANUP_LOCK:
        now = time()
        if now - _last_cleanup_ts < min_interval_seconds:
            return

        cutoff = now - max_age_seconds
        for folder in folders:
            _cleanup_folder(folder, cutoff)

        _last_cleanup_ts = now


def _cleanup_folder(folder: Path, cutoff_ts: float) -> None:
    if not folder.exists():
        return

    for file_path in folder.glob("*"):
        if not file_path.is_file():
            continue
        if file_path.stat().st_mtime < cutoff_ts:
            file_path.unlink(missing_ok=True)
