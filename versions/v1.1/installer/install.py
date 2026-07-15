"""
Claude Code 浮窗 — Windows 安装器
用法: python install.py          (图形安装向导)
      python install.py --quiet  (静默安装)
      python install.py --uninstall (卸载)
"""
import sys, io, os, json, subprocess, shutil, ctypes

if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except: pass

# ── 路径配置 ─────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DIST_DIR     = os.path.join(SCRIPT_DIR, "..", "dist")
EXE_NAME     = "ClaudeFloat.exe"
EXE_SRC      = os.path.join(DIST_DIR, EXE_NAME)
RES_DIR      = os.path.join(SCRIPT_DIR, "..", "..", "资源素材")
ICO_SRC      = os.path.join(RES_DIR, "claude_icon.ico")
PNG_SRC      = os.path.join(RES_DIR, "claude_icon.png")
# 安装路径：使用 LOCALAPPDATA，空值时回退到 USERPROFILE
_LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", "") or os.environ.get("USERPROFILE", os.path.expanduser("~"))
INSTALL_DIR  = os.path.join(_LOCAL_APPDATA, "ClaudeFloat")
_START_MENU_BASE = os.environ.get("APPDATA", "") or os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "AppData", "Roaming")
STARTUP_DIR  = os.path.join(_START_MENU_BASE, r"Microsoft\Windows\Start Menu\Programs\Startup")
DESKTOP_DIR  = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
START_MENU   = os.path.join(_START_MENU_BASE, r"Microsoft\Windows\Start Menu\Programs")
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ClaudeFloat"

def _escape_ps_path(path):
    """转义路径中的特殊字符以便安全嵌入 PowerShell 单引号字符串"""
    return path.replace("'", "''")

def _safe_ps(cmd, **paths):
    """通过环境变量安全传递路径参数到 PowerShell，防止注入"""
    env = os.environ.copy()
    for k, v in paths.items():
        env[k] = v
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], env=env,
                       capture_output=True, text=True)
    return r

def check_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return False

def create_shortcut(target, shortcut_path, icon=None, workdir=None, desc=""):
    """通过环境变量安全传递路径，避免 PowerShell 注入"""
    ps = (
        '$ws=New-Object -ComObject WScript.Shell;'
        '$sc=$ws.CreateShortcut($env:CC_LNK);'
        '$sc.TargetPath=$env:CC_TARGET;'
        '$sc.WindowStyle=7;'
        'if ($env:CC_WORKDIR) { $sc.WorkingDirectory=$env:CC_WORKDIR };'
        'if ($env:CC_ICON) { if (Test-Path $env:CC_ICON) { $sc.IconLocation=$env:CC_ICON } };'
        'if ($env:CC_DESC) { $sc.Description=$env:CC_DESC };'
        '$sc.Save()'
    )
    paths = {"CC_LNK": shortcut_path, "CC_TARGET": target}
    if workdir: paths["CC_WORKDIR"] = workdir
    if icon and os.path.exists(icon): paths["CC_ICON"] = icon
    if desc: paths["CC_DESC"] = desc
    r = _safe_ps(ps, **paths)
    return r.returncode == 0

def create_uninstall_bat(install_dir):
    """在安装目录创建独立的卸载脚本（正确转义 BAT 特殊字符）"""
    bat_path = os.path.join(install_dir, "uninstall.bat")
    app_name = "Claude Code 浮窗"
    exe_name = "ClaudeFloat.exe"
    uninstall_key = UNINSTALL_KEY

    # 转义 BAT 特殊字符：% → %%，其他危险字符已通过双引号保护
    safe_dir = install_dir.replace("%", "%%")
    safe_name = app_name.replace("%", "%%")

    bat_content = f'''@echo off
chcp 65001 >nul
title 卸载 {safe_name}
echo.
echo ╔══════════════════════════════════════════╗
echo ║   卸载 {safe_name}                  ║
echo ╚══════════════════════════════════════════╝
echo.
echo 正在关闭运行中的程序...
taskkill /f /im {exe_name} >nul 2>&1
timeout /t 1 /nobreak >nul

echo 正在删除快捷方式...
del /q "%USERPROFILE%\\Desktop\\{safe_name}.lnk" 2>nul
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{safe_name}.lnk" 2>nul
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{safe_name}.lnk" 2>nul

echo 正在清除注册表...
powershell -NoProfile -Command "Remove-Item -Path 'HKCU:{uninstall_key}' -Recurse -Force -ErrorAction SilentlyContinue"

echo 正在删除程序文件...
cd /d "%USERPROFILE%"
rmdir /s /q "{safe_dir}" 2>nul

echo.
echo 卸载完成！
echo.
timeout /t 2 /nobreak >nul
'''
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    return bat_path


def register_uninstall():
    """在控制面板注册卸载信息（安全 env-var 传参）"""
    bat_path = create_uninstall_bat(INSTALL_DIR)
    icon_path = os.path.join(INSTALL_DIR, "资源素材", "claude_icon.ico")
    ps = (
        '$key = "HKCU:" + $env:CC_UNINSTALL_KEY;'
        'if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null };'
        'Set-ItemProperty -Path $key -Name "DisplayName" -Value "Claude Code 浮窗";'
        'Set-ItemProperty -Path $key -Name "UninstallString" -Value $env:CC_BAT;'
        'Set-ItemProperty -Path $key -Name "DisplayIcon" -Value $env:CC_ICON;'
        'Set-ItemProperty -Path $key -Name "Publisher" -Value "Claude Code";'
        'Set-ItemProperty -Path $key -Name "DisplayVersion" -Value "1.1";'
        'Set-ItemProperty -Path $key -Name "NoModify" -Value 1;'
        'Set-ItemProperty -Path $key -Name "NoRepair" -Value 1'
    )
    # 用双引号包裹 bat 路径，让注册表的 UninstallString 被正确引用
    r = _safe_ps(ps, CC_BAT=f'"{bat_path}"', CC_ICON=icon_path, CC_UNINSTALL_KEY=UNINSTALL_KEY)
    return r.returncode == 0

def unregister_uninstall():
    ps = 'Remove-Item -Path ("HKCU:" + $env:CC_UNINSTALL_KEY) -Recurse -Force -ErrorAction SilentlyContinue'
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   env={**os.environ, "CC_UNINSTALL_KEY": UNINSTALL_KEY},
                   capture_output=True)

def install(desktop_icon=True, startup=False):
    """执行安装"""
    if not os.path.exists(EXE_SRC):
        print(f"[ERROR] 未找到 {EXE_SRC}\n请先运行 build.bat 编译程序")
        return False

    # 1. 创建安装目录
    os.makedirs(INSTALL_DIR, exist_ok=True)
    os.makedirs(os.path.join(INSTALL_DIR, "资源素材"), exist_ok=True)

    # 2. 复制文件
    exe_dst = os.path.join(INSTALL_DIR, EXE_NAME)
    print(f"[1/5] 复制程序文件...")
    shutil.copy2(EXE_SRC, exe_dst)
    for src, name in [(ICO_SRC, "claude_icon.ico"), (PNG_SRC, "claude_icon.png")]:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(INSTALL_DIR, "资源素材", name))

    # 3. 复制卸载器
    uninstaller_src = os.path.join(SCRIPT_DIR, "install.py")
    uninstaller_dst = os.path.join(INSTALL_DIR, "uninstall.py")
    shutil.copy2(uninstaller_src, uninstaller_dst)

    # 4. 创建快捷方式
    print(f"[2/5] 创建快捷方式...")
    if desktop_icon:
        create_shortcut(exe_dst, os.path.join(DESKTOP_DIR, "Claude Code 浮窗.lnk"),
                        icon=ICO_SRC, workdir=INSTALL_DIR, desc="Claude Code 桌面浮窗")
    create_shortcut(exe_dst, os.path.join(START_MENU, "Claude Code 浮窗.lnk"),
                    icon=ICO_SRC, workdir=INSTALL_DIR, desc="Claude Code 桌面浮窗")

    # 5. 开机自启
    print(f"[3/5] 开机自启: {'是' if startup else '否'}")
    startup_lnk = os.path.join(STARTUP_DIR, "Claude Code 浮窗.lnk")
    if startup:
        create_shortcut(exe_dst, startup_lnk, icon=ICO_SRC, workdir=INSTALL_DIR)
    elif os.path.exists(startup_lnk):
        os.remove(startup_lnk)

    # 6. 注册卸载信息
    print(f"[4/5] 注册卸载信息...")
    register_uninstall()

    # 7. 启动程序
    print(f"[5/5] 启动浮窗...")
    subprocess.Popen([exe_dst], cwd=INSTALL_DIR, creationflags=subprocess.CREATE_NO_WINDOW)

    print(f"""
╔══════════════════════════════════════════╗
║  ✅ Claude Code 浮窗 安装完成！          ║
║  安装位置: {INSTALL_DIR}
║  桌面快捷方式: {'是' if desktop_icon else '否'}
║  开机自启: {'是' if startup else '否'}
║  卸载: 控制面板 → 程序和功能 → 卸载     ║
╚══════════════════════════════════════════╝
""")
    return True

def uninstall():
    """卸载"""
    print("正在卸载 Claude Code 浮窗...")

    # 结束进程
    print("  正在关闭运行中的程序...")
    subprocess.run(["taskkill","/f","/im",EXE_NAME], capture_output=True)
    import time; time.sleep(0.5)

    # 删除快捷方式
    for d, name in [(DESKTOP_DIR, "Claude Code 浮窗.lnk"),
                    (START_MENU, "Claude Code 浮窗.lnk"),
                    (STARTUP_DIR, "Claude Code 浮窗.lnk")]:
        p = os.path.join(d, name)
        if os.path.exists(p):
            try: os.remove(p); print(f"  已删除: {p}")
            except OSError as e: print(f"  跳过: {p} ({e})")

    # 删除安装目录
    if os.path.exists(INSTALL_DIR):
        try:
            shutil.rmtree(INSTALL_DIR)
            print(f"  已删除: {INSTALL_DIR}")
        except PermissionError:
            print(f"  部分文件被占用，已尽力清理")
            # 至少尝试删除非 exe 文件
            for root, dirs, files in os.walk(INSTALL_DIR):
                for f in files:
                    if not f.endswith('.exe'):
                        try: os.remove(os.path.join(root, f))
                        except: pass

    # 清除注册表
    unregister_uninstall()
    print(f"  已清除注册表")

    print("\n✅ 卸载完成！（如程序正在运行请先关闭）")

def main():
    if "--uninstall" in sys.argv:
        uninstall()
    elif "--quiet" in sys.argv:
        install(desktop_icon=True, startup=False)
    else:
        # 交互式安装
        print("=" * 50)
        print("  Claude Code 浮窗 — 安装向导")
        print("=" * 50)
        print()

        if not os.path.exists(EXE_SRC):
            print(f"[ERROR] 未找到 {EXE_SRC}")
            print("请确保已运行 PyInstaller 编译: cd 浮窗工具 && pyinstaller ...")
            return 1

        desktop = input("创建桌面快捷方式? [Y/n]: ").strip().lower() != 'n'
        startup = input("开机自动启动? [y/N]: ").strip().lower() == 'y'

        install(desktop_icon=desktop, startup=startup)
    return 0

if __name__ == "__main__":
    sys.exit(main())
