# Deepseek 用量监控 — AI 助手指引

## 项目简介

这是一个运行在 macOS 上的桌面悬浮窗应用，用于实时监控 Deepseek 开放平台账号的用量数据（余额、本日/本周消费金额和 Tokens）。目标用户是不懂代码的普通用户，最终交付物是双击即可运行的 `.app` 程序。

## 核心理念

- **分阶段小步推进**：每次只实现一个阶段，验证通过后再进入下一阶段
- **零依赖优先**：尽量使用 Python 标准库（tkinter, urllib, json），唯一外部依赖是 pynput（全局快捷键）
- **每天记录日志**：每次开发会话结束后，更新 `logs/YYYY-MM-DD.md`

## 标准文档路径

所有开发规范和设计决策均有文档记录，开发前应先查阅：

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求规格说明 | [docs/requirements.md](docs/requirements.md) | 功能需求、非功能需求、界面风格 |
| 技术选型与架构 | [docs/technical-spec.md](docs/technical-spec.md) | 技术栈、架构图、数据流、模块职责 |
| UI 设计规范 | [docs/design-spec.md](docs/design-spec.md) | 颜色、字体、尺寸、间距、按钮样式 |
| 分阶段执行步骤 | [docs/implementation-steps.md](docs/implementation-steps.md) | 每阶段具体任务清单 |
| API 参考文档 | [docs/api-reference.md](docs/api-reference.md) | Deepseek API 接口详情、错误处理 |
| 全局常量定义 | [src/constants.py](src/constants.py) | 颜色值、阈值、API 地址、窗口尺寸 |

## 开发工作流

### 开始新阶段

1. 阅读 [docs/implementation-steps.md](docs/implementation-steps.md) 确认当前阶段
2. 阅读相关设计文档了解规范
3. 更新 todo list，标记当前阶段为 in_progress
4. 逐个完成阶段内的任务

### 开发规范

- **代码风格**：简洁优先，函数短小，单一职责
- **注释**：仅在最必要的地方写注释（WHY，不是 WHAT）。代码本身应该是自解释的
- **命名**：函数用 `snake_case`，类用 `PascalCase`，常量用 `UPPER_CASE`
- **错误处理**：仅在系统边界（网络请求、文件 IO、用户输入）处理错误，内部逻辑不需要防御式编程
- **不引入新依赖**：除非绝对必要，使用 Python 标准库
- **编辑优先于重写**：修改现有文件时用精确的 Edit 操作，不要重写整个文件

### 每个阶段完成后

1. 验证阶段目标全部达成
2. 更新 `logs/YYYY-MM-DD.md` 记录完成情况
3. 更新 todo list 状态

### 会话结束时

1. 更新当天的开发日志（`logs/YYYY-MM-DD.md`）
2. 日志格式：今日完成 / 遇到的问题 / 明日计划 / 当前状态

## 当前开发状态

| 阶段 | 状态 |
|------|------|
| 第 0 阶段：项目初始化 | 已完成 |
| 第 1 阶段：数据层 | 已完成 |
| 第 2 阶段：UI 组件 | 已完成 |
| 第 3 阶段：主流程串联 | 已完成 |
| 第 4 阶段：打包与文档 | 已完成 |

## 项目文件结构

```
Deepseek用量监控/
├── CLAUDE.md                        # 本文件
├── docs/                            # 项目标准文档
│   ├── requirements.md
│   ├── technical-spec.md
│   ├── design-spec.md
│   ├── implementation-steps.md
│   └── api-reference.md
├── logs/                            # 开发日志
│   └── YYYY-MM-DD.md
├── src/                             # 源代码
│   ├── constants.py                 ✅
│   ├── storage.py                   ✅
│   ├── api.py                       ✅
│   ├── traffic_light.py             ✅
│   ├── ui_bind.py                   ✅
│   ├── ui_settings.py               ✅
│   ├── ui_main.py                   ✅
│   ├── hotkey.py                    ✅
│   └── main.py                      ✅
├── build_app.py                     ✅
├── test_api.py                      ✅
└── README.md                        ✅
```
