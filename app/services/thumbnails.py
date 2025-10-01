from __future__ import annotations
import io
import json
import os
import time
import zipfile
from dataclasses import dataclass
from typing import Literal, Optional

import aiosqlite
from PIL import Image, ImageOps

from ..settings import settings
from ..utils.hashing import cache_path
from ..utils.fs import is_image_name
from ..utils.events import events


FitMode = Literal["cover", "contain"]


def _open_image_from_path(album_type: str, album_path: str, entry_path: Optional[str] = None) -> Image.Image:
    if album_type == "folder":
        fp = os.path.join(album_path, entry_path) if entry_path else album_path
        img = Image.open(fp)
        return img
    elif album_type == "zip":
        if not entry_path:
            raise ValueError("entry_path required for zip album")
        with zipfile.ZipFile(album_path, 'r') as zf:
            with zf.open(entry_path, 'r') as fp:
                img = Image.open(fp)
                # keep file handle open until load() completes
                img.load()
                return img
    else:
        raise ValueError("unknown album type")


def _apply_exif_and_rgb(img: Image.Image) -> Image.Image:
    Image.MAX_IMAGE_PIXELS = settings.max_input_pixels
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def _resize(img: Image.Image, w: int, h: int, fit: FitMode) -> Image.Image:
    if fit == "contain":
        img.thumbnail((w, h), Image.Resampling.LANCZOS)
        return img
    # cover
    src_w, src_h = img.size
    target_ratio = w / h
    src_ratio = src_w / src_h if src_h else 1.0
    if src_ratio > target_ratio:
        # wider -> crop width
        new_w = int(src_h * target_ratio)
        x0 = (src_w - new_w) // 2
        box = (x0, 0, x0 + new_w, src_h)
    else:
        # taller -> crop height
        new_h = int(src_w / target_ratio)
        y0 = (src_h - new_h) // 2
        box = (0, y0, src_w, y0 + new_h)
    img = img.crop(box)
    return img.resize((w, h), Image.Resampling.LANCZOS)


async def _ensure_thumbs_table(db: aiosqlite.Connection):
    # already created in schema; no-op function left for symmetry
    return


async def get_or_create_thumb(
    db: aiosqlite.Connection,
    *,
    album_id: int,
    album_type: str,
    album_path: str,
    entry_path: Optional[str],
    w: int,
    h: int,
    fit: FitMode,
    fmt: str = "webp",
    quality: int | None = None,
    crop: Optional[dict] = None,
) -> tuple[str, str]:
    # key format aligns with design: album_id|entry|w|h|fit|fmt|q|v
    q = int(quality or settings.default_quality)
    crop_part = ""
    if crop:
        crop_part = f"|crop:{crop.get('x',0):.4f},{crop.get('y',0):.4f},{crop.get('w',1):.4f},{crop.get('h',1):.4f}"
    key = f"{album_id}|{entry_path or 'cover'}|{w}|{h}|{fit}|{fmt}|{q}{crop_part}|v1"
    file_path = cache_path(os.path.join(settings.cache_dir, "thumbs"), key, fmt)

    # try DB first
    async with db.execute("SELECT file_path FROM thumbs WHERE album_id=? AND key=?", (album_id, key)) as cur:
        row = await cur.fetchone()
        if row and os.path.exists(row[0]):
            await db.execute("UPDATE thumbs SET last_access=? WHERE album_id=? AND key=?", (int(time.time()), album_id, key))
            await db.commit()
            events.publish("thumb:hit", {"album_id": album_id, "key": key})
            return key, row[0]

    # (re)generate
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    events.publish("thumb:start", {"album_id": album_id, "entry": entry_path, "w": w, "h": h})
    img = _open_image_from_path(album_type, album_path, entry_path)
    # apply crop if provided (normalized 0..1)
    if crop:
        x = max(0.0, min(1.0, float(crop.get('x', 0))))
        y = max(0.0, min(1.0, float(crop.get('y', 0))))
        cw = max(0.0, min(1.0, float(crop.get('w', 1))))
        ch = max(0.0, min(1.0, float(crop.get('h', 1))))
        sw, sh = img.size
        box = (int(x * sw), int(y * sh), int((x + cw) * sw), int((y + ch) * sh))
        img = img.crop(box)
    img = _resize(img, w, h, fit)
    save_params = {"format": fmt.upper()}
    if fmt.lower() == "webp":
        save_params.update({"quality": q, "method": 4})
    tmp_path = f"{file_path}.tmp"
    img.save(tmp_path, **save_params)
    os.replace(tmp_path, file_path)

    stat = os.stat(file_path)
    now = int(time.time())
    await db.execute(
        """
        INSERT INTO thumbs(album_id, key, file_path, bytes, width, height, created_at, last_access)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(album_id, key) DO UPDATE SET
          file_path=excluded.file_path,
          bytes=excluded.bytes,
          width=excluded.width,
          height=excluded.height,
          last_access=excluded.last_access
        """,
        (album_id, key, file_path, stat.st_size, img.width, img.height, now, now),
    )
    await db.commit()
    events.publish("thumb:done", {"album_id": album_id, "key": key, "path": file_path})
    return key, file_path


async def lru_cleanup(db: aiosqlite.Connection):
    # simple LRU by bytes sum vs settings.cache_max_bytes
    async with db.execute("SELECT SUM(bytes) FROM thumbs") as cur:
        row = await cur.fetchone()
        total = row[0] or 0
    if total <= settings.cache_max_bytes:
        return {"removed": 0}
    to_remove = total - settings.cache_max_bytes
    removed = 0
    async with db.execute(
        "SELECT album_id, key, file_path, bytes FROM thumbs ORDER BY last_access ASC"
    ) as cur:
        rows = await cur.fetchall()
    for album_id, key, file_path, bytes_ in rows:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        await db.execute("DELETE FROM thumbs WHERE album_id=? AND key=?", (album_id, key))
        removed += bytes_ or 0
        if removed >= to_remove:
            break
    await db.commit()
    return {"removed": removed}
