"""
py2app 打包配置 — 构建独立的 macOS .app

运行: /usr/local/bin/python3.8 setup.py py2app
"""

from setuptools import setup

APP = ["app_main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "VCAPI Monitor",
        "CFBundleDisplayName": "VCAPI Monitor",
        "CFBundleIdentifier": "com.deepseek.monitor",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSMinimumSystemVersion": "10.15",
        "NSHighResolutionCapable": True,
        "CFBundleIconFile": "app_icon.icns",
    },
    "packages": ["src"],
    "includes": [
        "tkinter", "json", "urllib.request", "urllib.error",
        "datetime", "signal", "os", "subprocess", "atexit",
    ],
}

setup(
    name="VCAPIMonitor",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
