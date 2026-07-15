# v1.4.0 — 2026-07-14

## 新增功能

### 暗色模式
- iOS 风格暗色毛玻璃配色方案：暗色玻璃背景 `#1C1C1E`、暗色边框 `#48484A`、暗色强调色 `#0A84FF`
- 浮窗主体完整适配：7 层渐变、涟漪动画、悬停微染全部跟随主题
- 设置对话框完整适配：所有控件样式（容器、按钮、滑块、复选框、输入框）动态适应主题
- 右键菜单和托盘菜单样式跟随主题
- 主题切换即时生效，无需重启
- 首次启动自动检测 Windows 系统主题（深色/浅色模式）
- 配置项 `theme`: `"light"` (默认) | `"dark"`

### 日志系统
- 使用 Python `logging` + `RotatingFileHandler`（最多 5 个文件，每个最大 1MB）
- 日志路径：`%APPDATA%\ClaudeFloat\logs\ClaudeFloat.log`
- 覆盖 15+ 关键事件：启动/退出、配置加载/迁移、Claude 检测/启动、进程状态、吸附、热键、设置变更
- 崩溃日志保留：桌面 `ClaudeFloat_crash.log` 作为最后防线
- 设置对话框底部显示日志文件路径

### 设置对话框 UI 重构
- 标准标题栏 → 无边框磨砂风格（`FramelessWindowHint` + `WA_TranslucentBackground`）
- 尺寸 400×660 → 420×680
- 新增自定义标题栏：左对齐标题 + 版本号 + ✕ 关闭按钮
- 圆角容器（16px 边框）+ 分隔线
- 支持无边框窗口拖拽移动
- 启动时自动屏幕居中
- 新增"外观主题"设置分组

## 配置新增
- `theme` (string, 默认 `"light"`) — 外观主题选择

## 构建产物
- `ClaudeFloat.exe` — ~53 MB
- `ClaudeFloat_debug.exe` — ~53 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — ~63 MB

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | +274 行（暗色主题系统、日志系统、设置对话框重构） |
| `config.json` | +theme 键 |
| `VERSIONING.md` | 更新当前版本 |
| 其他 | 无变更 |
