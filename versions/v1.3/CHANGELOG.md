# v1.3.0 — 2026-07-13

## 新增功能

### Claude 未安装检查 (P3-4)
- 点击浮窗时先检查 `claude` 是否在系统 PATH 中
- 未安装时弹出系统对话框提示安装命令：`npm install -g @anthropic-ai/claude-code`
- 使用 `shutil.which("claude")` 检测

### Claude 运行中指示灯 (P4-4)
- 左下角绿色圆点指示器 — Claude Code 进程运行时亮起
- 每 3 秒通过 `tasklist` 检测 `claude.exe` 进程
- 状态变化时自动重绘，零性能开销

### 绘制性能优化 (P4-2)
- 预缓存 7 个渐变对象（radial/diag/border/hl/inner/spec）+ QPainterPath + 缩放后图标
- `paintEvent` 从每帧创建 ~10 个对象 → 全部复用缓存，大幅减少内存分配
- 尺寸变化时（`set_widget_size_prop`）自动重建缓存

### 退出清理 (P4-5)
- 程序退出时自动 `taskkill /f /im claude.exe` 清理孤儿 Claude 进程
- 新增配置项 `cleanup_on_quit` (bool, 默认 true)
- 使用 `app.aboutToQuit` 信号触发

## 改进
- 添加 `import shutil` 和 `from ctypes import wintypes`
- `VERSION` 常量更新为 "1.3.0"
- crash log 中包含 VERSION 信息
- 设置对话框标题下方显示版本号 `v1.3.0`
- 安装器版本号从 `VERSION` 文件动态读取（不再硬编码）
- Inno Setup `setup.iss` 版本号更新为 1.3
- `build_setup_exe.py` 自动包含 `VERSION` 文件到安装包
- 每个版本 `dist/` 包含 debug 版 exe

## 配置新增
- `cleanup_on_quit` (bool, 默认 true)

## 构建产物
- `ClaudeFloat.exe` — 53 MB
- `ClaudeFloat_debug.exe` — 53 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — 63 MB

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | +shutil 导入、shutil.which 检查、缓存系统、进程检测、退出清理 |
| `config.json` | +cleanup_on_quit |
| 其他 | 无变更 |
