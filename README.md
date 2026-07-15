# ClaudeFloat — Claude Code 桌面悬浮启动器

[![Version](https://img.shields.io/badge/version-1.5.0-blue)](VERSION)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey)]()

一个精致的 Windows 桌面悬浮按钮，一键启动 [Claude Code](https://claude.ai/code)。iOS 风格毛玻璃外观，支持亮色/暗色双主题。

<p align="center">
  <img src="../资源素材/claude_icon.png" alt="ClaudeFloat Icon" width="128">
</p>

## ✨ 功能特性

- 🎨 **iOS 风格毛玻璃** — 7 层渐变绘制，亮色/暗色双主题
- 🖱️ **自由拖拽** — 任意位置拖放，带按压缩放和涟漪动画
- 📌 **边缘吸附** — 拖到屏幕边缘自动贴边，支持自动隐藏
- 🌓 **即时换肤** — 设置对话框中一键切换，无需重启
- ⚡ **一键启动** — 点击浮窗启动 Claude Code，支持普通/跳过权限两种模式
- 🔔 **系统托盘** — 最小化到托盘，右键菜单快速操作
- 🟢 **状态指示** — 绿色指示灯显示 Claude Code 运行状态
- 🚀 **开机自启** — 可选注册到 Windows 启动文件夹
- 💾 **配置持久化** — JSON 配置文件，`%APPDATA%/ClaudeFloat/`

## 📸 截图

> 启动后桌面出现 52×52px 毛玻璃圆角浮窗，悬停放大至 108%，点击启动 Claude Code。右键浮窗或系统托盘图标打开设置。

## 📦 安装方式

### 方式一：安装包（推荐）

下载最新 [Release](https://github.com/GinyvaXu/ClaudeFloat/releases) 中的 `ClaudeFloat_Setup.exe`，双击运行安装向导。

### 方式二：便携版

下载 `ClaudeFloat.exe`，放到任意目录直接运行。配置自动保存在 `%APPDATA%/ClaudeFloat/`。

### 方式三：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/GinyvaXu/ClaudeFloat.git
cd ClaudeFloat

# 2. 安装依赖
pip install PyQt5 pywin32

# 3. 运行
python claude_floating_launcher.py
```

### 前置依赖

- **Claude Code CLI** — 浮窗仅负责启动，CLI 需单独安装：
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- **Windows Terminal**（推荐）— 提供最佳终端体验，非必需

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Alt+C` | 显示/隐藏浮窗 |
| 双击托盘图标 | 显示浮窗 |
| 右键浮窗 | 打开设置菜单 |

## 🔧 构建

```bash
# 构建主程序（无控制台窗口）
python build_exe.py

# 构建调试版（带控制台输出）
python build_debug.py

# 构建安装包
python build_setup_exe.py
```

构建产物在 `dist/` 目录下，约 52–63 MB（已排除 Qt WebEngine/Multimedia 等未用模块）。

## 📁 项目结构

```
浮窗工具/
├── claude_floating_launcher.py    # 主程序（~1900 行单文件）
├── config.json                    # 默认配置
├── VERSION                        # 版本号
├── VERSIONING.md                  # 版本管理规范
├── build_exe.py                   # PyInstaller 构建脚本
├── build_debug.py                 # 调试版构建脚本
├── build_setup_exe.py             # 安装包构建脚本
├── installer/                     # 安装器源码
│   ├── setup_wizard_tk.py         # tkinter 安装向导
│   └── setup.iss                  # Inno Setup 配置
├── versions/                      # 历史版本归档
└── dist/                          # 构建产物（gitignored）
```

## 🛡️ 安全

- ✅ 无硬编码 API 密钥或凭据
- ✅ 配置存储于 `%APPDATA%`（非脚本目录）
- ✅ PowerShell 使用环境变量传参（防注入）
- ✅ 不使用 `eval`/`exec`/`pickle`
- 详见 [安全审查报告](审查报告_v1.0.md)

## 📄 许可证

本项目基于 [MIT License](LICENSE) 发布。

## 🙏 致谢

- [Claude Code](https://claude.ai/code) — Anthropic 的 AI 编程助手
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) — Python Qt 绑定
- [PyInstaller](https://pyinstaller.org/) — Python 打包工具

---

> 🤖 本项目由 [Claude Code](https://claude.ai/code) 辅助开发，包括代码生成、UI 设计审查、安全审计和文档撰写。
