"""
全局快捷键模块

监听 Cmd+Shift+D 组合键，控制悬浮窗显示/隐藏。
依赖 pynput 库。首次运行时 macOS 会提示授予辅助功能权限。
"""


class GlobalHotkey:
    """全局快捷键监听器"""

    def __init__(self, toggle_callback):
        self._callback = toggle_callback
        self._listener = None
        self._keys_pressed = set()
        self._running = False

    def start(self):
        """启动快捷键监听（后台线程）"""
        from pynput import keyboard  # 延迟导入，避免缺少依赖时崩溃

        if self._running:
            return
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """停止监听"""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        from pynput import keyboard
        self._keys_pressed.add(key)
        if (keyboard.Key.cmd in self._keys_pressed and
                keyboard.Key.shift in self._keys_pressed and
                keyboard.KeyCode.from_char('d') in self._keys_pressed):
            self._callback()

    def _on_release(self, key):
        self._keys_pressed.discard(key)
