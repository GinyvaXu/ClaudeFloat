# v1.4.2 — 2026-07-15

## Bug 修复（2026-07-15 修订）

### 修复 Claude Code 无法正常启动
- **根因 1**：`shutil.which("claude")` 已解析完整路径但启动时仅用 `"claude"` 短名，依赖子进程 PATH 二次查找。在打包 exe 或系统启动场景下子进程可能继承不到完整 PATH
- **根因 2**：`cmd = "claude --dangerously-skip-permissions"` 是含空格的单字符串，在 `subprocess.Popen` list 形式下会被整体引号包裹，导致 `start` 命令将其视为程序名而非「程序+参数」
- **修复**：使用 `shutil.which` 解析的完整 `claude_path` 替代短名；将程序路径与参数分离为独立 list 元素；扩大 wt 异常捕获范围使 fallback 更可靠；`cmd start` 回退路径使用完整 claude 路径

## UX 改进

### 设置对话框去繁杂 — Tooltip 悬停提示
- 移除 4 处设置组底部的常驻描述文字，所有功能描述改为控件 `setToolTip()` 悬停提示
- 精简选项文字：Radio 仅保留模式名称（如"普通模式""跳过权限"），详细说明通过 tooltip 展示
- Checkbox 文字同步精简（如"启用边缘吸附""自动隐藏""退出时关闭 Claude Code 进程"）
- 在「跳过权限」选项旁增加 "ℹ" 信息图标，鼠标悬停即可查看详细安全说明
- 安全警告标签放入固定高度容器，选中/取消时不再导致布局跳动
- 各模块标题字号从 10pt 增大至 12pt bold，层级更清晰

### 修复 Radio/Checkbox 切换时文字跳动
- **根因**：`::indicator` 样式在 checked/unchecked 状态间切换 `border` 有无，导致指示器实际渲染尺寸变化（20px ↔ 16px），文本随之位移
- **修复**：checked 状态下使用同色边框 `border: 2px solid {accent}` 替代 `border: none`，视觉上无边框但尺寸恒定为 20×20px

### 主题即时切换（含标签颜色同步）
- 设置对话框中切换 ☀/☾ 单选按钮立刻生效，同时更新对话框自身和背后浮窗的外观
- `_label()` 方法自动追踪所有标签控件，主题切换时统一更新颜色（修复"边长""不透明度"等字样不变色问题）
- 新增 `_live_switch_theme()` 方法：即时更新配色 → 重建样式表 → 重新应用所有控件样式 → 同步浮窗
- 新增 `_reapply_dialog_styles()` 方法：遍历所有已记录控件（容器、GroupBox、Radio、Checkbox、按钮、滑块、输入框、标签）重新设置 stylesheet
- `reject()` 方法重写：取消时自动还原为打开对话框前的原始主题
- 主题 radio 按钮使用 `blockSignals` 防护避免 toggled 信号循环递归

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | 指示器样式修复 + Tooltip 系统 + label 自动追踪 + 选项文字精简 + 标题字号增大 + 即时主题切换 |
| `VERSION` | 1.4.1 → 1.4.2 |
| `VERSIONING.md` | 更新当前版本 |

## 构建产物
- `ClaudeFloat.exe` — ~53 MB
- `ClaudeFloat_debug.exe` — ~53 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — ~63 MB
