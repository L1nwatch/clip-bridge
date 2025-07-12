# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Add the utils directory to the path
utils_path = os.path.abspath('.')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

a = Analysis(
    ['server.py'],
    pathex=[utils_path],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
        ('client.py', '.'),
    ],
    hiddenimports=[
        'asyncio',
        'websockets',
        'websockets.server',
        'websockets.exceptions',
        'json',
        'logging',
        'argparse',
        'threading',
        'queue',
        'time',
        'sys',
        'os',
        'loguru',
        'pyperclip'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6'
    ],
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
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
    icon='../assets/icon.ico' if os.path.exists('../assets/icon.ico') else None,
)
