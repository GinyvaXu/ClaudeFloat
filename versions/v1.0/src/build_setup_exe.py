"""
构建安装包: 将 SetupWizard + ClaudeFloat.exe + 图标 打包为一个 Setup.exe
"""
import PyInstaller.__main__
import os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SETUP_PY = os.path.join(BASE, "installer", "setup_wizard_tk.py")
DIST    = os.path.join(BASE, "dist")
APP_EXE = os.path.join(DIST, "ClaudeFloat.exe")
ICON    = os.path.join(os.path.dirname(BASE), "资源素材", "claude_icon.ico")
RES_DIR = os.path.join(os.path.dirname(BASE), "资源素材")
OUT_DIR = os.path.join(DIST, "SetupPackage")

# 1. 确保 ClaudeFloat.exe 存在
if not os.path.exists(APP_EXE):
    print("[ERROR] ClaudeFloat.exe not found. Run build_exe.py first.")
    exit(1)

# 2. 创建打包目录
os.makedirs(OUT_DIR, exist_ok=True)

# 3. 复制文件到打包目录
setup_py_temp = os.path.join(OUT_DIR, "setup_wizard_tk.py")
shutil.copy2(SETUP_PY, setup_py_temp)
shutil.copy2(APP_EXE, os.path.join(OUT_DIR, "ClaudeFloat.exe"))
for f in ["claude_icon.ico", "claude_icon.png"]:
    src = os.path.join(RES_DIR, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(OUT_DIR, f))

# 也复制卸载脚本
uninstall_py = os.path.join(BASE, "installer", "install.py")
if os.path.exists(uninstall_py):
    shutil.copy2(uninstall_py, os.path.join(OUT_DIR, "uninstall.py"))

# 4. PyInstaller 打包
# 将 ClaudeFloat.exe 和图标作为数据文件嵌入
add_data = [
    f"{os.path.join(OUT_DIR, 'ClaudeFloat.exe')}{os.pathsep}.",
    f"{os.path.join(OUT_DIR, 'claude_icon.ico')}{os.pathsep}.",
    f"{os.path.join(OUT_DIR, 'claude_icon.png')}{os.pathsep}.",
    f"{os.path.join(OUT_DIR, 'uninstall.py')}{os.pathsep}.",
]

args = [
    setup_py_temp,
    "--onefile",
    "--windowed",
    "--name", "ClaudeFloat_Setup",
    f"--icon={ICON}",
    "--distpath", OUT_DIR,
    "--workpath", os.path.join(OUT_DIR, "build"),
    "--specpath", os.path.join(OUT_DIR, "build"),
    "--noconfirm",
]
for d in add_data:
    args.extend(["--add-data", d])

print("Building installer...")
PyInstaller.__main__.run(args)

# 5. 清理临时文件
for f in ["setup_wizard_tk.py", "ClaudeFloat.exe", "claude_icon.ico", "claude_icon.png", "uninstall.py"]:
    p = os.path.join(OUT_DIR, f)
    if os.path.exists(p): os.remove(p)
shutil.rmtree(os.path.join(OUT_DIR, "build"), ignore_errors=True)

setup_exe = os.path.join(OUT_DIR, "ClaudeFloat_Setup.exe")
if os.path.exists(setup_exe):
    size_mb = os.path.getsize(setup_exe) / (1024*1024)
    print(f"\nBuild complete: {setup_exe} ({size_mb:.0f} MB)")
else:
    print("\n[ERROR] Build failed")
