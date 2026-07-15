# v1.0.0 — 2026-07-12

## 首次发布

### 核心功能
- iOS 风格毛玻璃悬浮窗（7 层玻璃绘制）
- 自由拖拽 + 涟漪动画 + 按压反馈
- 点击启动 Claude Code（普通模式 / skip-permissions 模式）
- 系统托盘图标 + 右键菜单
- 设置对话框：启动方式、浮窗大小、透明度、默认工作目录
- 配置持久化 (JSON)
- 开机自启支持

### 打包
- PyInstaller onefile → ClaudeFloat.exe (~53MB)
- PyInstaller 安装向导 → ClaudeFloat_Setup.exe (~63MB)
- Inno Setup 安装脚本 (setup.iss)

### 已知问题
- PowerShell f-string 注入漏洞（7 处）
- PyInstaller 打包后配置丢失
- VBS 启动脚本指向临时目录
- 100ms 轮询持续运行（浪费电量）
- 未排除不需要的 Qt 模块（EXE 体积可缩减）
- 多显示器热插拔支持不完善
- Inno Setup 配置冲突（autopf + PrivilegesRequired=lowest）
- 高分屏 DPI 缩放未设置

详见 `审查报告_v1.0.md`（12 安全漏洞 + 28 代码缺陷）。
