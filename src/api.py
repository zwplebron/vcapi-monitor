"""
Deepseek API 调用模块

仅封装余额查询接口。用量数据通过追踪余额变化推算。
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from typing import Optional
from src.constants import DEEPSEEK_BASE_URL, BALANCE_API, API_TIMEOUT


# macOS 系统 SSL 证书路径（Python 3.8 默认不加载系统证书）
_CERT_PATHS = [
    "/etc/ssl/cert.pem",             # macOS 系统证书
    "/etc/ssl/certs/ca-certificates.crt",  # Linux
]


def _ssl_context() -> ssl.SSLContext:
    """创建 SSL context，加载系统证书"""
    ctx = ssl.create_default_context()
    for path in _CERT_PATHS:
        if os.path.exists(path):
            ctx.load_verify_locations(path)
            break
    return ctx


def _api_request(api_key: str, path: str) -> Optional[dict]:
    """通用 API 请求封装"""
    url = f"{DEEPSEEK_BASE_URL}{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT, context=_ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
        except json.JSONDecodeError:
            error_data = {"error": error_body}
        return {"_error": True, "_status": e.code, "_detail": error_data}
    except (urllib.error.URLError, OSError) as e:
        return {"_error": True, "_status": 0, "_detail": str(e.reason)}


def fetch_balance(api_key: str) -> Optional[dict]:
    """
    查询账号余额，返回 API 原始响应。
    返回示例:
    {
        "is_available": true,
        "balance_infos": [{
            "currency": "CNY",
            "total_balance": "110.00",
            "granted_balance": "10.00",
            "topped_up_balance": "100.00"
        }]
    }
    """
    return _api_request(api_key, BALANCE_API)


def parse_balance(balance_data: Optional[dict]) -> float:
    """从余额 API 响应中提取总余额（元），出错返回 0.0"""
    if not balance_data or balance_data.get("_error"):
        return 0.0
    try:
        infos = balance_data.get("balance_infos", [])
        if infos:
            return float(infos[0].get("total_balance", "0"))
    except (ValueError, TypeError, IndexError):
        pass
    return 0.0
