# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — FakturyFZ (Import FZ do Comarch XL)."""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['tools/xl_invoice_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # XlProxy.exe — musi być obok FakturyFZ.exe
        ('tools/xl_proxy/XlProxy.exe', 'xl_proxy'),
        # Konfiguracja magazynów — edytowalna przez użytkownika
        ('config/fz_magazyn.csv', 'config'),
    ],
    hiddenimports=[
        'pyodbc',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'cryptography', 'anthropic', 'httpx'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FakturyFZ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,      # brak czarnego okna konsoli
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FakturyFZ',
)
