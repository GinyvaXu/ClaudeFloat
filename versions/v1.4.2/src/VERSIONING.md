# 版本管理规范 — Claude Code 浮窗工具

## 版本号制度

采用 **语义化版本号 (Semantic Versioning)**：

```
v<MAJOR>.<MINOR>.<PATCH>

MAJOR — 重大架构变更或不兼容的 API 改动
MINOR — 新功能、优化（向后兼容）
PATCH — Bug 修复、安全补丁
```

### 示例

| 版本 | 说明 |
|------|------|
| v1.0.0 | 当前基线版本 |
| v1.0.1 | 修复 PowerShell 注入 + 配置丢失 Bug |
| v1.1.0 | 新增边缘吸附 + 全局快捷键 |
| v1.2.0 | 新增暗色模式 + 自动更新 |
| v2.0.0 | 架构重构（如拆分为多文件模块） |

---

## 目录结构

```
浮窗工具/
├── claude_floating_launcher.py    # 当前主程序
├── launcher_config.json           # 当前配置
├── CLAUDE.md                      # 项目说明
├── VERSION                        # 纯文本版号文件
├── VERSIONING.md                  # 本文件（版本管理规范）
├── .gitignore
├── 审查报告_v<version>.md         # 各版本审查报告
│
├── versions/                      # 历史版本归档（每个版本独立完整）
│   ├── v1.0/
│   │   ├── src/                   # 源代码快照
│   │   ├── installer/             # 安装器源码快照
│   │   ├── dist/                  # ★ 构建产物（ClaudeFloat.exe + ClaudeFloat_Setup.exe）
│   │   └── CHANGELOG.md           # 本版本变更记录
│   └── v1.1/
│       ├── src/
│       ├── installer/
│       ├── dist/                  # ★ 构建产物
│       └── CHANGELOG.md
│
├── installer/                     # 安装器源码（当前工作副本）
├── dist/                          # 构建产物（当前工作副本）
├── build/                         # PyInstaller 临时文件
└── 资源素材/                      # 图标等静态资源
```

---

## 发布流程

### 1. 开发阶段

- 在 `VERSION` 文件和 `claude_floating_launcher.py` 顶部注释中维护版本号
- 小改动直接在 `claude_floating_launcher.py` 顶部增加变更注释

### 2. 发布前

```
1. 更新 VERSION 文件为新的版本号
2. 在 versions/ 下创建 v<version>/ 目录（含 src/ installer/ dist/ 子目录）
3. 复制所有源文件到 versions/v<version>/src/ 和 versions/v<version>/installer/
4. 编写 versions/v<version>/CHANGELOG.md
5. 运行 build_exe.py 生成新的 dist/ClaudeFloat.exe
6. 运行 build_setup_exe.py 生成新的 dist/SetupPackage/ClaudeFloat_Setup.exe
7. 将构建产物复制到 versions/v<version>/dist/（必须，确保每个版本有独立安装包）
8. （可选）运行 Inno Setup compile.bat 生成 Inno Setup 安装包
```

### 3. 发布后

- 打 Git tag: `git tag v<version>`
- 确认 `versions/v<version>/dist/` 包含 ClaudeFloat.exe 和 ClaudeFloat_Setup.exe

---

## CHANGELOG 格式

```markdown
# v1.0.1 — 2026-07-14

## 安全修复
- [S-01] 修复 PowerShell f-string 注入漏洞，改用环境变量传参

## Bug 修复
- [B-02] 修复 PyInstaller 打包后配置丢失（迁移到 %APPDATA%）
- [B-03] 修复开机自启 VBS 指向临时目录
- [B-06] 修复第三个启动 fallback 缺少 CREATE_NO_WINDOW

## 改进
- 配置迁移逻辑：自动检测旧路径并迁移到新路径
```

---

## 归档规则

| 规则 | 说明 |
|------|------|
| 每次发布时必须归档 | 包含源文件、安装包、更新日志 |
| 归档内容 | `src/`（所有 `.py` `.json` `.bat` `.vbs` `.iss` `.spec`）、`installer/`（安装器源码）、`dist/`（ClaudeFloat.exe + ClaudeFloat_Setup.exe）、`CHANGELOG.md` |
| 归档不包括 | `build/`、`__pycache__/`、`*.pyc` |
| 构建产物 | **必须**归档到 `versions/v<version>/dist/` |
| 命名规范 | 目录名严格使用 `v<MAJOR>.<MINOR>.<PATCH>` 格式 |

---

## 当前版本

**v1.4.2** — UX 改进（2026-07-14）

设置对话框 Tooltip 化 + Radio/Checkbox 指示器尺寸修复 + 主题即时切换。见 `versions/v1.4.2/CHANGELOG.md`。
