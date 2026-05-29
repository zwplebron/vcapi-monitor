"""
Codex 本地用量快照读取。

读取 Codex 客户端写入的本地 session 日志，提取最近一次 rate_limits 快照。
不读取、不输出、不复用用户 token。
"""

import glob
import json
import os
from dataclasses import dataclass
from typing import Optional


CODEX_SESSIONS_GLOB = os.path.join(
    os.path.expanduser("~"),
    ".codex",
    "sessions",
    "**",
    "*.jsonl",
)


@dataclass
class CodexUsageSnapshot:
    timestamp: str
    primary_used_percent: Optional[float]
    primary_window_minutes: Optional[int]
    primary_resets_at: Optional[int]
    secondary_used_percent: Optional[float]
    secondary_window_minutes: Optional[int]
    secondary_resets_at: Optional[int]
    credits_has_credits: bool
    credits_unlimited: bool
    credits_balance: Optional[float]
    rate_limit_reached_type: Optional[str]

    @property
    def primary_remaining_percent(self) -> Optional[float]:
        return _remaining(self.primary_used_percent)

    @property
    def secondary_remaining_percent(self) -> Optional[float]:
        return _remaining(self.secondary_used_percent)


def _remaining(used_percent: Optional[float]) -> Optional[float]:
    if used_percent is None:
        return None
    return max(0.0, min(100.0, 100.0 - used_percent))


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _snapshot_from_rate_limits(timestamp: str, rate_limits: dict) -> CodexUsageSnapshot:
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}
    credits = rate_limits.get("credits") or {}
    return CodexUsageSnapshot(
        timestamp=timestamp or "",
        primary_used_percent=_to_float(primary.get("used_percent")),
        primary_window_minutes=_to_int(primary.get("window_minutes")),
        primary_resets_at=_to_int(primary.get("resets_at")),
        secondary_used_percent=_to_float(secondary.get("used_percent")),
        secondary_window_minutes=_to_int(secondary.get("window_minutes")),
        secondary_resets_at=_to_int(secondary.get("resets_at")),
        credits_has_credits=bool(credits.get("has_credits")),
        credits_unlimited=bool(credits.get("unlimited")),
        credits_balance=_to_float(credits.get("balance")),
        rate_limit_reached_type=rate_limits.get("rate_limit_reached_type"),
    )


def find_latest_snapshot() -> Optional[CodexUsageSnapshot]:
    """返回最近一次 Codex rate_limits 快照。"""
    paths = []
    for path in glob.glob(CODEX_SESSIONS_GLOB, recursive=True):
        try:
            paths.append((os.path.getmtime(path), path))
        except OSError:
            pass

    for _, path in sorted(paths, reverse=True):
        snapshot = _read_last_snapshot(path)
        if snapshot:
            return snapshot
    return None


def _read_last_snapshot(path: str) -> Optional[CodexUsageSnapshot]:
    last = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = event.get("payload") or {}
                if payload.get("type") != "token_count":
                    continue
                rate_limits = payload.get("rate_limits")
                if rate_limits:
                    last = _snapshot_from_rate_limits(
                        event.get("timestamp", ""),
                        rate_limits,
                    )
    except OSError:
        return None
    return last


def codex_available() -> bool:
    return os.path.exists(os.path.expanduser("~/.codex"))
