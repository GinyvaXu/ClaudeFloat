# v1.2.0 — 2026-07-13

## 新功能

### 边缘吸附 + 自动隐藏 (P2-1)
- 拖拽浮窗到屏幕边缘（<25px 阈值）自动吸附贴边
- 支持左/右/上/下四个方向
- 自动隐藏模式：鼠标离开后滑出屏幕（仅留 6px 可见），靠近边缘时平滑滑回
- 滑动动画 180ms InOutCubic 曲线
- 透明 HoverDetector 子类窗口检测鼠标靠近（3px 细条沿屏幕边缘）
- 设置面板：吸附开关 + 自动隐藏开关

### 全局快捷键 Ctrl+Alt+C (P2-3)
- `RegisterHotKey` 注册系统级全局热键
- 按下 Ctrl+Alt+C 切换浮窗显示/隐藏
- 程序退出时自动注销热键
- 系统托盘提示更新为 "Claude Code 浮窗 — 点击启动 | Ctrl+Alt+C 显示/隐藏"

### Hover 检测优化 (P2-2)
- `hideEvent`/`showEvent` 控制 hover timer 启停 — 隐藏到托盘时停止 100ms 轮询，节省电量
- 吸附模式下自动管理显示/隐藏与 hover 状态联动

### EXE 构建优化 (P2-4)
- `build_exe.py` / `build_setup_exe.py`: 添加 30+ 未使用 Qt 模块的 `--exclude-module` 排除列表
- 新增 `build_debug.py` 调试构建脚本（带控制台窗口）

### 安装机制统一 (P2-5)
- 移除冗余文件：`install.py`、`install_startup.py`、`启动浮窗.bat`、`启动浮窗.vbs`、`installer/setup_wizard.py`
- 保留统一安装器：`installer/setup_wizard_tk.py` (tkinter GUI)
- 保留 `installer/setup.iss` 用于可选 Inno Setup 构建

## Bug 修复

### v1.2.0 初版修复
- **启动崩溃 (Critical)**: `_restore_position()` 中 `edge` 变量在 `if snap_enabled` 块内定义但块外引用，`snap_enabled=False` 时触发 `NameError`。修复：将 `edge` 定义移到 `if` 之前。
- **自动滑出失效**: `detector.enterEvent = lambda` 猴子补丁对 PyQt5 C++ 虚函数无效。修复：创建 `HoverDetector(QWidget)` 子类，正确重写 `enterEvent`。

### v1.2.0 第二版修复
- **启动崩溃 (Critical)**: `nativeEvent` 中 `message` 参数是 `sip.voidptr` 指针，直接用 `.message` 访问触发 `AttributeError`。修复：用 `ctypes` 定义 `MSG` 结构体，通过 `MSG.from_address(int(message))` 解析 Windows 消息。

### 其他修复
- `QPropertyAnimation` 属性定义顺序问题（`press_scale` 和 `widget_size_prop` 警告）—— 无害，不影响功能

## 配置新增
- `snap_enabled` (bool, 默认 true) — 启用边缘吸附
- `snap_hidden` (bool, 默认 true) — 启用自动隐藏
- `hide_delay_ms` (int, 默认 800) — 鼠标离开后延迟隐藏毫秒数
- `VERSION` 常量 — "1.2.0"

## 崩溃日志
- `main()` 函数包裹 try/except，异常时写入 `%USERPROFILE%\Desktop\ClaudeFloat_crash.log`

## 构建产物
- `ClaudeFloat.exe` (release) — 53 MB
- `ClaudeFloat_debug.exe` (debug, console) — 53 MB
- `ClaudeFloat_Setup.exe` (installer) — 63 MB

## 文件变更
| 文件 | 状态 |
|------|------|
| `claude_floating_launcher.py` | 重写（吸附系统、快捷键、hover优化、崩溃修复） |
| `build_exe.py` | 修改（Qt 模块排除） |
| `build_setup_exe.py` | 修改（移除冗余引用、Qt 模块排除） |
| `build_debug.py` | 新增（调试构建） |
| `launcher_config.json` → `config.json` | 重命名 |
| `installer/setup_wizard_tk.py` | 无变更（来自 v1.1） |
| `installer/install.py` | 删除 |
| `installer/setup_wizard.py` | 删除 |
| `install_startup.py` | 删除 |
| `启动浮窗.bat` | 删除 |
| `启动浮窗.vbs` | 删除 |
| `launcher.vbs` | 删除（生成文件） |
