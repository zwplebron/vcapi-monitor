# Deepseek API 参考文档

## 基础信息

- **Base URL**: `https://api.deepseek.com`
- **认证方式**: HTTP Header `Authorization: Bearer <API_KEY>`
- **Content-Type**: `application/json`

## 获取 API Key

1. 登录 [Deepseek 开放平台](https://platform.deepseek.com)
2. 进入「API Keys」页面
3. 点击「创建 API Key」
4. 复制生成的 Key（格式：`sk-xxxxxxxxxxxxxxxx`）
5. 妥善保管，平台不会再次显示完整 Key

---

## 接口 1：查询余额

### 请求

```
GET /user/balance
```

### 请求头

```
Authorization: Bearer <API_KEY>
Accept: application/json
```

### 响应示例

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "110.00",
      "granted_balance": "10.00",
      "topped_up_balance": "100.00"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| is_available | boolean | 余额是否可用 |
| balance_infos[].currency | string | 币种（CNY/USD） |
| balance_infos[].total_balance | string | 总余额（字符串形式的数字） |
| balance_infos[].granted_balance | string | 赠送余额 |
| balance_infos[].topped_up_balance | string | 充值余额 |

### 程序中的使用

我们取 `balance_infos[0].total_balance` 作为"剩余金额"，转换为 float 后与阈值比较，确定指示灯颜色。

---

## 接口 2：查询用量（不可用）

Deepseek 公有云 API **没有公开的用量查询接口**。`/v1/usage`、`/usage`、`/user/usage` 均返回 404。

程序改用**余额追踪法**推算消费：

1. 每次刷新时记录当前余额到 `balance_log.json`
2. 每日首次刷新时记录"今日起始余额"
3. **今日消费 = 今日起始余额 - 当前余额**
4. **本周消费 = 本周每日消费之和**

此方法无需额外 API，完全基于余额变化推算，数据更实时可靠。

---

## 日期计算

### 本日

```python
today = datetime.now().strftime("%Y-%m-%d")
# start_date = today, end_date = today
```

### 本周

```python
today = datetime.now()
monday = today - timedelta(days=today.weekday())
# start_date = monday.strftime("%Y-%m-%d"), end_date = today.strftime("%Y-%m-%d")
```

---

## 错误处理

| HTTP 状态码 | 含义 | 程序处理 |
|-------------|------|----------|
| 200 | 成功 | 正常解析 |
| 401 | API Key 无效 | 提示"API Key 无效" |
| 429 | 请求频率过高 | 等待后重试 |
| 500 | 服务器错误 | 提示"服务器错误，稍后重试" |
| 网络超时 | 无法连接 | 提示"网络连接失败" |
