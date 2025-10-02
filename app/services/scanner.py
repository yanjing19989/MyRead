from __future__ import annotations
import asyncio
import os
import time
import zipfile
from dataclasses import dataclass
from typing import Iterable, Set

import aiosqlite
from natsort import natsorted, ns

from ..utils.fs import is_image_name, basename_without_ext
from ..utils.events import events


@dataclass
class ScanOptions:
    recursive: bool = False


async def stat_path(path: str) -> tuple[int, int]:
    st = os.stat(path)
    return int(st.st_mtime), int(st.st_size)


def normalize_album_path(path: str) -> str:
    if not path:
        return ""
    real = os.path.normpath(os.path.abspath(path))
    norm = real.replace("\\", "/")
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm.rstrip("/")
    return norm


def album_path_key(path: str) -> str:
    norm = normalize_album_path(path)
    if os.name == "nt":
        return norm.lower()
    return norm


async def _load_existing_album_keys(db: aiosqlite.Connection) -> Set[str]:
    existing: Set[str] = set()
    async with db.execute("SELECT path FROM albums") as cur:
        rows = await cur.fetchall()
    for (path,) in rows:
        key = album_path_key(path)
        if key:
            existing.add(key)
    return existing


async def scan_zip(db: aiosqlite.Connection, path: str, seen_paths: Set[str]) -> dict | None:
    real_path = os.path.normpath(os.path.abspath(path))
    key = album_path_key(real_path)
    normalized_path = normalize_album_path(real_path)
    if key and key in seen_paths:
        return None
    mtime, size = await stat_path(real_path)
    name = basename_without_ext(real_path)
    file_count = 0
    try:
        with zipfile.ZipFile(real_path, 'r') as zf:
            names = [i.filename for i in zf.infolist() if not i.is_dir()]
            images = [n for n in names if is_image_name(n)]
            # 自然排序
            images = natsorted(images, alg=ns.IGNORECASE)
            file_count = len(images)
    except zipfile.BadZipFile:
        return None
    now = int(time.time())
    await db.execute(
        """
        INSERT INTO albums(type, path, name, mtime, size, file_count, added_at)
        VALUES('zip', ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            mtime=excluded.mtime,
            size=excluded.size,
            file_count=excluded.file_count,
            name=excluded.name
        """,
        (normalized_path, name, mtime, size, file_count, now),
    )
    if key:
        seen_paths.add(key)
    return {
        "path": normalized_path,
        "type": "zip",
        "name": name,
        "mtime": mtime,
        "size": size,
        "file_count": file_count,
    }


async def scan_folder(
    db: aiosqlite.Connection,
    path: str,
    recursive: bool = False,
    seen_paths: Set[str] | None = None,
) -> list[dict]:
    """Scan a folder. When recursive=True, insert an album for each subfolder/zip
    under `path` that contains images; when False, insert only for `path` itself.

    Returns a list of album info dicts that were inserted/updated.
    """

    results: list[dict] = []
    if seen_paths is None:
        seen_paths = set()

    async def upsert_folder_album(folder_path: str, files_in_folder: list[str]) -> dict | None:
        # count images among the provided file names (not recursing)
        real_folder_path = os.path.normpath(os.path.abspath(folder_path))
        normalized_path = normalize_album_path(real_folder_path)
        key = album_path_key(normalized_path)
        if key and key in seen_paths:
            return None
        images = [f for f in files_in_folder if is_image_name(f)]
        file_count = len(images)
        mtime, size = await stat_path(real_folder_path)
        name = os.path.basename(real_folder_path.rstrip("/\\")) or real_folder_path
        now = int(time.time())
        await db.execute(
            """
            INSERT INTO albums(type, path, name, mtime, size, file_count, added_at)
            VALUES('folder', ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                mtime=excluded.mtime,
                size=excluded.size,
                file_count=excluded.file_count,
                name=excluded.name
            """,
            (normalized_path, name, mtime, size, file_count, now),
        )
        if key:
            seen_paths.add(key)
        return {
            "path": normalized_path,
            "type": "folder",
            "name": name,
            "mtime": mtime,
            "size": size,
            "file_count": file_count,
        }

    if recursive:
        # Traverse all subdirectories; for each subdir (excluding root), create an album if it has images.
        for root, dirs, files in os.walk(path):
            # Albums for subfolders only ("path 下的每一个有图片的文件夹")
            info = await upsert_folder_album(root, files)
            if info:
                results.append(info)
            # Albums for zip files under this folder
            for f in files:
                if f.lower().endswith('.zip'):
                    zip_path = os.path.join(root, f)
                    info = await scan_zip(db, zip_path, seen_paths)
                    if info and info.get("file_count", 0) > 0:
                        results.append(info)
    else:
        # Only this folder itself
        try:
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        except FileNotFoundError:
            files = []
        info = await upsert_folder_album(path, files)
        if info:
            results.append(info)

    return results


async def scan_paths(db: aiosqlite.Connection, paths: list[str], options: ScanOptions) -> dict:
    seen_paths = await _load_existing_album_keys(db)
    added_or_updated = 0
    details: list[dict] = []
    for p in paths:
        abs_path = normalize_album_path(os.path.abspath(p))
        events.publish("scan:progress", {"path": abs_path, "status": "start"})
        if not os.path.exists(abs_path):
            events.publish("scan:progress", {"path": abs_path, "status": "skip", "reason": "not_exists"})
            continue
        if os.path.isdir(abs_path):
            items = await scan_folder(db, abs_path, options.recursive, seen_paths)
            details.extend(items)
            added_or_updated += len(items)
            events.publish(
                "scan:progress",
                {"path": abs_path, "status": "done", "items": items, "count": len(items)},
            )
        elif abs_path.lower().endswith('.zip'):
            info = await scan_zip(db, abs_path, seen_paths)
            if info and info.get("file_count", 0) > 0:
                details.append(info)
                added_or_updated += 1
            status_payload = {"path": abs_path, "status": "done"}
            if info:
                status_payload["info"] = info
            else:
                status_payload["reason"] = "duplicate"
            events.publish("scan:progress", status_payload)
        else:
            # 非文件夹/非 zip 跳过
            events.publish("scan:progress", {"path": abs_path, "status": "skip", "reason": "unsupported"})
            continue
    await db.commit()
    events.publish("scan:done", {"count": added_or_updated})
    return {"count": added_or_updated, "items": details}
