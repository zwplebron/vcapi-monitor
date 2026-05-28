"""
macOS 状态栏管理模块

通过 Swift 编译的 MenuBarHelper 在 macOS 菜单栏显示余额文本。
Python 进程通过写文件更新标题，通过 SIGUSR1 信号接收点击事件。
"""

import os
import signal
import subprocess
import atexit
from src.constants import APP_SUPPORT_DIR


_TITLE_FILE = "/tmp/deepseek_statusbar_title.txt"
_helper_process = None
_cleanup_registered = False


def _get_helper_path() -> str:
    """获取 MenuBarHelper 二进制路径"""
    import sys
    # 开发模式：在项目根目录
    dev_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "MenuBarHelper"
    )
    if os.path.exists(dev_path):
        return dev_path
    # .app 模式：在 MacOS 目录
    app_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "MacOS", "MenuBarHelper"
    )
    return app_path


def start():
    """启动 MenuBarHelper 子进程"""
    global _helper_process, _cleanup_registered

    helper_path = _get_helper_path()
    if not os.path.exists(helper_path):
        return False

    _helper_process = subprocess.Popen(
        [helper_path, str(os.getpid())],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _cleanup_registered:
        atexit.register(stop)
        _cleanup_registered = True

    # 初始化标题文件
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write("¥ --.--")
    except OSError:
        pass

    return True


def stop():
    """停止 MenuBarHelper 子进程"""
    global _helper_process
    if _helper_process:
        try:
            _helper_process.terminate()
            _helper_process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                _helper_process.kill()
            except OSError:
                pass
        _helper_process = None


def set_balance(balance: float):
    """更新状态栏显示的余额（无指示灯）"""
    text = f"¥ {balance:.2f}"
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write(text)
    except OSError:
        pass


def set_balance_with_status(balance: float):
    """更新状态栏显示的余额（带红/黄/绿指示灯）"""
    from src.storage import get_thresholds
    threshold_red, threshold_yellow = get_thresholds()
    if balance <= threshold_red:
        indicator = "🔴"
    elif balance <= threshold_yellow:
        indicator = "🟡"
    else:
        indicator = "🟢"
    text = f"{indicator} ¥ {balance:.2f}"
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write(text)
    except OSError:
        pass


def set_icon_mode():
    """切换到图标模式（窗口可见时只显示图标）"""
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write("▪")  # small dot icon
    except OSError:
        pass
