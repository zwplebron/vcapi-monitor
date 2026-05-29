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
    APP_VERSION,
)
from src.storage import load_api_key, save_api_key, clear_api_key, codex_enabled, set_codex_enabled


def _round_rect(canvas, x1, y1, x2, y2, r, fill, outline=""):
    return canvas.create_polygon([
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ], smooth=True, fill=fill, outline=outline, width=1)


class SettingsWindow(tk.Toplevel):
    """账号设置窗口"""

    def __init__(self, parent, on_unbind: callable):
        super().__init__(parent)
        self._on_unbind = on_unbind
        self._codex_var = tk.BooleanVar(value=codex_enabled())
        self._saved_codex_enabled = self._codex_var.get()
        self._save_enabled = False

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
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        self.after(0, self._update_save_state)

    def _build_ui(self):
        api_key = load_api_key() or ""

        title = tk.Label(
            self, text="账号设置",
            font=("SF Pro Display", 18, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG
        )
        title.pack(pady=(30, 16))

        # 当前 Key 显示
        key_shell = tk.Canvas(self, width=340, height=120, highlightthickness=0, bg=COLOR_BG)
        key_shell.pack(padx=30)
        _round_rect(key_shell, 0, 0, 340, 120, 12, fill=COLOR_CARD_BG, outline="#E0E0E0")
        key_frame = tk.Frame(key_shell, bg=COLOR_CARD_BG)
        key_shell.create_window(10, 10, anchor="nw", window=key_frame, width=320, height=100)

        tk.Label(
            key_frame, text="当前 Deepseek API Key",
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

        entry_shell = tk.Canvas(self, width=340, height=42, highlightthickness=0, bg=COLOR_BG)
        entry_shell.pack(padx=30, fill="x")
        _round_rect(entry_shell, 0, 0, 340, 42, 11, fill=COLOR_CARD_BG, outline="#E0E0E0")
        self._new_key_entry = tk.Entry(
            entry_shell,
            font=("SF Pro Display", 13),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG,
            relief="flat", bd=0, show="*",
            highlightthickness=0,
            insertbackground=COLOR_ACCENT
        )
        entry_shell.create_window(12, 21, anchor="w", window=self._new_key_entry, width=316, height=24)
        self._new_key_entry.insert(0, "输入新的 API Key")
        self._new_key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")
        self._new_key_entry.bind("<FocusIn>", self._on_focus_in)
        self._new_key_entry.bind("<FocusOut>", self._on_focus_out)
        self._new_key_entry.bind("<KeyRelease>", lambda e: self._update_save_state())

        codex_check = tk.Checkbutton(
            self,
            text="启用 Codex 本机余量监控",
            variable=self._codex_var,
            font=("SF Pro Display", 11),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG,
            activebackground=COLOR_BG,
            selectcolor=COLOR_BG,
        )
        codex_check.pack(pady=(12, 0), anchor="w", padx=30)
        self._codex_var.trace_add("write", lambda *a: self._update_save_state())

        # 按钮行
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(pady=(16, 10))

        self._save_btn = tk.Canvas(btn_frame, width=110, height=36, highlightthickness=0, bg=COLOR_BG)
        self._save_btn.pack(side="left", padx=(0, 10))
        self._save_btn_bg = _round_rect(self._save_btn, 0, 0, 110, 36, 16, fill="#D5D7DB")
        self._save_btn_text = self._save_btn.create_text(55, 18, text="保存", font=("SF Pro Display", 13, "bold"), fill=COLOR_TEXT_SECONDARY)
        self._save_btn.bind("<Enter>", lambda e: self._on_save_hover(True))
        self._save_btn.bind("<Leave>", lambda e: self._on_save_hover(False))
        self._save_btn.bind("<ButtonPress-1>", lambda e: self._on_save_press())
        self._save_btn.bind("<ButtonRelease-1>", lambda e: self._on_save_release())

        unbind_btn = tk.Canvas(btn_frame, width=110, height=36, highlightthickness=0, bg=COLOR_BG)
        unbind_btn.pack(side="left")
        self._unbind_btn_bg = _round_rect(unbind_btn, 0, 0, 110, 36, 16, fill="#E57373")
        unbind_btn.create_text(55, 18, text="解绑", font=("SF Pro Display", 13), fill=COLOR_BTN_TEXT)
        unbind_btn.bind("<Enter>", lambda e: unbind_btn.itemconfig(self._unbind_btn_bg, fill="#EF5350"))
        unbind_btn.bind("<Leave>", lambda e: unbind_btn.itemconfig(self._unbind_btn_bg, fill="#E57373"))
        unbind_btn.bind("<ButtonPress-1>", lambda e: unbind_btn.itemconfig(self._unbind_btn_bg, fill="#E53935"))
        unbind_btn.bind("<ButtonRelease-1>", lambda e: (unbind_btn.itemconfig(self._unbind_btn_bg, fill="#EF5350"), self._do_unbind()))

        # 版本号
        version_label = tk.Label(
            self, text=APP_VERSION,
            font=("SF Pro Display", 12),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        )
        version_label.place(relx=0.5, rely=1.0, y=-16, anchor="s")

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
        self._update_save_state()

    def _has_changes(self) -> bool:
        typed = self._new_key_entry.get().strip()
        placeholder = "输入新的 API Key"
        key_changed = bool(typed) and typed != placeholder
        codex_changed = self._codex_var.get() != self._saved_codex_enabled
        return key_changed or codex_changed

    def _update_save_state(self):
        self._save_enabled = self._has_changes()
        if self._save_enabled:
            self._save_btn.itemconfig(self._save_btn_bg, fill=COLOR_ACCENT)
            self._save_btn.itemconfig(self._save_btn_text, fill=COLOR_BTN_TEXT)
        else:
            self._save_btn.itemconfig(self._save_btn_bg, fill="#D5D7DB")
            self._save_btn.itemconfig(self._save_btn_text, fill=COLOR_TEXT_SECONDARY)

    def _on_save_hover(self, entering: bool):
        if not self._save_enabled:
            return
        self._save_btn.itemconfig(self._save_btn_bg, fill="#1565C0" if entering else COLOR_ACCENT)

    def _on_save_press(self):
        if self._save_enabled:
            self._save_btn.itemconfig(self._save_btn_bg, fill="#0D47A1")

    def _on_save_release(self):
        if not self._save_enabled:
            return
        self._save_btn.itemconfig(self._save_btn_bg, fill="#1565C0")
        self._do_save()

    def _do_save(self):
        if not self._save_enabled:
            return
        new_key = self._new_key_entry.get().strip()
        placeholder = "输入新的 API Key"
        if not new_key or new_key == placeholder:
            self._persist_codex_enabled()
            return
        if not new_key.startswith("sk-"):
            messagebox.showwarning("格式错误", "API Key 应以 'sk-' 开头", parent=self)
            return

        save_api_key(new_key)
        self._persist_codex_enabled()
        self._key_label.config(text=self._mask_key(new_key))
        self._new_key_entry.delete(0, "end")
        self._new_key_entry.insert(0, "输入新的 API Key")
        self._new_key_entry.config(fg=COLOR_TEXT_SECONDARY, show="")
        self._update_save_state()

    def _persist_codex_enabled(self):
        current = self._codex_var.get()
        if current == self._saved_codex_enabled:
            return
        set_codex_enabled(current)
        self._saved_codex_enabled = current
        self._update_save_state()
        try:
            with open("/tmp/deepseek_app_refresh.txt", "w") as f:
                f.write("rebuild")
        except OSError:
            pass

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
