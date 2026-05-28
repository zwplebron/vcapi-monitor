"""
悬浮窗主界面 v1.0.1

浅色极简风格，圆角卡片式布局，胶囊按钮。
"""

import tkinter as tk
from datetime import datetime
from src.constants import (
    COLOR_WINDOW_BG, COLOR_TITLE_BAR, COLOR_TITLE_TEXT, COLOR_TITLE_ACCENT,
    COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_PRIMARY_HOVER,
    COLOR_DIVIDER,
    COLOR_STATUS_OK, COLOR_STATUS_WARN, COLOR_STATUS_DANGER,
    COLOR_BTN_TEXT, COLOR_ERROR,
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, AUTO_REFRESH_INTERVAL_MS,
)
from src.api import fetch_balance, parse_balance
from src.storage import (
    load_api_key, record_balance_snapshot,
    get_today_consumption, get_week_consumption,
)
from src.traffic_light import TrafficLight
from src.ui_settings import SettingsWindow
from src.statusbar import (
    set_balance_with_status as statusbar_set_balance_status,
    set_icon_mode as statusbar_set_icon,
)

CARD_RADIUS = 12
BTN_RADIUS = 18
WINDOW_RADIUS = 16


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


class MonitorWindow(tk.Toplevel):
    """悬浮窗主界面"""

    def __init__(self, parent, on_unbind: callable = None):
        super().__init__(parent)
        self.overrideredirect(True)

        self._on_unbind_callback = on_unbind
        self._api_key = load_api_key()

        self.resizable(False, False)

        ws = self.winfo_screenwidth()
        x = ws - MAIN_WINDOW_WIDTH - 20
        y = 40
        self.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}+{x}+{y}")
        self.minsize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self.attributes("-topmost", True)

        # 透明窗口 → 圆角效果
        try:
            self.attributes('-transparent', True)
            self.configure(bg='systemTransparent')
            self._is_transparent = True
        except tk.TclError:
            self.configure(bg=COLOR_WINDOW_BG)
            self._is_transparent = False

        self._build_ui()
        self._setup_drag()
        self.bind("<Map>", lambda e: self._on_window_show())
        self.bind("<Unmap>", lambda e: self._on_window_hide())
        self._schedule_refresh()
        self._do_refresh()

        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

    # ============================================================
    # UI 构建
    # ============================================================

    def _build_ui(self):
        self._build_background()
        self._build_title_bar()
        self._build_content()

    def _build_background(self):
        """绘制窗口背景（圆角）"""
        if self._is_transparent:
            self._bg_canvas = tk.Canvas(
                self, width=MAIN_WINDOW_WIDTH, height=MAIN_WINDOW_HEIGHT,
                highlightthickness=0, bg='systemTransparent'
            )
            self._bg_canvas.place(x=0, y=0)
            _round_rect(self._bg_canvas, 1, 1,
                        MAIN_WINDOW_WIDTH - 1, MAIN_WINDOW_HEIGHT - 1,
                        WINDOW_RADIUS, fill=COLOR_WINDOW_BG)
        else:
            self._bg_canvas = None

    def _build_title_bar(self):
        """自定义标题栏"""
        bg = 'systemTransparent' if self._is_transparent else COLOR_TITLE_BAR
        bar = tk.Frame(self, bg=bg, height=36)
        bar.pack(fill="x", padx=(14, 8) if self._is_transparent else (0, 0))
        bar.pack_propagate(False)

        # 左边品牌标题
        left = tk.Frame(bar, bg=bg)
        left.pack(side="left")

        tk.Label(
            left, text="Deepseek",
            font=("SF Pro Display", 15, "bold"),
            fg=COLOR_TITLE_TEXT, bg=bg
        ).pack(side="left")
        tk.Label(
            left, text="用量监控",
            font=("SF Pro Display", 12),
            fg=COLOR_TITLE_ACCENT, bg=bg
        ).pack(side="left", padx=(2, 0))

        # 右边最小化按钮
        self._minimize_btn = tk.Label(
            bar, text="—", font=("SF Pro Display", 14, "bold"),
            fg=COLOR_TEXT_SECONDARY, bg=bg, cursor="hand2",
            width=2
        )
        self._minimize_btn.pack(side="right")
        self._minimize_btn.bind("<ButtonRelease-1>", lambda e: self.withdraw())
        self._minimize_btn.bind("<Enter>", lambda e: self._minimize_btn.config(fg=COLOR_TEXT_PRIMARY))
        self._minimize_btn.bind("<Leave>", lambda e: self._minimize_btn.config(fg=COLOR_TEXT_SECONDARY))

        self._title_bar = bar

    def _build_content(self):
        """构建卡片区域"""
        content_bg = 'systemTransparent' if self._is_transparent else COLOR_WINDOW_BG
        content = tk.Frame(self, bg=content_bg)
        content.pack(fill="both", expand=True, padx=16)

        self._build_balance_card(content)
        self._build_consumption_card(content)
        self._build_footer(content)

    def _build_balance_card(self, parent):
        """余额状态卡片"""
        card_w = MAIN_WINDOW_WIDTH - 32
        card_h = 158

        canvas = tk.Canvas(
            parent, width=card_w, height=card_h,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        canvas.pack(pady=(8, 0))

        _round_rect(canvas, 0, 0, card_w, card_h, CARD_RADIUS,
                    fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=1)

        light_container = tk.Frame(canvas, bg=COLOR_CARD_BG)
        self._traffic_light = TrafficLight(light_container, balance=0.0, bg=COLOR_CARD_BG)
        self._traffic_light.pack()
        canvas.create_window(card_w // 2, 36, window=light_container)

        self._balance_label = tk.Label(
            canvas, text="¥ --.--",
            font=("SF Pro Display", 34, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(card_w // 2, 94, window=self._balance_label)

        self._balance_status = tk.Label(
            canvas, text="",
            font=("SF Pro Display", 11),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG
        )
        canvas.create_window(card_w // 2, 132, window=self._balance_status)

        self._balance_canvas = canvas

    def _build_consumption_card(self, parent):
        """消费明细卡片"""
        card_w = MAIN_WINDOW_WIDTH - 32
        card_h = 88

        canvas = tk.Canvas(
            parent, width=card_w, height=card_h,
            highlightthickness=0, bg=COLOR_WINDOW_BG
        )
        canvas.pack(pady=(12, 0))

        _round_rect(canvas, 0, 0, card_w, card_h, CARD_RADIUS,
                    fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=1)

        row_y1 = 24
        row_y2 = 64

        canvas.create_text(
            18, row_y1, text="今日消费", anchor="w",
            font=("SF Pro Display", 12), fill=COLOR_TEXT_SECONDARY
        )
        self._today_cost = canvas.create_text(
            card_w - 18, row_y1, text="¥ --", anchor="e",
            font=("SF Pro Display", 14, "bold"), fill=COLOR_TEXT_PRIMARY
        )

        canvas.create_line(
            16, 44, card_w - 16, 44,
            fill=COLOR_DIVIDER, width=1
        )

        canvas.create_text(
            18, row_y2, text="本周消费", anchor="w",
            font=("SF Pro Display", 12), fill=COLOR_TEXT_SECONDARY
        )
        self._week_cost = canvas.create_text(
            card_w - 18, row_y2, text="¥ --", anchor="e",
            font=("SF Pro Display", 14, "bold"), fill=COLOR_TEXT_PRIMARY
        )

        self._consumption_canvas = canvas

    def _build_footer(self, parent):
        """底部：更新时间 + 操作按钮"""
        bg = 'systemTransparent' if self._is_transparent else COLOR_WINDOW_BG

        self._update_time = tk.Label(
            parent, text="最后更新: --:--:--",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=bg
        )
        self._update_time.pack(pady=(14, 6))

        self._error_label = tk.Label(
            parent, text="",
            font=("SF Pro Display", 10),
            fg=COLOR_ERROR, bg=bg
        )
        self._error_label.pack()

        btn_frame = tk.Frame(parent, bg=bg)
        btn_frame.pack(pady=(12, 14))

        # 刷新按钮（蓝色胶囊）
        refresh_btn = tk.Canvas(
            btn_frame, width=110, height=36,
            highlightthickness=0, bg=bg, cursor="hand2"
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        self._refresh_btn_bg = _round_rect(
            refresh_btn, 0, 0, 110, 36, BTN_RADIUS,
            fill=COLOR_BUTTON_PRIMARY
        )
        refresh_btn.create_text(
            55, 18, text="刷 新",
            font=("SF Pro Display", 13, "bold"), fill=COLOR_BTN_TEXT
        )
        refresh_btn.bind("<ButtonPress-1>", lambda e: refresh_btn.itemconfig(
            self._refresh_btn_bg, fill=COLOR_BUTTON_PRIMARY_HOVER))
        refresh_btn.bind("<ButtonRelease-1>", lambda e: (
            refresh_btn.itemconfig(self._refresh_btn_bg, fill=COLOR_BUTTON_PRIMARY),
            self._do_refresh()
        ))
        self._refresh_canvas = refresh_btn

        # 账号设置按钮（灰色胶囊，无边框）
        settings_btn = tk.Canvas(
            btn_frame, width=110, height=36,
            highlightthickness=0, bg=bg, cursor="hand2"
        )
        settings_btn.pack(side="left")
        self._settings_btn_bg = _round_rect(
            settings_btn, 0, 0, 110, 36, BTN_RADIUS,
            fill="#E8ECF0"
        )
        settings_btn.create_text(
            55, 18, text="账号设置",
            font=("SF Pro Display", 12), fill=COLOR_TEXT_PRIMARY
        )
        settings_btn.bind("<ButtonPress-1>", lambda e: settings_btn.itemconfig(
            self._settings_btn_bg, fill="#D0D5DC"))
        settings_btn.bind("<ButtonRelease-1>", lambda e: (
            settings_btn.itemconfig(self._settings_btn_bg, fill="#E8ECF0"),
            self._open_settings()
        ))

    # ============================================================
    # 拖动支持
    # ============================================================

    def _setup_drag(self):
        self._title_bar.bind("<Button-1>", self._drag_start)
        self._title_bar.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ============================================================
    # 功能逻辑
    # ============================================================

    def _do_refresh(self):
        self._error_label.config(text="")

        balance_data = fetch_balance(self._api_key)
        if balance_data is None or balance_data.get("_error"):
            self._error_label.config(text="刷新失败，请检查网络")
            self._schedule_refresh()
            return

        balance = parse_balance(balance_data)
        record_balance_snapshot(balance)

        self._traffic_light.set_balance(balance)
        self._balance_label.config(text=f"¥ {balance:.2f}")

        from src.storage import get_thresholds
        threshold_red, threshold_yellow = get_thresholds()
        if balance <= threshold_red:
            status_text = "余额不足，请尽快充值"
            status_color = COLOR_STATUS_DANGER
        elif balance <= threshold_yellow:
            status_text = "余额偏低"
            status_color = COLOR_STATUS_WARN
        else:
            status_text = "余额充足"
            status_color = COLOR_STATUS_OK
        self._balance_status.config(text=status_text, fg=status_color)

        today = get_today_consumption()
        week = get_week_consumption()
        self._consumption_canvas.itemconfig(
            self._today_cost, text=f"¥ {today:.2f}")
        self._consumption_canvas.itemconfig(
            self._week_cost, text=f"¥ {week:.2f}")

        now = datetime.now().strftime("%H:%M:%S")
        self._update_time.config(text=f"最后更新: {now}")
        self._error_label.config(text="")

        if self.state() == "withdrawn":
            try:
                statusbar_set_balance_status(balance)
            except Exception:
                pass

        self._schedule_refresh()

    def _schedule_refresh(self):
        if hasattr(self, "_refresh_timer"):
            self.after_cancel(self._refresh_timer)
        self._refresh_timer = self.after(AUTO_REFRESH_INTERVAL_MS, self._do_refresh)

    def _on_window_show(self):
        try:
            statusbar_set_icon()
        except Exception:
            pass

    def _on_window_hide(self):
        try:
            from src.storage import get_last_balance
            bal = get_last_balance()
            if bal > 0:
                statusbar_set_balance_status(bal)
        except Exception:
            pass

    def _open_settings(self):
        SettingsWindow(self, on_unbind=self._on_unbind)

    def _on_unbind(self):
        self.destroy()
        if self._on_unbind_callback:
            self._on_unbind_callback()
