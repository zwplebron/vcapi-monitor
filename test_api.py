"""
API 调用测试脚本

用法: /usr/bin/python3 test_api.py <你的API_KEY>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.api import fetch_balance, parse_balance
from src.storage import save_api_key, load_api_key, clear_api_key, config_exists
from src.storage import record_balance_snapshot, get_today_consumption, get_week_consumption


def main():
    if len(sys.argv) < 2:
        print("用法: /usr/bin/python3 test_api.py <API_KEY>")
        print("示例: /usr/bin/python3 test_api.py sk-xxxxxxxxxxxxxxxx")
        sys.exit(1)

    api_key = sys.argv[1]

    print("=" * 50)
    print("Deepseek API 测试")
    print("=" * 50)

    # 测试余额查询
    print("\n[1] 查询余额...")
    balance_data = fetch_balance(api_key)
    if balance_data is None or balance_data.get("_error"):
        print(f"  失败: {balance_data}")
        sys.exit(1)

    balance = parse_balance(balance_data)
    is_available = balance_data.get("is_available", False)
    print(f"  余额可用: {is_available}")
    print(f"  总余额: ¥{balance:.2f}")

    # 测试存储
    print("\n[2] 测试存储...")
    save_api_key(api_key)
    loaded = load_api_key()
    print(f"  存储/读取: {'通过' if loaded == api_key else '失败'}")
    print(f"  已绑定: {config_exists()}")

    # 测试余额追踪
    print("\n[3] 测试余额追踪...")
    record_balance_snapshot(balance + 5.0)    # 模拟之前余额较高
    record_balance_snapshot(balance)           # 当前余额
    today_cost = get_today_consumption()
    week_cost = get_week_consumption()
    print(f"  今日推算消费: ¥{today_cost:.2f}")
    print(f"  本周推算消费: ¥{week_cost:.2f}")

    # 清理测试数据
    clear_api_key()
    print("\n[4] 清理: 测试配置已删除")

    print("\n" + "=" * 50)
    print("全部测试通过！")
    print("=" * 50)


if __name__ == "__main__":
    main()
