from __future__ import annotations
import os
import zipfile
from typing import List

import aiosqlite
from natsort import natsorted, ns

from ..utils.fs import is_image_name


async def _read_album(db: aiosqlite.Connection, album_id: int):
    async with db.execute("SELECT id, type, path FROM albums WHERE id=?", (album_id,)) as cur:
        row = await cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "type": row[1], "path": row[2]}


def _list_album_images(album: dict) -> List[str]:
    """List image entry paths for an album without persisting to DB.

    For folder albums: return file names under the folder (non-recursive).
    For zip albums: return inner entry names (paths inside zip).
    Returns a naturally-sorted list.
    """
    images: List[str] = []
    if not album:
        return images
    if album["type"] == "zip":
        try:
            with zipfile.ZipFile(album["path"], 'r') as zf:
                names = [i.filename for i in zf.infolist() if (not i.is_dir()) and is_image_name(i.filename)]
                images = natsorted(names, alg=ns.IGNORECASE)
        except Exception:
            images = []
    else:
        try:
            for name in os.listdir(album["path"]):
                if is_image_name(name):
                    images.append(name)
            images = natsorted(images, alg=ns.IGNORECASE)
        except Exception:
            images = []
    return images


async def list_entries(db: aiosqlite.Connection, album_id: int, page: int, per_page: int):
    album = await _read_album(db, album_id)
    images = _list_album_images(album)
    total = len(images)
    if total == 0:
        return {"total": 0, "items": [], "page": page, "per_page": per_page}
    offset = (max(1, page) - 1) * max(1, per_page)
    items = images[offset : offset + per_page]
    return {"total": total, "items": items, "page": page, "per_page": per_page}


async def first_entry(db: aiosqlite.Connection, album_id: int) -> str | None:
    album = await _read_album(db, album_id)
    images = _list_album_images(album)
    return images[0] if images else None
