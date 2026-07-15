"""PyInstaller 调试构建 — v1.4.1（带控制台窗口）"""
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
    "QtSql", "QtXml", "QtTest", "QtNetwork",
    "Qt3D", "QtCharts", "QtDataVisualization",
    "QtSensors", "QtSerialPort", "QtPositioning",
    "QtPrintSupport", "QtQuick", "QtQml", "QtQuickWidgets",
    "QtSvg", "QtSvgWidgets", "QtBluetooth", "QtNfc",
    "QtTextToSpeech", "QtSpeech", "QtLocation",
]

args = [
    script,
    "--onefile",
    "--console",
    "--name", "ClaudeFloat_debug",
    f"--icon={icon}",
    "--add-data", add_data,
    "--distpath", os.path.join(BASE, "dist"),
    "--workpath", os.path.join(BASE, "build"),
    "--specpath", os.path.join(BASE, "build"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print("Building ClaudeFloat_debug.exe (v1.4.1, console enabled)...")
PyInstaller.__main__.run(args)
print("\nDebug build complete!")
