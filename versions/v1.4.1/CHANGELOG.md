# v1.4.1 — 2026-07-14

## Bug 修复

### 设置对话框拖拽后子控件无响应 (Critical)

**根因 #1 — `super()` 调用触发 `DefWindowProc` 接管**
- 移除 `SettingsDialog.mousePressEvent`、`mouseMoveEvent`、`mouseReleaseEvent` 中的 `super()` 调用
- 原因：frameless 窗口的 `QWidget::mousePressEvent` 调用 `event.ignore()`，导致 Windows `DefWindowProc` 接管鼠标事件为 `SC_MOVE`。系统级移动与 Qt 应用级 `move()` 冲突，破坏了 layered window 的 `WM_NCHITTEST` 状态，后续所有鼠标点击被错误路由为 `WM_NCLBUTTONDOWN` / `HTCAPTION`，子控件无法收到事件

**根因 #2 — `setFixedSize(420, 680)` 高度不足以容纳全部内容**
- Windows 实际需要 910px 才能完整显示所有控件（`QWindowsWindow::setGeometry: Unable to set geometry 420x680... Resulting geometry: 420x910`）
- `setFixedSize` 锁死 min=max=680 与 Windows 强制 910 冲突，拖拽时 `setGeometry` 失败，窗口状态损坏
- 修复：高度恢复为 800px（与 v1.4.0 实际代码一致，v1.4.0 CHANGELOG 中 "420×680" 为文档错误）

**附加修复：**
- 参照 `FloatingWidget`（~line 1459-1483）的实现，完全不调用 `super()`。拖动由 Qt `move()` 在应用层完成
- 在 `__init__` 中初始化 `_dragging = False`、`_drag_start = QPoint()`、`_window_origin = QPoint()`，移除 `hasattr` 临时方案
- 添加 4px 曼哈顿距离拖动阈值（与 `FloatingWidget.CLICK_THRESHOLD` 一致）
- 鼠标事件添加 debug 日志（`[设置] mousePress/drag start/mouseRelease`）

### `cleanup_on_quit` 默认值统一为 `False`
- `_main()` 中的 `config.get("cleanup_on_quit", True)` 修正为 `config.get("cleanup_on_quit", False)`
- `load_config()` 默认值（line 186）和 `SettingsDialog` 复选框（line 649）已经使用 `False`，只有 `_main()` 的 fallback 不一致
- 行为不变（`load_config()` 始终提供该键，fallback 为死代码），但代码一致性提升
- 更新注释以明确"默认不清理"行为

## 关于 v1.3.0 CHANGELOG 中 cleanup_on_quit 默认值的说明
v1.3.0 CHANGELOG 记载 `cleanup_on_quit` 默认值为 `true`，但这与 `load_config()` 中实际的默认值 `False` 不一致。自 v1.3.0 发布以来，`load_config()` 始终提供该键且默认值为 `False`，因此实际行为从未为 `true`。v1.4.1 统一所有 fallback 为 `False`，使之与代码行为一致。历史文档不作修改。

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | 设置对话框拖拽修复（3 个鼠标事件处理器重写 + __init__ 初始化）+ cleanup_on_quit fallback 修正 |
| `VERSION` | 1.4.0 → 1.4.1 |
| `VERSIONING.md` | 更新当前版本 |
| `config.json` | 无变更 |

## 构建产物
- `ClaudeFloat.exe` — ~53 MB
- `ClaudeFloat_debug.exe` — ~53 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — ~63 MB
