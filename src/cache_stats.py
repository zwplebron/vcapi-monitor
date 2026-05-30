"""
Token cache hit-rate storage.

Deepseek usage is recorded from API responses that include a `usage` object.
Codex usage is read directly from local JSONL logs in `codex_usage.py`.
"""

import sqlite3
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.constants import CACHE_STATS_DB_FILE


@dataclass
class CacheStats:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_miss_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    @property
    def hit_rate(self) -> Optional[float]:
        if self.input_tokens <= 0:
            return None
        return self.cached_input_tokens / self.input_tokens * 100


def _connect():
    os.makedirs(os.path.dirname(CACHE_STATS_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(CACHE_STATS_DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT,
            project TEXT,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            prompt_cache_hit_tokens INTEGER NOT NULL DEFAULT 0,
            prompt_cache_miss_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            cost REAL,
            created_at TEXT NOT NULL
        )
    """)
    return conn


def _to_int(value) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def record_deepseek_usage(response: dict, model: str = "", project: str = "", cost: Optional[float] = None):
    """Record Deepseek API usage from a response with a `usage` object."""
    if not response or not isinstance(response, dict):
        return
    usage = response.get("usage") or {}
    if not usage:
        return

    prompt_tokens = _to_int(usage.get("prompt_tokens"))
    hit_tokens = _to_int(usage.get("prompt_cache_hit_tokens"))
    miss_tokens = _to_int(usage.get("prompt_cache_miss_tokens"))
    completion_tokens = _to_int(usage.get("completion_tokens"))
    total_tokens = _to_int(usage.get("total_tokens"))
    reasoning_tokens = _to_int(usage.get("reasoning_tokens") or usage.get("reasoning_output_tokens"))

    now = datetime.now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO token_usage (
                date, provider, model, project,
                prompt_tokens, prompt_cache_hit_tokens, prompt_cache_miss_tokens,
                completion_tokens, reasoning_tokens, total_tokens,
                cost, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now.strftime("%Y-%m-%d"),
                "deepseek",
                model,
                project,
                prompt_tokens,
                hit_tokens,
                miss_tokens,
                completion_tokens,
                reasoning_tokens,
                total_tokens,
                cost,
                now.isoformat(timespec="seconds"),
            ),
        )


def get_today_deepseek_cache_stats() -> CacheStats:
    today = datetime.now().strftime("%Y-%m-%d")
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(prompt_cache_hit_tokens), 0),
                COALESCE(SUM(prompt_cache_miss_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(reasoning_tokens), 0),
                COALESCE(SUM(total_tokens), 0)
            FROM token_usage
            WHERE provider = 'deepseek' AND date = ?
            """,
            (today,),
        ).fetchone()
    return CacheStats(*(int(v or 0) for v in row))
