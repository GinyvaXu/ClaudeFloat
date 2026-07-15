"""构建 v1.4.2 安装包 — ClaudeFloat_Setup.exe"""
import PyInstaller.__main__
import os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SETUP_PY = os.path.join(BASE, "installer", "setup_wizard_tk.py")
APP_EXE  = os.path.join(BASE, "dist", "ClaudeFloat.exe")
ICON     = os.path.join(BASE, "..", "..", "..", "资源素材", "claude_icon.ico")
RES_DIR  = os.path.join(BASE, "..", "..", "..", "资源素材")
VERSION  = os.path.join(BASE, "src", "VERSION")
DIST     = os.path.join(BASE, "dist")

# 临时打包目录
TMP = os.path.join(DIST, "_setup_tmp")

# 1. 确保 ClaudeFloat.exe 存在
if not os.path.exists(APP_EXE):
    print(f"[ERROR] ClaudeFloat.exe not found at {APP_EXE}. Run build_exe.py first.")
    exit(1)

# 2. 创建临时打包目录并复制文件
os.makedirs(TMP, exist_ok=True)
shutil.copy2(SETUP_PY, os.path.join(TMP, "setup_wizard_tk.py"))
shutil.copy2(APP_EXE, os.path.join(TMP, "ClaudeFloat.exe"))
if os.path.exists(VERSION):
    shutil.copy2(VERSION, os.path.join(TMP, "VERSION"))
for f in ["claude_icon.ico", "claude_icon.png"]:
    src = os.path.join(RES_DIR, f)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(TMP, f))

# 3. PyInstaller 打包
add_data = [
    f"{os.path.join(TMP, 'ClaudeFloat.exe')}{os.pathsep}.",
    f"{os.path.join(TMP, 'claude_icon.ico')}{os.pathsep}.",
    f"{os.path.join(TMP, 'claude_icon.png')}{os.pathsep}.",
]
if os.path.exists(os.path.join(TMP, "VERSION")):
    add_data.append(f"{os.path.join(TMP, 'VERSION')}{os.pathsep}.")

EXCLUDES = [
    "QtWebEngine", "QtWebEngineCore", "QtWebEngineWidgets", "QtWebChannel",
    "QtMultimedia", "QtMultimediaWidgets",
    "QtSql", "QtXml", "QtTest", "QtNetwork",
    "Qt3D", "QtCharts", "QtDataVisualization",
    "QtSensors", "QtSerialPort", "QtPositioning",
    "QtPrintSupport", "QtQuick", "QtQml", "QtQuickWidgets",
]

args = [
    os.path.join(TMP, "setup_wizard_tk.py"),
    "--onefile", "--windowed",
    "--name", "ClaudeFloat_Setup",
    f"--icon={ICON}",
    "--distpath", DIST,
    "--workpath", os.path.join(BASE, "build_setup"),
    "--specpath", os.path.join(BASE, "build_setup"),
    "--noconfirm",
]
for d in add_data:
    args.extend(["--add-data", d])
for m in EXCLUDES:
    args.extend(["--exclude-module", m])

print(f"Building ClaudeFloat_Setup.exe (v1.4.2) → {DIST}")
PyInstaller.__main__.run(args)

# 4. 清理
shutil.rmtree(TMP, ignore_errors=True)

setup_exe = os.path.join(DIST, "ClaudeFloat_Setup.exe")
if os.path.exists(setup_exe):
    size_mb = os.path.getsize(setup_exe) / (1024*1024)
    print(f"OK: ClaudeFloat_Setup.exe ({size_mb:.0f} MB)")
else:
    print("ERROR: Build failed")
