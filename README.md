# Deepseek 用量监控

一款运行在 macOS 上的桌面悬浮窗应用，实时监控 Deepseek 开放平台账号余额和 Codex 本机使用率快照。

## 功能

- 实时显示 Deepseek 账号余额（每 5 分钟自动刷新，支持手动刷新）
- 读取 Codex 本机 `rate_limits` 快照，显示剩余百分比
- 单灯状态提示：绿色（充足）、黄色（偏低）、红色（不足）
- 今日消费、本周消费金额推算
- 悬浮窗置顶/隐藏控制
- 全局快捷键快速显示/隐藏
- 状态栏可设置只显示 Deepseek、只显示 Codex、同时显示或交替显示

## 安装

### 普通用户

1. 下载 `DeepseekMonitor_v2.0.0.dmg`
2. 双击打开安装镜像
3. 将 `Deepseek 用量监控.app` 拖到 `Applications` 文件夹
4. 在「应用程序」中双击运行

### 开发者重新打包

1. 打开终端，运行打包脚本：
   ```bash
   cd ~/Desktop/Deepseek用量监控
   python3 build_app.py
   ```
2. 将生成的 `Deepseek 用量监控.app` 拖到 `Applications` 文件夹
3. 双击运行

## 获取 API Key

1. 打开 https://platform.deepseek.com ，注册或登录
2. 左侧菜单点击「API Keys」
3. 点击「创建 API Key」，输入名称后确认
4. **立即复制保存**（格式为 `sk-xxxxxxxxxxxxxxxx`，平台不会再次显示）

## 使用

### 首次启动
1. 输入你的 Deepseek API Key（`sk-` 开头），或勾选「启用 Codex 本机余量监控」
2. 至少绑定或启用一个服务
3. 点击「绑定」

### 日常使用
- 悬浮窗会自动显示 Deepseek 余额和/或 Codex 剩余百分比
- 点击「刷新」立即更新数据
- 点击「—」隐藏窗口
- 快捷键 `Cmd + Shift + D` 快速显示/隐藏（需要先安装 pynput）

### 状态灯说明

| 灯色 | 含义 |
|------|---------|------|
| 绿灯 | 余量充足 |
| 黄灯 | 余量偏低，建议关注 |
| 红灯 | 余量不足，请尽快处理 |
| 灰灯 | 未绑定、未知或获取失败 |

## 账号管理

点击悬浮窗「账号设置」可以：
- 查看当前绑定的 API Key
- 更换 API Key
- 解绑账号
- 启用或停用 Codex 本机余量监控

## Codex 监控说明

Codex 监控读取本机 Codex 客户端写入的 `rate_limits` 快照，不读取或复用用户 token。

如果界面显示「暂无快照」，请先打开 Codex 并完成一次操作，然后回到本应用点击「刷新」。

## 常见问题

**Q: 提示"刷新失败，请检查网络"？**
A: 检查网络连接，确认能访问 https://api.deepseek.com

**Q: 消费数据显示为 ¥0.00？**
A: 首次启动时没有历史数据，刷新几次后会自动追踪计算

**Q: 快捷键不生效？**
A: 需要安装 pynput（`pip3 install pynput`）并在系统设置中授予终端或应用的「辅助功能」权限

## 数据存储

配置和余额历史存储在：
```
~/Library/Application Support/DeepseekMonitor/
```
