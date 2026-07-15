"""
Claude Code 浮窗 — 图形化安装向导
打包为独立 exe 后即为专业安装包
"""
import sys, io, os, json, subprocess, shutil, ctypes

if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except: pass

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QProgressBar, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor

# ── 路径配置 ─────────────────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后，数据文件在 _MEIPASS 临时目录
    SETUP_DIR = sys._MEIPASS
else:
    SETUP_DIR = os.path.dirname(os.path.abspath(__file__))

EXE_NAME      = "ClaudeFloat.exe"
INSTALL_DIR_DEFAULT = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ClaudeFloat")
STARTUP_DIR   = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
DESKTOP_DIR   = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
START_MENU    = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ClaudeFloat"

STYLE = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F2F2F7, stop:1 #E8E8ED);
    font-family: "Microsoft YaHei";
}
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007AFF, stop:1 #5856D6);
    border-radius: 12px;
}
QLabel#title {
    color: white;
    font-size: 20px;
    font-weight: bold;
}
QLabel#subtitle {
    color: rgba(255,255,255,0.85);
    font-size: 12px;
}
QLabel#step {
    color: #8E8E93;
    font-size: 11px;
}
QPushButton#nextBtn {
    background: #007AFF;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#nextBtn:hover { background: #0066D6; }
QPushButton#cancelBtn {
    background: #F2F2F7;
    color: #007AFF;
    border: 1px solid #C7C7CC;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
}
QPushButton#cancelBtn:hover { background: #E5E5EA; }
QCheckBox {
    font-size: 13px;
    color: #1C1C1E;
    spacing: 8px;
}
QLabel#info {
    color: #3C3C43;
    font-size: 13px;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background: #E5E5EA;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background: #007AFF;
    border-radius: 4px;
}
"""

class InstallThread(QThread):
    progress = pyqtSignal(int, str)

    def __init__(self, install_dir, desktop, startup):
        super().__init__()
        self.install_dir = install_dir
        self.desktop = desktop
        self.startup = startup

    def run(self):
        exe_src = os.path.join(SETUP_DIR, EXE_NAME)
        ico_src = os.path.join(SETUP_DIR, "claude_icon.ico")
        png_src = os.path.join(SETUP_DIR, "claude_icon.png")

        steps = [
            (10, "创建安装目录..."),
            (30, "复制程序文件..."),
            (50, "创建快捷方式..."),
            (70, "配置开机自启..."),
            (90, "注册程序信息..."),
            (100, "安装完成!"),
        ]

        self.progress.emit(5, "准备安装...")
        os.makedirs(self.install_dir, exist_ok=True)
        os.makedirs(os.path.join(self.install_dir, "资源素材"), exist_ok=True)

        self.progress.emit(20, "复制程序文件...")
        for src, dst_name in [(exe_src, EXE_NAME), (ico_src, "资源素材/claude_icon.ico"), (png_src, "资源素材/claude_icon.png")]:
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(self.install_dir, dst_name))

        self.progress.emit(45, "创建快捷方式...")
        exe_dst = os.path.join(self.install_dir, EXE_NAME)
        ico_dst = os.path.join(self.install_dir, "资源素材", "claude_icon.ico")
        self._create_shortcut(exe_dst, os.path.join(START_MENU, "Claude Code 浮窗.lnk"), ico_dst)
        if self.desktop:
            self._create_shortcut(exe_dst, os.path.join(DESKTOP_DIR, "Claude Code 浮窗.lnk"), ico_dst)

        self.progress.emit(65, "配置开机自启...")
        startup_lnk = os.path.join(STARTUP_DIR, "Claude Code 浮窗.lnk")
        if self.startup:
            self._create_shortcut(exe_dst, startup_lnk, ico_dst)
        elif os.path.exists(startup_lnk):
            os.remove(startup_lnk)

        self.progress.emit(85, "注册程序信息...")
        self._register()

        self.progress.emit(100, "安装完成!")

    def _create_shortcut(self, target, lnk, icon):
        ps = f'''$ws=New-Object -ComObject WScript.Shell
$sc=$ws.CreateShortcut("{lnk}")
$sc.TargetPath="{target}"
$sc.WindowStyle=7
$sc.IconLocation="{icon}"
$sc.Description="Claude Code 桌面浮窗"
$sc.WorkingDirectory="{os.path.dirname(target)}"
$sc.Save()'''
        subprocess.run(["powershell","-NoProfile","-Command",ps], capture_output=True)

    def _register(self):
        ico = os.path.join(self.install_dir, "资源素材", "claude_icon.ico")
        ps = f'''$k="HKCU:{UNINSTALL_KEY}"
if(-not(Test-Path $k)){{New-Item -Path $k -Force|Out-Null}}
Set-ItemProperty -Path $k -Name "DisplayName" -Value "Claude Code 浮窗"
Set-ItemProperty -Path $k -Name "UninstallString" -Value '"{sys.executable}" "{os.path.join(self.install_dir, "uninstall.py")}"'
Set-ItemProperty -Path $k -Name "DisplayIcon" -Value "{ico}"
Set-ItemProperty -Path $k -Name "Publisher" -Value "Claude Code"
Set-ItemProperty -Path $k -Name "DisplayVersion" -Value "1.0"
Set-ItemProperty -Path $k -Name "NoModify" -Value 1
Set-ItemProperty -Path $k -Name "NoRepair" -Value 1'''
        subprocess.run(["powershell","-NoProfile","-Command",ps], capture_output=True)
        # 复制卸载脚本
        uninstall_src = os.path.join(SETUP_DIR, "uninstall.py")
        if os.path.exists(uninstall_src):
            shutil.copy2(uninstall_src, os.path.join(self.install_dir, "uninstall.py"))


class SetupWizard(QDialog):
    def __init__(self):
        super().__init__()
        self.install_dir = INSTALL_DIR_DEFAULT
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Claude Code 浮窗 安装向导")
        self.setFixedSize(440, 380)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部 Header ──
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(100)
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 18, 28, 12)

        title = QLabel("Claude Code 浮窗")
        title.setObjectName("title")
        hl.addWidget(title)

        sub = QLabel("快速启动 Claude Code 的桌面悬浮工具")
        sub.setObjectName("subtitle")
        hl.addWidget(sub)
        hl.addStretch()

        layout.addWidget(header)

        # ── 内容区 ──
        content = QVBoxLayout()
        content.setContentsMargins(28, 20, 28, 16)
        content.setSpacing(16)

        self.step_label = QLabel("选择安装选项")
        self.step_label.setObjectName("step")
        content.addWidget(self.step_label)

        # 安装路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("安装位置:"))
        self.path_label = QLabel(self.install_dir)
        self.path_label.setObjectName("info")
        self.path_label.setStyleSheet("color: #007AFF; font-size: 11px;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        browse_btn = QPushButton("更改...")
        browse_btn.setStyleSheet("QPushButton { background: transparent; color: #007AFF; border: none; font-size: 12px; } QPushButton:hover { color: #0066D6; }")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        content.addLayout(path_layout)

        content.addSpacing(8)

        self.cb_desktop = QCheckBox("创建桌面快捷方式")
        self.cb_desktop.setChecked(True)
        content.addWidget(self.cb_desktop)

        self.cb_startup = QCheckBox("开机自动启动")
        content.addWidget(self.cb_startup)

        content.addSpacing(10)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        content.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setObjectName("step")
        self.status_label.setVisible(False)
        content.addWidget(self.status_label)

        content.addStretch()

        # ── 按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(28, 0, 28, 20)
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        btn_layout.addStretch()

        self.install_btn = QPushButton("立即安装")
        self.install_btn.setObjectName("nextBtn")
        self.install_btn.clicked.connect(self._install)
        btn_layout.addWidget(self.install_btn)

        layout.addLayout(content)
        layout.addLayout(btn_layout)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "选择安装位置", self.install_dir)
        if d:
            self.install_dir = d
            self.path_label.setText(d)

    def _install(self):
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setVisible(True)

        self.thread = InstallThread(
            self.install_dir,
            self.cb_desktop.isChecked(),
            self.cb_startup.isChecked()
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_finish)
        self.thread.start()

    def _on_progress(self, val, msg):
        self.progress.setValue(val)
        self.status_label.setText(msg)

    def _on_finish(self):
        self.progress.setValue(100)
        self.status_label.setText("安装完成！")
        self.install_btn.setText("完成")
        self.install_btn.setEnabled(True)
        self.install_btn.clicked.disconnect()
        self.install_btn.clicked.connect(self.accept)
        self.cancel_btn.setVisible(False)

        # 启动程序
        exe = os.path.join(self.install_dir, EXE_NAME)
        if os.path.exists(exe):
            subprocess.Popen([exe], cwd=self.install_dir, creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))

    # 检查是否在安装包中（exe 同目录有 ClaudeFloat.exe）
    if not os.path.exists(os.path.join(SETUP_DIR, EXE_NAME)):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "错误",
            f"未找到 {EXE_NAME}\n请确保安装程序与程序文件在同一目录")
        return 1

    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
