"""
账号设置窗口

查看/解绑/换绑 Deepseek API Key。
"""

import tkinter as tk
from tkinter import messagebox
from src.constants import (
    COLOR_BG, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_CARD_BG, COLOR_BTN_TEXT, COLOR_BTN_DANGER_TEXT,
    SETTINGS_WINDOW_WIDTH, SETTINGS_WINDOW_HEIGHT,
)
from src.storage import load_api_key, save_api_key, clear_api_key


class SettingsWindow(tk.Toplevel):
    """账号设置窗口"""

    def __init__(self, parent, on_unbind: callable):
        super().__init__(parent)
        self._on_unbind = on_unbind

        self.title("账号设置")
        self.resizable(False, False)

        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws - SETTINGS_WINDOW_WIDTH) // 2
        y = (hs - SETTINGS_WINDOW_HEIGHT) // 2
        self.geometry(f"{SETTINGS_WINDOW_WIDTH}x{SETTINGS_WINDOW_HEIGHT}+{x}+{y}")

        self.configure(bg=COLOR_BG)
        self._build_ui()
        self.transient(self.master)

    def _build_ui(self):
        api_key = load_api_key() or ""

        title = tk.Label(
            self, text="账号设置",
            font=("SF Pro Display", 18, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG
        )
        title.pack(pady=(30, 16))

        # 当前 Key 显示
        key_frame = tk.Frame(self, bg=COLOR_CARD_BG, highlightbackground="#E0E0E0",
                             highlightthickness=1)
        key_frame.pack(padx=30, fill="x", ipady=10)

        tk.Label(
            key_frame, text="当前 API Key",
            font=("SF Pro Display", 11),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        ).pack(pady=(12, 4))

        self._key_label = tk.Label(
            key_frame, text=self._mask_key(api_key),
            font=("SF Pro Display", 13, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        self._key_label.pack(pady=(0, 12))

        # 换绑区域
        tk.Label(
            self, text="输入新的 API Key 后点击保存",
            font=("SF Pro Display", 11),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        ).pack(pady=(16, 4), anchor="w", padx=30)

        self._new_key_entry = tk.Entry(
            self,
            font=("SF Pro Display", 13),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG,
            relief="solid", show="*",
            highlightbackground="#E0E0E0", highlightthickness=1,
            insertbackground=COLOR_ACCENT
        )
        self._new_key_entry.pack(padx=30, fill="x", ipady=6)
        self._new_key_entry.insert(0, "输入新的 API Key")
        self._new_key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")
        self._new_key_entry.bind("<FocusIn>", self._on_focus_in)
        self._new_key_entry.bind("<FocusOut>", self._on_focus_out)

        # 按钮行
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(pady=(16, 20))

        save_btn = tk.Label(
            btn_frame, text="保 存",
            font=("SF Pro Display", 13, "bold"),
            fg=COLOR_BTN_TEXT, bg=COLOR_ACCENT,
            cursor="hand2", padx=24, pady=4
        )
        save_btn.pack(side="left", padx=(0, 8))
        save_btn.bind("<ButtonPress-1>", lambda e: e.widget.config(bg="#1E88E5"))
        save_btn.bind("<ButtonRelease-1>", lambda e: (e.widget.config(bg=COLOR_ACCENT), self._do_save()))

        unbind_btn = tk.Label(
            btn_frame, text="解绑账号",
            font=("SF Pro Display", 13),
            fg=COLOR_BTN_DANGER_TEXT, bg=COLOR_BG,
            cursor="hand2", padx=16, pady=4,
            highlightbackground="#E53935", highlightthickness=1
        )
        unbind_btn.pack(side="left")
        unbind_btn.bind("<ButtonPress-1>", lambda e: e.widget.config(bg="#FFEBEE"))
        unbind_btn.bind("<ButtonRelease-1>", lambda e: (e.widget.config(bg=COLOR_BG), self._do_unbind()))

    def _mask_key(self, key: str) -> str:
        if len(key) <= 11:
            return key[:3] + "****" + key[-4:]
        return key[:3] + "*" * (len(key) - 7) + key[-4:]

    def _on_focus_in(self, event):
        if self._new_key_entry.get() == "输入新的 API Key":
            self._new_key_entry.delete(0, "end")
            self._new_key_entry.config(fg=COLOR_TEXT_PRIMARY, show="*")

    def _on_focus_out(self, event):
        if not self._new_key_entry.get():
            self._new_key_entry.insert(0, "输入新的 API Key")
            self._new_key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")

    def _do_save(self):
        new_key = self._new_key_entry.get().strip()
        placeholder = "输入新的 API Key"
        if not new_key or new_key == placeholder:
            messagebox.showwarning("提示", "请输入新的 API Key", parent=self)
            return
        if not new_key.startswith("sk-"):
            messagebox.showwarning("格式错误", "API Key 应以 'sk-' 开头", parent=self)
            return

        save_api_key(new_key)
        self._key_label.config(text=self._mask_key(new_key))
        self._new_key_entry.delete(0, "end")
        self._new_key_entry.insert(0, "输入新的 API Key")
        self._new_key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")
        messagebox.showinfo("成功", "API Key 已更新，将在下次刷新时生效", parent=self)

    def _do_unbind(self):
        ok = messagebox.askyesno(
            "确认解绑",
            "解绑后需要重新绑定 API Key 才能使用。\n\n确定解绑？",
            parent=self
        )
        if ok:
            clear_api_key()
            self.destroy()
            self._on_unbind()
