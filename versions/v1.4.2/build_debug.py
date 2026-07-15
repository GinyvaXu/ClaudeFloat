"""PyInstaller 调试构建 v1.4.2 — ClaudeFloat_debug.exe（带控制台）"""
import PyInstaller.__main__
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "src", "claude_floating_launcher.py")
ICON = os.path.join(BASE, "..", "..", "..", "资源素材", "claude_icon.ico")
RES  = os.path.join(BASE, "..", "..", "..", "资源素材")
DIST = os.path.join(BASE, "dist")

add_data = f"{RES}{os.pathsep}资源素材"

EXCLUDES = [
    "QtWebEngine", "QtWebEngineCore", "QtWebEngineWidgets", "QtWebChannel",
    "QtMultimedia", "QtMultimediaWidgets",
    "QtSql", "QtXml", "QtTest", "QtNetwork",
    "Qt3D", "QtCharts", "QtDataVisualization",
    "QtSensors", "QtSerialPort", "QtPositioning",
    "QtPrintSupport", "QtQuick", "QtQml", "QtQuickWidgets",
    "QtSvg", "QtSvgWidgets", "QtBluetooth", "QtNfc",
    "QtTextToSpeech", "QtSpeech", "QtLocation",
]

args = [
    SRC,
    "--onefile",
    "--console",
    "--name", "ClaudeFloat_debug",
    f"--icon={ICON}",
    "--add-data", add_data,
    "--distpath", DIST,
    "--workpath", os.path.join(BASE, "build_debug"),
    "--specpath", os.path.join(BASE, "build_debug"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print(f"Building ClaudeFloat_debug.exe (v1.4.2) → {DIST}")
PyInstaller.__main__.run(args)
print("\nDebug build complete!")
