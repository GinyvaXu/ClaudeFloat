"""PyInstaller 构建脚本（避开命令行编码问题）"""
import PyInstaller.__main__
import os

script = os.path.join(os.path.dirname(__file__), "claude_floating_launcher.py")
icon   = os.path.join(os.path.dirname(__file__), "..", "资源素材", "claude_icon.ico")
res    = os.path.join(os.path.dirname(__file__), "..", "资源素材")

# 构建 --add-data 参数: 源目录;目标目录
add_data = f"{res}{os.pathsep}资源素材"

# 排除不需要的 Qt 模块以缩减 EXE 体积
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
    "--distpath", os.path.join(os.path.dirname(__file__), "dist"),
    "--workpath", os.path.join(os.path.dirname(__file__), "build"),
    "--specpath", os.path.join(os.path.dirname(__file__), "build"),
    "--noconfirm",
    *[f"--exclude-module={m}" for m in EXCLUDES],
]

print("PyInstaller args:", args)
PyInstaller.__main__.run(args)
print("\nBuild complete!")
