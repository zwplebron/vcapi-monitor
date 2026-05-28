"""
悬浮窗主界面

始终置顶的桌面悬浮窗，显示余额、信号灯、消费数据和刷新控制。
"""

import tkinter as tk
from datetime import datetime
from src.constants import (
    COLOR_BG, COLOR_ACCENT, COLOR_ACCENT_DARK, COLOR_TITLE_BAR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_CARD_BG,
    COLOR_BTN_TEXT, COLOR_ERROR, COLOR_SEPARATOR,
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
    set_balance as statusbar_set_balance,
    set_balance_with_status as statusbar_set_balance_status,
    set_icon_mode as statusbar_set_icon,
)


class MonitorWindow(tk.Toplevel):
    """悬浮窗主界面"""

    def __init__(self, parent, on_unbind: callable = None):
        super().__init__(parent)
        # 必须在所有窗口配置之前去掉标准标题栏
        self.overrideredirect(True)

        self._on_unbind_callback = on_unbind
        self._api_key = load_api_key()

        self.resizable(False, False)

        # 窗口位置：屏幕右上角
        ws = self.winfo_screenwidth()
        x = ws - MAIN_WINDOW_WIDTH - 20
        y = 40
        self.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}+{x}+{y}")
        self.minsize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self.attributes("-topmost", True)

        self.configure(bg=COLOR_BG)

        self._build_ui()
        self._setup_drag()
        self.bind("<Map>", lambda e: self._on_window_show())
        self.bind("<Unmap>", lambda e: self._on_window_hide())
        self._schedule_refresh()
        self._do_refresh()

        # 强制窗口渲染并置前
        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

    # ============================================================
    # UI 构建
    # ============================================================

    def _build_ui(self):
        """构建悬浮窗布局"""
        # --- 自定义标题栏 ---
        self._title_bar = tk.Frame(self, bg=COLOR_TITLE_BAR, height=32)
        self._title_bar.pack(fill="x")
        self._title_bar.pack_propagate(False)

        title_label = tk.Label(
            self._title_bar, text="Deepseek 用量监控",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_ACCENT_DARK, bg=COLOR_TITLE_BAR
        )
        title_label.pack(side="left", padx=10)

        # 右侧按钮 — 最小化到状态栏
        btn_frame = tk.Frame(self._title_bar, bg=COLOR_TITLE_BAR)
        btn_frame.pack(side="right")

        self._minimize_btn = tk.Label(
            btn_frame, text="—", font=("SF Pro Display", 13, "bold"),
            fg=COLOR_ACCENT_DARK, bg=COLOR_TITLE_BAR, cursor="hand2",
            width=2
        )
        self._minimize_btn.pack(side="left")
        self._minimize_btn.bind("<ButtonRelease-1>", lambda e: self.withdraw())

        # --- 信号灯 ---
        light_frame = tk.Frame(self, bg=COLOR_BG)
        light_frame.pack(pady=(16, 4))
        self._traffic_light = TrafficLight(light_frame, balance=0.0, bg=COLOR_BG)
        self._traffic_light.pack()

        # --- 余额显示 ---
        self._balance_label = tk.Label(
            self, text="¥ --.--",
            font=("SF Pro Display", 28, "bold"),
            fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG
        )
        self._balance_label.pack(pady=(0, 4))

        # 余额状态文字
        self._balance_status = tk.Label(
            self, text="",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        )
        self._balance_status.pack()

        # --- 分隔线 ---
        sep = tk.Frame(self, bg=COLOR_SEPARATOR, height=1)
        sep.pack(fill="x", padx=16, pady=(12, 8))

        # --- 消费数据卡片 ---
        card = tk.Frame(self, bg=COLOR_CARD_BG, highlightbackground="#E8E8E8",
                        highlightthickness=1)
        card.pack(padx=16, fill="x", ipady=4)

        # 今日消费
        row1 = tk.Frame(card, bg=COLOR_CARD_BG)
        row1.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(row1, text="今日消费", font=("SF Pro Display", 11),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).pack(side="left")
        self._today_cost = tk.Label(row1, text="¥ --", font=("SF Pro Display", 13, "bold"),
                                     fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        self._today_cost.pack(side="right")

        # 本周消费
        row2 = tk.Frame(card, bg=COLOR_CARD_BG)
        row2.pack(fill="x", padx=12, pady=(2, 8))
        tk.Label(row2, text="本周消费", font=("SF Pro Display", 11),
                 fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).pack(side="left")
        self._week_cost = tk.Label(row2, text="¥ --", font=("SF Pro Display", 13, "bold"),
                                    fg=COLOR_TEXT_PRIMARY, bg=COLOR_CARD_BG)
        self._week_cost.pack(side="right")

        # --- 更新时间 ---
        self._update_time = tk.Label(
            self, text="最后更新: --:--:--",
            font=("SF Pro Display", 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG
        )
        self._update_time.pack(pady=(8, 2))

        # --- 错误提示 ---
        self._error_label = tk.Label(
            self, text="",
            font=("SF Pro Display", 10),
            fg=COLOR_ERROR, bg=COLOR_BG
        )
        self._error_label.pack()

        # --- 底部按钮 ---
        btn_bottom = tk.Frame(self, bg=COLOR_BG)
        btn_bottom.pack(pady=(8, 12))

        refresh_btn = tk.Label(
            btn_bottom, text="刷 新",
            font=("SF Pro Display", 12, "bold"),
            fg=COLOR_BTN_TEXT, bg=COLOR_ACCENT,
            cursor="hand2", padx=16, pady=4
        )
        refresh_btn.pack(side="left", padx=(0, 8))
        refresh_btn.bind("<ButtonPress-1>", lambda e: e.widget.config(bg="#1E88E5"))
        refresh_btn.bind("<ButtonRelease-1>", lambda e: (e.widget.config(bg=COLOR_ACCENT), self._do_refresh()))

        settings_btn = tk.Label(
            btn_bottom, text="账号设置",
            font=("SF Pro Display", 12),
            fg=COLOR_ACCENT, bg=COLOR_BG,
            cursor="hand2", padx=16, pady=4,
            highlightbackground=COLOR_ACCENT, highlightthickness=1
        )
        settings_btn.pack(side="left")
        settings_btn.bind("<ButtonPress-1>", lambda e: e.widget.config(bg="#E3F2FD"))
        settings_btn.bind("<ButtonRelease-1>", lambda e: (e.widget.config(bg=COLOR_BG), self._open_settings()))

    # ============================================================
    # 拖动支持
    # ============================================================

    def _setup_drag(self):
        """绑定标题栏拖动事件"""
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
        """执行数据刷新"""
        self._error_label.config(text="刷新中...")

        balance_data = fetch_balance(self._api_key)
        if balance_data is None or balance_data.get("_error"):
            self._error_label.config(text="刷新失败，请检查网络")
            self._schedule_refresh()
            return

        balance = parse_balance(balance_data)
        record_balance_snapshot(balance)

        # 更新指示灯
        self._traffic_light.set_balance(balance)

        # 更新余额
        self._balance_label.config(text=f"¥ {balance:.2f}")

        # 更新状态文字
        from src.storage import get_thresholds
        threshold_red, threshold_yellow = get_thresholds()
        if balance <= threshold_red:
            status_text = "余额不足，请尽快充值"
            status_color = COLOR_ERROR
        elif balance <= threshold_yellow:
            status_text = "余额偏低"
            status_color = "#F57C00"
        else:
            status_text = "余额充足"
            status_color = "#2E7D32"
        self._balance_status.config(text=status_text, fg=status_color)

        # 更新消费
        today = get_today_consumption()
        week = get_week_consumption()
        self._today_cost.config(text=f"¥ {today:.2f}")
        self._week_cost.config(text=f"¥ {week:.2f}")

        # 更新时间
        now = datetime.now().strftime("%H:%M:%S")
        self._update_time.config(text=f"最后更新: {now}")
        self._error_label.config(text="")

        # 更新状态栏（仅在窗口隐藏时显示余额+指示灯）
        if self.state() == "withdrawn":
            try:
                statusbar_set_balance_status(balance)
            except Exception:
                pass

        self._schedule_refresh()

    def _schedule_refresh(self):
        """安排下次自动刷新（取消已有定时器后重新计时）"""
        if hasattr(self, "_refresh_timer"):
            self.after_cancel(self._refresh_timer)
        self._refresh_timer = self.after(AUTO_REFRESH_INTERVAL_MS, self._do_refresh)

    def _on_window_show(self):
        """窗口显示时：状态栏只显示小图标"""
        try:
            statusbar_set_icon()
        except Exception:
            pass

    def _on_window_hide(self):
        """窗口隐藏时：状态栏显示余额+指示灯"""
        try:
            from src.storage import get_last_balance
            bal = get_last_balance()
            if bal > 0:
                statusbar_set_balance_status(bal)
        except Exception:
            pass

    def _open_settings(self):
        """打开账号设置窗口"""
        SettingsWindow(self, on_unbind=self._on_unbind)

    def _on_unbind(self):
        """解绑后销毁主窗口，触发回调显示绑定窗口"""
        self.destroy()
        if self._on_unbind_callback:
            self._on_unbind_callback()
