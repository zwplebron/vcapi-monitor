"""
Deepseek 用量监控 — 全局常量定义

颜色规范（参考 docs/design-spec.md）
所有颜色值、阈值、API 地址等集中管理于此文件。
"""

# ============================================================
# 应用版本
# ============================================================

APP_VERSION = "v1.0.0"
APP_NAME = "VCAPI Monitor"

# ============================================================
# 配色方案 (v2.0.0 — 双服务监控风格)
# ============================================================

# 窗口 / 背景
COLOR_WINDOW_BG = "#EDF1F5"           # 窗口背景（浅灰蓝，近似 macOS 风格）
COLOR_TITLE_BAR = "#EDF1F5"           # 标题栏背景（与窗口一致）
COLOR_TITLE_TEXT = "#1565C0"          # 标题品牌蓝
COLOR_TITLE_ACCENT = "#1A1A2E"        # 标题辅助深色

# 卡片
COLOR_CARD_BG = "#FFFFFF"             # 卡片背景（纯白）
COLOR_CARD_BORDER = "#E1E5EA"         # 卡片浅边框

# 文字
COLOR_TEXT_PRIMARY = "#1A1A2E"        # 主文字（深灰蓝）
COLOR_TEXT_SECONDARY = "#8E8E93"      # 次要文字（iOS 灰色）

# 按钮
COLOR_BUTTON_PRIMARY = "#1976D2"      # 主按钮填充蓝
COLOR_BUTTON_PRIMARY_HOVER = "#1565C0"
COLOR_BUTTON_SECONDARY_BORDER = "#1976D2"  # 描边按钮边框
COLOR_BTN_TEXT = "#FFFFFF"            # 主按钮文字（白）

# 信号灯
COLOR_LIGHT_GREEN = "#34C759"
COLOR_LIGHT_YELLOW = "#FFCC00"
COLOR_LIGHT_RED = "#FF3B30"
COLOR_LIGHT_OFF = "#E5E5EA"
COLOR_LIGHT_FRAME = "#C7C7CC"
COLOR_LIGHT_GLOW_GREEN = "#D4F5DD"
COLOR_LIGHT_GLOW_YELLOW = "#FFF5CC"
COLOR_LIGHT_GLOW_RED = "#FFD6D4"

# 状态文字
COLOR_STATUS_OK = COLOR_LIGHT_GREEN
COLOR_STATUS_WARN = COLOR_LIGHT_YELLOW
COLOR_STATUS_DANGER = COLOR_LIGHT_RED

# 分割线
COLOR_DIVIDER = "#E8ECF0"

# 错误/提示
COLOR_ERROR = "#FF3B30"
COLOR_SUCCESS = "#34C759"

# 向后兼容别名
COLOR_BG = COLOR_WINDOW_BG
COLOR_ACCENT = COLOR_BUTTON_PRIMARY
COLOR_ACCENT_DARK = COLOR_BUTTON_PRIMARY_HOVER
COLOR_SEPARATOR = COLOR_DIVIDER
COLOR_BTN_HOVER = COLOR_BUTTON_PRIMARY_HOVER
COLOR_BTN_SECONDARY_TEXT = COLOR_BUTTON_SECONDARY_BORDER
COLOR_BTN_DANGER_TEXT = "#E53935"

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

MAIN_WINDOW_WIDTH = 400
MAIN_WINDOW_HEIGHT = 560

BIND_WINDOW_WIDTH = 400
BIND_WINDOW_HEIGHT = 360

SETTINGS_WINDOW_WIDTH = 400
SETTINGS_WINDOW_HEIGHT = 430

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
CACHE_STATS_DB_FILE = os.path.join(APP_SUPPORT_DIR, "cache_stats.sqlite3")
LOCK_FILE = os.path.join(APP_SUPPORT_DIR, "app.lock")
