# 分阶段执行步骤

## 第 0 阶段：项目初始化

**目标**：搭建项目骨架，让开发规范化、可追踪。

1. 创建 `docs/` 文件夹，编写 5 份标准文档
2. 创建 `logs/` 文件夹，建立开发日志模板
3. 创建 `CLAUDE.md`，写入项目指引
4. 创建 `src/` 文件夹
5. 编写 `src/constants.py`（颜色、阈值、API 地址等常量）

**验证**：项目结构完整，所有文档齐全

---

## 第 1 阶段：数据层

**目标**：打通数据通路，能成功调用 Deepseek API。

1. 编写 `src/storage.py`
   - `save_api_key(key)` — base64 编码后存入 JSON
   - `load_api_key()` — 读取并解码
   - `clear_api_key()` — 删除配置
   - `config_exists()` — 检查是否已绑定
2. 编写 `src/api.py`
   - `fetch_balance(api_key)` — 调用 /user/balance
   - `fetch_usage(api_key, start_date, end_date)` — 调用 /v1/usage
   - 返回结构化数据（dict）
   - 处理网络异常、API 错误响应
3. 命令行测试：用真实 API Key 验证

**验证**：用真实 API Key 测试，确认能正确返回余额和用量数据

---

## 第 2 阶段：UI 组件

**目标**：逐个实现 UI 组件，每个组件独立可测。

1. `src/traffic_light.py` — TrafficLight 类
   - 继承 `tk.Canvas`
   - `set_status(balance)` 方法：根据余额更新灯色
2. `src/ui_bind.py` — BindWindow 类
   - 继承 `tk.Toplevel`
   - API Key 输入框 + 绑定按钮 + 帮助链接
   - 输入验证（非空、格式检查）
3. `src/ui_settings.py` — SettingsWindow 类
   - 继承 `tk.Toplevel`
   - 显示当前 Key（部分隐藏）
   - 解绑按钮（二次确认）+ 换绑按钮
4. `src/ui_main.py` — MonitorWindow 类
   - 继承 `tk.Tk`
   - 集成标题栏、信号灯、余额、用量、刷新、设置
   - 窗口拖动逻辑
   - Pin/隐藏/关闭按钮

**验证**：每个 UI 窗口能独立打开、交互正确

---

## 第 3 阶段：主流程串联

**目标**：将所有组件串联成完整的应用流程。

1. `src/hotkey.py`
   - 使用 pynput 监听 `Cmd+Shift+D`
   - 回调函数中调用窗口显隐切换
2. `src/main.py`
   - 检测是否已绑定 → 显示绑定窗口或悬浮窗
   - 5 分钟自动刷新定时器
   - 手动刷新重置计时器
   - 单实例检测：通过临时文件标记 PID
   - 重复启动时恢复已有窗口

**验证**：完整流程可用

---

## 第 4 阶段：打包与文档

**目标**：交付用户可直接使用的 .app。

1. `build_app.py` — 打包脚本
2. `README.md` — 用户使用说明
3. 全流程测试

**验证**：双击 .app 正常运行
