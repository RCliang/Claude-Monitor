# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Claude Monitor."""

import os
from pathlib import Path

block_cipher = None

ROOT = os.path.abspath('.')

a = Analysis(
    ['mini_window.py'],
    pathex=[ROOT, os.path.join(ROOT, 'backend')],
    binaries=[],
    datas=[
        # Backend Python modules (already on pathex, but include explicitly)
        (os.path.join(ROOT, 'backend', 'main.py'), '.'),
        (os.path.join(ROOT, 'backend', 'scanner.py'), '.'),
        (os.path.join(ROOT, 'backend', 'log_reader.py'), '.'),
        (os.path.join(ROOT, 'backend', 'ws_manager.py'), '.'),
        (os.path.join(ROOT, 'backend', 'file_watcher.py'), '.'),
        (os.path.join(ROOT, 'backend', 'session_cache.py'), '.'),
        (os.path.join(ROOT, 'backend', 'updater.py'), '.'),
        (os.path.join(ROOT, 'backend', 'mini_page.py'), '.'),
        (os.path.join(ROOT, 'backend', 'console_writer.py'), '.'),
        # Frontend built files
        (os.path.join(ROOT, 'frontend', 'dist'), 'frontend_dist'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'webview',
        'webview.platforms',
        'webview.platforms.winforms',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL'],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Claude Monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='Claude Monitor',
)
