# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

FRONTEND_ROOT = Path(SPECPATH).resolve().parent
ROOT = FRONTEND_ROOT.parent

block_cipher = None

a = Analysis(
    ["bonus_guess.py"],
    pathex=[str(Path(SPECPATH).resolve().parent)],
    binaries=[],
    datas=[
        (str(ROOT / "words"), "words"),
        (str(ROOT / "docs"), "docs"),
        (str(ROOT / "clues"), "clues"),
        (str(FRONTEND_ROOT / "assets"), "assets"),
        (str(FRONTEND_ROOT / "tcl"), "tcl"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="有（×）无奖竞猜",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(FRONTEND_ROOT / "assets" / "bonus_guess.ico"),
)
