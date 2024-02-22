# -*- mode: python ; coding: utf-8 -*-

import sys

block_cipher = None


a = Analysis(
    ['tgrtool.py'],
    pathex=[],
    binaries=[],
    datas=[('.\\data', 'data')],
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

splash = Splash(
	'image.png',
	binaries=a.binaries,
	datas=a.datas,
	text_pos=(10, 50),
	text_size=12,
	text_color='black')
	
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
	# Static link the Visual C++ Redistributable DLLs if on Windows
	a.binaries + [('msvcp100.dll', 'C:\\Windows\\System32\\msvcp100.dll', 'BINARY'),
				  ('msvcr100.dll', 'C:\\Windows\\System32\\msvcr100.dll', 'BINARY')]
    if sys.platform == 'win32' else a.binaries,
    splash,
    splash.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tgrtool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
	icon='.\\data\\app-icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
