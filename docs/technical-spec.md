# 技术选型与架构说明

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 语言 | Python 3.9.6 | macOS 自带，无需安装 |
| GUI 框架 | tkinter | Python 标准库自带 |
| HTTP 请求 | urllib.request | Python 标准库自带 |
| JSON 解析 | json | Python 标准库自带 |
| 全局快捷键 | pynput | 唯一的外部依赖（打包后用户无感） |
| 配置存储 | JSON 文件 | 存于 ~/Library/Application Support/DeepseekMonitor/ |
| 打包工具 | py2app / 手动 .app bundle | 生成 macOS 原生应用 |

## 选择 Python + tkinter 的原因

1. **零依赖**：Python 3.9 和 tkinter 均随 macOS 预装，用户无需安装任何东西
2. **稳定性**：Python 标准库经过充分测试，向后兼容性好
3. **打包简单**：可以通过 py2app 或手动创建 .app bundle 打包为独立应用
4. **足够胜任**：悬浮窗应用不需要复杂的 UI 能力，tkinter 完全满足

## 架构设计

```
┌─────────────────────────────────────┐
│            main.py (入口)            │
│  启动判断 → 绑定窗口 OR 悬浮窗       │
│  定时器管理 / 单实例检测             │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐  ┌────▼────┐
│ API 层  │  │  UI 层   │
│ api.py  │  │ ui_main  │
│ storage │  │ ui_bind  │
│         │  │ ui_setting│
│         │  │ traffic_  │
│         │  │ light     │
└────────┘  └────┬─────┘
                 │
          ┌──────▼──────┐
          │  hotkey.py   │
          │  全局快捷键   │
          └─────────────┘
```

## 数据流

```
用户操作 → UI 层触发 → API 层请求 → Deepseek API
                                    ↓
UI 层更新 ← 数据解析 ← API 层接收 ← JSON 响应
```

## 关键模块

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| api.py | 封装 Deepseek API 调用 | api_key, 日期范围 | 余额/用量数据 |
| storage.py | 配置读写 | api_key | 无 |
| ui_main.py | 悬浮窗主界面 | 余额/用量数据 | 用户操作事件 |
| ui_bind.py | 首次绑定窗口 | 无 | api_key |
| ui_settings.py | 账号设置窗口 | 当前配置 | 解绑/换绑操作 |
| traffic_light.py | 信号灯组件 | 余额数值 | Canvas 绘制 |
| hotkey.py | 全局快捷键 | 键盘事件 | 显隐切换 |
| main.py | 应用入口 | 无 | 启动应用 |
