"""
应用设置窗口

从状态栏右键菜单"设置"打开。
提供：开机自启、自定义红/黄/绿阈值。
"""

import os
import tkinter as tk
from src.constants import (
    COLOR_BG, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_CARD_BG, COLOR_BTN_TEXT,
    APP_VERSION,
)
from src.storage import load_settings, save_settings


LAUNCH_AGENT_DIR = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents")
LAUNCH_AGENT_PLIST = os.path.join(LAUNCH_AGENT_DIR, "com.deepseek.monitor.plist")


def _plist_content(app_path: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.deepseek.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""


def _get_app_path() -> str:
    import sys
    proj = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(proj, "DeepseekMonitor.app")


def get_auto_launch() -> bool:
    return os.path.exists(LAUNCH_AGENT_PLIST)


def set_auto_launch(enable: bool):
    if enable:
        os.makedirs(LAUNCH_AGENT_DIR, exist_ok=True)
        app_path = _get_app_path()
        with open(LAUNCH_AGENT_PLIST, "w") as f:
            f.write(_plist_content(app_path))
    else:
        if os.path.exists(LAUNCH_AGENT_PLIST):
            os.remove(LAUNCH_AGENT_PLIST)


class AppSettingsWindow(tk.Toplevel):
    """应用设置窗口（阈值 + 开机自启）"""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("设置")
        self.resizable(False, False)

        w, h = 400, 420
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws - w) // 2
        y = (hs - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.configure(bg=COLOR_BG)

        # 加载已保存的设置
        settings = load_settings()
        self._saved_auto = get_auto_launch()
        self._saved_red = float(settings["threshold_red"])
        self._saved_yellow = float(settings["threshold_yellow"])

        # 当前值用 StringVar / BooleanVar 追踪
        self._auto_var = tk.BooleanVar(value=self._saved_auto)
        self._red_var = tk.StringVar(value=str(int(self._saved_red)))
        self._yellow_var = tk.StringVar(value=str(int(self._saved_yellow)))

        self._build_ui()
        self.transient(self.master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # 绑定变更监听 — 使用 trace 确保可靠性
        self._auto_var.trace_add("write", lambda *a: self._check_changes())
        self._red_var.trace_add("write", lambda *a: self._check_changes())
        self._yellow_var.trace_add("write", lambda *a: self._check_changes())

        self._update_save_state()

    def _build_ui(self):
        # 标题
        title = tk.Label(
            self, text="设置",
            font=("SF Pro Display", 18, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG
        )
        title.pack(pady=(28, 20))

        # --- 开机自启 ---
        row1 = tk.Frame(self, bg=COLOR_BG)
        row1.pack(fill="x", padx=30, pady=(0, 8))
        cb = tk.Checkbutton(
            row1, text="开机自启",
            variable=self._auto_var,
            font=("SF Pro Display", 13),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG,
            activebackground=COLOR_BG,
            selectcolor=COLOR_BG,
        )
        cb.pack(anchor="w")

        # --- 阈值设置 ---
        card = tk.Frame(self, bg=COLOR_CARD_BG, highlightbackground="#E0E0E0",
                        highlightthickness=1)
        card.pack(padx=30, fill="x", pady=(8, 0))

        tk.Label(card, text="自定义余额阈值",
                 font=("SF Pro Display", 12, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(pady=(14, 10), anchor="w", padx=14)

        # 红灯阈值
        self._red_var.trace_add("write", lambda *a: None)  # 先取消自动 trace，构建期不触发
        self._yellow_var.trace_add("write", lambda *a: None)

        r1 = tk.Frame(card, bg=COLOR_CARD_BG)
        r1.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(r1, text="红灯阈值（≤ 此值亮红灯）", font=("SF Pro Display", 10),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).pack(anchor="w")
        ir1 = tk.Frame(card, bg=COLOR_CARD_BG)
        ir1.pack(fill="x", padx=14, pady=(0, 2))
        tk.Label(ir1, text="¥", font=("SF Pro Display", 13, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(side="left")
        self._red_entry = tk.Entry(
            ir1, textvariable=self._red_var,
            font=("SF Pro Display", 14),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG,
            relief="solid", width=8,
            highlightbackground="#E0E0E0", highlightthickness=1,
            insertbackground=COLOR_ACCENT
        )
        self._red_entry.pack(side="left", padx=(4, 0))

        # 黄灯阈值
        r2 = tk.Frame(card, bg=COLOR_CARD_BG)
        r2.pack(fill="x", padx=14, pady=(8, 0))
        tk.Label(r2, text="黄灯阈值（≤ 此值且 > 红灯阈值时亮黄灯）", font=("SF Pro Display", 10),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).pack(anchor="w")
        ir2 = tk.Frame(card, bg=COLOR_CARD_BG)
        ir2.pack(fill="x", padx=14, pady=(2, 14))
        tk.Label(ir2, text="¥", font=("SF Pro Display", 13, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(side="left")
        self._yellow_entry = tk.Entry(
            ir2, textvariable=self._yellow_var,
            font=("SF Pro Display", 14),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG,
            relief="solid", width=8,
            highlightbackground="#E0E0E0", highlightthickness=1,
            insertbackground=COLOR_ACCENT
        )
        self._yellow_entry.pack(side="left", padx=(4, 0))

        # --- 保存按钮 ---
        self._save_btn = tk.Label(
            self, text="保 存",
            font=("SF Pro Display", 13, "bold"),
            fg=COLOR_TEXT_SECONDARY, bg="#E0E0E0",
            padx=24, pady=6
        )
        self._save_btn.pack(pady=(16, 12))
        self._save_btn.bind("<ButtonRelease-1>", lambda e: self._do_save())

        # 版本号
        tk.Label(
            self, text=APP_VERSION,
            font=("SF Pro Display", 9),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        ).pack(side="bottom", pady=(0, 8))

    def _check_changes(self):
        """每次输入变更时，比较当前值与已保存值，决定按钮状态"""
        self._update_save_state()

    def _has_real_changes(self) -> bool:
        """检查当前值是否真的与已保存值不同"""
        try:
            red = float(self._red_var.get().strip())
            yellow = float(self._yellow_var.get().strip())
        except ValueError:
            return False
        return (
            self._auto_var.get() != self._saved_auto
            or red != self._saved_red
            or yellow != self._saved_yellow
        )

    def _update_save_state(self):
        if self._has_real_changes() and self._inputs_valid():
            self._save_btn.config(fg=COLOR_BTN_TEXT, bg=COLOR_ACCENT, cursor="hand2")
        else:
            self._save_btn.config(fg=COLOR_TEXT_SECONDARY, bg="#E0E0E0", cursor="arrow")

    def _inputs_valid(self) -> bool:
        try:
            red = float(self._red_var.get().strip())
            yellow = float(self._yellow_var.get().strip())
            return red > 0 and yellow > 0
        except ValueError:
            return False

    def _do_save(self):
        if not self._has_real_changes():
            return
        if not self._inputs_valid():
            return

        red = float(self._red_var.get().strip())
        yellow = float(self._yellow_var.get().strip())

        if yellow <= red:
            from tkinter import messagebox
            messagebox.showwarning("阈值错误", "黄灯阈值必须大于红灯阈值", parent=self)
            return

        set_auto_launch(self._auto_var.get())
        save_settings({
            "auto_launch": self._auto_var.get(),
            "threshold_red": red,
            "threshold_yellow": yellow,
        })

        self._saved_auto = self._auto_var.get()
        self._saved_red = red
        self._saved_yellow = yellow
        self._update_save_state()

        # 通知主窗口立即刷新应用新阈值
        try:
            with open("/tmp/deepseek_app_refresh.txt", "w") as f:
                f.write("1")
        except OSError:
            pass

        from tkinter import messagebox
        messagebox.showinfo("已保存", "设置已保存", parent=self)
