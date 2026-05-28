"""
首次绑定窗口

用户输入 Deepseek API Key 完成账号绑定。
"""

import tkinter as tk
from tkinter import messagebox
from src.constants import (
    COLOR_BG, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_CARD_BG, COLOR_BTN_TEXT, COLOR_ERROR,
    BIND_WINDOW_WIDTH, BIND_WINDOW_HEIGHT,
)
from src.storage import save_api_key


class BindWindow(tk.Toplevel):
    """绑定窗口 — 首次启动时或解绑后显示"""

    def __init__(self, parent, on_bind_success: callable):
        super().__init__(parent)
        self._on_bind_success = on_bind_success

        self.title("绑定 Deepseek 账号")
        self.resizable(False, False)

        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws - BIND_WINDOW_WIDTH) // 2
        y = (hs - BIND_WINDOW_HEIGHT) // 2
        self.geometry(f"{BIND_WINDOW_WIDTH}x{BIND_WINDOW_HEIGHT}+{x}+{y}")
        self.minsize(BIND_WINDOW_WIDTH, BIND_WINDOW_HEIGHT)

        self.configure(bg=COLOR_BG)
        self._build_ui()

        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """构建 UI 布局"""
        title = tk.Label(
            self, text="绑定 Deepseek 账号",
            font=("SF Pro Display", 18, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG
        )
        title.pack(pady=(30, 8))

        desc = tk.Label(
            self, text="请输入你的 Deepseek API Key 完成账号绑定",
            font=("SF Pro Display", 12),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG, wraplength=340
        )
        desc.pack(pady=(0, 16))

        input_frame = tk.Frame(self, bg=COLOR_CARD_BG, highlightbackground="#E0E0E0",
                               highlightthickness=1)
        input_frame.pack(padx=30, fill="x")

        self._key_entry = tk.Entry(
            input_frame,
            font=("SF Pro Display", 13),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG,
            relief="flat",
            insertbackground=COLOR_ACCENT
        )
        self._key_entry.pack(fill="x", ipady=6, padx=8)
        self._key_entry.insert(0, "请输入 API Key (sk-...)")
        self._key_entry.config(fg=COLOR_TEXT_SECONDARY)
        self._key_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._key_entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._key_entry.bind("<Return>", lambda e: self._do_bind())

        help_text = tk.Label(
            self, text="如何获取 API Key？\n登录 platform.deepseek.com → API Keys → 创建",
            font=("SF Pro Display", 10),
            fg=COLOR_ACCENT, bg=COLOR_BG, cursor="hand2"
        )
        help_text.pack(pady=(12, 20))

        bind_btn = tk.Label(
            self, text="绑 定",
            font=("SF Pro Display", 14, "bold"),
            fg=COLOR_BTN_TEXT, bg=COLOR_ACCENT,
            cursor="hand2", padx=40, pady=6
        )
        bind_btn.pack(pady=(4, 0))
        bind_btn.bind("<ButtonPress-1>", lambda e: e.widget.config(bg="#1E88E5"))
        bind_btn.bind("<ButtonRelease-1>", self._on_bind_click)

    def _on_entry_focus_in(self, event):
        if self._key_entry.get() == "请输入 API Key (sk-...)":
            self._key_entry.delete(0, "end")
            self._key_entry.config(fg=COLOR_TEXT_PRIMARY, show="*")

    def _on_entry_focus_out(self, event):
        if not self._key_entry.get():
            self._key_entry.insert(0, "请输入 API Key (sk-...)")
            self._key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")

    def _on_bind_click(self, event):
        """处理绑定按钮点击（使用 ButtonRelease 避免被 FocusOut 吞掉）"""
        event.widget.config(bg=COLOR_ACCENT)
        self._do_bind()

    def _do_bind(self):
        api_key = self._key_entry.get().strip()
        placeholder = "请输入 API Key (sk-...)"

        if not api_key or api_key == placeholder:
            messagebox.showwarning("提示", "请输入 API Key", parent=self)
            return
        if not api_key.startswith("sk-"):
            messagebox.showwarning("格式错误", "API Key 应以 'sk-' 开头", parent=self)
            return
        if len(api_key) < 20:
            messagebox.showwarning("格式错误", "API Key 长度不足，请检查", parent=self)
            return

        try:
            save_api_key(api_key)
            self.destroy()
            self._on_bind_success()
        except Exception as e:
            import traceback, tempfile
            log_path = "/tmp/deepseek_monitor_error.log"
            with open(log_path, "w") as f:
                traceback.print_exc(file=f)
            messagebox.showerror("错误", f"绑定失败: {e}\n\n详情已写入 {log_path}", parent=self)

    def _on_close(self):
        """关闭窗口 → 销毁根窗口退出应用"""
        self.master.destroy()
