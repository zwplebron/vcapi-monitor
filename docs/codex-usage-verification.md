# Codex 额度自动获取技术验证

## 验证目标

确认 V2.0.0 是否可以自动获取 ChatGPT Codex 余量，并判断可展示的数据字段。

## 官方资料结论

- Codex 使用量计入 ChatGPT 账号的 agentic usage limit。
- Codex 的可购买/可消耗单位是 credits。
- Plus / Pro 用户在达到套餐内限制后，可使用或购买 credits。
- 官方说明中，用户可以在 `Codex Settings > Usage Dashboard` 查看 credits balance 和 recent usage。
- 官方资料没有说明面向普通桌面应用的公开“Codex 余额查询 API”。
- Enterprise 方向存在 Compliance API / Analytics，但这更偏企业审计与管理能力，不适合作为普通用户版桌面应用的默认方案。

参考资料：
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- https://help.openai.com/en/articles/12642688
- https://help.openai.com/en/articles/20001106-codex-rate-card
- https://developers.openai.com/codex/pricing

## 本机验证结果

### 1. Codex 本地认证文件

本机存在 `~/.codex/auth.json`。

已验证字段结构，但未输出 token 值：

- `auth_mode`
- `OPENAI_API_KEY`
- `tokens`
- `last_refresh`

其中 `tokens` 内包含：

- `id_token`
- `access_token`
- `refresh_token`
- `account_id`

结论：Codex 本地确实保存 ChatGPT 登录态，但直接读取和使用这些 token 具有安全与稳定性风险，不应在普通用户版中作为首选方案。

### 2. Codex 本地会话日志

本机 `~/.codex/sessions/**/*.jsonl` 中存在 `token_count` 事件，事件内包含 `rate_limits` 字段。

可读取到的字段包括：

- `primary.used_percent`
- `primary.window_minutes`
- `primary.resets_at`
- `secondary.used_percent`
- `secondary.window_minutes`
- `secondary.resets_at`
- `credits.has_credits`
- `credits.unlimited`
- `credits.balance`
- `plan_type`
- `rate_limit_reached_type`

本机样例结果：

- `primary.used_percent`: 可获取
- `secondary.used_percent`: 可获取
- `credits.has_credits`: 可获取
- `credits.balance`: 当前为 `null`
- `plan_type`: 当前为 `null`

结论：可以自动读取最近一次 Codex 本地使用率快照，并计算剩余百分比：

```text
primary_remaining_percent = 100 - primary.used_percent
secondary_remaining_percent = 100 - secondary.used_percent
```

但这不是实时接口，而是 Codex 运行过程中写入的本地快照。

## 可行性判断

### 可稳定支持的部分

- 自动读取 Codex 最近一次本地使用率百分比。
- 显示剩余百分比。
- 显示重置窗口信息，例如 5 小时窗口、7 天窗口。
- 显示 credits 状态：
  - 是否拥有 credits
  - 是否无限额度
  - 若本地快照存在 `credits.balance`，则显示余额

### 暂不建议承诺的部分

- 不建议承诺一定能显示 Codex credits 余额。
- 不建议通过未公开的 ChatGPT/Codex 后端接口主动查询余额。
- 不建议读取或复用用户的 refresh token 调内部接口。
- 不建议把本地会话日志方案描述为官方 API。

## V2.0.0 推荐方案

第一版 Codex 监控建议采用“本地快照读取模式”：

- 绑定方式：检测本机是否已登录 Codex。
- 数据来源：读取 `~/.codex/sessions/**/*.jsonl` 中最新 `rate_limits` 快照。
- 主要显示：剩余百分比。
- 辅助显示：credits balance（仅当本地快照存在数值时显示）。
- 状态提示：如果没有找到快照，提示“请先打开 Codex 并完成一次操作后刷新”。

界面文案建议：

- `Codex 剩余 97%`
- `5小时窗口剩余 97%`
- `7天窗口剩余 100%`
- `Credits: 未启用 / 未购买 / 暂不可用`

## 风险

- 本地日志格式属于 Codex 客户端内部实现，未来版本可能变化。
- 只有在 Codex 写入过 `rate_limits` 事件后才能读取到数据。
- 该方法不能保证获取精确 credits 余额。
- 多账号/多工作区场景下，需要确认日志中的 `account_id` 或上下文是否能区分账号。

## 结论

可以自动获取 Codex 的“使用率百分比快照”，适合满足“让用户直观看到还剩多少余量”的核心目标。

暂时不能确认存在稳定公开的 Codex credits 余额查询 API。V2.0.0 应优先以百分比显示为核心，把 credits balance 作为可选字段。
