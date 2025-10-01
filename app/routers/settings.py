from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import aiosqlite
from ..db import get_db
from ..settings import settings as runtime_settings, AppSettings

router = APIRouter(tags=["settings"])


class SettingsDTO(BaseModel):
    cacheDir: str | None = None
    cacheMaxBytes: int | None = None
    defaultQuality: int | None = None
    encodeFormat: str | None = None
    ioConcurrency: int | None = None
    decodeConcurrency: int | None = None
    allowRecursive: bool | None = None
    maxInputPixels: int | None = None


def merge_runtime(dto: SettingsDTO) -> AppSettings:
    # start from current runtime settings, override with dto if provided
    data = runtime_settings.model_dump()
    if dto.cacheDir is not None:
        data["cache_dir"] = dto.cacheDir
    if dto.cacheMaxBytes is not None:
        data["cache_max_bytes"] = dto.cacheMaxBytes
    if dto.defaultQuality is not None:
        data["default_quality"] = dto.defaultQuality
    if dto.encodeFormat is not None:
        data["encode_format"] = dto.encodeFormat
    if dto.ioConcurrency is not None:
        data["io_concurrency"] = dto.ioConcurrency
    if dto.decodeConcurrency is not None:
        data["decode_concurrency"] = dto.decodeConcurrency
    if dto.allowRecursive is not None:
        data["allow_recursive"] = dto.allowRecursive
    if dto.maxInputPixels is not None:
        data["max_input_pixels"] = dto.maxInputPixels
    return AppSettings(**data)


@router.get("/settings")
async def get_settings(db: aiosqlite.Connection = Depends(get_db)):
    # read overrides from DB, if any
    rows = []
    async with db.execute("SELECT key, value FROM settings") as cur:
        async for r in cur:
            rows.append(r)
    overrides = {k: json.loads(v) for (k, v) in rows}
    data = runtime_settings.model_dump()
    # map DB keys (camel) to runtime snake if needed
    key_map = {
        "cacheDir": "cache_dir",
        "cacheMaxBytes": "cache_max_bytes",
        "defaultQuality": "default_quality",
        "encodeFormat": "encode_format",
        "ioConcurrency": "io_concurrency",
        "decodeConcurrency": "decode_concurrency",
        "allowRecursive": "allow_recursive",
        "maxInputPixels": "max_input_pixels",
    }
    for k, v in overrides.items():
        sk = key_map.get(k)
        if sk:
            data[sk] = v
    # return camel case for API
    return {
        "cacheDir": data["cache_dir"],
        "cacheMaxBytes": data["cache_max_bytes"],
        "defaultQuality": data["default_quality"],
        "encodeFormat": data["encode_format"],
        "ioConcurrency": data["io_concurrency"],
        "decodeConcurrency": data["decode_concurrency"],
        "allowRecursive": data["allow_recursive"],
        "maxInputPixels": data["max_input_pixels"],
    }


@router.put("/settings")
async def put_settings(dto: SettingsDTO, db: aiosqlite.Connection = Depends(get_db)):
    # persist only provided keys (as camelCase) into DB
    payload = dto.model_dump(exclude_none=True)
    if not payload:
        return {"updated": 0}
    # upsert
    async with db.execute("BEGIN"):
        for k, v in payload.items():
            await db.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?)\n                 ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, json.dumps(v)),
            )
        await db.commit()
    return {"updated": len(payload)}
