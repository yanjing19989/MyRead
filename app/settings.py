from __future__ import annotations
import os
from pydantic import BaseModel


class AppSettings(BaseModel):
    cache_dir: str = os.getenv("APP_CACHE_DIR", os.path.abspath("cache"))
    cache_max_bytes: int = int(os.getenv("APP_CACHE_MAX_BYTES", 10 * 1024 * 1024 * 1024))
    default_quality: int = int(os.getenv("APP_DEFAULT_QUALITY", 75))
    encode_format: str = os.getenv("APP_ENCODE_FORMAT", "webp")
    io_concurrency: int = int(os.getenv("APP_IO_CONCURRENCY", 8))
    decode_concurrency: int = int(os.getenv("APP_DECODE_CONCURRENCY", 3))
    allow_recursive: bool = os.getenv("APP_ALLOW_RECURSIVE", "false").lower() == "true"
    max_input_pixels: int = int(os.getenv("APP_MAX_INPUT_PIXELS", 178_000_000))


settings = AppSettings()
