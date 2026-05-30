# V1.0.0 缓存命中率设计稿

## 目标

在现有 `V1.0.0` 基础上，为 `Codex` 和 `Deepseek` 增加“缓存命中率”展示能力，并在悬浮窗中清晰呈现当天累计结果。

## 设计原则

1. 先保证数据来源真实可验证，不使用猜测值。
2. 缓存命中率只针对输入 token 计算，不使用 `total_tokens` 做分母。
3. 若某服务无法获取可靠数据，界面显示占位值 `--%`，不伪造结果。
4. 两个服务的采集方式可以不同，但对外展示格式保持一致。

## 方案总览

### Codex

- 数据来源：本机 `~/.codex/sessions/**/*.jsonl`
- 采集方式：后台定时扫描本地 JSONL 日志
- 统计粒度：按天累计
- 核心字段：
  - `info.total_token_usage.input_tokens`
  - `info.total_token_usage.cached_input_tokens`
  - `info.last_token_usage.input_tokens`
  - `info.last_token_usage.cached_input_tokens`
- 推荐显示：
  - `Cache 78%`
  - `今日缓存命中率 78.4%`

### Deepseek

- 数据来源：API 响应 `usage`
- 核心字段：
  - `usage.prompt_tokens`
  - `usage.prompt_cache_hit_tokens`
  - `usage.prompt_cache_miss_tokens`
  - `usage.completion_tokens`
  - `usage.total_tokens`
- 推荐采集方式：
  - 优先方案：应用内统一请求封装，读取响应后写入本地 SQLite
  - 兼容方案：本地代理 `127.0.0.1:xxxx` 转发请求并记录响应
- 推荐显示：
  - `Deepseek Cache 75%`
  - `今日缓存命中率 75.0%`

## Codex 方案细节

### 数据来源判断

已完成技术验证，Codex 本地 JSONL 的 `token_count` 事件里存在输入和缓存输入统计字段，可用于当天聚合：

- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `reasoning_output_tokens`
- `total_tokens`

### 计算逻辑

```text
今日缓存命中率 = 今日 cached_input_tokens / 今日 input_tokens × 100%
```

注意：

- 只计算输入 token
- 分母为 0 时显示 `--%`
- 低于缓存阈值的请求仍然按 0 统计，不额外修正

### 采集策略

- 后台每 30 秒或 1 分钟扫描一次 `~/.codex/sessions/`
- 采用增量扫描，记录上次扫描时间或最后处理文件位置
- 按自然日累计今日数据
- 若当天没有新记录，则沿用上一次已知状态，但更新时间要单独显示

### 风险

- JSONL 字段结构可能随 Codex 客户端版本变化
- 本地快照不是实时接口，存在轻微延迟
- 需要避免重复累计同一条事件

## Deepseek 方案细节

### 数据来源判断

Deepseek 的 `usage` 响应可用于计算缓存命中率，口径如下：

- `prompt_tokens = prompt_cache_hit_tokens + prompt_cache_miss_tokens`
- `prompt_cache_hit_tokens / prompt_tokens × 100%`

### 推荐采集方式

#### 方案 A: 应用内请求封装

适用场景：

- Deepseek 请求由本应用直接发出
- 统计目标主要是本应用自己的调用流量

做法：

1. 所有 Deepseek 请求统一走一个封装函数
2. 在拿到响应后读取 `usage`
3. 将明细写入本地 SQLite
4. 悬浮窗按天汇总展示

优点：

- 实现简单
- 风险低
- 不需要额外代理进程

缺点：

- 只能统计走本应用发起的请求

#### 方案 B: 本地代理

适用场景：

- 需要统计多个 AI Coding 工具或多个客户端的 Deepseek 流量
- 希望统一拦截所有请求

做法：

1. 本地启动 HTTP 代理 `127.0.0.1:xxxx`
2. 客户端配置走该代理
3. 代理仅转发请求，不修改请求体和响应体
4. 代理读取 response `usage` 后写入 SQLite

优点：

- 可以覆盖多个客户端
- 适合做统一统计

缺点：

- 需要处理代理、HTTPS、流式响应和失败重试
- 运维复杂度高于应用内封装

### 计算逻辑

```text
今日缓存命中率 = 今日 prompt_cache_hit_tokens / 今日 prompt_tokens × 100%
```

附加显示可选项：

- 今日输入
- 今日缓存命中
- 今日未命中
- 今日命中率

### SQLite 建议字段

```text
date
provider
model
project
prompt_tokens
prompt_cache_hit_tokens
prompt_cache_miss_tokens
completion_tokens
total_tokens
cost
created_at
```

说明：

- `project` 为可选扩展字段，若上游没有就置空
- `cost` 可作为后续扩展，不影响命中率核心功能

### 风险

- 如果请求流不经过本应用或代理，就不会被统计
- 流式响应需要等待最终 usage 才能落库
- 不同客户端版本的 usage 结构可能不同

## 悬浮窗展示建议

### Deepseek 卡片

- 标题行：服务图标 + `Deepseek`
- 主值：余额
- 第二行：今日消费 / 本周消费
- 新增行：`今日缓存命中率 xx%`
- 可选行：`今日输入 / 今日缓存命中`

### Codex 卡片

- 标题行：服务图标 + `Codex`
- 主值：剩余百分比
- 第二行：5 小时窗口 / 7 天窗口 / 下次重置
- 新增行：`今日缓存命中率 xx%`
- 可选行：`今日输入 / 今日缓存命中`

### 空值表现

- 数据缺失时显示 `--%`
- 未绑定时显示灰态
- 获取失败时保留最后一次有效值，并标注更新时间

## 刷新策略

- Codex：本地 JSONL 增量扫描，每 30 秒或 1 分钟
- Deepseek：按请求发生时写库，悬浮窗读取当天聚合结果
- 悬浮窗刷新只负责展示层重算，不直接承担所有原始数据采集

## 实施顺序建议

1. 先完成 Deepseek 数据源方案确认
2. 再完成 Codex 与 Deepseek 的统一数据模型
3. 最后做悬浮窗展示和设置项

## 暂不做的事

- 不把未验证的缓存字段写成正式展示文案
- 不把缓存命中率当作实时精确值承诺
- 不在没有数据源确认前直接改主界面 UI

## 结论

`Codex` 和 `Deepseek` 的缓存命中率都可以做，但采集路径不同：

- `Codex` 适合本地 JSONL 聚合
- `Deepseek` 更适合请求封装或本地代理落库

等你审核通过后，再进入实现阶段。
