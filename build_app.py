"""
打包脚本 — 将 Python 源码打包为 macOS .app 应用

用法: /usr/bin/python3 build_app.py

生成的 DeepseekMonitor.app 可以拖到 Applications 文件夹，
双击即可运行。无需安装任何依赖。
"""

import os
import shutil
import stat

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "DeepseekMonitor.app"
APP_PATH = os.path.join(PROJECT_ROOT, APP_NAME)
PYTHON_BIN = "/usr/local/bin/python3.8"


def build():
    # 清理旧的 .app
    if os.path.exists(APP_PATH):
        shutil.rmtree(APP_PATH)

    # 创建 .app 目录结构
    contents = os.path.join(APP_PATH, "Contents")
    macos_dir = os.path.join(contents, "MacOS")
    resources_dir = os.path.join(contents, "Resources")
    app_src = os.path.join(resources_dir, "src")

    os.makedirs(macos_dir)
    os.makedirs(app_src)

    # 复制源码
    src_dir = os.path.join(PROJECT_ROOT, "src")
    for f in os.listdir(src_dir):
        src_file = os.path.join(src_dir, f)
        dst_file = os.path.join(app_src, f)
        if os.path.isfile(src_file):
            shutil.copy2(src_file, dst_file)

    # 复制自定义状态栏图标（如果存在）
    icon_src = os.path.join(PROJECT_ROOT, "status_icon.png")
    if os.path.exists(icon_src):
        shutil.copy2(icon_src, os.path.join(resources_dir, "status_icon.png"))
        print("状态栏图标已复制")

    # 复制应用图标（如果存在）
    app_icon_src = os.path.join(PROJECT_ROOT, "app_icon.icns")
    if os.path.exists(app_icon_src):
        shutil.copy2(app_icon_src, os.path.join(resources_dir, "app_icon.icns"))
        print("应用图标已复制")

    # 编译 Swift 状态栏助手
    swift_src = os.path.join(PROJECT_ROOT, "MenuBarHelper.swift")
    helper_bin = os.path.join(macos_dir, "MenuBarHelper")
    if os.path.exists("/usr/bin/swiftc"):
        import subprocess
        subprocess.run(
            ["/usr/bin/swiftc", "-o", helper_bin, swift_src],
            check=True,
            capture_output=True
        )
        print("MenuBarHelper 编译完成")
    else:
        print("警告: swiftc 不可用，跳过状态栏助手编译")

    # 创建 Python 启动脚本（直接作为可执行文件，不用 bash 包装）
    launcher = os.path.join(macos_dir, "DeepseekMonitor")
    with open(launcher, "w") as f:
        f.write(f"""#!/usr/local/bin/python3.8
import sys, os

_resources = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_resources = os.path.join(_resources, "Resources")
_src = os.path.join(_resources, "src")

sys.path.insert(0, _resources)
sys.path.insert(0, _src)
os.chdir(_resources)

from src.main import main
main()
""")
    os.chmod(launcher, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    # 创建 Info.plist
    plist_path = os.path.join(contents, "Info.plist")
    with open(plist_path, "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>DeepseekMonitor</string>
    <key>CFBundleDisplayName</key>
    <string>Deepseek 用量监控</string>
    <key>CFBundleIdentifier</key>
    <string>com.deepseek.monitor</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>DeepseekMonitor</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
</dict>
</plist>""")

    print(f"打包完成: {APP_PATH}")
    print("将 DeepseekMonitor.app 拖到 Applications 文件夹即可使用。")


if __name__ == "__main__":
    build()
