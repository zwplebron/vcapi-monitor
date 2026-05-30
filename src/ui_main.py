"""
悬浮窗主界面 v2.0.0

浅色极简风格，圆角卡片式布局，胶囊按钮。
"""

import sys
import tkinter as tk
from datetime import datetime
import time
from src.constants import (
    COLOR_WINDOW_BG, COLOR_TITLE_TEXT, COLOR_TITLE_ACCENT,
    COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_PRIMARY_HOVER,
    COLOR_DIVIDER,
    COLOR_STATUS_OK, COLOR_STATUS_WARN, COLOR_STATUS_DANGER,
    COLOR_BTN_TEXT, COLOR_ERROR, APP_NAME,
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, AUTO_REFRESH_INTERVAL_MS,
)
from src.api import fetch_balance, parse_balance
from src.storage import (
    load_api_key, record_balance_snapshot,
    get_today_consumption, get_week_consumption,
    codex_enabled, is_main_window_pinned, set_main_window_pinned, load_settings,
)
from src.cache_stats import get_today_deepseek_cache_stats
from src.codex_usage import find_latest_snapshot, get_today_cache_stats as get_today_codex_cache_stats
from src.ui_settings import SettingsWindow
from src.statusbar import (
    set_services_status as statusbar_set_services_status,
    set_icon_mode as statusbar_set_icon,
)

CARD_RADIUS = 12
BTN_RADIUS = 18
WINDOW_RADIUS = 12
TITLE_BAR_HEIGHT = 36
TRANSPARENT_BG = "#FF00FF"


def _round_rect(canvas, x1, y1, x2, y2, r, fill, outline="", width=0):
    """在 Canvas 上绘制圆角矩形"""
    return canvas.create_polygon([
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ], smooth=True, fill=fill, outline=outline, width=width)


def _fill_round_rect(canvas, x1, y1, x2, y2, r, fill):
    """用真实圆弧填充圆角矩形，适合窗口底板。"""
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
    canvas.create_oval(x1, y1, x1 + r * 2, y1 + r * 2, fill=fill, outline="")
    canvas.create_oval(x2 - r * 2, y1, x2, y1 + r * 2, fill=fill, outline="")
    canvas.create_oval(x2 - r * 2, y2 - r * 2, x2, y2, fill=fill, outline="")
    canvas.create_oval(x1, y2 - r * 2, x1 + r * 2, y2, fill=fill, outline="")


def _format_reset_time(ts: int) -> str:
    if not ts:
        return "--:--"
    if ts > 10_000_000_000:
        ts = ts // 1000
    try:
        return datetime.fromtimestamp(ts).strftime("%H:%M")
    except (ValueError, OSError):
        return "--:--"


def _next_reset_epoch(base_reset_ts: int, window_minutes: int) -> int:
    if not base_reset_ts or not window_minutes or window_minutes <= 0:
        return 0
    now = int(time.time())
    if now <= base_reset_ts:
        return base_reset_ts
    step = window_minutes * 60
    passed = (now - base_reset_ts) // step + 1
    return base_reset_ts + passed * step


def _format_tokens(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _format_cache_rate(stats) -> str:
    if not stats or stats.hit_rate is None:
        return "Cache --%"
    return f"Cache {stats.hit_rate:.1f}%"


def _format_cache_detail(stats) -> str:
    if not stats:
        return "输入 -- · 命中 -- · 未命中 --"
    return (
        f"输入 {_format_tokens(stats.input_tokens)} · "
        f"命中 {_format_tokens(stats.cached_input_tokens)} · "
        f"未命中 {_format_tokens(stats.cache_miss_tokens)}"
    )


class MonitorWindow(tk.Toplevel):
    """悬浮窗主界面"""

    def __init__(self, parent, on_unbind: callable = None):
        super().__init__(parent)
        self.overrideredirect(True)

        self._on_unbind_callback = on_unbind
        self._api_key = load_api_key()
        self._deepseek_enabled = self._api_key is not None
        self._codex_enabled = codex_enabled()
        self._last_deepseek_balance = None
        self._last_codex_snapshot = None
        self._last_deepseek_update_text = "--:--:--"
        self._last_codex_update_text = "--:--:--"
        self._last_deepseek_refresh_ts = 0.0
        self._last_codex_refresh_ts = 0.0
        self._pinned = is_main_window_pinned()

        self.resizable(False, False)

        ws = self.winfo_screenwidth()
        x = ws - MAIN_WINDOW_WIDTH - 20
        y = 40
        self.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}+{x}+{y}")
        self.minsize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self.attributes("-topmost", self._pinned)
        self._transparent_bg = self._setup_transparent_background()

        self._build_ui()
        self._setup_drag()
        self.bind("<Map>", lambda e: self._on_window_show())
        self.bind("<Unmap>", lambda e: self._on_window_hide())
        self._schedule_refresh()
        self._do_refresh(force=True)

        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

    # ============================================================
    # UI 构建
    # ============================================================

    def _setup_transparent_background(self) -> str:
        if sys.platform == "darwin":
            try:
                self.configure(bg="systemTransparent")
                self.attributes("-transparent", True)
                return "systemTransparent"
            except tk.TclError:
                pass

        try:
            self.configure(bg=TRANSPARENT_BG)
            self.attributes("-transparentcolor", TRANSPARENT_BG)
            return TRANSPARENT_BG
        except tk.TclError:
            pass

        try:
            self.configure(bg="systemTransparent")
            self.attributes("-transparent", True)
            return "systemTransparent"
        except tk.TclError:
            self.configure(bg=COLOR_WINDOW_BG)
            return COLOR_WINDOW_BG

    def _build_ui(self):
        self._shell_canvas = tk.Canvas(
            self,
            width=MAIN_WINDOW_WIDTH,
            height=MAIN_WINDOW_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=self._transparent_bg,
        )
        self._shell_canvas.pack(fill="both", expand=True)
        _fill_round_rect(
            self._shell_canvas,
            0, 0,
            MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT,
            WINDOW_RADIUS,
            COLOR_WINDOW_BG,
        )
        self._build_title_bar()
        self._build_content()

    def _build_title_bar(self):
        """自定义标题栏"""
        self._shell_canvas.create_text(
            12, 18,
            text=APP_NAME,
            anchor="w",
            font=("SF Pro Display", 15, "bold"),
            fill=COLOR_TITLE_TEXT,
        )

        self._minimize_btn = self._shell_canvas.create_text(
            MAIN_WINDOW_WIDTH - 20, 18,
            text="—",
            font=("SF Pro Display", 14, "bold"),
            fill=COLOR_TEXT_SECONDARY,
        )
        self._pin_btn = self._shell_canvas.create_text(
            MAIN_WINDOW_WIDTH - 50, 18,
            text="⤒" if self._pinned else "⤓",
            font=("SF Pro Display", 12, "bold"),
            fill=COLOR_BUTTON_PRIMARY if self._pinned else COLOR_TEXT_SECONDARY,
        )
        self._shell_canvas.tag_bind(self._pin_btn, "<ButtonRelease-1>", lambda e: self._toggle_pin())
        self._shell_canvas.tag_bind(
            self._pin_btn, "<Enter>",
            lambda e: self._shell_canvas.itemconfig(self._pin_btn, fill=COLOR_TEXT_PRIMARY),
        )
        self._shell_canvas.tag_bind(
            self._pin_btn, "<Leave>",
            lambda e: self._shell_canvas.itemconfig(
                self._pin_btn, fill=COLOR_BUTTON_PRIMARY if self._pinned else COLOR_TEXT_SECONDARY
            ),
        )
        self._shell_canvas.tag_bind(self._minimize_btn, "<ButtonRelease-1>", lambda e: self.withdraw())
        self._shell_canvas.tag_bind(
            self._minimize_btn,
            "<Enter>",
            lambda e: self._shell_canvas.itemconfig(self._minimize_btn, fill=COLOR_TEXT_PRIMARY),
        )
        self._shell_canvas.tag_bind(
            self._minimize_btn,
            "<Leave>",
            lambda e: self._shell_canvas.itemconfig(self._minimize_btn, fill=COLOR_TEXT_SECONDARY),
        )

        self._title_bar = self._shell_canvas

    def _build_content(self):
        """卡片区域"""
        y = 48
        if self._deepseek_enabled:
            self._build_deepseek_card(y)
            y += 204
        if self._codex_enabled:
            self._build_codex_card(y)
            y += 194
        if not self._deepseek_enabled and not self._codex_enabled:
            self._build_empty_card(y)
            y += 132
        self._build_footer(y + 2)

    def _draw_service_icon(self, canvas, x, y, text, fill):
        canvas.create_oval(x, y, x + 24, y + 24, fill=fill, outline="")
        canvas.create_text(
            x + 12, y + 12,
            text=text,
            font=("SF Pro Display", 10, "bold"),
            fill=COLOR_BTN_TEXT,
        )

    def _draw_status_dot(self, canvas, x, y, fill):
        return canvas.create_oval(x, y, x + 14, y + 14, fill=fill, outline="")

    def _build_deepseek_card(self, y):
        """Deepseek 余额卡片"""
        card_w = MAIN_WINDOW_WIDTH - 32
        card_h = 190

        canvas = tk.Canvas(
            self._shell_canvas, width=card_w, height=card_h,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        self._shell_canvas.create_window(16, y, anchor="nw", window=canvas)

        _round_rect(canvas, 0, 0, card_w, card_h, CARD_RADIUS,
                    fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=1)

        self._draw_service_icon(canvas, 18, 16, "DS", COLOR_BUTTON_PRIMARY)
        canvas.create_text(
            52, 28, text="Deepseek", anchor="w",
            font=("SF Pro Display", 13, "bold"), fill=COLOR_TEXT_PRIMARY
        )
        self._deepseek_dot = self._draw_status_dot(canvas, card_w - 34, 21, COLOR_TEXT_SECONDARY)

        self._deepseek_balance_label = tk.Label(
            canvas, text="¥ --.--",
            font=("SF Pro Display", 30, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 66, anchor="w", window=self._deepseek_balance_label)

        self._deepseek_status_label = tk.Label(
            canvas, text="",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(card_w - 18, 68, anchor="e", window=self._deepseek_status_label)

        self._deepseek_detail = tk.Label(
            canvas, text="",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 104, anchor="w", window=self._deepseek_detail)

        self._deepseek_cache_rate = tk.Label(
            canvas, text="Cache --%",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 128, anchor="w", window=self._deepseek_cache_rate)

        self._deepseek_cache_detail = tk.Label(
            canvas, text="输入 -- · 命中 -- · 未命中 --",
            font=("SF Pro Display", 9),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 150, anchor="w", window=self._deepseek_cache_detail)

        self._deepseek_update_label = tk.Label(
            canvas, text="最后更新 --:--:--",
            font=("SF Pro Display", 9),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 170, anchor="w", window=self._deepseek_update_label)

        deepseek_refresh_btn = tk.Canvas(
            canvas, width=64, height=22,
            highlightthickness=0, bg=COLOR_CARD_BG
        )
        self._deepseek_refresh_bg = _round_rect(
            deepseek_refresh_btn, 0, 0, 64, 22, 9, fill=COLOR_BUTTON_PRIMARY
        )
        deepseek_refresh_btn.create_text(
            32, 11, text="刷新",
            font=("SF Pro Display", 10), fill=COLOR_BTN_TEXT
        )
        deepseek_refresh_btn.bind("<ButtonPress-1>", lambda e: deepseek_refresh_btn.itemconfig(
            self._deepseek_refresh_bg, fill=COLOR_BUTTON_PRIMARY_HOVER))
        deepseek_refresh_btn.bind("<ButtonRelease-1>", lambda e: (
            deepseek_refresh_btn.itemconfig(self._deepseek_refresh_bg, fill=COLOR_BUTTON_PRIMARY),
            self._refresh_deepseek()
        ))
        deepseek_refresh_btn.bind("<Enter>", lambda e: deepseek_refresh_btn.itemconfig(
            self._deepseek_refresh_bg, fill=COLOR_BUTTON_PRIMARY_HOVER))
        deepseek_refresh_btn.bind("<Leave>", lambda e: deepseek_refresh_btn.itemconfig(
            self._deepseek_refresh_bg, fill=COLOR_BUTTON_PRIMARY))
        canvas.create_window(card_w - 18, 170, anchor="e", window=deepseek_refresh_btn)

        self._deepseek_canvas = canvas

    def _build_codex_card(self, y):
        """Codex 额度卡片"""
        card_w = MAIN_WINDOW_WIDTH - 32
        card_h = 180

        canvas = tk.Canvas(
            self._shell_canvas, width=card_w, height=card_h,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        self._shell_canvas.create_window(16, y, anchor="nw", window=canvas)

        _round_rect(canvas, 0, 0, card_w, card_h, CARD_RADIUS,
                    fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=1)

        self._draw_service_icon(canvas, 18, 16, "CX", "#6C5CE7")
        canvas.create_text(
            52, 28, text="Codex", anchor="w",
            font=("SF Pro Display", 13, "bold"), fill=COLOR_TEXT_PRIMARY
        )
        self._codex_dot = self._draw_status_dot(canvas, card_w - 34, 21, COLOR_TEXT_SECONDARY)

        self._codex_remaining_label = tk.Label(
            canvas, text="--%",
            font=("SF Pro Display", 32, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 66, anchor="w", window=self._codex_remaining_label)

        self._codex_status_label = tk.Label(
            canvas, text="",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(card_w - 18, 68, anchor="e", window=self._codex_status_label)

        self._codex_detail = tk.Label(
            canvas, text="请先运行一次 Codex",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 98, anchor="w", window=self._codex_detail)

        self._codex_cache_rate = tk.Label(
            canvas, text="Cache --%",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 120, anchor="w", window=self._codex_cache_rate)

        self._codex_cache_detail = tk.Label(
            canvas, text="输入 -- · 命中 -- · 未命中 --",
            font=("SF Pro Display", 9),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 140, anchor="w", window=self._codex_cache_detail)

        self._codex_update_label = tk.Label(
            canvas, text="最后更新 --:--:--",
            font=("SF Pro Display", 9),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(18, 160, anchor="w", window=self._codex_update_label)

        codex_refresh_btn = tk.Canvas(
            canvas, width=64, height=22,
            highlightthickness=0, bg=COLOR_CARD_BG
        )
        self._codex_refresh_bg = _round_rect(
            codex_refresh_btn, 0, 0, 64, 22, 9, fill=COLOR_BUTTON_PRIMARY
        )
        codex_refresh_btn.create_text(
            32, 11, text="刷新",
            font=("SF Pro Display", 10), fill=COLOR_BTN_TEXT
        )
        codex_refresh_btn.bind("<ButtonPress-1>", lambda e: codex_refresh_btn.itemconfig(
            self._codex_refresh_bg, fill=COLOR_BUTTON_PRIMARY_HOVER))
        codex_refresh_btn.bind("<ButtonRelease-1>", lambda e: (
            codex_refresh_btn.itemconfig(self._codex_refresh_bg, fill=COLOR_BUTTON_PRIMARY),
            self._refresh_codex()
        ))
        codex_refresh_btn.bind("<Enter>", lambda e: codex_refresh_btn.itemconfig(
            self._codex_refresh_bg, fill=COLOR_BUTTON_PRIMARY_HOVER))
        codex_refresh_btn.bind("<Leave>", lambda e: codex_refresh_btn.itemconfig(
            self._codex_refresh_bg, fill=COLOR_BUTTON_PRIMARY))
        canvas.create_window(card_w - 18, 160, anchor="e", window=codex_refresh_btn)

        self._codex_canvas = canvas

    def _build_empty_card(self, y):
        card_w = MAIN_WINDOW_WIDTH - 32
        card_h = 120
        canvas = tk.Canvas(
            self._shell_canvas, width=card_w, height=card_h,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        self._shell_canvas.create_window(16, y, anchor="nw", window=canvas)
        _round_rect(canvas, 0, 0, card_w, card_h, CARD_RADIUS,
                    fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=1)
        canvas.create_text(
            card_w // 2, card_h // 2,
            text="请先绑定 Deepseek 或启用 Codex 监控",
            font=("SF Pro Display", 12),
            fill=COLOR_TEXT_SECONDARY,
        )

    def _build_footer(self, y):
        """底部：更新时间 + 操作按钮"""
        self._error_label = tk.Label(
            self._shell_canvas, text="",
            font=("SF Pro Display", 10),
            fg=COLOR_ERROR, bg=COLOR_WINDOW_BG
        )
        self._shell_canvas.create_window(MAIN_WINDOW_WIDTH // 2, y + 6, window=self._error_label)

        btn_frame = tk.Frame(self._shell_canvas, bg=COLOR_WINDOW_BG)
        self._shell_canvas.create_window(MAIN_WINDOW_WIDTH // 2, y + 28, window=btn_frame)

        # 账号设置按钮（灰色胶囊）
        settings_btn = tk.Canvas(
            btn_frame, width=110, height=36,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        settings_btn.pack(side="left")
        self._settings_btn_bg = _round_rect(
            settings_btn, 0, 0, 110, 36, BTN_RADIUS,
            fill="#D0D5DC"
        )
        settings_btn.create_text(
            55, 18, text="账号设置",
            font=("SF Pro Display", 12), fill=COLOR_TEXT_PRIMARY
        )
        settings_btn.bind("<ButtonPress-1>", lambda e: settings_btn.itemconfig(
            self._settings_btn_bg, fill="#BCC2C9"))
        settings_btn.bind("<ButtonRelease-1>", lambda e: (
            settings_btn.itemconfig(self._settings_btn_bg, fill="#D0D5DC"),
            self._open_settings()
        ))
        settings_btn.bind("<Enter>", lambda e: settings_btn.itemconfig(
            self._settings_btn_bg, fill="#BCC2C9"))
        settings_btn.bind("<Leave>", lambda e: settings_btn.itemconfig(
            self._settings_btn_bg, fill="#D0D5DC"))

    # ============================================================
    # 拖动支持
    # ============================================================

    def _setup_drag(self):
        self._title_bar.bind("<Button-1>", self._drag_start)
        self._title_bar.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        if event.y > TITLE_BAR_HEIGHT:
            return
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        if not hasattr(self, "_drag_x"):
            return
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ============================================================
    # 功能逻辑
    # ============================================================

    def _read_refresh_minutes(self):
        s = load_settings()
        try:
            deepseek_minutes = max(1, int(s.get("deepseek_refresh_minutes", 5)))
        except (TypeError, ValueError):
            deepseek_minutes = 5
        try:
            codex_minutes = max(1, int(s.get("codex_refresh_minutes", 5)))
        except (TypeError, ValueError):
            codex_minutes = 5
        return deepseek_minutes, codex_minutes

    def _do_refresh(self, force=False):
        self._error_label.config(text="")
        now = time.time()
        deepseek_minutes, codex_minutes = self._read_refresh_minutes()

        if self._deepseek_enabled and (force or now - self._last_deepseek_refresh_ts >= deepseek_minutes * 60):
            self._refresh_deepseek()
            self._last_deepseek_refresh_ts = now

        if self._codex_enabled and (force or now - self._last_codex_refresh_ts >= codex_minutes * 60):
            self._refresh_codex()
            self._last_codex_refresh_ts = now

        if self.state() == "withdrawn":
            try:
                statusbar_set_services_status(self._last_deepseek_balance, self._last_codex_snapshot)
            except Exception:
                pass

        self._schedule_refresh()

    def _refresh_deepseek(self):
        self._last_deepseek_refresh_ts = time.time()
        balance_data = fetch_balance(self._api_key)
        if balance_data is None or balance_data.get("_error"):
            self._error_label.config(text="Deepseek 刷新失败")
            self._deepseek_detail.config(text="刷新失败，请检查网络")
            stats = get_today_deepseek_cache_stats()
            self._deepseek_cache_rate.config(text=_format_cache_rate(stats))
            self._deepseek_cache_detail.config(text=_format_cache_detail(stats))
            self._deepseek_canvas.itemconfig(self._deepseek_dot, fill=COLOR_TEXT_SECONDARY)
            self._deepseek_update_label.config(text=f"最后更新 {self._last_deepseek_update_text}")
            return

        balance = parse_balance(balance_data)
        self._last_deepseek_balance = balance
        self._last_deepseek_update_text = datetime.now().strftime("%H:%M:%S")
        record_balance_snapshot(balance)

        self._deepseek_balance_label.config(text=f"¥ {balance:.2f}")

        from src.storage import get_thresholds
        threshold_red, threshold_yellow = get_thresholds()
        if balance <= threshold_red:
            status_text = "余额不足"
            status_color = COLOR_STATUS_DANGER
        elif balance <= threshold_yellow:
            status_text = "余额偏低"
            status_color = COLOR_STATUS_WARN
        else:
            status_text = "余额充足"
            status_color = COLOR_STATUS_OK

        self._deepseek_canvas.itemconfig(self._deepseek_dot, fill=status_color)
        self._deepseek_status_label.config(text="", fg=status_color)

        today = get_today_consumption()
        week = get_week_consumption()
        stats = get_today_deepseek_cache_stats()
        self._deepseek_detail.config(text=f"今日 ¥{today:.2f} · 本周 ¥{week:.2f}")
        self._deepseek_cache_rate.config(text=_format_cache_rate(stats))
        self._deepseek_cache_detail.config(text=_format_cache_detail(stats))
        self._deepseek_update_label.config(text=f"最后更新 {self._last_deepseek_update_text}")
        self._sync_hidden_statusbar()

    def _refresh_codex(self):
        self._last_codex_refresh_ts = time.time()
        snapshot = find_latest_snapshot()
        stats = get_today_codex_cache_stats()
        self._last_codex_snapshot = snapshot
        self._last_codex_update_text = datetime.now().strftime("%H:%M:%S")
        if not snapshot or snapshot.primary_remaining_percent is None:
            self._codex_remaining_label.config(text="--%")
            self._codex_status_label.config(text="", fg=COLOR_TEXT_SECONDARY)
            self._codex_detail.config(text="请先打开 Codex 并完成一次操作")
            self._codex_cache_rate.config(text=_format_cache_rate(stats))
            self._codex_cache_detail.config(text=_format_cache_detail(stats))
            self._codex_canvas.itemconfig(self._codex_dot, fill=COLOR_TEXT_SECONDARY)
            self._codex_update_label.config(text=f"最后更新 {self._last_codex_update_text}")
            self._sync_hidden_statusbar()
            return

        remaining = snapshot.primary_remaining_percent
        next_reset_ts = _next_reset_epoch(
            snapshot.primary_resets_at or 0,
            snapshot.primary_window_minutes or 0,
        )
        # 重置时间已过但仍未拿到新快照时，不继续展示旧百分比，避免误导。
        if next_reset_ts and snapshot.primary_resets_at and int(time.time()) >= snapshot.primary_resets_at + 120:
            if snapshot.timestamp:
                try:
                    snapshot_ts = datetime.fromisoformat(snapshot.timestamp.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    snapshot_ts = 0
            else:
                snapshot_ts = 0
            if snapshot_ts and snapshot_ts < snapshot.primary_resets_at:
                self._codex_remaining_label.config(text="--%")
                self._codex_status_label.config(text="", fg=COLOR_TEXT_SECONDARY)
                self._codex_detail.config(text=f"等待新快照 · 下次重置 {_format_reset_time(next_reset_ts)}")
                self._codex_cache_rate.config(text=_format_cache_rate(stats))
                self._codex_cache_detail.config(text=_format_cache_detail(stats))
                self._codex_canvas.itemconfig(self._codex_dot, fill=COLOR_TEXT_SECONDARY)
                self._codex_update_label.config(text=f"最后更新 {self._last_codex_update_text}")
                self._sync_hidden_statusbar()
                return

        from src.storage import get_codex_thresholds
        threshold_red, threshold_yellow = get_codex_thresholds()
        if remaining <= threshold_red:
            status_text = "额度不足"
            status_color = COLOR_STATUS_DANGER
        elif remaining <= threshold_yellow:
            status_text = "额度偏低"
            status_color = COLOR_STATUS_WARN
        else:
            status_text = "额度充足"
            status_color = COLOR_STATUS_OK

        weekly_text = ""
        if snapshot.secondary_remaining_percent is not None:
            weekly_text = f" · 7天 {snapshot.secondary_remaining_percent:.0f}%"
        credits_text = ""
        if snapshot.credits_unlimited:
            credits_text = " · Credits 不限"
        elif snapshot.credits_balance is not None:
            credits_text = f" · Credits {snapshot.credits_balance:.0f}"

        self._codex_canvas.itemconfig(self._codex_dot, fill=status_color)
        self._codex_remaining_label.config(text=f"{remaining:.0f}%")
        reset_at = _format_reset_time(next_reset_ts or snapshot.primary_resets_at or 0)
        self._codex_status_label.config(text="", fg=status_color)
        self._codex_detail.config(text=f"5小时 {remaining:.0f}%{weekly_text} · 下次重置 {reset_at}{credits_text}")
        self._codex_cache_rate.config(text=_format_cache_rate(stats))
        self._codex_cache_detail.config(text=_format_cache_detail(stats))
        self._codex_update_label.config(text=f"最后更新 {self._last_codex_update_text}")
        self._sync_hidden_statusbar()

    def _schedule_refresh(self):
        if hasattr(self, "_refresh_timer"):
            self.after_cancel(self._refresh_timer)
        self._refresh_timer = self.after(30 * 1000, self._do_refresh)

    def _on_window_show(self):
        self.attributes("-topmost", self._pinned)
        try:
            statusbar_set_icon()
        except Exception:
            pass

    def _on_window_hide(self):
        self._sync_hidden_statusbar()

    def _sync_hidden_statusbar(self):
        if self.state() != "withdrawn":
            return
        try:
            statusbar_set_services_status(self._last_deepseek_balance, self._last_codex_snapshot)
        except Exception:
            pass

    def _open_settings(self):
        SettingsWindow(self, on_unbind=self._on_unbind)

    def _toggle_pin(self):
        self._pinned = not self._pinned
        self.attributes("-topmost", self._pinned)
        set_main_window_pinned(self._pinned)
        self._shell_canvas.itemconfig(self._pin_btn, text="⤒" if self._pinned else "⤓")
        self._shell_canvas.itemconfig(
            self._pin_btn, fill=COLOR_BUTTON_PRIMARY if self._pinned else COLOR_TEXT_SECONDARY
        )

    def _on_unbind(self):
        self.destroy()
        if self._on_unbind_callback:
            self._on_unbind_callback()
