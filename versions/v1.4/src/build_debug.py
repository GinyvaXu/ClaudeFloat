"""PyInstaller 调试构建 — 带控制台窗口，可看到错误输出"""
import PyInstaller.__main__
import os

script = os.path.join(os.path.dirname(__file__), "claude_floating_launcher.py")
icon   = os.path.join(os.path.dirname(__file__), "..", "资源素材", "claude_icon.ico")
res    = os.path.join(os.path.dirname(__file__), "..", "资源素材")
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
    "--console",   # <-- 带控制台，可以看到 print/错误输出
    "--name", "ClaudeFloat_debug",
    f"--icon={icon}",
    "--add-data", add_data,
    "--distpath", os.path.join(os.path.dirname(__file__), "dist"),
    "--workpath", os.path.join(os.path.dirname(__file__), "build"),
    "--specpath", os.path.join(os.path.dirname(__file__), "build"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print("Building DEBUG version (console enabled)...")
PyInstaller.__main__.run(args)
print("\nDebug build complete! Run dist/ClaudeFloat_debug.exe")
