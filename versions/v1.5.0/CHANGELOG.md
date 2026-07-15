# v1.5.0 — 2026-07-15

## 安全加固（GitHub 发布准备）

### 代码安全修复
- **TOCTOU 竞态条件**：`load_config()` 移除 `os.path.exists()` 前置检查，改为 try/except 捕获 FileNotFoundError
- **TOCTOU 竞态条件**：`_load_icon()` 移除 `os.path.exists()` 前置检查，直接尝试 QPixmap 加载
- **崩溃日志路径**：从用户桌面 (`Desktop/ClaudeFloat_crash.log`) 迁移至 `%APPDATA%/ClaudeFloat/logs/`，避免路径泄露
- **日志隐私**：`launch_claude_code()` 日志移除工作目录路径，`load_config()` 日志仅输出文件名而非完整路径
- **函数重命名**：`_escape_ps_path()` → `_escape_vbs_path()`，增加 VBScript 双引号转义，消除命名误导

### PII 清理（版本归档）
- 删除 `versions/v1.0/src/launcher.vbs` — 含硬编码绝对路径及用户目录名
- 删除 `versions/v1.4.1/src/ClaudeFloat_Setup.spec` — 含硬编码 PII 路径
- 删除 `versions/v1.4.2/src/ClaudeFloat.spec` / `ClaudeFloat_Setup.spec` / `ClaudeFloat_debug.spec` — 含硬编码 PII 路径
- 删除 `versions/v1.4.1/build/`、`versions/v1.4.2/build*/` — PyInstaller 构建残留（含用户路径的 .toc/.html 文件）

### .gitignore 全面更新
- 新增：`**/launcher.vbs`、`*.spec`、`*.toc`、`*.pyz`、`*.pkg`、`*.zip`、`localpycs/`、`xref-*.html`、`warn-*.txt`
- 新增：`logs/`、`*.log`、`venv/`、`.venv/`、`env/`、`.env`、`*.egg-info/`、`.DS_Store`
- 新增：`build_debug/`、`build_setup/`、`*.tmp`、`~$*`

## 延续前版改进（v1.4.3 → v1.5.0）

### UI 完善（v1.4.3）
- 字体层级重整：H1 16pt / H2 13pt / H3 11pt / Body 9pt 四级体系
- Radio/Checkbox 字号统一（移除 CSS font-size，统一 QFont 11pt）
- text_secondary 纳入 THEMES 字典（去硬编码）
- 暗色模式安全警告适配（WARN_BG/WARN_FG 主题感知色）
- ~~键盘焦点指示器~~ — 已移除（v1.4.3 修订）

### 启动修复（v1.4.2 修订）
- `launch_claude_code()` 使用 `shutil.which` 完整路径 + 参数分离

## 文件变更
| 文件 | 变更 |
|------|------|
| `claude_floating_launcher.py` | TOCTOU 修复 ×2 + crash log 迁移 + 日志脱敏 + `_escape_vbs_path` 重命名 |
| `.gitignore` | 全面更新（16 项新增） |
| `VERSION` | 1.4.3 → 1.5.0 |
| `versions/v1.0/src/launcher.vbs` | 已删除（PII） |
| `versions/v1.4.*/src/*.spec` | 已删除（PII） |
| `versions/v1.4.*/build*/` | 已删除（构建残留） |

## 构建产物
- `ClaudeFloat.exe` — ~52 MB
- `ClaudeFloat_debug.exe` — ~52 MB（控制台调试版）
- `ClaudeFloat_Setup.exe` — ~63 MB

## 安全审查结论
经三维度（代码注入/密钥泄露/PII暴露）全面审查：
- ✅ 无硬编码 API 密钥/Token/凭据
- ✅ 无 eval/exec/pickle 不安全反序列化
- ✅ PowerShell 命令使用环境变量传参（注入已修复）
- ✅ 配置存储于 `%APPDATA%`（非脚本目录）
- ✅ 所有历史 PII 路径已清理
- ✅ .gitignore 完整覆盖构建产物
