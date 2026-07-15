# v1.1.0 — 2026-07-13

## 安全修复 (P1-1 ~ P1-5)

### P1-1: 修复 PowerShell 命令注入漏洞 (CRITICAL)
- **影响文件**: `claude_floating_launcher.py`, `installer/install.py`, `installer/setup_wizard_tk.py`, `install_startup.py`
- **修复方式**: 所有 PowerShell 调用改用环境变量 (`$env:CC_*`) 传参，替代 f-string 直接拼接路径
- **原理**: 路径中的特殊字符 (`$`, `` ` ``, `"` 等) 不再经过 PowerShell 解释器解析

### P1-2: 配置迁移到 %APPDATA% (配置持久化)
- **影响文件**: `claude_floating_launcher.py`
- `CONFIG_PATH`: 打包后 → `%APPDATA%\ClaudeFloat\config.json`；开发模式 → 脚本目录 `launcher_config.json`
- 自动检测旧路径配置并迁移到新路径，迁移后删除旧文件
- `save_config()` 增加自动创建父目录

### P1-3: VBS 开机自启修复
- **影响文件**: `claude_floating_launcher.py`
- 打包为 exe 时：快捷方式直接指向 `sys.executable`（exe 自身），无需 VBS 中间层
- 开发模式：保持 VBS 方式，但使用 `sys.executable` 和正确的路径转义

### P1-4: skip-permissions 安全警告
- **影响文件**: `claude_floating_launcher.py`
- 设置界面新增红色警告标签（选中 skip-permissions 时显示）
- 保存时弹出详细的安全确认对话框（需用户确认）
- 浮窗右上角显示红色圆点指示器（skip-permissions 激活时）
- 默认启动模式改为 `"normal"`

### P1-5: Inno Setup 修复
- **影响文件**: `installer/setup.iss`
- `DefaultDirName`: `{autopf}` → `{localappdata}`，解决非管理员安装失败问题
- `AppId`: 手写占位 GUID → 真实 UUID v4 (`CB80F83A-EE67-491B-B6AF-8AFF048ECF40`)

## Bug 修复

### 启动修复
- `launch_claude_code` 第三个 fallback 添加 `CREATE_NO_WINDOW`（修复控制台窗口闪烁）
- 第二个 fallback 修正 `start` 命令语法（空标题 + 正确命令）

### 安装器修复
- `installer/install.py`: `LOCALAPPDATA` 为空时回退到 `USERPROFILE`
- `installer/install.py`: BAT 卸载脚本中 `%` 正确转义为 `%%`
- `installer/setup_wizard_tk.py`: 安装线程添加 try/except 异常处理，失败时弹错误提示
- `installer/setup_wizard_tk.py`: 移除虚假进度条，改为按实际步骤报告进度
- `installer/setup_wizard_tk.py`: 使用 `subprocess.CREATE_NO_WINDOW` 替代魔术数字 `0x08000000`
- `install_startup.py`: stdout 封装添加 try/except 保护；路径使用 `replace` 替代 `.format()` 避免花括号崩溃

## 配置改进
- 移除死键 `snap_edge`, `snap_hidden`, `bubble_size`
- 移除 `auto_start` 键（改为直接检测启动文件夹）
- 添加配置值范围校验：size [30,200], opacity [0.1,1.0]
- 默认配置：`launch_mode: "normal"`, `opacity: 0.88`

## 项目组织
- 添加 `.gitignore`（排除 `launcher.vbs`, `build/`, `dist/`, `__pycache__/`）
- 添加 `VERSION` 文件 (1.1.0)
- 添加 `VERSIONING.md` 版本管理规范
- 添加 `审查报告_v1.0.md` 综合审查报告
- 建立 `versions/` 历史版本归档目录
- 删除已生成的 `launcher.vbs`

## 已知剩余问题
- 边缘吸附/自动隐藏功能（配置键已移除，待 v1.2 实现）
- 100ms 轮询未优化（计划 v1.2 事件驱动方案）
- EXE 体积 53MB（计划 v1.2 添加 exclude 缩减）
- 安装机制仍需统一（计划 v1.2）
