"""
macOS 状态栏管理模块

通过 Swift 编译的 MenuBarHelper 在 macOS 菜单栏显示余额文本。
Python 进程通过写文件更新标题，通过 SIGUSR1 信号接收点击事件。
"""

import os
import signal
import subprocess
import atexit
import time
from src.constants import APP_SUPPORT_DIR


_TITLE_FILE = "/tmp/deepseek_statusbar_title.txt"
_WIDTH_MODE_FILE = "/tmp/deepseek_statusbar_width_mode.txt"
_helper_process = None
_cleanup_registered = False


def _get_helper_path() -> str:
    """获取 MenuBarHelper 二进制路径"""
    # 开发模式：项目根目录
    dev_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "MenuBarHelper"
    )
    if os.path.exists(dev_path):
        return dev_path

    # PyInstaller 打包模式：可执行文件同级目录
    import sys
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, "MenuBarHelper")

    # 旧版 .app 模式：Contents/MacOS/ 目录
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

    # 窗口默认可见，状态栏先进入图标模式，避免启动时闪出占位余额。
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write("ICON")
    except OSError:
        pass
    try:
        with open(_WIDTH_MODE_FILE, "w") as f:
            f.write("auto")
    except OSError:
        pass

    _helper_process = subprocess.Popen(
        [helper_path, str(os.getpid())],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _cleanup_registered:
        atexit.register(stop)
        _cleanup_registered = True

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


def _deepseek_status_text(balance: float) -> str:
    from src.storage import get_thresholds
    threshold_red, threshold_yellow = get_thresholds()
    if balance <= threshold_red:
        indicator = "🔴"
    elif balance <= threshold_yellow:
        indicator = "🟡"
    else:
        indicator = "🟢"
    return f"{indicator} DS ¥{balance:5.2f}"


def _codex_status_text(snapshot) -> str:
    if not snapshot or snapshot.primary_remaining_percent is None:
        return "⚪ CX  --%"
    remaining = snapshot.primary_remaining_percent
    from src.storage import get_codex_thresholds
    threshold_red, threshold_yellow = get_codex_thresholds()
    if remaining <= threshold_red:
        indicator = "🔴"
    elif remaining <= threshold_yellow:
        indicator = "🟡"
    else:
        indicator = "🟢"
    return f"{indicator} CX {remaining:3.0f}%"


def set_services_status(deepseek_balance=None, codex_snapshot=None):
    """根据设置更新状态栏服务余量。"""
    from src.storage import load_settings
    settings = load_settings()
    mode = settings.get("statusbar_mode", "auto")
    has_deepseek = deepseek_balance is not None
    has_codex = codex_snapshot is not None
    parts = []

    if mode == "deepseek":
        if has_deepseek:
            parts = [_deepseek_status_text(deepseek_balance)]
    elif mode == "codex":
        parts = [_codex_status_text(codex_snapshot)]
    elif mode == "both":
        if has_deepseek:
            parts.append(_deepseek_status_text(deepseek_balance))
        if has_codex:
            parts.append(_codex_status_text(codex_snapshot))
    elif mode == "alternate":
        interval = max(1, int(settings.get("statusbar_alternate_seconds", 5)))
        show_codex = int(time.time() / interval) % 2 == 1
        if show_codex and has_codex:
            parts = [_codex_status_text(codex_snapshot)]
        elif has_deepseek:
            parts = [_deepseek_status_text(deepseek_balance)]
        elif has_codex:
            parts = [_codex_status_text(codex_snapshot)]
    else:
        # auto: 有两个服务时自动轮换，有一个服务时只显示该服务
        if has_deepseek and has_codex:
            interval = max(1, int(settings.get("statusbar_alternate_seconds", 5)))
            show_codex = int(time.time() / interval) % 2 == 1
            parts = [_codex_status_text(codex_snapshot)] if show_codex else [_deepseek_status_text(deepseek_balance)]
        elif has_deepseek:
            parts = [_deepseek_status_text(deepseek_balance)]
        elif has_codex:
            parts = [_codex_status_text(codex_snapshot)]

    text = "  ".join(parts) if parts else "▪"
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write(text)
    except OSError:
        pass
    try:
        width_mode = "fixed" if mode in ("auto", "alternate") else "auto"
        with open(_WIDTH_MODE_FILE, "w") as f:
            f.write(width_mode)
    except OSError:
        pass


def set_icon_mode():
    """切换到图标模式（窗口可见时只显示图标）"""
    try:
        with open(_TITLE_FILE, "w") as f:
            f.write("ICON")
    except OSError:
        pass
    try:
        with open(_WIDTH_MODE_FILE, "w") as f:
            f.write("auto")
    except OSError:
        pass
