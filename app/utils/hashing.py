from __future__ import annotations
import hashlib
import os


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def cache_path(base_dir: str, key: str, ext: str) -> str:
    h = sha1_hex(key)
    sub1, sub2 = h[:2], h[2:4]
    ext = ext.lstrip('.')
    dir_path = os.path.join(base_dir, sub1, sub2)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{h}.{ext}")
