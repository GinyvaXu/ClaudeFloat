"""PyInstaller 构建脚本 v1.4.2 — ClaudeFloat.exe（无控制台）"""
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
    "QtSql", "QtXml", "QtTest",
    "QtNetwork",
    "Qt3D", "Qt3DCore", "Qt3DRender", "Qt3DInput", "Qt3DLogic",
    "QtCharts", "QtDataVisualization",
    "QtSensors", "QtSerialPort", "QtPositioning",
    "QtPrintSupport",
    "QtQuick", "QtQml", "QtQmlModels", "QtQuickWidgets",
    "QtSvg", "QtSvgWidgets",
    "QtBluetooth", "QtNfc",
    "QtTextToSpeech", "QtSpeech",
    "QtLocation",
]

args = [
    SRC,
    "--onefile",
    "--windowed",
    "--name", "ClaudeFloat",
    f"--icon={ICON}",
    "--add-data", add_data,
    "--distpath", DIST,
    "--workpath", os.path.join(BASE, "build"),
    "--specpath", os.path.join(BASE, "build"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print(f"Building ClaudeFloat.exe (v1.4.2) → {DIST}")
PyInstaller.__main__.run(args)
print("\nBuild complete!")
