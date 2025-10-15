from __future__ import annotations
import os

# 支持的图片扩展（小写，不含点）
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}


def is_image_name(name: str) -> bool:
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    return ext in IMAGE_EXTS


def basename_without_ext(path: str) -> str:
    base = os.path.basename(path)
    name, _ = os.path.splitext(base)
    return name


def is_zip_name(name: str) -> bool:
    return os.path.splitext(name)[1].lower() == ".zip"
