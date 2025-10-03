from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import aiosqlite

from ..db import get_db
from ..settings import settings
from ..services.thumbnails import get_or_create_thumb
from ..services.entries import first_entry

router = APIRouter(tags=["images"])


async def _get_album(db: aiosqlite.Connection, album_id: int):
    async with db.execute("SELECT id, type, path, cover_path FROM albums WHERE id=?", (album_id,)) as cur:
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="album not found")
    return {"id": r[0], "type": r[1], "path": r[2], "cover_path": r[3]}


@router.get("/albums/{album_id}/cover")
async def get_cover(
    album_id: int,
    w: int = 640,
    h: int = 960,
    fit: str = "cover",
    fmt: str = "webp",
    q: int | None = settings.default_quality,
    db: aiosqlite.Connection = Depends(get_db),
):
    album = await _get_album(db, album_id)
    # 优先使用 cover_path；若是绝对路径且存在则直接返回原图；
    # 若是相对/内部条目名，则作为 entry_path 生成缩略；为空或无效则回退到首图。
    entry_path = None
    cp = album.get("cover_path")
    atype = album.get("type")
    apath = album.get("path")
    if cp:
        # 绝对路径：视为外部封面
        if os.path.isabs(cp) and os.path.exists(cp):
            if cp.endswith(f"{w}_{h}.{fmt}"):
                return FileResponse(cp, media_type="image/*") 
    key = f"{album_id}_{fit}_{q}_{w}_{h}.{fmt}"
     # try DB first
    async with db.execute("SELECT file_path FROM thumbs WHERE album_id=? AND key=?", (album_id, key)) as cur:
        row = await cur.fetchone()
        if row and os.path.exists(row[0]):
            return FileResponse(row[0], media_type="image/*")
    print("not found in thumbs, generate new")
    entry_path = await first_entry(db, album_id)
    if not entry_path and album["type"] == "folder":
        parent_path = album["path"]
        prefix = parent_path.rstrip("\\")
        async with db.execute(
            "SELECT id, type, path, cover_path FROM albums WHERE path LIKE ? AND path != ? ORDER BY mtime DESC",
            (prefix + "%", parent_path),
        ) as cur:
            rows = await cur.fetchall()
        child_entry = None
        for cid, ctype, cpath, cover in rows:
            if cover:
                if os.path.isabs(cover) and os.path.exists(cover):
                    return FileResponse(cover, media_type="image/*")
            child_entry = await first_entry(db, cid)
            if child_entry:
                entry_path = child_entry
                atype = ctype
                apath = cpath
                break
        if not entry_path:
            raise HTTPException(status_code=404, detail="no images in album or its children")
    _, path = await get_or_create_thumb(
        db,
        album_id=album["id"],
        album_type=atype,
        album_path=apath,
        entry_path=entry_path,
        w=w,
        h=h,
        fit=fit if fit in ("cover", "contain") else "cover",
        fmt=fmt,
        quality=q,
    )
    media_type = "image/webp" if fmt.lower() == "webp" else "application/octet-stream"
    await db.execute("UPDATE albums SET cover_path=? WHERE id=?", (path, album_id))
    await db.commit()
    return FileResponse(path, media_type=media_type)


@router.get("/thumbnail")
async def get_thumbnail(
    album_id: int,
    entry_path: str,
    w: int,
    h: int,
    fit: str = "cover",
    fmt: str = "webp",
    q: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    album = await _get_album(db, album_id)
    if not entry_path:
        raise HTTPException(status_code=400, detail="entry_path is required")
    _, path = await get_or_create_thumb(
        db,
        album_id=album["id"],
        album_type=album["type"],
        album_path=album["path"],
        entry_path=entry_path,
        w=w,
        h=h,
        fit=fit if fit in ("cover", "contain") else "cover",
        fmt=fmt,
        quality=q,
    )
    media_type = "image/webp" if fmt.lower() == "webp" else "application/octet-stream"
    return FileResponse(path, media_type=media_type)
