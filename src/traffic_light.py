"""
交通信号灯组件

三个圆形灯并排显示，根据余额自动切换激活状态。
- 绿灯: 余额 > 10 元
- 黄灯: 2 < 余额 ≤ 10 元
- 红灯: 余额 ≤ 2 元

外观参考交通信号灯：深灰外壳 + 彩色发光圆。
"""

import tkinter as tk
from src.constants import (
    COLOR_LIGHT_GREEN, COLOR_LIGHT_YELLOW, COLOR_LIGHT_RED,
    COLOR_LIGHT_OFF, COLOR_LIGHT_FRAME,
    COLOR_LIGHT_GLOW_GREEN, COLOR_LIGHT_GLOW_YELLOW, COLOR_LIGHT_GLOW_RED,
)


class TrafficLight(tk.Canvas):
    """交通信号灯组件，继承 tk.Canvas"""

    # (填充色, 外发光色)
    _COLORS = {
        "green":  (COLOR_LIGHT_GREEN,  COLOR_LIGHT_GLOW_GREEN),
        "yellow": (COLOR_LIGHT_YELLOW, COLOR_LIGHT_GLOW_YELLOW),
        "red":    (COLOR_LIGHT_RED,    COLOR_LIGHT_GLOW_RED),
    }

    def __init__(self, parent, balance: float = 0.0, **kwargs):
        self._balance = balance

        # 固定尺寸：三个灯水平排列
        width = kwargs.pop("width", 100)
        height = kwargs.pop("height", 40)
        kwargs.pop("bg", None)  # 我们自己用 parent["bg"]，避免重复
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=parent["bg"], **kwargs)

        self._light_radius = 8          # 发光圆半径
        self._frame_radius = 11         # 外壳圆半径
        self._spacing = 30              # 圆心间距
        self._center_y = 20             # 垂直居中

        self._draw()

    def _draw(self):
        """绘制三个灯"""
        self.delete("all")
        active = self._active_light()

        colors = [
            ("red",    12),
            ("yellow", 42),
            ("green",  72),
        ]

        for light_type, cx in colors:
            is_active = (light_type == active)
            fill, glow = self._COLORS[light_type]

            # 外发光（仅激活时绘制）
            if is_active:
                self._draw_circle(cx, self._center_y, self._light_radius + 3, glow, "")

            # 主灯
            main_fill = fill if is_active else COLOR_LIGHT_OFF
            self._draw_circle(cx, self._center_y, self._light_radius, main_fill, "")

            # 外壳圆环
            self._draw_circle(cx, self._center_y, self._frame_radius, "", COLOR_LIGHT_FRAME)

    def _draw_circle(self, cx, cy, r, fill, outline):
        """绘制一个圆形"""
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fill, outline=outline, width=1.5 if outline else 0
        )

    def _active_light(self) -> str:
        """根据余额和当前阈值判断激活哪个灯"""
        from src.storage import get_thresholds
        threshold_red, threshold_yellow = get_thresholds()
        if self._balance <= threshold_red:
            return "red"
        elif self._balance <= threshold_yellow:
            return "yellow"
        else:
            return "green"

    def set_balance(self, balance: float):
        """更新余额并重新绘制信号灯"""
        self._balance = balance
        self._draw()
