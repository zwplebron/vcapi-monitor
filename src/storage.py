"""
配置存储模块

负责:
1. API Key 的加密存储与读取
2. 余额历史追踪 — 通过记录余额快照推算消费金额

存储位置: ~/Library/Application Support/DeepseekMonitor/

文件:
- config.json       API Key 配置（base64 编码）
- balance_log.json  余额历史快照（用于计算今日/本周消费）
"""

import os
import json
import base64
from typing import Optional
from datetime import datetime, timedelta
from src.constants import APP_SUPPORT_DIR, CONFIG_FILE, BALANCE_LOG_FILE, SETTINGS_FILE


def _ensure_dir():
    """确保存储目录存在"""
    os.makedirs(APP_SUPPORT_DIR, exist_ok=True)


# ============================================================
# API Key 管理
# ============================================================

def save_api_key(api_key: str):
    """保存 API Key（base64 编码后存储）"""
    _ensure_dir()
    encoded = base64.b64encode(api_key.encode("utf-8")).decode("utf-8")
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_key": encoded}, f, ensure_ascii=False, indent=2)


def load_api_key() -> Optional[str]:
    """读取并解码 API Key，未配置时返回 None"""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        encoded = config.get("api_key", "")
        if not encoded:
            return None
        return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
    except (json.JSONDecodeError, KeyError, base64.binascii.Error):
        return None


def clear_api_key():
    """删除 API Key 配置"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def config_exists() -> bool:
    """检查是否已绑定账号"""
    if not os.path.exists(CONFIG_FILE):
        return False
    return load_api_key() is not None


# ============================================================
# 余额历史追踪
# ============================================================

def _load_history() -> dict:
    """加载余额历史文件"""
    if not os.path.exists(BALANCE_LOG_FILE):
        return {}
    try:
        with open(BALANCE_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_history(history: dict):
    """保存余额历史文件"""
    _ensure_dir()
    with open(BALANCE_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def record_balance_snapshot(balance: float):
    """
    记录当前余额快照。
    如果今天的快照已存在，只更新 current_balance。
    如果是新的一天，创建新的日快照。
    """
    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in history:
        # 新的一天，记录起始余额
        history[today] = {
            "start_balance": balance,
            "current_balance": balance,
            "first_seen": datetime.now().isoformat()
        }
    else:
        # 今天已有记录，更新当前余额
        history[today]["current_balance"] = balance

    # 清理超过 14 天的旧记录
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    history = {k: v for k, v in history.items() if k >= cutoff}

    _save_history(history)


def get_today_consumption() -> float:
    """
    计算今日消费金额（元）。
    今日消费 = 今日首次记录的余额 - 当前余额
    """
    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    if today in history:
        entry = history[today]
        return entry["start_balance"] - entry["current_balance"]
    return 0.0


def get_week_consumption() -> float:
    """
    计算本周累计消费金额（元）。
    将本周每天的前后余额差求和。
    """
    history = _load_history()
    today = datetime.now()
    total = 0.0
    for i in range(7):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day in history:
            entry = history[day]
            total += entry["start_balance"] - entry["current_balance"]
    return total


def get_last_balance() -> float:
    """获取最近一次记录的余额"""
    history = _load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    if today in history:
        return history[today].get("current_balance", 0.0)
    # 尝试找最近一天的记录
    if history:
        last_day = max(history.keys())
        return history[last_day].get("current_balance", 0.0)
    return 0.0


# ============================================================
# 应用设置管理
# ============================================================

def _default_settings() -> dict:
    """返回默认设置"""
    return {
        "auto_launch": False,
        "threshold_red": 2.0,
        "threshold_yellow": 10.0,
    }


def load_settings() -> dict:
    """加载应用设置，文件不存在或损坏时返回默认值"""
    if not os.path.exists(SETTINGS_FILE):
        return _default_settings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        defaults = _default_settings()
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data
    except (json.JSONDecodeError, OSError):
        return _default_settings()


def save_settings(settings: dict):
    """保存应用设置"""
    _ensure_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_thresholds() -> tuple:
    """返回当前的 (threshold_red, threshold_yellow)"""
    s = load_settings()
    return (s["threshold_red"], s["threshold_yellow"])
