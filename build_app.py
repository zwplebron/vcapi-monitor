"""
打包脚本 — 使用 PyInstaller 构建独立的 macOS .app 应用

用法: /usr/local/bin/python3.8 build_app.py

PyInstaller 会嵌入 Python 运行环境，使 .app 拥有独立的应用身份，
在菜单栏和 Dock 中显示正确的名称和图标。
"""

import os
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "VCAPI Monitor.app"
APP_PATH = os.path.join(PROJECT_ROOT, APP_NAME)
PYTHON_BIN = "/usr/local/bin/python3.8"


def build():
    # 清理旧的构建产物
    for d in [APP_PATH, os.path.join(PROJECT_ROOT, "build"), os.path.join(PROJECT_ROOT, "dist")]:
        if os.path.exists(d):
            shutil.rmtree(d)

    # --- 步骤 1: PyInstaller 构建 ---
    print("正在构建 .app (PyInstaller)...")
    env = os.environ.copy()
    env["TMPDIR"] = "/tmp/claude_tmp"
    subprocess.run(
        [PYTHON_BIN, "-m", "PyInstaller", "DeepseekMonitor.spec"],
        check=True,
        cwd=PROJECT_ROOT,
        env=env,
    )

    # PyInstaller 生成的 .app 在 dist/ 目录
    dist_app = os.path.join(PROJECT_ROOT, "dist", APP_NAME)
    if not os.path.exists(dist_app):
        print(f"错误: PyInstaller 构建失败，dist/ 中没有 {APP_NAME}")
        return

    # 移动到项目根目录
    if os.path.exists(APP_PATH):
        shutil.rmtree(APP_PATH)
    shutil.move(dist_app, APP_PATH)
    shutil.rmtree(os.path.join(PROJECT_ROOT, "dist"))

    # --- 步骤 2: 编译 MenuBarHelper ---
    helper_bin = os.path.join(APP_PATH, "Contents", "MacOS", "MenuBarHelper")
    swift_src = os.path.join(PROJECT_ROOT, "MenuBarHelper.swift")
    if os.path.exists("/usr/bin/swiftc"):
        subprocess.run(
            ["/usr/bin/swiftc", "-o", helper_bin, swift_src],
            check=True,
        )
        print("MenuBarHelper 编译完成")
    else:
        print("警告: swiftc 不可用")

    # --- 步骤 3: 确保图标就位 ---
    resources_dir = os.path.join(APP_PATH, "Contents", "Resources")
    icon_src = os.path.join(PROJECT_ROOT, "status_icon.png")
    if os.path.exists(icon_src):
        dst = os.path.join(resources_dir, "status_icon.png")
        if not os.path.exists(dst):
            shutil.copy2(icon_src, dst)
            print("状态栏图标已复制")

    print(f"\n打包完成: {APP_PATH}")
    print("将 \"VCAPI Monitor.app\" 拖到 Applications 文件夹即可使用。")


if __name__ == "__main__":
    build()
