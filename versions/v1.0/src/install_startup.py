"""
Claude Code 浮窗 — 开机自启管理工具

用法:
    python install_startup.py --install      # 启用开机自启
    python install_startup.py --uninstall    # 取消开机自启
    python install_startup.py --status       # 查看当前状态
"""
import sys
import io
import os

# Windows 下修复控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import subprocess
import argparse


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)

# 启动文件夹路径
STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
STARTUP_LNK_NAME = "ClaudeCode浮窗.lnk"
VBS_NAME = "launcher.vbs"

VBS_CONTENT = '''Set ws = CreateObject("WScript.Shell")
ws.Run "pythonw.exe ""{script_path}""", 0, False
'''


def get_launcher_path():
    """获取主程序 Python 脚本路径"""
    return os.path.join(SCRIPT_DIR, "claude_floating_launcher.py")


def get_vbs_path():
    """获取 VBS 启动器路径"""
    return os.path.join(SCRIPT_DIR, VBS_NAME)


def get_lnk_path():
    """获取启动文件夹中快捷方式的路径"""
    return os.path.join(STARTUP_FOLDER, STARTUP_LNK_NAME)


def get_status():
    """检查开机自启状态"""
    lnk_exists = os.path.exists(get_lnk_path())
    vbs_exists = os.path.exists(get_vbs_path())
    return {
        "enabled": lnk_exists,
        "lnk_path": get_lnk_path(),
        "lnk_exists": lnk_exists,
        "vbs_exists": vbs_exists,
        "startup_folder": STARTUP_FOLDER,
    }


def install():
    """启用开机自启"""
    # 1. 创建 VBS 启动器脚本
    vbs_path = get_vbs_path()
    launcher_path = get_launcher_path()

    vbs = VBS_CONTENT.format(script_path=launcher_path)
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs)
        print(f"[OK] VBS 启动器已创建: {vbs_path}")
    except IOError as e:
        print(f"[FAIL] 无法创建 VBS 文件: {e}")
        return False

    # 2. 使用 PowerShell COM 在启动文件夹创建快捷方式
    lnk_path = get_lnk_path()

    ps_script = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{lnk_path}")
$sc.TargetPath = "{vbs_path}"
$sc.WindowStyle = 7
$sc.WorkingDirectory = "{SCRIPT_DIR}"
$sc.Description = "Claude Code 桌面浮窗启动器"
$sc.Save()
Write-Output "OK"
'''

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and "OK" in result.stdout:
            print(f"[OK] 启动快捷方式已创建: {lnk_path}")
        else:
            print(f"[FAIL] PowerShell 执行失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[FAIL] PowerShell 执行超时")
        return False
    except FileNotFoundError:
        print("[FAIL] 未找到 PowerShell")
        return False

    print()
    print("=" * 50)
    print("  开机自启已启用！")
    print(f"  快捷方式: {lnk_path}")
    print("  重启电脑后浮窗将自动启动")
    print("=" * 50)
    return True


def uninstall():
    """取消开机自启"""
    all_ok = True

    # 1. 删除快捷方式
    lnk_path = get_lnk_path()
    if os.path.exists(lnk_path):
        try:
            os.remove(lnk_path)
            print(f"[OK] 已删除快捷方式: {lnk_path}")
        except OSError as e:
            print(f"[FAIL] 无法删除快捷方式: {e}")
            all_ok = False
    else:
        print(f"[INFO] 快捷方式不存在，无需删除")

    # 2. 删除 VBS
    vbs_path = get_vbs_path()
    if os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
            print(f"[OK] 已删除 VBS 文件: {vbs_path}")
        except OSError as e:
            print(f"[FAIL] 无法删除 VBS 文件: {e}")
            all_ok = False
    else:
        print(f"[INFO] VBS 文件不存在，无需删除")

    if all_ok:
        print()
        print("=" * 50)
        print("  开机自启已取消！")
        print("=" * 50)
    return all_ok


def print_status():
    """打印状态信息"""
    status = get_status()
    print("=" * 50)
    print("  Claude Code 浮窗 — 开机自启状态")
    print("=" * 50)
    print(f"  状态:     {'[ENABLED] 已启用' if status['enabled'] else '[DISABLED] 未启用'}")
    print(f"  启动文件夹: {status['startup_folder']}")
    print(f"  快捷方式:   {status['lnk_path']}")
    print(f"              {'存在' if status['lnk_exists'] else '不存在'}")
    print(f"  VBS 脚本:   {'存在' if status['vbs_exists'] else '不存在'}")
    print("=" * 50)
    return 0 if status["enabled"] else 1


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code 浮窗 — 开机自启管理"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="启用开机自启")
    group.add_argument("--uninstall", action="store_true", help="取消开机自启")
    group.add_argument("--status", action="store_true", help="查看当前状态")

    args = parser.parse_args()

    if args.install:
        success = install()
        return 0 if success else 1
    elif args.uninstall:
        success = uninstall()
        return 0 if success else 1
    elif args.status:
        return print_status()

    return 0


if __name__ == "__main__":
    sys.exit(main())
