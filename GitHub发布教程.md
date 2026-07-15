# 🚀 GitHub 首次发布完整教程

> ClaudeFloat v1.5.0 | 2026-07-15

---

## 目录

1. [前置准备](#1-前置准备)
2. [创建 GitHub 仓库](#2-创建-github-仓库)
3. [配置 Git 身份认证](#3-配置-git-身份认证)
4. [初始化本地仓库并推送](#4-初始化本地仓库并推送)
5. [创建 Release 发布](#5-创建-release-发布)
6. [后续维护流程](#6-后续维护流程)

---

## 1. 前置准备

### 1.1 确认环境

打开终端（Git Bash），逐条运行以下命令：

```bash
# 检查 Git 版本（需 ≥ 2.30）
git --version

# 检查当前 Git 用户名和邮箱
git config --global user.name
git config --global user.email
```

### 1.2 配置 Git 身份

如果上面命令输出为空，需先配置：

```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub注册邮箱"
```

> ⚠️ **邮箱隐私提示**：GitHub 提供匿名提交邮箱（`username@users.noreply.github.com`），可在 GitHub → Settings → Emails 中找到。

### 1.3 安装 GitHub CLI（推荐）

下载安装 [GitHub CLI](https://cli.github.com/)（`gh`），后续可直接在终端操作仓库。

```bash
# 安装后验证
gh --version
```

---

## 2. 创建 GitHub 仓库

### 方式 A：网页创建（最简单）

1. 浏览器打开 https://github.com/new
2. 填写仓库信息：

   | 字段 | 内容 |
   |------|------|
   | **Repository name** | `ClaudeFloat` |
   | **Description** | `Windows 桌面悬浮启动器 — 一键启动 Claude Code，iOS 风格毛玻璃外观` |
   | **Public / Private** | 选 `Public`（公开） |
   | **Initialize with README** | ❌ **不要勾选**（本地已有） |
   | **Add .gitignore** | ❌ **不要勾选**（本地已有） |
   | **Choose a license** | ❌ **不要勾选**（本地已有 MIT） |

3. 点击 **Create repository**
4. 记录仓库地址：`https://github.com/YOUR_USERNAME/ClaudeFloat.git`

### 方式 B：CLI 创建

```bash
gh repo create ClaudeFloat --public --description "Windows 桌面悬浮启动器 — 一键启动 Claude Code，iOS 风格毛玻璃外观"
```

---

## 3. 配置 Git 身份认证

GitHub 不再支持密码登录，需使用以下任一方式：

### 方式 A：GitHub CLI 认证（推荐，最简单）

```bash
gh auth login
```

按提示选择：
- `GitHub.com` → `HTTPS` → `Login with a web browser`

### 方式 B：Personal Access Token（经典方式）

1. 打开 https://github.com/settings/tokens
2. 点击 **Generate new token** → **Generate new token (classic)**
3. 勾选权限：
   - ✅ `repo`（全部）
   - ✅ `workflow`（如果需要 GitHub Actions）
4. 点击 **Generate token**，**立即复制**（离开页面后不可再查看）
5. 配置 Git 凭据缓存：

```bash
# 启用凭据缓存（避免每次输入）
git config --global credential.helper wincred
```

> 推送时会提示输入密码，**粘贴 Token** 而非 GitHub 密码。

---

## 4. 初始化本地仓库并推送

### 4.1 检查项目文件

确认以下文件存在且内容正确（均已在项目中创建）：

```
浮窗工具/
├── README.md          ✅ 项目说明
├── LICENSE            ✅ MIT 许可证
├── .gitignore         ✅ 忽略规则
├── .gitattributes     ✅ 换行符规范
├── VERSION            ✅ 版本号
├── VERSIONING.md      ✅ 版本规范
└── claude_floating_launcher.py  ✅ 主程序
```

### 4.2 编辑 README 中的仓库地址

推送前，修改 `README.md` 中两处占位 URL：

```markdown
# 搜索替换：YOUR_USERNAME → 你的实际 GitHub 用户名
https://github.com/YOUR_USERNAME/ClaudeFloat
```

### 4.3 添加到暂存区并提交

```bash
cd "E:\匡时的资料库\ClaudeCode & AI\浮窗工具"

# 查看将要提交的文件
git status

# 添加所有文件（.gitignore 会自动排除不应提交的）
git add .

# 再次确认暂存区内容
git status

# 提交
git commit -m "🎉 Initial release: ClaudeFloat v1.5.0

Windows 桌面悬浮启动器 — 一键启动 Claude Code

- iOS 风格毛玻璃外观，亮色/暗色双主题
- 边缘吸附 + 自动隐藏
- 系统托盘 + 全局快捷键
- PyQt5 + PyInstaller 构建
- MIT License"
```

### 4.4 关联远程仓库并推送

```bash
# 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/ClaudeFloat.git

# 推送
git push -u origin main
```

> 如果默认分支是 `master`，将 `main` 改为 `master`。

### 4.5 验证

浏览器打开 `https://github.com/YOUR_USERNAME/ClaudeFloat`，确认所有文件已上传。

---

## 5. 创建 Release 发布

### 5.1 上传构建产物

Release 页面需要手动上传 exe 文件（exe 太大，不适合存 Git）。

#### 网页方式：

1. 打开 `https://github.com/YOUR_USERNAME/ClaudeFloat/releases/new`
2. 填写：

   | 字段 | 内容 |
   |------|------|
   | **Tag** | `v1.5.0`（新建） |
   | **Release title** | `v1.5.0 — 安全加固 + UI 完善` |
   | **Description** | 见下方 [Release 文案](#release-文案) |

3. 上传文件（拖拽或点击选择）：

   | 文件 | 路径 |
   |------|------|
   | `ClaudeFloat.exe` | `dist/ClaudeFloat.exe` |
   | `ClaudeFloat_Setup.exe` | `dist/SetupPackage/ClaudeFloat_Setup.exe` |
   | `ClaudeFloat_debug.exe` | `dist/ClaudeFloat_debug.exe` |

4. 点击 **Publish release**

#### CLI 方式：

```bash
gh release create v1.5.0 \
  --title "v1.5.0 — 安全加固 + UI 完善" \
  --notes-file - <<'EOF'
（见下方 Release 文案）
EOF
  dist/ClaudeFloat.exe \
  dist/SetupPackage/ClaudeFloat_Setup.exe \
  dist/ClaudeFloat_debug.exe
```

### Release 文案

复制以下内容到 Release 描述框：

```markdown
## v1.5.0 — 安全加固 + UI 完善

### 🔒 安全加固（GitHub 发布准备）
- TOCTOU 竞态条件修复 ×2
- 崩溃日志从桌面迁移至 `%APPDATA%`
- 日志脱敏（移除完整路径）
- `.gitignore` 全面更新（16 项）
- 历史版本 PII 路径清理

### 🎨 UI 完善
- 四级字体层级体系（H1/H2/H3/Body）
- Radio/Checkbox 字号统一
- 暗色模式安全警告适配
- `text_secondary` 纳入 THEMES 字典

### 🐛 修复
- 启动 Claude Code 使用完整路径 + 参数分离

### 📦 下载

| 文件 | 说明 | 大小 |
|------|------|------|
| `ClaudeFloat_Setup.exe` | 安装向导（推荐） | ~63 MB |
| `ClaudeFloat.exe` | 便携版（免安装） | ~52 MB |
| `ClaudeFloat_debug.exe` | 调试版（带控制台） | ~52 MB |

### 🔧 安装

1. 下载 `ClaudeFloat_Setup.exe`
2. 双击运行，选择安装目录
3. 安装完成后自动创建桌面快捷方式
4. 确保已安装 [Claude Code CLI](https://www.npmjs.com/package/@anthropic-ai/claude-code)：`npm install -g @anthropic-ai/claude-code`

### 📝 校验

```
SHA256:
ClaudeFloat.exe        (计算中)
ClaudeFloat_Setup.exe  (计算中)
ClaudeFloat_debug.exe  (计算中)
```
```

### 5.2 计算 SHA256 校验值

```bash
cd "E:\匡时的资料库\ClaudeCode & AI\浮窗工具\dist"
sha256sum ClaudeFloat.exe ClaudeFloat_debug.exe
sha256sum SetupPackage/ClaudeFloat_Setup.exe
```

将输出的校验值填入 Release 文案的 SHA256 部分。

---

## 6. 后续维护流程

### 日常开发 → 发布

```bash
# 1. 修改代码后构建
python build_exe.py && python build_debug.py && python build_setup_exe.py

# 2. 提交
git add .
git commit -m "feat: 描述你的改动"

# 3. 推送
git push

# 4. 打 Tag 并推送
git tag v1.5.1
git push origin v1.5.1

# 5. 创建 Release（网页或 CLI）
gh release create v1.5.1 --title "v1.5.1 — 描述" dist/*.exe dist/SetupPackage/*.exe
```

### 常用 Git 命令速查

| 场景 | 命令 |
|------|------|
| 查看状态 | `git status` |
| 查看提交历史 | `git log --oneline -10` |
| 撤销暂存 | `git reset HEAD <file>` |
| 查看远程地址 | `git remote -v` |
| 拉取最新 | `git pull origin main` |
| 切换 Tag | `git checkout v1.5.0` |

### Commit 消息规范

```
feat:     新功能
fix:      Bug 修复
security: 安全相关
docs:     文档更新
style:    UI/样式调整
refactor: 代码重构
chore:    构建/工具变动
```

示例：
```
security: 修复 TOCTOU 竞态条件，迁移 crash log 路径
feat: 新增全局快捷键 Ctrl+Alt+C
docs: 更新 README 安装说明
```

---

## 快速检查清单

推送前逐项确认：

- [ ] `git config user.name` 和 `user.email` 已配置
- [ ] GitHub 仓库已创建（`Public`）
- [ ] `README.md` 中 `YOUR_USERNAME` 已替换为实际用户名
- [ ] `.gitignore` 正确排除 `build/` `dist/` `*.spec`
- [ ] `git status` 无意外文件
- [ ] `LICENSE` 文件存在
- [ ] 仓库 URL 正确（`git remote -v`）
- [ ] GitHub 认证方式已配置（Token 或 gh auth）
- [ ] Release 已创建并上传 exe 文件

---

## 遇到问题？

| 错误 | 解决方法 |
|------|----------|
| `Permission denied (publickey)` | 未配置 SSH Key 或 Token。改用 HTTPS + Token |
| `fatal: remote origin already exists` | `git remote set-url origin <新地址>` |
| `failed to push some refs` | 远程有新提交，先 `git pull origin main --rebase` |
| `403 Forbidden` | Token 权限不足，重新生成含 `repo` 权限的 Token |
| `error: src refspec main does not match any` | 尚未提交，先 `git add . && git commit -m "init"` |
| 文件太大推送失败 | exe 不应提交到 Git。确认 `.gitignore` 包含 `dist/`，exe 通过 Release 发布 |
