"""
Deepseek 用量监控 — 全局常量定义

颜色规范（参考 docs/design-spec.md）
所有颜色值、阈值、API 地址等集中管理于此文件。
"""

# ============================================================
# 配色方案
# ============================================================

# 主色
COLOR_BG = "#E3F2FD"            # 主背景（淡蓝 50）
COLOR_ACCENT = "#2196F3"        # 强调色（蓝色 500）
COLOR_ACCENT_DARK = "#1976D2"   # 深色强调（蓝色 700）
COLOR_TITLE_BAR = "#BBDEFB"     # 标题栏背景（蓝色 100）
COLOR_SEPARATOR = "#BBDEFB"     # 分隔线

# 文字色
COLOR_TEXT_PRIMARY = "#212121"   # 主文字（灰 900）
COLOR_TEXT_SECONDARY = "#757575" # 次要文字（灰 600）

# 卡片/按钮
COLOR_CARD_BG = "#FFFFFF"
COLOR_BTN_TEXT = "#FFFFFF"
COLOR_BTN_HOVER = "#1E88E5"
COLOR_BTN_SECONDARY_TEXT = "#2196F3"
COLOR_BTN_DANGER_TEXT = "#E53935"

# 信号灯
COLOR_LIGHT_GREEN = "#4CAF50"    # 余额充足
COLOR_LIGHT_YELLOW = "#FFC107"   # 余额不足
COLOR_LIGHT_RED = "#F44336"      # 余额告急
COLOR_LIGHT_OFF = "#E0E0E0"      # 未激活
COLOR_LIGHT_FRAME = "#424242"    # 灯框
COLOR_LIGHT_GLOW_GREEN = "#A5D6A7"   # 外发光
COLOR_LIGHT_GLOW_YELLOW = "#FFF9C4"  # 外发光
COLOR_LIGHT_GLOW_RED = "#EF9A9A"     # 外发光

# 错误/状态
COLOR_ERROR = "#E53935"
COLOR_SUCCESS = "#4CAF50"

# ============================================================
# 余额阈值（单位：元）
# ============================================================

THRESHOLD_RED = 2.0        # 余额 ≤ 此值 → 红灯
THRESHOLD_YELLOW = 10.0    # 余额 ≤ 此值且 > THRESHOLD_RED → 黄灯
                            # 余额 > 此值 → 绿灯

# ============================================================
# API 配置
# ============================================================

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
BALANCE_API = "/user/balance"
USAGE_API = "/v1/usage"

# API 请求超时（秒）
API_TIMEOUT = 10

# ============================================================
# 窗口尺寸
# ============================================================

MAIN_WINDOW_WIDTH = 280
MAIN_WINDOW_HEIGHT = 340

BIND_WINDOW_WIDTH = 400
BIND_WINDOW_HEIGHT = 320

SETTINGS_WINDOW_WIDTH = 400
SETTINGS_WINDOW_HEIGHT = 340

# ============================================================
# 刷新与快捷键
# ============================================================

# 自动刷新间隔（毫秒）
AUTO_REFRESH_INTERVAL_MS = 5 * 60 * 1000   # 5 分钟

# 全局快捷键
HOTKEY_COMBO = "<cmd>+<shift>+d"
HOTKEY_DISPLAY = "Cmd+Shift+D"

# ============================================================
# 存储路径
# ============================================================

import os

APP_SUPPORT_DIR = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "DeepseekMonitor"
)
CONFIG_FILE = os.path.join(APP_SUPPORT_DIR, "config.json")
BALANCE_LOG_FILE = os.path.join(APP_SUPPORT_DIR, "balance_log.json")
SETTINGS_FILE = os.path.join(APP_SUPPORT_DIR, "settings.json")
LOCK_FILE = os.path.join(APP_SUPPORT_DIR, "app.lock")
