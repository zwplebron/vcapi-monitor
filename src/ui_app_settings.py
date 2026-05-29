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


def _round_rect(canvas, x1, y1, x2, y2, r, fill, outline="", width=0):
    return canvas.create_polygon([
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ], smooth=True, fill=fill, outline=outline, width=width)


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
    return os.path.join(proj, "VCAPI Monitor.app")


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

        w, h = 480, 620
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
        self._saved_codex_red = float(settings["codex_threshold_red"])
        self._saved_codex_yellow = float(settings["codex_threshold_yellow"])
        self._saved_deepseek_refresh_minutes = int(settings.get("deepseek_refresh_minutes", 5))
        self._saved_codex_refresh_minutes = int(settings.get("codex_refresh_minutes", 5))
        self._saved_statusbar_mode = settings["statusbar_mode"]

        # 当前值用 StringVar / BooleanVar 追踪
        self._auto_var = tk.BooleanVar(value=self._saved_auto)
        self._red_var = tk.StringVar(value=str(int(self._saved_red)))
        self._yellow_var = tk.StringVar(value=str(int(self._saved_yellow)))
        self._codex_red_var = tk.StringVar(value=str(int(self._saved_codex_red)))
        self._codex_yellow_var = tk.StringVar(value=str(int(self._saved_codex_yellow)))
        self._deepseek_refresh_var = tk.StringVar(value=str(self._saved_deepseek_refresh_minutes))
        self._codex_refresh_var = tk.StringVar(value=str(self._saved_codex_refresh_minutes))
        self._statusbar_mode_var = tk.StringVar(value=self._saved_statusbar_mode)

        self._build_ui()
        self.transient(self.master)
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # 绑定变更监听 — 使用 trace 确保可靠性
        self._auto_var.trace_add("write", lambda *a: self._check_changes())
        self._red_var.trace_add("write", lambda *a: self._check_changes())
        self._yellow_var.trace_add("write", lambda *a: self._check_changes())
        self._codex_red_var.trace_add("write", lambda *a: self._check_changes())
        self._codex_yellow_var.trace_add("write", lambda *a: self._check_changes())
        self._deepseek_refresh_var.trace_add("write", lambda *a: self._check_changes())
        self._codex_refresh_var.trace_add("write", lambda *a: self._check_changes())
        self._statusbar_mode_var.trace_add("write", lambda *a: self._check_changes())

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
        card_shell = tk.Canvas(self, width=420, height=330, highlightthickness=0, bg=COLOR_BG)
        card_shell.pack(padx=30, pady=(8, 0))
        _round_rect(card_shell, 0, 0, 420, 330, 14, fill=COLOR_CARD_BG, outline="#E0E0E0", width=1)
        card = tk.Frame(card_shell, bg=COLOR_CARD_BG)
        card_shell.create_window(10, 10, anchor="nw", window=card, width=400, height=310)

        tk.Label(card, text="自定义余额阈值",
                 font=("SF Pro Display", 12, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).pack(pady=(14, 10), anchor="w", padx=14)

        grid = tk.Frame(card, bg=COLOR_CARD_BG)
        grid.pack(fill="x", padx=14, pady=(0, 4))
        grid.grid_columnconfigure(0, minsize=176, weight=1, uniform="th_cols")
        grid.grid_columnconfigure(1, minsize=176, weight=1, uniform="th_cols")

        tk.Label(grid, text="Deepseek", font=("SF Pro Display", 11, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 6)
        )
        tk.Label(grid, text="Codex", font=("SF Pro Display", 11, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG).grid(
            row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 6)
        )

        def _make_row(row_idx, left_label, right_label, left_var, right_var):
            tk.Label(grid, text=left_label, font=("SF Pro Display", 10),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).grid(
                row=row_idx, column=0, sticky="w", padx=(0, 10), pady=(0, 4)
            )
            tk.Label(grid, text=right_label, font=("SF Pro Display", 10),
                     fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).grid(
                row=row_idx, column=1, sticky="w", padx=(10, 0), pady=(0, 4)
            )

            left_shell = tk.Canvas(grid, width=160, height=36, highlightthickness=0, bg=COLOR_CARD_BG)
            left_shell.grid(row=row_idx + 1, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
            _round_rect(left_shell, 0, 0, 160, 36, 13, fill=COLOR_BG, outline="#E0E0E0", width=1)
            left_entry = tk.Entry(
                left_shell, textvariable=left_var, font=("SF Pro Display", 14),
                fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG, relief="flat", bd=0, width=9,
                highlightthickness=0, insertbackground=COLOR_ACCENT
            )
            left_shell.create_window(12, 18, anchor="w", window=left_entry, width=134, height=24)

            right_shell = tk.Canvas(grid, width=160, height=36, highlightthickness=0, bg=COLOR_CARD_BG)
            right_shell.grid(row=row_idx + 1, column=1, sticky="w", padx=(10, 0), pady=(0, 8))
            _round_rect(right_shell, 0, 0, 160, 36, 13, fill=COLOR_BG, outline="#E0E0E0", width=1)
            right_entry = tk.Entry(
                right_shell, textvariable=right_var, font=("SF Pro Display", 14),
                fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG, relief="flat", bd=0, width=9,
                highlightthickness=0, insertbackground=COLOR_ACCENT
            )
            right_shell.create_window(12, 18, anchor="w", window=right_entry, width=134, height=24)
            return left_entry, right_entry

        self._red_entry, self._codex_red_entry = _make_row(
            1, "红灯阈值（¥）", "红灯阈值（%）", self._red_var, self._codex_red_var
        )
        self._yellow_entry, self._codex_yellow_entry = _make_row(
            3, "黄灯阈值（¥）", "黄灯阈值（%）", self._yellow_var, self._codex_yellow_var
        )
        self._deepseek_refresh_entry, self._codex_refresh_entry = _make_row(
            5, "Deepseek 自动更新间隔（分钟）", "Codex 自动更新间隔（分钟）",
            self._deepseek_refresh_var, self._codex_refresh_var
        )

        # --- 状态栏显示 ---
        mode_row = tk.Frame(self, bg=COLOR_BG)
        mode_row.pack(fill="x", padx=30, pady=(10, 0))
        tk.Label(mode_row, text="状态栏显示", font=("SF Pro Display", 12, "bold"),
                 fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG).pack(anchor="w")
        mode_menu = tk.OptionMenu(
            mode_row,
            self._statusbar_mode_var,
            "auto",
            "deepseek",
            "codex",
            "both",
            "alternate",
        )
        mode_menu.config(font=("SF Pro Display", 12), bg=COLOR_BG, highlightthickness=0)
        mode_menu.pack(anchor="w", pady=(4, 0))
        tk.Label(
            mode_row,
            text="auto: 双服务时自动轮换；alternate: 强制按 5 秒轮换",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        ).pack(anchor="w", pady=(4, 0))

        # --- 保存按钮 ---
        self._save_enabled = False
        self._save_btn = tk.Canvas(self, width=112, height=36, highlightthickness=0, bg=COLOR_BG)
        self._save_btn.pack(pady=(16, 12))
        self._save_btn_bg = _round_rect(self._save_btn, 0, 0, 112, 36, 16, fill="#E0E0E0")
        self._save_btn_text = self._save_btn.create_text(
            56, 18, text="保存", font=("SF Pro Display", 13, "bold"), fill=COLOR_TEXT_SECONDARY
        )
        self._save_btn.bind("<Enter>", lambda e: self._on_save_hover(True))
        self._save_btn.bind("<Leave>", lambda e: self._on_save_hover(False))
        self._save_btn.bind("<ButtonPress-1>", lambda e: self._on_save_press())
        self._save_btn.bind("<ButtonRelease-1>", lambda e: self._on_save_release())

        # 版本号
        tk.Label(
            self, text=APP_VERSION,
            font=("SF Pro Display", 12),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        ).pack(side="bottom", pady=(0, 10))

    def _check_changes(self):
        """每次输入变更时，比较当前值与已保存值，决定按钮状态"""
        self._update_save_state()

    def _has_real_changes(self) -> bool:
        """检查当前值是否真的与已保存值不同"""
        try:
            red = float(self._red_var.get().strip())
            yellow = float(self._yellow_var.get().strip())
            codex_red = float(self._codex_red_var.get().strip())
            codex_yellow = float(self._codex_yellow_var.get().strip())
        except ValueError:
            return False
        return (
            self._auto_var.get() != self._saved_auto
            or red != self._saved_red
            or yellow != self._saved_yellow
            or codex_red != self._saved_codex_red
            or codex_yellow != self._saved_codex_yellow
            or int(self._deepseek_refresh_var.get().strip()) != self._saved_deepseek_refresh_minutes
            or int(self._codex_refresh_var.get().strip()) != self._saved_codex_refresh_minutes
            or self._statusbar_mode_var.get() != self._saved_statusbar_mode
        )

    def _update_save_state(self):
        if self._has_real_changes() and self._inputs_valid():
            self._save_enabled = True
            self._save_btn.itemconfig(self._save_btn_bg, fill=COLOR_ACCENT)
            self._save_btn.itemconfig(self._save_btn_text, fill=COLOR_BTN_TEXT)
        else:
            self._save_enabled = False
            self._save_btn.itemconfig(self._save_btn_bg, fill="#E0E0E0")
            self._save_btn.itemconfig(self._save_btn_text, fill=COLOR_TEXT_SECONDARY)

    def _on_save_hover(self, entering: bool):
        if not self._save_enabled:
            return
        self._save_btn.itemconfig(self._save_btn_bg, fill="#1565C0" if entering else COLOR_ACCENT)

    def _on_save_press(self):
        if not self._save_enabled:
            return
        self._save_btn.itemconfig(self._save_btn_bg, fill="#0D47A1")

    def _on_save_release(self):
        if not self._save_enabled:
            return
        self._save_btn.itemconfig(self._save_btn_bg, fill="#1565C0")
        self._do_save()

    def _inputs_valid(self) -> bool:
        try:
            red = float(self._red_var.get().strip())
            yellow = float(self._yellow_var.get().strip())
            codex_red = float(self._codex_red_var.get().strip())
            codex_yellow = float(self._codex_yellow_var.get().strip())
            deepseek_refresh = int(self._deepseek_refresh_var.get().strip())
            codex_refresh = int(self._codex_refresh_var.get().strip())
            return (
                red > 0 and yellow > 0 and
                0 <= codex_red <= 100 and 0 <= codex_yellow <= 100 and
                deepseek_refresh >= 1 and codex_refresh >= 1
            )
        except ValueError:
            return False

    def _do_save(self):
        if not self._has_real_changes():
            return
        if not self._inputs_valid():
            return

        red = float(self._red_var.get().strip())
        yellow = float(self._yellow_var.get().strip())
        codex_red = float(self._codex_red_var.get().strip())
        codex_yellow = float(self._codex_yellow_var.get().strip())
        deepseek_refresh = int(self._deepseek_refresh_var.get().strip())
        codex_refresh = int(self._codex_refresh_var.get().strip())

        if yellow <= red:
            from tkinter import messagebox
            messagebox.showwarning("阈值错误", "黄灯阈值必须大于红灯阈值", parent=self)
            return
        if codex_yellow <= codex_red:
            from tkinter import messagebox
            messagebox.showwarning("阈值错误", "Codex 黄灯阈值必须大于红灯阈值", parent=self)
            return

        set_auto_launch(self._auto_var.get())
        saved = load_settings()
        saved.update({
            "auto_launch": self._auto_var.get(),
            "threshold_red": red,
            "threshold_yellow": yellow,
            "codex_threshold_red": codex_red,
            "codex_threshold_yellow": codex_yellow,
            "deepseek_refresh_minutes": deepseek_refresh,
            "codex_refresh_minutes": codex_refresh,
            "statusbar_mode": self._statusbar_mode_var.get(),
            "statusbar_alternate_seconds": 5,
        })
        save_settings(saved)

        self._saved_auto = self._auto_var.get()
        self._saved_red = red
        self._saved_yellow = yellow
        self._saved_codex_red = codex_red
        self._saved_codex_yellow = codex_yellow
        self._saved_deepseek_refresh_minutes = deepseek_refresh
        self._saved_codex_refresh_minutes = codex_refresh
        self._saved_statusbar_mode = self._statusbar_mode_var.get()
        self._update_save_state()

        # 通知主窗口立即刷新应用新阈值
        try:
            with open("/tmp/deepseek_app_refresh.txt", "w") as f:
                f.write("1")
        except OSError:
            pass

        # 按需求：保存后不弹提示框，只更新按钮状态
