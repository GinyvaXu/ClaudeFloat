# v1.4.3 — 2026-07-15

## Bug 修复

### Radio/Checkbox 字号不一致（P0 — UI 审查报告 3.2）
- **根因**：Radio 通过 QFont(11pt) 设置字号而 Checkbox CSS 中存在 `font-size: 11px`，Qt 的 pt(≈1.333px) 与 px 单位不一致导致两类控件文字大小不同（Radio ≈14.7px vs Checkbox 11px）
- **修复**：移除 Checkbox CSS 中的 `font-size: 11px`，统一使用 `setFont(self._font(11))` QFont 设置

### 字体层级混乱（P1 — UI 审查报告 3.1）
- 建立清晰的 4 级字体层级：
  - H1 页面标题: 15pt → **16pt Bold**
  - H2 模块标题: 12pt → **13pt Bold**（所有 6 个 GroupBox 统一）
  - H3 选项文字: 11pt（Radio/Checkbox，保持不变）
  - Body 辅助信息: Slider 描述标签 12pt → **9pt**，日志路径 8pt → **9pt**
- 移除死设置 `setFont(9)` 不再需要的依赖

### 缺少键盘焦点指示器（P1 — UI 审查报告 3.7）
- Radio/Checkbox: 添加 `:focus::indicator` 样式，焦点时显示 accent 色边框
- QPushButton: 添加 `:focus` 样式（accent 色边框或白色边框 + outline）
- QSlider: 添加 `:focus` 样式（移除默认 outline）
- QLineEdit: 添加 `:focus` 样式（accent 色边框）
- 提升键盘可访问性（a11y）

## UX 改进

### text_secondary 纳入 THEMES 字典（P2 — UI 审查报告 3.3）
- THEMES 新增 `TEXT_SECONDARY` 键：light=(60,60,67), dark=(235,235,245)
- `_build_styles()` 从 THEMES 读取而非硬编码，支持未来多主题扩展

### 安全警告暗色模式适配（P2 — UI 审查报告 3.6）
- THEMES 新增 `WARN_BG` / `WARN_FG` 键：
  - light: 浅红底 #FFE5E5 + 红色文字 #FF3B30
  - dark: 暗红底 #3D1F1F + 柔和红 #FF6B6B
- warn_label 改为从 `self._s["warn_label"]` 读取主题感知样式
- `_reapply_dialog_styles()` 同步 warn_label 样式刷新

## 启动修复（延续 v1.4.2 修订）
- `launch_claude_code()`: 使用 `shutil.which` 解析的完整路径替代 `"claude"` 短名
- 程序路径与参数分离为独立 list 元素，避免 Popen 引号问题
- 扩大 wt 异常捕获范围，fallback 更可靠

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | THEMES 扩展 + 字体层级重整 + :focus 样式 + warn 主题适配 + text_secondary 去硬编码 |
| `VERSION` | 1.4.2 → 1.4.3 |

## 构建产物
- `ClaudeFloat.exe` — ~52 MB
- `ClaudeFloat_debug.exe` — ~52 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — ~63 MB
