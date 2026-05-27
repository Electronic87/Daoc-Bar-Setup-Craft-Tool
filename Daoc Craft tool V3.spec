# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


python_dir = Path(sys.executable).resolve().parent
dll_dir = python_dir / 'DLLs'
tcl_dir = python_dir / 'tcl'

a = Analysis(
    ['sc_craft_tool_gui.py'],
    pathex=[],
    binaries=[(str(dll_dir / 'tcl86t.dll'), '.'), (str(dll_dir / 'tk86t.dll'), '.'), (str(dll_dir / '_tkinter.pyd'), '.')],
    datas=[('daoc_craft_tool.ico', '.'), ('daoc_craft_tool_original.ico', '.'), ('daoc_gem_icons', 'daoc_gem_icons'), ('daoc_realm_icons', 'daoc_realm_icons'), ('daoc_app_assets', 'daoc_app_assets'), (str(tcl_dir / 'tcl8.6'), '_tcl_data'), (str(tcl_dir / 'tk8.6'), '_tk_data')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', '_tkinter'],
    hookspath=['pyinstaller_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Daoc Bar setup and craft tool v3.0.3',
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
    icon=['daoc_craft_tool.ico'],
)
