# -*- mode: python ; coding: ascii -*-
"""PyInstaller spec for packaging the MyRead server in one-folder mode."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH)

analysis = Analysis(
    ["server.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'frontend'), 'frontend'),
    ],
    hiddenimports=[
        'app.main'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # exclude avif-related PIL modules to avoid pulling in avif support
    excludes=[
        'PIL.avif',
        'PIL._avif',
        'avif',
        'pyavif',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

analysis.datas = [d for d in analysis.datas if '__pycache__' not in d[0] and not d[0].endswith('.pyc')]

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=None)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MyRead",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'frontend' / 'favicon.ico')
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MyRead",
)
