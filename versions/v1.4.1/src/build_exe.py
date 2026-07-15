"""PyInstaller 构建脚本 — v1.4.1"""
import PyInstaller.__main__
import os

BASE = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(BASE, "src", "claude_floating_launcher.py")
icon   = os.path.join(BASE, "..", "..", "资源素材", "claude_icon.ico")
res    = os.path.join(BASE, "..", "..", "资源素材")

add_data = f"{res}{os.pathsep}资源素材"

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
    script,
    "--onefile",
    "--windowed",
    "--name", "ClaudeFloat",
    f"--icon={icon}",
    "--add-data", add_data,
    "--distpath", os.path.join(BASE, "dist"),
    "--workpath", os.path.join(BASE, "build"),
    "--specpath", os.path.join(BASE, "build"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print("Building ClaudeFloat.exe (v1.4.1)...")
PyInstaller.__main__.run(args)
print("\nBuild complete!")
