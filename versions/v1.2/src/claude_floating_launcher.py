"""
Claude Code 桌面悬浮启动器 — iOS 风格亮色毛玻璃
- 圆角矩形悬浮窗，亮色毛玻璃质感
- 自由拖拽，始终置顶
- 点击启动 Claude Code
- 系统托盘支持
- 配置持久化
"""
import sys
import io
import os
import json
import subprocess
import ctypes
from ctypes import wintypes

if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        pass

from PyQt5.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton,
    QSpinBox, QGroupBox, QRadioButton, QCheckBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import (
    Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QRectF
)
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, QRadialGradient, QLinearGradient, QPen, QFont,
    QPixmap, QIcon, QRegion, QCursor, QFontDatabase, QPainterPath
)

# ── 路径（兼容 PyInstaller 打包）──────────────────────
import sys as _sys
_IS_FROZEN = getattr(_sys, 'frozen', False)

def _resolve_path(*parts):
    """解析资源路径，兼容 PyInstaller 打包和开发模式"""
    if _IS_FROZEN:
        base = _sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
ICO_PATH  = _resolve_path("资源素材", "claude_icon.ico")
PNG_PATH  = _resolve_path("资源素材", "claude_icon.png")

# 配置路径：打包后存 %APPDATA%/ClaudeFloat/，开发时存脚本目录
def _get_config_dir():
    if _IS_FROZEN:
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ClaudeFloat")
    return SCRIPT_DIR

def _get_config_path():
    d = _get_config_dir()
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")

# 旧配置路径（用于自动迁移）
_OLD_CONFIG_PATH = os.path.join(SCRIPT_DIR, "launcher_config.json")
CONFIG_PATH = _get_config_path()

STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
STARTUP_LNK_NAME = "ClaudeCode浮窗.lnk"

def _escape_ps_path(path):
    """转义路径中的特殊字符以便安全嵌入 PowerShell 单引号字符串"""
    return path.replace("'", "''")

# ── iOS 风格配色 ──────────────────────────────────────
IOS_GLASS_BG   = (255, 255, 255)   # 毛玻璃白底
IOS_BORDER     = (255, 255, 255)   # 玻璃边框
IOS_SHADOW     = (0, 0, 0)         # 柔和阴影
IOS_ACCENT     = (0, 122, 255)     # iOS 蓝 #007AFF
IOS_TEXT       = (28, 28, 30)      # 深色文字 #1C1C1E
IOS_HINT       = (142, 142, 147)   # 系统灰
IOS_SURFACE    = (242, 242, 247)   # 浅灰底

FONT_FAMILY = "Microsoft YaHei"
VERSION = "1.2.0"

# ── 浮窗参数 ──────────────────────────────────────────
DEFAULT_SIZE  = 52          # 默认边长 px
CORNER_RADIUS = 18          # 圆角半径 (iOS 连续曲线风格)
HOVER_SCALE   = 1.08        # 悬停放大比例
PRESS_SCALE   = 0.94        # 按压缩小比例

# ── 配置 ──────────────────────────────────────────────
def load_config():
    defaults = {
        "window_x": -1, "window_y": -1,
        "auto_start": False,
        "launch_mode": "normal",
        "widget_size": DEFAULT_SIZE,
        "opacity": 0.88,
        "working_directory": "",
        "snap_enabled": True,
        "snap_edge": "right",
        "snap_hidden": True,
        "hide_delay_ms": 800,
    }
    loaded = {}

    # 尝试从当前配置路径加载
    config_sources = [CONFIG_PATH]
    # 如果旧路径存在且不同于新路径，也尝试加载并迁移
    if os.path.exists(_OLD_CONFIG_PATH) and os.path.abspath(_OLD_CONFIG_PATH) != os.path.abspath(CONFIG_PATH):
        config_sources.insert(0, _OLD_CONFIG_PATH)

    for src in config_sources:
        if os.path.exists(src):
            try:
                with open(src, "r", encoding="utf-8") as f:
                    loaded.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass

    defaults.update(loaded)

    # ── 值校验：防止损坏的配置导致不可恢复状态 ──
    defaults["widget_size"] = max(30, min(200, int(defaults.get("widget_size", DEFAULT_SIZE))))
    defaults["opacity"] = max(0.1, min(1.0, float(defaults.get("opacity", 0.88))))
    defaults["launch_mode"] = defaults["launch_mode"] if defaults["launch_mode"] in ("normal", "skip_permissions") else "normal"

    # 如果从旧路径加载了数据，迁移到新路径
    if config_sources[0] == _OLD_CONFIG_PATH and loaded:
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=False, indent=2)
            os.remove(_OLD_CONFIG_PATH)
        except (IOError, OSError):
            pass

    return defaults

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except (IOError, OSError):
        pass

def is_auto_start_enabled():
    return os.path.exists(os.path.join(STARTUP_FOLDER, STARTUP_LNK_NAME))

def toggle_auto_start(enable: bool):
    """启用/禁用开机自启。打包为 exe 时直接指向 exe 自身，无需 VBS。"""
    lnk = os.path.join(STARTUP_FOLDER, STARTUP_LNK_NAME)
    if enable:
        if _IS_FROZEN:
            # 打包模式：快捷方式直接指向 exe 自身，简洁可靠
            target = sys.executable
            workdir = os.path.dirname(sys.executable)
        else:
            # 开发模式：创建 VBS 通过 pythonw.exe 启动脚本
            vbs_path = os.path.join(SCRIPT_DIR, "launcher.vbs")
            script_path = os.path.join(SCRIPT_DIR, "claude_floating_launcher.py")
            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write('Set ws = CreateObject("WScript.Shell")\n')
                f.write(f'ws.Run """{_escape_ps_path(sys.executable)}"" ""{_escape_ps_path(script_path)}""", 0, False\n')
            target = vbs_path
            workdir = SCRIPT_DIR

        # 使用环境变量传参避免 PowerShell 注入
        ps_env = os.environ.copy()
        ps_env["CC_LNK"] = lnk
        ps_env["CC_TARGET"] = target
        ps_env["CC_WORKDIR"] = workdir
        ps = (
            '$ws=New-Object -ComObject WScript.Shell;'
            '$sc=$ws.CreateShortcut($env:CC_LNK);'
            '$sc.TargetPath=$env:CC_TARGET;'
            '$sc.WindowStyle=7;'
            '$sc.WorkingDirectory=$env:CC_WORKDIR;'
            '$sc.Description="Claude Code 浮窗";'
            '$sc.Save()'
        )
        r = subprocess.run(["powershell","-NoProfile","-Command",ps], env=ps_env, capture_output=True, text=True)
        return r.returncode == 0
    else:
        for p in [lnk, os.path.join(SCRIPT_DIR, "launcher.vbs")]:
            try:
                os.remove(p)
            except OSError:
                pass
        return True

# ── 启动 Claude Code ──────────────────────────────────
def launch_claude_code(config=None):
    if config is None: config = load_config()
    cmd = "claude --dangerously-skip-permissions" if config.get("launch_mode") == "skip_permissions" else "claude"

    # 确定工作目录：优先使用用户设置，为空则使用 USERPROFILE，再 fallback 到 WORKSPACE_DIR
    working_dir = config.get("working_directory", "").strip()
    if not working_dir:
        working_dir = os.environ.get("USERPROFILE", WORKSPACE_DIR)
    if not os.path.isdir(working_dir):
        working_dir = os.environ.get("USERPROFILE", WORKSPACE_DIR)

    try:
        subprocess.Popen(["wt","-d",working_dir,"cmd","/c",cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    except FileNotFoundError:
        try:
            subprocess.Popen(["cmd","/c","start","",cmd], cwd=working_dir, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            subprocess.Popen(["cmd","/c","start","",cmd], cwd=working_dir, creationflags=subprocess.CREATE_NO_WINDOW)

# ── 中文字体探测 ──────────────────────────────────────
def _get_cjk_font():
    db = QFontDatabase()
    families = set(db.families())
    for n in ["Microsoft YaHei","Microsoft YaHei UI","PingFang SC","SimHei","SimSun"]:
        if n in families: return n
    return FONT_FAMILY

# ── 设置对话框 ────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.result_config = None
        self._cjk = _get_cjk_font()
        self._setup_ui()

    def _font(self, size=12, bold=False):
        return QFont(self._cjk, size, QFont.Bold if bold else QFont.Normal)

    def _label(self, text, size=12, color="#3C3C43", bold=False):
        w = QLabel(text)
        w.setFont(self._font(size, bold=bold))
        w.setStyleSheet(f"color: {color};")
        return w

    def _setup_ui(self):
        self.setWindowTitle("浮窗设置")
        self.setFixedSize(400, 660)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setFont(self._font(9))
        self.setStyleSheet("QDialog { background: #F2F2F7; border: none; border-radius: 12px; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 16, 20, 16)

        title = self._label("Claude Code 浮窗设置", size=16, color="#1C1C1E")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(self._font(16, bold=True))
        layout.addWidget(title)

        # 通用按钮样式（提前定义，供后续各区块复用）
        btn_css = "QPushButton { background: #FFF; color: #007AFF; border: 1px solid #C7C7CC; border-radius: 8px; padding: 8px 16px; font-size: 12px; } QPushButton:hover { background: #F2F2F7; }"
        save_css = "QPushButton { background: #007AFF; color: #FFF; border: none; border-radius: 8px; padding: 8px 20px; font-size: 12px; font-weight: bold; } QPushButton:hover { background: #0066D6; }"

        # 启动方式
        box = QGroupBox("启动方式")
        box.setFont(self._font(10, bold=True))
        box.setStyleSheet("QGroupBox { color: #1C1C1E; border: none; padding-top: 12px; }")
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        self.rb_normal = QRadioButton("普通模式 — claude", box)
        self.rb_skip  = QRadioButton("跳过权限 — claude --dangerously-skip-permissions", box)
        for rb in [self.rb_normal, self.rb_skip]:
            rb.setFont(self._font(11))
            rb.setStyleSheet("QRadioButton { color: #3C3C43; spacing: 8px; } QRadioButton::indicator { width:16px; height:16px; } QRadioButton::indicator:unchecked { border:2px solid #C7C7CC; border-radius:8px; background:#FFF; } QRadioButton::indicator:checked { border:none; border-radius:8px; background:#007AFF; }")

        mode = self.config.get("launch_mode","normal")
        self.rb_normal.setChecked(mode != "skip_permissions")
        self.rb_skip.setChecked(mode == "skip_permissions")

        vl.addWidget(self.rb_normal)
        vl.addWidget(self.rb_skip)

        # 安全警告标签（仅在选中 skip-permissions 时显示）
        self.warn_label = QLabel(
            "⚠ 安全警告：此模式跳过所有权限检查，Claude Code 可自由\n"
            "执行命令、读写文件、访问网络。建议仅在受信任的项目中使用。"
        )
        self.warn_label.setFont(self._font(9, bold=True))
        self.warn_label.setStyleSheet(
            "QLabel { color: #FF3B30; background: #FFE5E5; border: 1px solid #FF3B30; "
            "border-radius: 6px; padding: 8px 10px; }"
        )
        self.warn_label.setWordWrap(True)
        self.warn_label.setVisible(mode == "skip_permissions")
        vl.addWidget(self.warn_label)
        self.rb_skip.toggled.connect(lambda checked: self.warn_label.setVisible(checked))

        vl.addWidget(self._label("点击浮窗时使用所选方式启动", 10, "#8E8E93"))
        layout.addWidget(box)

        # 大小
        box2 = QGroupBox("浮窗大小")
        box2.setFont(self._font(10, bold=True))
        box2.setStyleSheet(box.styleSheet())
        vl2 = QVBoxLayout(box2)
        row = QHBoxLayout()
        row.addWidget(self._label("边长:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(40, 90)
        self.size_slider.setValue(self.config.get("widget_size", DEFAULT_SIZE))
        self.size_slider.setStyleSheet("QSlider::groove:horizontal { height:4px; background:#E5E5EA; border-radius:2px; } QSlider::handle:horizontal { width:20px; height:20px; margin:-8px 0; background:#FFF; border:2px solid #007AFF; border-radius:10px; } QSlider::sub-page:horizontal { background:#007AFF; border-radius:2px; }")
        row.addWidget(self.size_slider)
        self.size_label = self._label(f"{self.size_slider.value()} px", bold=True)
        row.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v} px"))
        vl2.addLayout(row)
        layout.addWidget(box2)

        # 透明度
        box3 = QGroupBox("透明度")
        box3.setFont(self._font(10, bold=True))
        box3.setStyleSheet(box.styleSheet())
        vl3 = QVBoxLayout(box3)
        row3 = QHBoxLayout()
        row3.addWidget(self._label("不透明度:"))
        self.op_slider = QSlider(Qt.Horizontal)
        self.op_slider.setRange(40, 100)
        self.op_slider.setValue(int(self.config.get("opacity",0.88)*100))
        self.op_slider.setStyleSheet(self.size_slider.styleSheet())
        row3.addWidget(self.op_slider)
        self.op_label = self._label(f"{self.op_slider.value()}%", bold=True)
        row3.addWidget(self.op_label)
        self.op_slider.valueChanged.connect(lambda v: self.op_label.setText(f"{v}%"))
        vl3.addLayout(row3)
        layout.addWidget(box3)

        # 吸附设置
        box_snap = QGroupBox("边缘吸附")
        box_snap.setFont(self._font(10, bold=True))
        box_snap.setStyleSheet(box.styleSheet())
        vl_snap = QVBoxLayout(box_snap)
        vl_snap.setSpacing(6)

        snap_css = (
            "QCheckBox { color: #3C3C43; spacing: 8px; font-size: 11px; }"
            "QCheckBox::indicator { width: 16px; height: 16px; }"
            "QCheckBox::indicator:unchecked { border: 2px solid #C7C7CC; border-radius: 4px; background: #FFF; }"
            "QCheckBox::indicator:checked { border: none; border-radius: 4px; background: #007AFF; }"
        )

        self.cb_snap_enabled = QCheckBox("启用边缘吸附（拖拽到屏幕边缘自动贴边）")
        self.cb_snap_enabled.setFont(self._font(11))
        self.cb_snap_enabled.setStyleSheet(snap_css)
        self.cb_snap_enabled.setChecked(self.config.get("snap_enabled", True))
        vl_snap.addWidget(self.cb_snap_enabled)

        self.cb_snap_hidden = QCheckBox("自动隐藏（鼠标离开后滑出屏幕，靠近时滑回）")
        self.cb_snap_hidden.setFont(self._font(11))
        self.cb_snap_hidden.setStyleSheet(snap_css)
        self.cb_snap_hidden.setChecked(self.config.get("snap_hidden", True))
        self.cb_snap_hidden.setEnabled(self.cb_snap_enabled.isChecked())
        self.cb_snap_enabled.toggled.connect(lambda v: self.cb_snap_hidden.setEnabled(v))
        vl_snap.addWidget(self.cb_snap_hidden)

        vl_snap.addWidget(self._label("拖拽到屏幕边缘自动贴边，可设置自动隐藏以节省空间", 10, "#8E8E93"))
        layout.addWidget(box_snap)

        # 默认启动目录
        box4 = QGroupBox("默认启动目录")
        box4.setFont(self._font(10, bold=True))
        box4.setStyleSheet(box.styleSheet())
        vl4 = QVBoxLayout(box4)
        vl4.setSpacing(8)

        # 当前目录显示
        self.dir_edit = QLineEdit()
        self.dir_edit.setFont(self._font(10))
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setStyleSheet(
            "QLineEdit { background: #FFF; color: #1C1C1E; border: 1px solid #C7C7CC; "
            "border-radius: 6px; padding: 6px 8px; }"
        )
        wd = self.config.get("working_directory", "").strip()
        if not wd:
            wd = os.environ.get("USERPROFILE", "")
        self.dir_edit.setText(wd)
        self.dir_edit.setToolTip("Claude Code 将在此目录下启动。留空则使用用户主目录。")
        vl4.addWidget(self.dir_edit)

        # 浏览 + 重置按钮
        dir_btn_row = QHBoxLayout()
        dir_btn_row.setSpacing(8)

        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet(btn_css)
        browse_btn.clicked.connect(self._browse_folder)
        dir_btn_row.addWidget(browse_btn)

        reset_btn = QPushButton("重置为默认")
        reset_btn.setStyleSheet(btn_css)
        reset_btn.clicked.connect(self._reset_dir)
        dir_btn_row.addWidget(reset_btn)

        dir_btn_row.addStretch()
        vl4.addLayout(dir_btn_row)

        vl4.addWidget(self._label("Claude Code 启动时的默认工作目录", 10, "#8E8E93"))
        layout.addWidget(box4)

        layout.addStretch()

        # 按钮
        bl = QHBoxLayout()
        bl.setSpacing(10)

        preview_btn = QPushButton("应用")
        preview_btn.setStyleSheet(btn_css)
        preview_btn.clicked.connect(self._preview)
        bl.addWidget(preview_btn)

        bl.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(btn_css)
        cancel_btn.clicked.connect(self.reject)
        bl.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(save_css)
        save_btn.clicked.connect(self._save)
        bl.addWidget(save_btn)
        layout.addLayout(bl)

    def _collect(self):
        return {
            "launch_mode": "skip_permissions" if self.rb_skip.isChecked() else "normal",
            "widget_size": self.size_slider.value(),
            "opacity": self.op_slider.value() / 100.0,
            "working_directory": self.dir_edit.text().strip(),
            "snap_enabled": self.cb_snap_enabled.isChecked(),
            "snap_hidden": self.cb_snap_hidden.isChecked(),
        }
    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "选择 Claude Code 默认启动目录",
            self.dir_edit.text() or os.environ.get("USERPROFILE", ""),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder:
            self.dir_edit.setText(folder)
    def _reset_dir(self):
        self.dir_edit.setText(os.environ.get("USERPROFILE", ""))
    def _preview(self):
        self.result_config = self._collect()
        self.result_config["_preview"] = True
        self.accept()
    def _save(self):
        # 如果选中跳过权限模式，弹出安全确认
        if self.rb_skip.isChecked():
            reply = QMessageBox.warning(
                self, "安全确认 — 跳过权限模式",
                "您正在启用「跳过权限」模式。\n\n"
                "在此模式下，Claude Code 可以：\n"
                "• 执行任意终端命令\n"
                "• 读取和修改文件系统中的任何文件\n"
                "• 访问网络资源\n"
                "• 以上操作均不会弹出权限确认提示\n\n"
                "这可能导致数据丢失或安全风险。\n"
                "建议仅在完全受信任的项目中使用。\n\n"
                "确定要启用此模式吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.result_config = self._collect()
        self.result_config["_preview"] = False
        self.accept()

# ── 浮窗主体 ──────────────────────────────────────────
class FloatingWidget(QWidget):
    launch_requested  = pyqtSignal()
    quit_requested    = pyqtSignal()
    settings_requested = pyqtSignal()

    CLICK_THRESHOLD = 4

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.is_hovered = False
        self.is_pressed = False
        self.base_size = self.config.get("widget_size", DEFAULT_SIZE)
        self.current_size = self.base_size
        self.icon_pixmap = None

        # 拖拽状态
        self._drag_active = False
        self._drag_origin = QPoint()
        self._window_origin = QPoint()

        # 按压缩放 (0.0 ~ 1.0，1.0 = 正常)
        self._press_scale = 1.0
        # 涟漪 (0.0 ~ 1.0)
        self._ripple_progress = 0.0
        self._ripple_pos = QPoint()
        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(16)
        self._ripple_timer.timeout.connect(self._tick_ripple)

        # 吸附状态
        self._snapped = False
        self._snap_edge = ""
        self._visible_offset = 0  # 完全显示时的屏幕坐标
        self._hidden_offset = 0   # 隐藏时的偏移
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._auto_hide)
        # 边缘检测条（透明窗口，用于检测鼠标靠近屏幕边缘）
        self._edge_detector = None

        self._load_icon()
        self._setup_ui()
        self._apply_opacity()
        self._restore_position()

    def _load_icon(self):
        for p in (PNG_PATH, ICO_PATH):
            if os.path.exists(p):
                pix = QPixmap(p)
                if not pix.isNull():
                    self.icon_pixmap = pix
                    return
        self.icon_pixmap = None

    def _setup_ui(self):
        s = self.current_size
        self.setFixedSize(s, s)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._update_mask()

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(100)
        self._hover_timer.timeout.connect(self._check_hover)
        self._hover_timer.start()

        # 尺寸动画
        self._size_anim = QPropertyAnimation(self, b"widget_size_prop")
        self._size_anim.setDuration(200)
        self._size_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 按压动画
        self._press_anim = QPropertyAnimation(self, b"press_scale")
        self._press_anim.setDuration(100)
        self._press_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._press_anim.finished.connect(self._on_press_anim_done)

        # 全局快捷键
        self._hotkey_id = 1
        self._hotkey_registered = False
        self._register_hotkey()

    # ── 全局快捷键 ────────────────────────────────
    def _register_hotkey(self):
        """注册 Ctrl+Alt+C 全局快捷键"""
        if self._hotkey_registered:
            return
        try:
            MOD_ALT = 0x0001
            MOD_CONTROL = 0x0002
            VK_C = 0x43
            result = ctypes.windll.user32.RegisterHotKey(
                int(self.winId()), self._hotkey_id, MOD_CONTROL | MOD_ALT, VK_C
            )
            self._hotkey_registered = (result != 0)
        except Exception:
            self._hotkey_registered = False

    def _unregister_hotkey(self):
        """注销全局快捷键"""
        if self._hotkey_registered:
            try:
                ctypes.windll.user32.UnregisterHotKey(int(self.winId()), self._hotkey_id)
            except Exception:
                pass
            self._hotkey_registered = False

    def nativeEvent(self, eventType, message):
        """处理 Windows 原生消息（WM_HOTKEY）"""
        WM_HOTKEY = 0x0312
        if eventType == "windows_generic_MSG":
            # message 是 sip.voidptr，需要用 ctypes 解析 MSG 结构体
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt", POINT),
                ]
            msg = MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
                if self.isVisible():
                    self.hide()
                else:
                    self.show()
                return True, 0
        return super().nativeEvent(eventType, message)

    def showEvent(self, event):
        """显示时启动 hover 检测"""
        super().showEvent(event)
        if not self._hover_timer.isActive():
            self._hover_timer.start()

    def hideEvent(self, event):
        """隐藏时停止 hover 检测以节省 CPU"""
        super().hideEvent(event)
        self._hover_timer.stop()
        # 重置 hover 状态
        if self.is_hovered:
            self.is_hovered = False
            self._animate_size(self.base_size)

    # ── 按压 + 涟漪属性 ────────────────────────────
    def _tick_ripple(self):
        self._ripple_progress += 0.04
        if self._ripple_progress >= 1.0:
            self._ripple_progress = 0.0
            self._ripple_timer.stop()
        self.update()

    def get_press_scale(self): return self._press_scale
    def set_press_scale(self, v):
        self._press_scale = v
        self.update()
    press_scale = property(get_press_scale, set_press_scale)

    def _on_press_anim_done(self):
        self._press_anim.stop()
        self._press_anim.setDuration(300)
        self._press_anim.setEasingCurve(QEasingCurve.OutBack)
        self._press_anim.setStartValue(self._press_scale)
        self._press_anim.setEndValue(1.0)
        self._press_anim.start()

    def _apply_opacity(self):
        self.setWindowOpacity(max(0.3, min(1.0, self.config.get("opacity", 0.88))))

    def _update_mask(self):
        s = self.current_size
        r = CORNER_RADIUS
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, s, s), r, r)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def _check_hover(self):
        # 用 mapFromGlobal 替代 frameGeometry().contains() —
        # WA_ShowWithoutActivating 下 frameGeometry 坐标可能偏移
        local_pos = self.mapFromGlobal(QCursor.pos())
        was = self.is_hovered
        self.is_hovered = self.rect().contains(local_pos)
        hover_size = int(self.base_size * HOVER_SCALE)
        if self.is_hovered and not was:
            self._animate_size(hover_size)
        elif not self.is_hovered and was:
            self._animate_size(self.base_size)

    def _animate_size(self, target):
        if self.current_size == target: return
        self._size_anim.stop()
        self._size_anim.setStartValue(self.current_size)
        self._size_anim.setEndValue(target)
        self._size_anim.start()

    def get_widget_size_prop(self): return self.current_size
    def set_widget_size_prop(self, v):
        self.current_size = v
        c = self.geometry().center()
        self.setFixedSize(v, v)
        self._update_mask()
        ng = self.frameGeometry()
        ng.moveCenter(c)
        self.move(ng.topLeft())
    widget_size_prop = property(get_widget_size_prop, set_widget_size_prop)

    def _restore_position(self):
        x, y = self.config.get("window_x", -1), self.config.get("window_y", -1)
        if x < 0 or y < 0:
            screen = QApplication.primaryScreen()
            if screen:
                g = screen.availableGeometry()
                x = g.right() - 80
                y = (g.top() + g.bottom()) // 2 - self.current_size // 2

        edge = self.config.get("snap_edge", "right")
        # 如果启用了吸附，调整到正确位置
        if self.config.get("snap_enabled", True):
            screen = self._screen_geometry()
            if edge == "right":
                x = screen.right() - self.current_size - 2
            elif edge == "left":
                x = screen.left() + 2
            elif edge == "top":
                y = screen.top() + 2
            elif edge == "bottom":
                y = screen.bottom() - self.current_size - 2

        self.move(x, y)
        self._visible_offset = self.pos().x() if edge in ("left", "right") else self.pos().y()

        # 如果吸附 + 自动隐藏，初始化隐藏状态
        if self.config.get("snap_enabled", True) and self.config.get("snap_hidden", True):
            self._snapped = True
            self._snap_edge = edge
            self._setup_edge_detector()
            self._do_hide()

    # ── 边缘吸附系统 ────────────────────────────────
    def _screen_geometry(self):
        """获取当前屏幕的工作区域"""
        screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
        if screen:
            return screen.availableGeometry()
        return QRect(0, 0, 1920, 1080)

    def _check_snap(self):
        """检测拖拽后是否应吸附到屏幕边缘"""
        if not self.config.get("snap_enabled", True):
            return

        SNAP_THRESHOLD = 25
        g = self._screen_geometry()
        cx = self.pos().x() + self.current_size // 2
        cy = self.pos().y() + self.current_size // 2

        # 检测距离每个边缘的距离
        dist_left = cx - g.left()
        dist_right = g.right() - cx
        dist_top = cy - g.top()
        dist_bottom = g.bottom() - cy

        nearest = min(
            (dist_left, "left"), (dist_right, "right"),
            (dist_top, "top"), (dist_bottom, "bottom"), key=lambda d: d[0]
        )

        if nearest[0] < SNAP_THRESHOLD + self.current_size // 2:
            edge = nearest[1]
            self._snapped = True
            self._snap_edge = edge
            self.config["snap_edge"] = edge

            # 吸附到边缘
            if edge == "left":
                new_x = g.left() + 2
                new_y = max(g.top(), min(g.bottom() - self.current_size, self.pos().y()))
            elif edge == "right":
                new_x = g.right() - self.current_size - 2
                new_y = max(g.top(), min(g.bottom() - self.current_size, self.pos().y()))
            elif edge == "top":
                new_x = max(g.left(), min(g.right() - self.current_size, self.pos().x()))
                new_y = g.top() + 2
            else:  # bottom
                new_x = max(g.left(), min(g.right() - self.current_size, self.pos().x()))
                new_y = g.bottom() - self.current_size - 2

            self.move(new_x, new_y)
            self._visible_offset = new_x if edge in ("left", "right") else new_y
            save_config(self.config)

            # 自动隐藏
            if self.config.get("snap_hidden", True):
                self._setup_edge_detector()
                self._hide_timer.start(600)
        else:
            self._snapped = False
            self._snap_edge = ""
            self._remove_edge_detector()
            self.config["snap_edge"] = ""
            save_config(self.config)

    def _setup_edge_detector(self):
        """创建屏幕边缘的透明检测窗口"""
        self._remove_edge_detector()
        g = self._screen_geometry()
        edge = self._snap_edge
        sz = self.current_size

        # 必须子类化才能正确重写 C++ 虚函数 enterEvent
        parent_widget = self

        class HoverDetector(QWidget):
            def enterEvent(self_2, event):
                parent_widget._on_edge_detected()

        detector = HoverDetector()
        detector.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        detector.setAttribute(Qt.WA_TranslucentBackground)
        detector.setAttribute(Qt.WA_ShowWithoutActivating)
        detector.setStyleSheet("background: transparent;")
        detector.setMouseTracking(True)

        # 检测条：沿屏幕边缘 3px 宽的细条
        if edge == "right":
            detector.setGeometry(g.right() - 3, self.pos().y() - 5, 3, sz + 10)
        elif edge == "left":
            detector.setGeometry(g.left(), self.pos().y() - 5, 3, sz + 10)
        elif edge == "top":
            detector.setGeometry(self.pos().x() - 5, g.top(), sz + 10, 3)
        else:  # bottom
            detector.setGeometry(self.pos().x() - 5, g.bottom() - 3, sz + 10, 3)

        detector.show()
        self._edge_detector = detector

    def _remove_edge_detector(self):
        if self._edge_detector:
            try:
                self._edge_detector.close()
                self._edge_detector.deleteLater()
            except Exception:
                pass
            self._edge_detector = None

    def _on_edge_detected(self):
        """鼠标靠近隐藏的吸附边缘，滑出显示"""
        self._hide_timer.stop()
        if self._snapped:
            self._show_full()

    def _do_hide(self):
        """将 widget 滑出屏幕（仅留一小部分可见）"""
        if not self._snapped:
            return
        g = self._screen_geometry()
        s = self.current_size
        edge = self._snap_edge
        visible_tab = 6  # 留在屏幕内的像素

        if edge == "right":
            target = g.right() - visible_tab
        elif edge == "left":
            target = g.left() - s + visible_tab
        elif edge == "top":
            target = g.top() - s + visible_tab
        else:  # bottom
            target = g.bottom() - visible_tab

        self._hidden_offset = target
        self._animate_slide(target, edge)

    def _show_full(self):
        """将 widget 完全滑入屏幕"""
        if not self._snapped:
            return
        g = self._screen_geometry()
        s = self.current_size
        edge = self._snap_edge

        if edge == "right":
            target = g.right() - s - 2
        elif edge == "left":
            target = g.left() + 2
        elif edge == "top":
            target = g.top() + 2
        else:
            target = g.bottom() - s - 2

        self._animate_slide(target, edge)
        # 设置延迟重新隐藏
        self._hide_timer.start(self.config.get("hide_delay_ms", 800))

    def _auto_hide(self):
        """计时器触发：自动隐藏"""
        if self._snapped and not self.is_hovered:
            self._do_hide()

    def _animate_slide(self, target, edge):
        """滑动动画"""
        anim = QPropertyAnimation(self, b"slide_pos")
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setStartValue(self.pos().x() if edge in ("left", "right") else self.pos().y())
        anim.setEndValue(target)
        anim.start()
        # 保持引用防止被垃圾回收
        self._slide_anim = anim

    def get_slide_pos(self):
        return self.pos().x() if self._snap_edge in ("left", "right") else self.pos().y()

    def set_slide_pos(self, v):
        if self._snap_edge == "left" or self._snap_edge == "right":
            self.move(int(v), self.pos().y())
        elif self._snap_edge in ("top", "bottom"):
            self.move(self.pos().x(), int(v))
    slide_pos = property(get_slide_pos, set_slide_pos)

    def _check_hover(self):
        # 用 mapFromGlobal 替代 frameGeometry().contains() —
        # WA_ShowWithoutActivating 下 frameGeometry 坐标可能偏移
        local_pos = self.mapFromGlobal(QCursor.pos())
        was = self.is_hovered
        self.is_hovered = self.rect().contains(local_pos)

        # 吸附模式下自动管理显示/隐藏
        if self._snapped and self.config.get("snap_hidden", True):
            if self.is_hovered and not was:
                self._show_full()
            elif not self.is_hovered and was:
                self._hide_timer.start(self.config.get("hide_delay_ms", 800))

        hover_size = int(self.base_size * HOVER_SCALE)
        if self.is_hovered and not was:
            self._animate_size(hover_size)
        elif not self.is_hovered and was:
            self._animate_size(self.base_size)

    # ── 绘制（7 层玻璃 + 涟漪）──────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scale = self._press_scale
        s = self.current_size
        r = CORNER_RADIUS
        cx, cy = s / 2, s / 2

        if scale != 1.0:
            painter.translate(cx, cy)
            painter.scale(scale, scale)
            painter.translate(-cx, -cy)

        shadow_boost = 1.0 + (0.8 if self.is_hovered else 0)
        hover_alpha = 30 if self.is_hovered else 0
        border_alpha_boost = 1.3 if self.is_hovered else 1.0

        # ── Layer 0: 阴影（悬浮时加深 + 偏移增大） ──
        painter.setPen(Qt.NoPen)
        h_offset = 1 if self.is_hovered else 0
        for offset, base_alpha in [(0, 18), (2, 10), (4, 5)]:
            a = min(255, int(base_alpha * shadow_boost))
            so = offset + h_offset
            sr = QRectF(2 + so, 3 + so, s, s)
            sp = QPainterPath()
            sp.addRoundedRect(sr, r, r)
            painter.setBrush(QColor(*IOS_SHADOW, a))
            painter.drawPath(sp)

        # ── Layer 1: 玻璃基底 ──
        base_path = QPainterPath()
        base_path.addRoundedRect(QRectF(0, 0, s, s), r, r)

        radial = QRadialGradient(cx, cy, s * 0.7)
        radial.setColorAt(0.0, QColor(255, 255, 255, 18))
        radial.setColorAt(1.0, QColor(255, 255, 255, 0))

        diag = QLinearGradient(0, 0, s, s)
        diag.setColorAt(0.0, QColor(*IOS_GLASS_BG, 240))
        diag.setColorAt(0.35, QColor(*IOS_GLASS_BG, 228))
        diag.setColorAt(0.65, QColor(245, 244, 249, 218))
        diag.setColorAt(1.0, QColor(238, 237, 242, 205))

        painter.setBrush(QBrush(diag))
        painter.setPen(Qt.NoPen)
        painter.drawPath(base_path)
        painter.setBrush(QBrush(radial))
        painter.drawPath(base_path)

        # ── Layer 2: 玻璃边框（悬浮时加亮） ──
        border_grad = QLinearGradient(0, 0, 0, s)
        border_grad.setColorAt(0.0, QColor(*IOS_BORDER, int(190 * border_alpha_boost)))
        border_grad.setColorAt(0.45, QColor(*IOS_BORDER, int(110 * border_alpha_boost)))
        border_grad.setColorAt(1.0, QColor(*IOS_BORDER, int(55 * border_alpha_boost)))
        pen = QPen(QBrush(border_grad), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRect(0, 0, s - 1, s - 1), r, r)

        # ── Layer 3: 顶面柔光 ──
        hl_path = QPainterPath()
        hl_path.addRoundedRect(QRectF(0, 0, s, s), r, r)
        hl_grad = QLinearGradient(0, 0, 0, s * 0.58)
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, 125))
        hl_grad.setColorAt(0.45, QColor(255, 255, 255, 45))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(hl_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(hl_path)

        # ── Layer 4: 内阴影 ──
        inner_shadow = QRadialGradient(cx + s * 0.15, cy + s * 0.15, s * 0.75)
        inner_shadow.setColorAt(0.0, QColor(0, 0, 0, 0))
        inner_shadow.setColorAt(0.6, QColor(0, 0, 0, 0))
        inner_shadow.setColorAt(0.9, QColor(0, 0, 0, 8))
        inner_shadow.setColorAt(1.0, QColor(0, 0, 0, 20))
        painter.setBrush(QBrush(inner_shadow))
        painter.drawPath(hl_path)

        # ── Layer 5: 镜面反光 ──
        spec_r = s * 0.18
        spec_cx = s * 0.28
        spec_cy = s * 0.25
        spec_grad = QRadialGradient(spec_cx, spec_cy, spec_r * 1.5)
        spec_grad.setColorAt(0.0, QColor(255, 255, 255, 100))
        spec_grad.setColorAt(0.25, QColor(255, 255, 255, 55))
        spec_grad.setColorAt(0.6, QColor(255, 255, 255, 10))
        spec_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(spec_grad))
        painter.drawPath(hl_path)

        # ── Layer 6: 悬停蓝色微染 ──
        if hover_alpha > 0:
            painter.setBrush(QColor(*IOS_ACCENT, hover_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawPath(hl_path)

        # ── Layer 7: 图标 ──
        icon_frac = 0.52
        icon_size = int(s * icon_frac)
        icon_x = int((s - icon_size) / 2)
        icon_y = int((s - icon_size) / 2)

        if self.icon_pixmap and not self.icon_pixmap.isNull():
            pix = self.icon_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(icon_x, icon_y, pix)
        else:
            font = QFont(FONT_FAMILY, int(s * 0.40), QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(*IOS_TEXT, 200))
            painter.drawText(QRect(0, 0, s, s), Qt.AlignCenter, "CC")

        # ── 涟漪 ──
        if self._ripple_progress > 0 and not self._ripple_pos.isNull():
            rp = self._ripple_progress
            max_rad = s * 0.8
            rad = max_rad * rp
            alpha = int(60 * (1.0 - rp))
            ripple_grad = QRadialGradient(self._ripple_pos, rad)
            ripple_grad.setColorAt(0.0, QColor(*IOS_ACCENT, alpha))
            ripple_grad.setColorAt(1.0, QColor(*IOS_ACCENT, 0))
            painter.setBrush(QBrush(ripple_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(hl_path)

        # ── 安全模式指示器：skip-permissions 时右上角红色圆点 ──
        if self.config.get("launch_mode") == "skip_permissions":
            dot_r = max(4, s * 0.08)
            dot_margin = s * 0.18
            dot_cx = s - dot_margin
            dot_cy = dot_margin
            painter.setBrush(QColor(255, 59, 48, 220))  # iOS red
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dot_cx, dot_cy), dot_r, dot_r)

        painter.end()

    # ── 鼠标事件（拖拽修复）─────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_origin = event.globalPos()
            self._window_origin = self.pos()
            self._drag_active = False
            # 按压反馈
            self.is_pressed = True
            self._press_anim.stop()
            self._press_anim.setDuration(100)
            self._press_anim.setEasingCurve(QEasingCurve.OutCubic)
            self._press_anim.setStartValue(self._press_scale)
            self._press_anim.setEndValue(PRESS_SCALE)
            self._press_anim.start()
        elif event.button() == Qt.RightButton:
            self._context_menu()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        delta = (event.globalPos() - self._drag_origin).manhattanLength()
        if not self._drag_active and delta > self.CLICK_THRESHOLD:
            self._drag_active = True
        if self._drag_active:
            new_pos = self._window_origin + (event.globalPos() - self._drag_origin)
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._drag_active:
                # 点击 → 涟漪 + 启动
                self._start_ripple(event.pos())
                self.launch_requested.emit()
            else:
                # 拖拽结束 → 保存位置 + 检测吸附
                self.config["window_x"] = self.pos().x()
                self.config["window_y"] = self.pos().y()
                self._check_snap()
                # 无论是否吸附都保存位置
                self.config["window_x"] = self.pos().x()
                self.config["window_y"] = self.pos().y()
                save_config(self.config)
            self._drag_active = False
        self.is_pressed = False

    def _start_ripple(self, pos):
        self._ripple_pos = pos
        self._ripple_progress = 0.01
        self._ripple_timer.start()

    def _context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 4px 0; }
            QMenu::item { padding: 7px 32px 7px 16px; font-size: 12px; color: #1C1C1E; }
            QMenu::item:selected { background: #007AFF; color: #FFF; border-radius: 4px; margin: 1px 6px; }
            QMenu::separator { height: 1px; background: #E5E5EA; margin: 4px 8px; }
        """)

        menu.addAction("启动 Claude Code", self.launch_requested.emit)
        menu.addSeparator()
        menu.addAction("设置...", self.settings_requested.emit)
        menu.addSeparator()

        auto = menu.addAction("开机自启")
        auto.setCheckable(True)
        auto.setChecked(is_auto_start_enabled())
        auto.triggered.connect(lambda checked: toggle_auto_start(checked))

        menu.addSeparator()
        menu.addAction("退出", self.quit_requested.emit)

        menu.exec_(QCursor.pos())

    def closeEvent(self, event):
        self._unregister_hotkey()
        pos = self.pos()
        self.config["window_x"] = pos.x()
        self.config["window_y"] = pos.y()
        save_config(self.config)
        super().closeEvent(event)

    # ── 应用设置 ────────────────────────────────────
    def apply_settings(self, new_cfg, preview_only=False):
        changed = False
        ns = new_cfg.get("widget_size", self.base_size)
        if ns != self.base_size:
            self.base_size = ns
            self.set_widget_size_prop(ns)
            changed = True

        self.config["opacity"] = new_cfg.get("opacity", 0.88)
        self._apply_opacity()
        self.config["launch_mode"] = new_cfg.get("launch_mode", "normal")
        self.config["working_directory"] = new_cfg.get("working_directory", "")

        # 吸附设置
        old_snap = self.config.get("snap_enabled", True)
        old_hidden = self.config.get("snap_hidden", True)
        self.config["snap_enabled"] = new_cfg.get("snap_enabled", True)
        self.config["snap_hidden"] = new_cfg.get("snap_hidden", True)

        if not preview_only:
            self.config["widget_size"] = ns
            self.config["window_x"] = self.pos().x()
            self.config["window_y"] = self.pos().y()
            save_config(self.config)

            # 吸附设置变更后重新应用
            if self.config["snap_enabled"] != old_snap or self.config["snap_hidden"] != old_hidden:
                if not self.config["snap_enabled"]:
                    self._snapped = False
                    self._remove_edge_detector()
                elif self.config["snap_hidden"] and self._snapped:
                    self._do_hide()
                else:
                    self._show_full()
        if changed:
            self.update()


# ── 主入口 ──────────────────────────────────────────
def main():
    # ── 崩溃日志：写入桌面文件便于诊断 ──
    CRASH_LOG = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "ClaudeFloat_crash.log")
    try:
        _main()
    except Exception:
        import traceback
        try:
            with open(CRASH_LOG, "w", encoding="utf-8") as f:
                f.write(f"ClaudeFloat v{VERSION} Crash Report\n")
                f.write(f"Time: {__import__('datetime').datetime.now()}\n")
                f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        raise

def _main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("claude.floating.launcher")
    except Exception: pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Claude Code 浮窗")
    app.setFont(QFont(FONT_FAMILY, 9))

    config = load_config()
    widget = FloatingWidget()

    # ── 设置对话框 ──
    def open_settings():
        dlg = SettingsDialog(widget.config, parent=widget)
        if dlg.exec_() == QDialog.Accepted and dlg.result_config:
            preview = dlg.result_config.pop("_preview", False)
            widget.apply_settings(dlg.result_config, preview_only=preview)

    def do_launch():
        launch_claude_code(widget.config)

    # ── 系统托盘 ──
    tray_menu = QMenu()
    tray_menu.setStyleSheet("""
        QMenu { background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 4px 0; }
        QMenu::item { padding: 7px 32px 7px 16px; font-size: 12px; color: #1C1C1E; }
        QMenu::item:selected { background: #007AFF; color: #FFF; border-radius: 4px; margin: 1px 6px; }
        QMenu::separator { height: 1px; background: #E5E5EA; margin: 4px 8px; }
    """)

    tray_menu.addAction("显示浮窗", widget.show)
    tray_menu.addSeparator()
    tray_menu.addAction("启动 Claude Code", do_launch)
    tray_menu.addSeparator()
    tray_menu.addAction("设置...", open_settings)
    tray_menu.addSeparator()

    tray_auto = tray_menu.addAction("开机自启")
    tray_auto.setCheckable(True)
    tray_auto.setChecked(is_auto_start_enabled())
    tray_auto.triggered.connect(lambda c: toggle_auto_start(c))

    tray_menu.addSeparator()
    tray_menu.addAction("退出", app.quit)

    tray_icon = QSystemTrayIcon()
    if os.path.exists(ICO_PATH):
        tray_icon.setIcon(QIcon(ICO_PATH))
    else:
        pix = QPixmap(32, 32)
        pix.fill(QColor(*IOS_ACCENT))
        tray_icon.setIcon(QIcon(pix))

    tray_icon.setToolTip("Claude Code 浮窗 — 点击启动 | Ctrl+Alt+C 显示/隐藏")
    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(lambda r: widget.show() if r == QSystemTrayIcon.DoubleClick else None)
    tray_icon.show()
    tray_icon.showMessage("Claude Code 浮窗", "浮窗已启动", QSystemTrayIcon.Information, 2000)

    widget.launch_requested.connect(do_launch)
    widget.quit_requested.connect(app.quit)
    widget.settings_requested.connect(open_settings)
    widget.show()

    if config.get("auto_start") and not is_auto_start_enabled():
        toggle_auto_start(True)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
