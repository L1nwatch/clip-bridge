# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the absolute path to the utils directory
utils_dir = Path(SPECPATH).absolute()
project_root = utils_dir.parent

block_cipher = None

a = Analysis(
    ['server.py'],
    pathex=[str(utils_dir)],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
        ('client.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_sockets',
        'gevent',
        'gevent.socket',
        'gevent.websocket',
        'gevent.websocket.handler',
        'loguru',
        'websocket',
        'websocket_client',
        'requests',
    ],
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
    name='clipbridge-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
