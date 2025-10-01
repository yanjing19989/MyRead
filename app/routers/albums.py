from __future__ import annotations
from typing import Literal, Optional
import os
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import aiosqlite

from ..db import get_db
from ..services.scanner import scan_paths, ScanOptions, normalize_album_path
from ..services.entries import list_entries
from ..utils.fs import is_image_name, is_zip_name
from natsort import natsorted, ns

router = APIRouter(tags=["albums"])

def _split_segments(norm_path: str) -> list[str]:
    if not norm_path:
        return []
    if norm_path.startswith("//"):
        rest = norm_path[2:]
        if not rest:
            return [norm_path]
        parts = rest.split("/")
        return ["//" + parts[0], *parts[1:]]
    return norm_path.split("/")


def _join_segments(parts: list[str]) -> str:
    """Join segments back into a normalized path, preserving '//' head handling."""
    if not parts:
        return ""
    if parts[0].startswith("//"):
        head = parts[0][2:]
        tail = "/".join(parts[1:])
        return "//" + head + ("/" + tail if tail else "")
    return "/".join(parts)


def _parent_path(norm_path: str) -> str | None:
    """Return the parent normalized path or None for root-level paths."""
    segments = _split_segments(norm_path)
    if len(segments) <= 1:
        return None
    parent = _join_segments(segments[:-1])
    return parent or None


def _public_album(rec: dict) -> dict:
    """Return the public view of an album record (stable output used by API)."""
    keys = ("id", "type", "path", "name", "mtime", "size", "file_count", "added_at", "cover_path")
    return {k: rec.get(k) for k in keys}


async def _load_all_albums(db: aiosqlite.Connection) -> list[dict]:
    async with db.execute(
        "SELECT id, type, path, name, mtime, size, file_count, added_at, cover_path FROM albums"
    ) as cur:
        rows = await cur.fetchall()
    records: list[dict] = []
    for row in rows:
        rec = {
            "id": row[0],
            "type": row[1],
            "path": row[2],
            "name": row[3],
            "mtime": row[4],
            "size": row[5],
            "file_count": row[6],
            "added_at": row[7],
            "cover_path": row[8],
        }
        norm_path = normalize_album_path(rec["path"])
        rec["_norm_path"] = norm_path
        rec["_key_path"] = norm_path.lower()
        parts = _split_segments(norm_path)
        rec["_segments"] = parts
        rec["_depth"] = len(parts)
        records.append(rec)

    by_key = {rec["_key_path"]: rec for rec in records}
    for rec in records:
        parent_norm: str | None = None
        parent_key: str | None = None
        cursor = _parent_path(rec["_norm_path"])
        while cursor:
            candidate = by_key.get(cursor.lower())
            if candidate:
                parent_norm = candidate["_norm_path"]
                parent_key = candidate["_key_path"]
                break
            cursor = _parent_path(cursor)
        rec["_parent_norm"] = parent_norm
        rec["_parent_key"] = parent_key
    return records


def _gather_ancestors(rec: dict, by_key: dict[str, dict]) -> list[dict]:
    chain: list[dict] = []
    parent_key = rec.get("_parent_key")
    seen: set[str] = set()
    while parent_key and parent_key not in seen:
        seen.add(parent_key)
        parent = by_key.get(parent_key)
        if not parent:
            break
        chain.append(parent)
        parent_key = parent.get("_parent_key")
    chain.reverse()
    return chain


def _sort_children(records: list[dict], sort_by: str, order: Literal["ASC", "DESC"]) -> list[dict]:
    reverse = order == "DESC"
    return sorted(records, key=lambda r: (r.get(sort_by), r["name"], r["id"]), reverse=reverse)


def _build_tree(records: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    nodes: dict[str, dict] = {}
    for rec in records:
        node = {
            "album": _public_album(rec),
            "path": rec["_norm_path"],
            "children": [],
        }
        nodes[rec["_key_path"]] = node

    roots: list[dict] = []
    for rec in records:
        node = nodes[rec["_key_path"]]
        parent_key = rec.get("_parent_key")
        if parent_key and parent_key in nodes:
            nodes[parent_key]["children"].append(node)
        else:
            roots.append(node)

    def sort_branch(children: list[dict]) -> None:
        children.sort(key=lambda n: n["path"].lower())
        for child in children:
            sort_branch(child["children"])

    sort_branch(roots)
    return roots, nodes


def _filter_tree(nodes: list[dict], keyword: str) -> list[dict]:
    needle = keyword.lower()

    def filter_node(node: dict) -> dict | None:
        album = node["album"]
        match = False
        if album.get("name") and needle in album["name"].lower():
            match = True
        elif album.get("path") and needle in album["path"].lower():
            match = True
        filtered_children: list[dict] = []
        for child in node["children"]:
            filtered = filter_node(child)
            if filtered:
                filtered_children.append(filtered)
                match = True
        if match:
            return {"album": album, "path": node["path"], "children": filtered_children}
        return None

    result: list[dict] = []
    for node in nodes:
        filtered = filter_node(node)
        if filtered:
            result.append(filtered)
    return result


@router.post("/albums/scan")
async def scan_albums(body: dict, db: aiosqlite.Connection = Depends(get_db)):
    # body: { paths: [...], options?: { folder: { recursive: false } } }
    paths = body.get("paths") or []
    if not isinstance(paths, list) or not paths:
        raise HTTPException(status_code=400, detail="paths is required and must be a non-empty list")
    options_dict = (body.get("options") or {}).get("folder") or {}
    recursive = bool(options_dict.get("recursive", False))
    result = await scan_paths(db, paths, ScanOptions(recursive=recursive))
    return result


@router.get("/albums")
async def list_albums(
    sort_by: Literal["name", "added_at", "mtime", "size", "file_count"] = "added_at",
    order: Literal["asc", "desc"] = "desc",
    keyword: str | None = None,
    scope: Literal["children", "tree"] = "children",
    parent_path: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    sort_col = sort_by
    order_sql = "ASC" if order == "asc" else "DESC"
    scope_val = (scope or "children").lower()

    records = await _load_all_albums(db)
    by_key = {rec["_key_path"]: rec for rec in records}
    keyword_lower = keyword.lower() if keyword else None

    if scope_val == "children":
        parent_norm = normalize_album_path(parent_path) if parent_path else ""
        parent_key = parent_norm.lower() if parent_norm else None
        parent_rec = by_key.get(parent_key) if parent_key else None
        if parent_norm and not parent_rec:
            raise HTTPException(status_code=404, detail="album not found")

        if parent_rec:
            children = [rec for rec in records if rec.get("_parent_key") == parent_rec["_key_path"]]
        else:
            children = [rec for rec in records if not rec.get("_parent_key")]

        if keyword_lower:
            children = [
                rec
                for rec in children
                if (rec.get("name") and keyword_lower in rec["name"].lower())
                or (rec.get("_norm_path") and keyword_lower in rec["_norm_path"].lower())
            ]

        ordered = _sort_children(children, sort_col, order_sql)
        items = [_public_album(rec) for rec in ordered]
        parent_payload = _public_album(parent_rec) if parent_rec else None
        ancestors_payload = (
            [_public_album(a) for a in _gather_ancestors(parent_rec, by_key)] if parent_rec else []
        )

        return {
            "items": items,
            "total": len(items),
            "parent": parent_payload,
            "ancestors": ancestors_payload,
        }

    if scope_val == "tree":
        roots, node_map = _build_tree(records)

        parent_norm = normalize_album_path(parent_path) if parent_path else ""
        if parent_norm:
            node = node_map.get(parent_norm.lower())
            if not node:
                raise HTTPException(status_code=404, detail="album not found")
            roots = [node]

        if keyword:
            roots = _filter_tree(roots, keyword)

        return {"items": roots, "total": len(records)}

    raise HTTPException(status_code=400, detail="invalid scope value")


@router.get("/albums/{album_id}")
async def get_album(album_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute(
        "SELECT id, type, path, name, mtime, size, file_count, added_at, cover_path FROM albums WHERE id=?",
        (album_id,),
    ) as cur:
        r = await cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="album not found")
        return {
            "id": r[0],
            "type": r[1],
            "path": r[2],
            "name": r[3],
            "mtime": r[4],
            "size": r[5],
            "file_count": r[6],
            "added_at": r[7],
            "cover_path": r[8],
        }


@router.get("/albums/{album_id}/entries")
async def get_album_entries(
    album_id: int,
    page: int = 1,
    per_page: int = 48,
    db: aiosqlite.Connection = Depends(get_db),
):
    page = max(1, page)
    per_page = min(500, max(1, per_page))
    return await list_entries(db, album_id, page, per_page)


class CoverBodyDefault(dict):
    type: Literal["default"]


@router.post("/albums/{album_id}/cover")
async def set_album_cover(
    album_id: int,
    type: Literal["default", "internal", "external"] = Form(...),
    entry_path: Optional[str] = Form(None),
    file: UploadFile | None = File(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    # policy encoding: 'default' | 'internal:<entry>' | 'external:<abs_path>'
    path: str | None
    if type == "default":
        path = None
    elif type == "internal":
        if not entry_path:
            raise HTTPException(status_code=400, detail="entry_path required for internal cover")
        path = entry_path
    else:  # external
        if not file:
            raise HTTPException(status_code=400, detail="file required for external cover")
        covers_dir = os.path.abspath(os.path.join("cache", "covers"))
        os.makedirs(covers_dir, exist_ok=True)
        path = os.path.join(covers_dir, file.filename)
        content = await file.read()
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(content)
        os.replace(tmp, path)

    await db.execute("UPDATE albums SET cover_path=? WHERE id=?", (path, album_id))
    await db.commit()
    return {"ok": True, "cover_path": path}

@router.post("/albums/refresh")
async def refresh_albums(db: aiosqlite.Connection = Depends(get_db)):
    """Remove albums that no longer exist on disk.

    - For folder albums: path must be an existing directory.
    - For zip albums: path must be an existing regular file.
    Deletions cascade to thumbs via FK.
    """
    async with db.execute("SELECT id, type, path FROM albums") as cur:
        rows = await cur.fetchall()
    checked = len(rows)
    removed_ids: list[int] = []
    for album_id, typ, p in rows:
        try:
            if typ == "folder":
                ok = os.path.isdir(p)
            elif typ == "zip":
                ok = os.path.isfile(p)
            else:
                ok = os.path.exists(p)
        except Exception:
            ok = False
        if not ok:
            await db.execute("DELETE FROM albums WHERE id=?", (album_id,))
            removed_ids.append(album_id)
    if removed_ids:
        await db.commit()
    return {"checked": checked, "removed": len(removed_ids), "ids": removed_ids}


@router.delete("/albums/{album_id}")
async def delete_album(album_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """Delete an album by id. This removes the album record from the database.

    Note: Thumbs have ON DELETE CASCADE so they will be removed by DB. We also
    attempt to unlink the cover file if it exists on disk.
    """
    # load the album record (include type and path)
    async with db.execute("SELECT id, type, path, cover_path FROM albums WHERE id=?", (album_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="album not found")
    id, typ, parent_path, cover_path = row
    to_delete: list[tuple] = []  # rows of (id, type, path, cover_path)
    to_delete.append((id, cover_path))
    if typ == "folder":
        # collect target rows: parent + any descendants whose path starts with parent_path
        # normalize stripping trailing slashes/backslashes for prefix match
        prefix = parent_path.rstrip("\\/")
        pattern = prefix + "%"
        # include the parent explicitly and then any rows with path LIKE prefix%
        async with db.execute(
            "SELECT id, cover_path FROM albums WHERE path = ? OR path LIKE ? ORDER BY mtime DESC",
            (parent_path, pattern),
        ) as cur:
            rows = await cur.fetchall()
            for r in rows:
                to_delete.append((r[0], r[1]))

    ids = [r[0] for r in to_delete]

    # delete all in one operation
    placeholders = ",".join(["?"] * len(ids))
    await db.execute(f"DELETE FROM albums WHERE id IN ({placeholders})", tuple(ids))
    await db.commit()

    # best-effort: remove cover files for deleted rows if they are inside cache/covers
    cache_dir = os.path.abspath(os.path.join("cache", "covers"))
    for _id, cpath in to_delete:
        try:
            if cpath:
                abs_cover = os.path.abspath(cpath)
                if abs_cover.startswith(cache_dir) and os.path.exists(abs_cover):
                    try:
                        os.remove(abs_cover)
                    except Exception:
                        pass
        except Exception:
            # ignore filesystem issues per-row
            pass

    return {"ok": True, "deleted": len(ids), "ids": ids}
