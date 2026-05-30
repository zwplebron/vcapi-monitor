"""
Deepseek 用量监控 — 应用入口

启动流程：
1. 检查是否已绑定账号 → 否: 显示绑定窗口 / 是: 显示悬浮窗
2. 单实例检测 — 重复启动时恢复已有窗口
"""

import os
import sys

# 将项目根目录加入 Python 路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import signal
import tkinter as tk
from src.constants import LOCK_FILE, APP_SUPPORT_DIR, APP_NAME, APP_VERSION
from src.storage import config_exists


def _write_lock():
    """写入 PID 锁文件"""
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def _read_lock_pid() -> int:
    """读取已有实例的 PID，不存在返回 0"""
    if not os.path.exists(LOCK_FILE):
        return 0
    try:
        with open(LOCK_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return 0


def _is_process_running(pid: int) -> bool:
    """检查指定 PID 的进程是否存在"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _send_show_signal(pid: int):
    """向已有实例发送 SIGUSR1 信号让其显示窗口"""
    try:
        os.kill(pid, signal.SIGUSR1)
    except OSError:
        pass


def main():
    # --- 单实例检测 ---
    existing_pid = _read_lock_pid()
    if existing_pid and _is_process_running(existing_pid):
        _send_show_signal(existing_pid)
        sys.exit(0)

    _write_lock()

    import atexit
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))

    # --- 单一根 Tk 窗口（始终隐藏，所有子窗口为 Toplevel）---
    root = tk.Tk()
    root.overrideredirect(True)
    root.withdraw()
    _install_about_dialog(root)

    # 存储当前显示的窗口引用
    state = {"window": None, "settings_window": None}

    def show_bind():
        """显示绑定窗口"""
        if state["window"]:
            state["window"].destroy()
        from src.ui_bind import BindWindow
        state["window"] = BindWindow(root, on_bind_success=show_monitor)

    def show_monitor():
        """显示监控悬浮窗"""
        if state["window"]:
            state["window"].destroy()

        # 启动 macOS 状态栏（必须在 MonitorWindow 之前，否则 Map 事件写入的图标会被覆盖）
        try:
            from src.statusbar import start as start_statusbar
            start_statusbar()
        except Exception:
            pass

        from src.ui_main import MonitorWindow
        state["window"] = MonitorWindow(root, on_unbind=show_bind)

        # 全局快捷键（可选依赖）
        try:
            from src.hotkey import GlobalHotkey
            hotkey = GlobalHotkey(toggle_callback=lambda: _toggle_window(state["window"]))
            hotkey.start()
        except (ImportError, Exception):
            pass

        # SIGUSR1 信号处理 — 只写标记文件，不操作 Tk widget
        def _handle_usr1(sig, frame):
            settings_file = "/tmp/deepseek_statusbar_settings.txt"
            quit_file = "/tmp/deepseek_statusbar_quit.txt"
            if os.path.exists(settings_file):
                os.remove(settings_file)
                with open("/tmp/deepseek_app_settings.txt", "w") as f:
                    f.write("1")
            elif os.path.exists(quit_file):
                os.remove(quit_file)
                with open("/tmp/deepseek_app_quit.txt", "w") as f:
                    f.write("1")
            else:
                with open("/tmp/deepseek_app_show.txt", "w") as f:
                    f.write("1")
        signal.signal(signal.SIGUSR1, _handle_usr1)

        # 主循环轮询检查操作标记（所有 Tk 操作必须在主循环中执行）
        def _check_actions():
            settings_flag = "/tmp/deepseek_app_settings.txt"
            quit_flag = "/tmp/deepseek_app_quit.txt"
            show_flag = "/tmp/deepseek_app_show.txt"
            refresh_flag = "/tmp/deepseek_app_refresh.txt"

            # 刷新标记独立检查（不影响其他操作）
            if os.path.exists(refresh_flag):
                try:
                    with open(refresh_flag, "r") as f:
                        refresh_action = f.read().strip()
                except OSError:
                    refresh_action = ""
                os.remove(refresh_flag)
                try:
                    if state["window"] and state["window"].winfo_exists():
                        if refresh_action == "rebuild":
                            state["window"].destroy()
                            from src.ui_main import MonitorWindow
                            state["window"] = MonitorWindow(root, on_unbind=show_bind)
                        else:
                            state["window"]._do_refresh()
                except Exception:
                    pass

            if os.path.exists(settings_flag):
                os.remove(settings_flag)
                try:
                    _show_app_settings(root)
                except Exception:
                    pass
            elif os.path.exists(quit_flag):
                os.remove(quit_flag)
                try:
                    from src.statusbar import stop
                    stop()
                except Exception:
                    pass
                root.destroy()
                return
            elif os.path.exists(show_flag):
                os.remove(show_flag)
                _show_window(state["window"])
            else:
                try:
                    if state["window"] and state["window"].winfo_exists():
                        state["window"]._sync_hidden_statusbar()
                except Exception:
                    pass
            root.after(500, _check_actions)
        root.after(500, _check_actions)

    # 检查是否已绑定
    if not config_exists():
        show_bind()
    else:
        show_monitor()

    root.mainloop()


def _install_about_dialog(root):
    """接管 macOS 应用菜单的 About 面板，展示自定义信息。"""

    def _show_about():
        from tkinter import Toplevel

        for child in root.winfo_children():
            if isinstance(child, Toplevel) and getattr(child, "_is_about_dialog", False):
                child.deiconify()
                child.lift()
                child.focus_force()
                return

        win = Toplevel(root)
        win._is_about_dialog = True
        win.title(f"关于 {APP_NAME}")
        win.configure(bg="#EDF1F5")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.transient(root)

        try:
            icon_path = os.path.join(_PROJECT_ROOT, "status_icon.png")
            if os.path.exists(icon_path):
                icon_img = tk.PhotoImage(file=icon_path).subsample(12, 12)
                icon_label = tk.Label(win, image=icon_img, bg="#EDF1F5")
                icon_label.image = icon_img
                icon_label.pack(pady=(14, 6))
        except Exception:
            pass

        tk.Label(
            win, text=APP_NAME,
            font=("SF Pro Display", 18, "bold"),
            fg="#1A1A2E", bg="#EDF1F5"
        ).pack(pady=(0, 2), padx=24)
        tk.Label(
            win, text=APP_VERSION,
            font=("SF Pro Display", 12),
            fg="#8E8E93", bg="#EDF1F5"
        ).pack()
        tk.Label(
            win,
            text="API Usage Monitor for Deepseek & Codex\nCopyright © 2026",
            justify="center",
            font=("SF Pro Display", 11),
            fg="#1A1A2E", bg="#EDF1F5"
        ).pack(pady=(10, 14), padx=24)

        ok_btn = tk.Canvas(win, width=126, height=34, highlightthickness=0, bg="#EDF1F5")
        ok_btn.pack(pady=(4, 14))
        ok_bg = ok_btn.create_rectangle(0, 0, 126, 34, outline="", fill="#1976D2")
        ok_text = ok_btn.create_text(
            63, 17, text="确定",
            font=("SF Pro Display", 12, "bold"),
            fill="#FFFFFF"
        )

        def _ok_fill(color: str):
            ok_btn.itemconfig(ok_bg, fill=color)

        ok_btn.bind("<Enter>", lambda e: _ok_fill("#1565C0"))
        ok_btn.bind("<Leave>", lambda e: _ok_fill("#1976D2"))
        ok_btn.bind("<ButtonPress-1>", lambda e: _ok_fill("#0D47A1"))
        ok_btn.bind("<ButtonRelease-1>", lambda e: (ok_btn.after_idle(win.destroy), _ok_fill("#1565C0")))
        ok_btn.tag_bind(ok_text, "<ButtonPress-1>", lambda e: _ok_fill("#0D47A1"))
        ok_btn.tag_bind(ok_text, "<ButtonRelease-1>", lambda e: (ok_btn.after_idle(win.destroy), _ok_fill("#1565C0")))
        ok_btn.tag_bind(ok_text, "<Enter>", lambda e: _ok_fill("#1565C0"))
        ok_btn.tag_bind(ok_text, "<Leave>", lambda e: _ok_fill("#1976D2"))

        win.update_idletasks()
        w = max(300, win.winfo_reqwidth())
        h = max(210, win.winfo_reqheight())
        x = int((win.winfo_screenwidth() - w) / 2)
        y = int((win.winfo_screenheight() - h) / 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.focus_force()

    try:
        root.createcommand("tkAboutDialog", _show_about)
    except Exception:
        pass


def _toggle_window(app):
    """切换窗口显示/隐藏"""
    try:
        if app and app.winfo_exists():
            if app.state() == "withdrawn":
                app.deiconify()
                app.lift()
            else:
                app.withdraw()
    except Exception:
        pass


def _show_window(app):
    """显示窗口并置前"""
    try:
        if app and app.winfo_exists():
            app.deiconify()
            app.lift()
            app.attributes("-topmost", getattr(app, "_pinned", True))
    except Exception:
        pass


def _show_app_settings(root):
    """打开或置前应用设置窗口"""
    from src.ui_app_settings import AppSettingsWindow
    try:
        for child in root.winfo_children():
            if isinstance(child, AppSettingsWindow) and child.winfo_exists():
                child.deiconify()
                child.lift()
                return
    except Exception:
        pass
    AppSettingsWindow(root)


if __name__ == "__main__":
    main()
