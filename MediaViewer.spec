# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, str(Path('.').resolve()))
from app import __version__

ffmpeg_datas = collect_data_files('imageio_ffmpeg')
all_datas = ffmpeg_datas + [('assets', 'assets')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=['PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets', 'numpy', 'imageio_ffmpeg', 'cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Exclude windowsmediaplugin.dll to ensure Qt Multimedia exclusively uses the bundled ffmpegmediaplugin.dll,
# completely avoiding Windows Media Foundation fallback which lacks HEVC/H.265 on clean Windows systems.
a.binaries = [b for b in a.binaries if 'windowsmediaplugin' not in b[0].lower()]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'MediaViewer_v{__version__}',
    icon='assets/icon.ico',
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
)
