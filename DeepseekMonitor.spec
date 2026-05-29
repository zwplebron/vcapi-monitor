# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 独立的 macOS .app"""

import os

project_root = "/Users/zhaowenpei/Desktop/Deepseek用量监控"

a = Analysis(
    [os.path.join(project_root, 'app_main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'src'), 'src'),
        (os.path.join(project_root, 'assets'), 'assets'),
        (os.path.join(project_root, 'app_icon.icns'), '.'),
        (os.path.join(project_root, 'status_icon.png'), '.'),
    ],
    hiddenimports=['tkinter', 'json', 'urllib.request', 'urllib.error'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DeepseekMonitor',
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
    icon=[os.path.join(project_root, 'app_icon.icns')],
)

app = BUNDLE(
    exe,
    name='VCAPI Monitor.app',
    icon=os.path.join(project_root, 'app_icon.icns'),
    bundle_identifier='com.deepseek.monitor',
    info_plist={
        'CFBundleName': 'VCAPI Monitor',
        'CFBundleDisplayName': 'VCAPI Monitor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
        'CFBundleIconFile': 'app_icon.icns',
    },
)
