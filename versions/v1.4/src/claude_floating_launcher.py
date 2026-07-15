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
import shutil
import ctypes
import logging
from logging.handlers import RotatingFileHandler
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
    Qt, QPoint, QPointF, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QRectF
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

# ── 日志系统 ──────────────────────────────────────────
_logger = None

def _setup_logger():
    """初始化日志系统（RotatingFileHandler, 最多 5 个文件, 每个最大 1MB）"""
    global _logger
    if _logger is not None:
        return _logger

    log_dir = os.path.join(_get_config_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ClaudeFloat.log")

    logger = logging.getLogger("ClaudeFloat")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        _logger = logger
        return logger

    handler = RotatingFileHandler(
        log_path, maxBytes=1 * 1024 * 1024, backupCount=4, encoding="utf-8"
    )
    handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)-5s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    _logger = logger
    return logger

def _log():
    """获取 logger 实例（惰性初始化，避免循环依赖）"""
    global _logger
    if _logger is None:
        return _setup_logger()
    return _logger

STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
STARTUP_LNK_NAME = "ClaudeCode浮窗.lnk"

def _escape_ps_path(path):
    """转义路径中的特殊字符以便安全嵌入 PowerShell 单引号字符串"""
    return path.replace("'", "''")

# ── iOS 风格配色 ──────────────────────────────────────
THEMES = {
    "light": {
        "GLASS_BG":   (255, 255, 255),   # 毛玻璃白底
        "BORDER":     (255, 255, 255),   # 玻璃边框
        "SHADOW":     (0, 0, 0),         # 柔和阴影
        "ACCENT":     (0, 122, 255),     # iOS 蓝 #007AFF
        "TEXT":       (28, 28, 30),      # 深色文字 #1C1C1E
        "HINT":       (142, 142, 147),   # 系统灰 #8E8E93
        "SURFACE":    (242, 242, 247),   # 浅灰底 #F2F2F7
        "SEPARATOR":  (229, 229, 234),   # 分隔线 #E5E5EA
    },
    "dark": {
        "GLASS_BG":   (28, 28, 30),      # 暗色毛玻璃 #1C1C1E
        "BORDER":     (72, 72, 74),      # 暗色边框 #48484A
        "SHADOW":     (0, 0, 0),         # 阴影（不变）
        "ACCENT":     (10, 132, 255),    # iOS 暗色蓝 #0A84FF
        "TEXT":       (242, 242, 247),   # 浅色文字 #F2F2F7
        "HINT":       (152, 152, 157),   # 暗色灰 #98989D
        "SURFACE":    (44, 44, 46),      # 深灰底 #2C2C2E
        "SEPARATOR":  (56, 56, 58),      # 暗色分隔线 #38383A
    },
}

def get_colors(theme="light"):
    """返回当前主题的配色字典"""
    t = THEMES.get(theme, THEMES["light"])
    return t

# 兼容别名：模块加载时使用默认 light 主题
_LIGHT = THEMES["light"]
IOS_GLASS_BG   = _LIGHT["GLASS_BG"]
IOS_BORDER     = _LIGHT["BORDER"]
IOS_SHADOW     = _LIGHT["SHADOW"]
IOS_ACCENT     = _LIGHT["ACCENT"]
IOS_TEXT       = _LIGHT["TEXT"]
IOS_HINT       = _LIGHT["HINT"]
IOS_SURFACE    = _LIGHT["SURFACE"]

FONT_FAMILY = "Microsoft YaHei"
VERSION = "1.4.0"

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
        "cleanup_on_quit": False,
        "theme": "light",
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
                _log().debug("配置加载自: %s", src)
            except (json.JSONDecodeError, IOError):
                _log().warning("配置加载失败: %s", src)

    defaults.update(loaded)

    # ── 值校验：防止损坏的配置导致不可恢复状态 ──
    defaults["widget_size"] = max(30, min(200, int(defaults.get("widget_size", DEFAULT_SIZE))))
    defaults["opacity"] = max(0.1, min(1.0, float(defaults.get("opacity", 0.88))))
    defaults["launch_mode"] = defaults["launch_mode"] if defaults["launch_mode"] in ("normal", "skip_permissions") else "normal"
    defaults["theme"] = defaults["theme"] if defaults.get("theme") in ("light", "dark") else "light"

    # 首次启动时检测 Windows 系统主题
    if not loaded:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            apps_use_light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            if apps_use_light == 0:
                defaults["theme"] = "dark"
                _log().info("检测到 Windows 深色主题，自动设置为暗色模式")
        except Exception:
            pass

    # 如果从旧路径加载了数据，迁移到新路径
    if config_sources[0] == _OLD_CONFIG_PATH and loaded:
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=False, indent=2)
            os.remove(_OLD_CONFIG_PATH)
            _log().info("配置已迁移: %s → %s", _OLD_CONFIG_PATH, CONFIG_PATH)
        except (IOError, OSError):
            pass

    return defaults

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        _log().debug("配置已保存 (%d 键)", len(config))
    except (IOError, OSError):
        _log().warning("配置保存失败: %s", CONFIG_PATH)

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
        if r.returncode == 0:
            _log().info("开机自启已启用: %s", lnk)
        else:
            _log().warning("开机自启设置失败: %s", r.stderr.strip() if r.stderr else "unknown")
        return r.returncode == 0
    else:
        for p in [lnk, os.path.join(SCRIPT_DIR, "launcher.vbs")]:
            try:
                os.remove(p)
            except OSError:
                pass
        _log().info("开机自启已禁用")
        return True

# ── 启动 Claude Code ──────────────────────────────────
def launch_claude_code(config=None):
    if config is None: config = load_config()

    # 检查 claude 是否已安装
    claude_path = shutil.which("claude")
    if claude_path is None:
        _log().warning("Claude Code 未安装（which 返回 None）")
        # 使用系统 MessageBox 提示用户（不依赖 Qt widget 上下文）
        ctypes.windll.user32.MessageBoxW(
            0,
            "未检测到 Claude Code。\n\n请先在终端中运行以下命令安装：\n  npm install -g @anthropic-ai/claude-code\n\n安装后重新点击浮窗即可启动。",
            "Claude Code 未安装",
            0x00000030  # MB_ICONWARNING | MB_OK
        )
        return

    cmd = "claude --dangerously-skip-permissions" if config.get("launch_mode") == "skip_permissions" else "claude"

    # 确定工作目录：优先使用用户设置，为空则使用 USERPROFILE，再 fallback 到 WORKSPACE_DIR
    working_dir = config.get("working_directory", "").strip()
    if not working_dir:
        working_dir = os.environ.get("USERPROFILE", WORKSPACE_DIR)
    if not os.path.isdir(working_dir):
        working_dir = os.environ.get("USERPROFILE", WORKSPACE_DIR)

    try:
        _log().info("启动 Claude Code [%s], 目录: %s", mode, working_dir)
        subprocess.Popen(["wt","-d",working_dir,"cmd","/c",cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    except FileNotFoundError:
        try:
            subprocess.Popen(["cmd","/c","start","",cmd], cwd=working_dir, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            subprocess.Popen(["cmd","/c","start","",cmd], cwd=working_dir, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        _log().error("启动 Claude Code 失败: %s", e)

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
        self.theme = self.config.get("theme", "light")
        self._c = get_colors(self.theme)
        self._build_styles()
        self._setup_ui()

    def _build_styles(self):
        """根据当前主题预构建所有 stylesheet 字符串"""
        c = self._c
        # 提取常用颜色为 hex 字符串
        sf = f"#{c['SURFACE'][0]:02X}{c['SURFACE'][1]:02X}{c['SURFACE'][2]:02X}"
        tx = f"#{c['TEXT'][0]:02X}{c['TEXT'][1]:02X}{c['TEXT'][2]:02X}"
        hi = f"#{c['HINT'][0]:02X}{c['HINT'][1]:02X}{c['HINT'][2]:02X}"
        ac = f"#{c['ACCENT'][0]:02X}{c['ACCENT'][1]:02X}{c['ACCENT'][2]:02X}"
        sp = f"#{c['SEPARATOR'][0]:02X}{c['SEPARATOR'][1]:02X}{c['SEPARATOR'][2]:02X}"
        bd = f"#{c['BORDER'][0]:02X}{c['BORDER'][1]:02X}{c['BORDER'][2]:02X}"
        is_dark = (self.theme == "dark")
        # 卡片白/暗
        card_bg = "#2C2C2E" if is_dark else "#FFFFFF"
        text_secondary = "#EBEBF5" if is_dark else "#3C3C43"
        accent_hover = "#0066D6"  # 暗色下也保持深蓝变体

        self._s = {
            "container": f"#settingsContainer {{ background: {sf}; border: 1px solid {bd}; border-radius: 16px; }}",
            "group": f"QGroupBox {{ color: {tx}; border: none; padding-top: 12px; }}",
            "separator": f"background: {sp};",
            "btn": (
                f"QPushButton {{ background: {card_bg}; color: {ac}; border: 1px solid {bd};"
                f" border-radius: 8px; padding: 8px 16px; font-size: 12px; }}"
                f"QPushButton:hover {{ background: {sf}; }}"
            ),
            "save_btn": (
                f"QPushButton {{ background: {ac}; color: #FFF; border: none;"
                f" border-radius: 8px; padding: 8px 20px; font-size: 12px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {accent_hover}; }}"
            ),
            "radio": (
                f"QRadioButton {{ color: {text_secondary}; spacing: 8px; }}"
                f"QRadioButton::indicator {{ width:16px; height:16px; }}"
                f"QRadioButton::indicator:unchecked {{ border:2px solid {bd}; border-radius:8px; background:{card_bg}; }}"
                f"QRadioButton::indicator:checked {{ border:none; border-radius:8px; background:{ac}; }}"
            ),
            "checkbox": (
                f"QCheckBox {{ color: {text_secondary}; spacing: 8px; font-size: 11px; }}"
                f"QCheckBox::indicator {{ width: 16px; height: 16px; }}"
                f"QCheckBox::indicator:unchecked {{ border: 2px solid {bd}; border-radius: 4px; background: {card_bg}; }}"
                f"QCheckBox::indicator:checked {{ border: none; border-radius: 4px; background: {ac}; }}"
            ),
            "slider": (
                f"QSlider::groove:horizontal {{ height:4px; background:{sp}; border-radius:2px; }}"
                f"QSlider::handle:horizontal {{ width:20px; height:20px; margin:-8px 0;"
                f" background:{card_bg}; border:2px solid {ac}; border-radius:10px; }}"
                f"QSlider::sub-page:horizontal {{ background:{ac}; border-radius:2px; }}"
            ),
            "lineedit": (
                f"QLineEdit {{ background: {card_bg}; color: {tx}; border: 1px solid {bd};"
                f" border-radius: 6px; padding: 6px 8px; }}"
            ),
            "close_btn": (
                f"QPushButton {{ background: transparent; color: {hi}; border: none; border-radius: 14px; }}"
                f"QPushButton:hover {{ background: {sp}; color: {tx}; }}"
                f"QPushButton:pressed {{ background: {bd}; color: #000; }}"
            ),
            # 通用颜色快捷方式
            "sf": sf, "tx": tx, "hi": hi, "ac": ac, "sp": sp, "bd": bd,
            "card_bg": card_bg, "text_secondary": text_secondary,
        }

    def _font(self, size=12, bold=False):
        return QFont(self._cjk, size, QFont.Bold if bold else QFont.Normal)

    def _label(self, text, size=12, color=None, bold=False):
        if color is None:
            color = self._s["text_secondary"]
        w = QLabel(text)
        w.setFont(self._font(size, bold=bold))
        w.setStyleSheet(f"color: {color};")
        return w

    def _setup_ui(self):
        s = self._s
        self.setWindowTitle("浮窗设置")
        self.setFixedSize(420, 800)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(self._font(9))

        # 外层容器（模拟圆角边框）
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        container = QWidget()
        container.setObjectName("settingsContainer")
        container.setStyleSheet(s["container"])

        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 12, 20, 16)

        # ── 自定义标题栏 ──
        title_bar = QHBoxLayout()
        title_bar.setSpacing(0)

        # 标题 + 版本
        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title_text = self._label("Claude Code 浮窗设置", size=15, color=s["tx"])
        title_text.setFont(self._font(15, bold=True))
        title_block.addWidget(title_text)
        ver_text = self._label(f"v{VERSION}", size=9, color=s["hi"])
        title_block.addWidget(ver_text)
        title_bar.addLayout(title_block)

        title_bar.addStretch()

        # ✕ 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(self._font(14))
        close_btn.setStyleSheet(s["close_btn"])
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)

        layout.addLayout(title_bar)

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(s["separator"])
        layout.addWidget(sep)

        # 通用按钮样式（使用主题缓存）
        btn_css = s["btn"]
        save_css = s["save_btn"]

        # 启动方式
        box = QGroupBox("启动方式")
        box.setFont(self._font(10, bold=True))
        box.setStyleSheet(s["group"])
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        self.rb_normal = QRadioButton("普通模式 — claude", box)
        self.rb_skip  = QRadioButton("跳过权限 — claude --dangerously-skip-permissions", box)
        for rb in [self.rb_normal, self.rb_skip]:
            rb.setFont(self._font(11))
            rb.setStyleSheet(s["radio"])

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

        vl.addWidget(self._label("点击浮窗时使用所选方式启动", 10, s["hi"]))
        layout.addWidget(box)

        # ── 外观主题 ──
        box_theme = QGroupBox("外观主题")
        box_theme.setFont(self._font(10, bold=True))
        box_theme.setStyleSheet(s["group"])
        vl_theme = QVBoxLayout(box_theme)
        vl_theme.setSpacing(6)

        self.rb_light = QRadioButton("☀  浅色模式 — 亮色毛玻璃风格")
        self.rb_dark  = QRadioButton("☾  深色模式 — 暗色毛玻璃风格")
        for rb in [self.rb_light, self.rb_dark]:
            rb.setFont(self._font(11))
            rb.setStyleSheet(s["radio"])

        self.rb_light.setChecked(self.theme != "dark")
        self.rb_dark.setChecked(self.theme == "dark")

        vl_theme.addWidget(self.rb_light)
        vl_theme.addWidget(self.rb_dark)
        vl_theme.addWidget(self._label("切换外观主题，应用后即时生效", 10, s["hi"]))
        layout.addWidget(box_theme)

        # 大小
        box2 = QGroupBox("浮窗大小")
        box2.setFont(self._font(10, bold=True))
        box2.setStyleSheet(s["group"])
        vl2 = QVBoxLayout(box2)
        row = QHBoxLayout()
        row.addWidget(self._label("边长:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(40, 90)
        self.size_slider.setValue(self.config.get("widget_size", DEFAULT_SIZE))
        self.size_slider.setStyleSheet(s["slider"])
        row.addWidget(self.size_slider)
        self.size_label = self._label(f"{self.size_slider.value()} px", bold=True)
        row.addWidget(self.size_label)
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v} px"))
        vl2.addLayout(row)
        layout.addWidget(box2)

        # 透明度
        box3 = QGroupBox("透明度")
        box3.setFont(self._font(10, bold=True))
        box3.setStyleSheet(s["group"])
        vl3 = QVBoxLayout(box3)
        row3 = QHBoxLayout()
        row3.addWidget(self._label("不透明度:"))
        self.op_slider = QSlider(Qt.Horizontal)
        self.op_slider.setRange(40, 100)
        self.op_slider.setValue(int(self.config.get("opacity",0.88)*100))
        self.op_slider.setStyleSheet(s["slider"])
        row3.addWidget(self.op_slider)
        self.op_label = self._label(f"{self.op_slider.value()}%", bold=True)
        row3.addWidget(self.op_label)
        self.op_slider.valueChanged.connect(lambda v: self.op_label.setText(f"{v}%"))
        vl3.addLayout(row3)
        layout.addWidget(box3)

        # 吸附设置
        box_snap = QGroupBox("边缘吸附")
        box_snap.setFont(self._font(10, bold=True))
        box_snap.setStyleSheet(s["group"])
        vl_snap = QVBoxLayout(box_snap)
        vl_snap.setSpacing(6)

        self.cb_snap_enabled = QCheckBox("启用边缘吸附（拖拽到屏幕边缘自动贴边）")
        self.cb_snap_enabled.setFont(self._font(11))
        self.cb_snap_enabled.setStyleSheet(s["checkbox"])
        self.cb_snap_enabled.setChecked(self.config.get("snap_enabled", True))
        vl_snap.addWidget(self.cb_snap_enabled)

        self.cb_snap_hidden = QCheckBox("自动隐藏（鼠标离开后滑出屏幕，靠近时滑回）")
        self.cb_snap_hidden.setFont(self._font(11))
        self.cb_snap_hidden.setStyleSheet(s["checkbox"])
        self.cb_snap_hidden.setChecked(self.config.get("snap_hidden", True))
        self.cb_snap_hidden.setEnabled(self.cb_snap_enabled.isChecked())
        self.cb_snap_enabled.toggled.connect(lambda v: self.cb_snap_hidden.setEnabled(v))
        vl_snap.addWidget(self.cb_snap_hidden)

        vl_snap.addWidget(self._label("拖拽到屏幕边缘自动贴边，可设置自动隐藏以节省空间", 10, s["hi"]))
        layout.addWidget(box_snap)

        # 默认启动目录
        box4 = QGroupBox("默认启动目录")
        box4.setFont(self._font(10, bold=True))
        box4.setStyleSheet(s["group"])
        vl4 = QVBoxLayout(box4)
        vl4.setSpacing(8)

        # 当前目录显示
        self.dir_edit = QLineEdit()
        self.dir_edit.setFont(self._font(10))
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setStyleSheet(s["lineedit"])
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

        vl4.addWidget(self._label("Claude Code 启动时的默认工作目录", 10, s["hi"]))
        layout.addWidget(box4)

        # 退出行为
        self.cb_cleanup = QCheckBox("退出浮窗时自动关闭所有 Claude Code 聊天窗口")
        self.cb_cleanup.setFont(self._font(11))
        self.cb_cleanup.setStyleSheet(s["checkbox"])
        self.cb_cleanup.setChecked(self.config.get("cleanup_on_quit", False))
        layout.addWidget(self.cb_cleanup)

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

        # 日志文件路径提示
        log_hint = self._label(
            f"日志文件: %APPDATA%\\ClaudeFloat\\logs\\ClaudeFloat.log", size=8, color=s["hi"]
        )
        layout.addWidget(log_hint)

        outer.addWidget(container)

        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 420) // 2, (screen.height() - 800) // 2)

    # ── 无边框窗口拖拽支持 ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.globalPos() - self.frameGeometry().topLeft()
            self._dragging = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if hasattr(self, '_dragging') and self._dragging:
            self.move(event.globalPos() - self._drag_start)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def _collect(self):
        return {
            "launch_mode": "skip_permissions" if self.rb_skip.isChecked() else "normal",
            "widget_size": self.size_slider.value(),
            "opacity": self.op_slider.value() / 100.0,
            "working_directory": self.dir_edit.text().strip(),
            "snap_enabled": self.cb_snap_enabled.isChecked(),
            "snap_hidden": self.cb_snap_hidden.isChecked(),
            "theme": "dark" if self.rb_dark.isChecked() else "light",
            "cleanup_on_quit": self.cb_cleanup.isChecked(),
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
    theme_changed     = pyqtSignal(str)

    CLICK_THRESHOLD = 4

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.theme = self.config.get("theme", "light")
        _log().info("浮窗初始化: size=%s, opacity=%.2f, theme=%s",
                     self.config.get("widget_size", DEFAULT_SIZE),
                     self.config.get("opacity", 0.88),
                     self.theme)
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

        # Claude 进程检测（绿色指示灯）
        self._claude_running = False
        self._proc_timer = QTimer(self)
        self._proc_timer.setInterval(3000)  # 每 3 秒检测一次
        self._proc_timer.timeout.connect(self._check_claude_process)
        self._proc_timer.start()

        # 预缓存绘制资源
        self._cache = {}

        self._load_icon()
        self._setup_ui()
        self._apply_opacity()
        self._restore_position()
        self._build_paint_cache()

    def _load_icon(self):
        for p in (PNG_PATH, ICO_PATH):
            if os.path.exists(p):
                pix = QPixmap(p)
                if not pix.isNull():
                    self.icon_pixmap = pix
                    return
        self.icon_pixmap = None

    def _build_paint_cache(self, theme=None):
        """预构建所有渐变和路径对象（避免每帧重复创建）"""
        if theme is None:
            theme = self.theme
        c = get_colors(theme)
        gb = c["GLASS_BG"]
        bd = c["BORDER"]

        s = self.current_size
        r = CORNER_RADIUS
        cx, cy = s / 2, s / 2

        # 基底路径
        base = QPainterPath()
        base.addRoundedRect(QRectF(0, 0, s, s), r, r)
        self._cache["base"] = base

        # 7 个渐变 — 亮色/暗色共享结构，仅颜色值不同
        is_dark = (theme == "dark")

        radial = QRadialGradient(cx, cy, s * 0.7)
        radial.setColorAt(0.0, QColor(255, 255, 255, 10 if is_dark else 18))
        radial.setColorAt(1.0, QColor(255, 255, 255, 0))
        self._cache["radial"] = radial

        diag = QLinearGradient(0, 0, s, s)
        if is_dark:
            diag.setColorAt(0.0, QColor(*gb, 220))
            diag.setColorAt(0.35, QColor(*gb, 210))
            diag.setColorAt(0.65, QColor(gb[0]+4, gb[1]+4, gb[2]+6, 200))
            diag.setColorAt(1.0, QColor(gb[0]-2, gb[1]-2, gb[2]+0, 190))
        else:
            diag.setColorAt(0.0, QColor(*gb, 240))
            diag.setColorAt(0.35, QColor(*gb, 228))
            diag.setColorAt(0.65, QColor(245, 244, 249, 218))
            diag.setColorAt(1.0, QColor(238, 237, 242, 205))
        self._cache["diag"] = diag

        # 玻璃边框渐变（垂直）
        border = QLinearGradient(0, 0, 0, s)
        border.setColorAt(0.0, QColor(*bd, 190))
        border.setColorAt(0.45, QColor(*bd, 110))
        border.setColorAt(1.0, QColor(*bd, 55))
        self._cache["border"] = border

        # 顶面柔光渐变 — 暗色下降低 alpha
        hl_alpha_top = 60 if is_dark else 125
        hl_alpha_mid = 20 if is_dark else 45
        hl = QLinearGradient(0, 0, 0, s * 0.58)
        hl.setColorAt(0.0, QColor(255, 255, 255, hl_alpha_top))
        hl.setColorAt(0.45, QColor(255, 255, 255, hl_alpha_mid))
        hl.setColorAt(1.0, QColor(255, 255, 255, 0))
        self._cache["hl"] = hl

        # 内阴影渐变
        inner = QRadialGradient(cx + s * 0.15, cy + s * 0.15, s * 0.75)
        inner.setColorAt(0.0, QColor(0, 0, 0, 0))
        inner.setColorAt(0.6, QColor(0, 0, 0, 0))
        inner.setColorAt(0.9, QColor(0, 0, 0, 12 if is_dark else 8))
        inner.setColorAt(1.0, QColor(0, 0, 0, 30 if is_dark else 20))
        self._cache["inner"] = inner

        # 镜面反光渐变 — 暗色下降低 alpha
        spec_alpha_0 = 55 if is_dark else 100
        spec_alpha_1 = 30 if is_dark else 55
        spec_alpha_2 = 5 if is_dark else 10
        spec_r = s * 0.18
        spec = QRadialGradient(s * 0.28, s * 0.25, spec_r * 1.5)
        spec.setColorAt(0.0, QColor(255, 255, 255, spec_alpha_0))
        spec.setColorAt(0.25, QColor(255, 255, 255, spec_alpha_1))
        spec.setColorAt(0.6, QColor(255, 255, 255, spec_alpha_2))
        spec.setColorAt(1.0, QColor(255, 255, 255, 0))
        self._cache["spec"] = spec

        # 图标缓存
        icon_frac = 0.52
        icon_size = int(s * icon_frac)
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            self._cache["icon"] = self.icon_pixmap.scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._cache["icon_x"] = int((s - icon_size) / 2)
            self._cache["icon_y"] = int((s - icon_size) / 2)
        else:
            self._cache["icon"] = None

    def _check_claude_process(self):
        """检测 claude.exe 是否在运行，更新指示灯状态"""
        try:
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq claude.exe", "/nh"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            was_running = self._claude_running
            self._claude_running = "claude.exe" in result.stdout
            if was_running != self._claude_running:
                _log().debug("Claude 进程状态变化: running=%s", self._claude_running)
                self.update()  # 状态变化时重绘
        except Exception:
            self._claude_running = False

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
            if self._hotkey_registered:
                _log().debug("全局快捷键 Ctrl+Alt+C 注册成功")
            else:
                _log().warning("全局快捷键注册失败（可能被其他程序占用）")
        except Exception:
            self._hotkey_registered = False
            _log().warning("全局快捷键注册异常")

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
        _log().debug("浮窗显示")
        if not self._hover_timer.isActive():
            self._hover_timer.start()

    def hideEvent(self, event):
        """隐藏时停止 hover 检测以节省 CPU"""
        super().hideEvent(event)
        _log().debug("浮窗隐藏")
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

    def rebuild_theme(self, theme):
        """切换主题：更新配色缓存 → 重建绘制资源 → 重绘"""
        self.theme = theme
        self.config["theme"] = theme
        self._build_paint_cache(theme=theme)
        self.update()
        self.theme_changed.emit(theme)
        _log().info("主题切换为: %s", theme)

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
        if v == self.current_size:
            return
        self.current_size = v
        c = self.geometry().center()
        self.setFixedSize(v, v)
        self._update_mask()
        self._build_paint_cache()
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
            _log().debug("脱离吸附")
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

    # ── 绘制（7 层玻璃 + 涟漪 + 指示灯）─────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取当前主题配色
        tc = get_colors(self.theme)
        shadow = tc["SHADOW"]
        border = tc["BORDER"]
        accent = tc["ACCENT"]
        text = tc["TEXT"]

        scale = self._press_scale
        s = self.current_size
        r = CORNER_RADIUS
        cx, cy = s / 2, s / 2

        if scale != 1.0:
            painter.translate(cx, cy)
            painter.scale(scale, scale)
            painter.translate(-cx, -cy)

        shadow_boost = 1.0 + (0.8 if self.is_hovered else 0)
        is_dark = (self.theme == "dark")
        hover_alpha = 20 if (self.is_hovered and is_dark) else (30 if self.is_hovered else 0)

        # 使用预缓存的绘制资源
        c = self._cache
        base_path = c["base"]

        # ── Layer 0: 阴影 ──
        painter.setPen(Qt.NoPen)
        h_offset = 1 if self.is_hovered else 0
        for offset, base_alpha in [(0, 18), (2, 10), (4, 5)]:
            a = min(255, int(base_alpha * shadow_boost))
            so = offset + h_offset
            sr = QRectF(2 + so, 3 + so, s, s)
            sp = QPainterPath()
            sp.addRoundedRect(sr, r, r)
            painter.setBrush(QColor(*shadow, a))
            painter.drawPath(sp)

        # ── Layer 1: 玻璃基底 ──
        painter.setBrush(QBrush(c["diag"]))
        painter.setPen(Qt.NoPen)
        painter.drawPath(base_path)
        painter.setBrush(QBrush(c["radial"]))
        painter.drawPath(base_path)

        # ── Layer 2: 玻璃边框 ──
        if self.is_hovered:
            border_grad = QLinearGradient(0, 0, 0, s)
            border_grad.setColorAt(0.0, QColor(*border, int(190 * 1.3)))
            border_grad.setColorAt(0.45, QColor(*border, int(110 * 1.3)))
            border_grad.setColorAt(1.0, QColor(*border, int(55 * 1.3)))
            pen = QPen(QBrush(border_grad), 1.0)
        else:
            pen = QPen(QBrush(c["border"]), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRect(0, 0, s - 1, s - 1), r, r)

        # ── Layer 3-5: 柔光 + 内阴影 + 镜面反光 ──
        hl_path = base_path
        painter.setBrush(QBrush(c["hl"]))
        painter.setPen(Qt.NoPen)
        painter.drawPath(hl_path)
        painter.setBrush(QBrush(c["inner"]))
        painter.drawPath(hl_path)
        painter.setBrush(QBrush(c["spec"]))
        painter.drawPath(hl_path)

        # ── Layer 6: 悬停蓝色微染 ──
        if hover_alpha > 0:
            painter.setBrush(QColor(*accent, hover_alpha))
            painter.setPen(Qt.NoPen)
            painter.drawPath(hl_path)

        # ── Layer 7: 图标 ──
        if c.get("icon"):
            painter.drawPixmap(c["icon_x"], c["icon_y"], c["icon"])
        else:
            font = QFont(FONT_FAMILY, int(s * 0.40), QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(*text, 200))
            painter.drawText(QRect(0, 0, s, s), Qt.AlignCenter, "CC")

        # ── 涟漪 ──
        if self._ripple_progress > 0 and not self._ripple_pos.isNull():
            rp = self._ripple_progress
            max_rad = s * 0.8
            rad = max_rad * rp
            alpha = int(60 * (1.0 - rp))
            ripple_grad = QRadialGradient(self._ripple_pos, rad)
            ripple_grad.setColorAt(0.0, QColor(*accent, alpha))
            ripple_grad.setColorAt(1.0, QColor(*accent, 0))
            painter.setBrush(QBrush(ripple_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(hl_path)

        # ── 安全模式指示器：skip-permissions 时右上角红色圆点 ──
        if self.config.get("launch_mode") == "skip_permissions":
            dot_r = max(4, s * 0.08)
            dot_margin = s * 0.18
            dot_cx = s - dot_margin
            dot_cy = dot_margin
            painter.setBrush(QColor(255, 59, 48, 220))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(dot_cx, dot_cy), dot_r, dot_r)

        # ── Claude 运行中指示器：左下角绿色圆点 ──
        if self._claude_running:
            dot_r = max(4, s * 0.07)
            dot_margin = s * 0.18
            dot_cx = dot_margin
            dot_cy = s - dot_margin
            painter.setBrush(QColor(52, 199, 89, 220))
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
        tc = get_colors(self.theme)
        sfc = tc["SURFACE"]
        txt = tc["TEXT"]
        acc = tc["ACCENT"]
        sep = tc["SEPARATOR"]
        menu_css = (
            f"QMenu {{ background: rgba({sfc[0]},{sfc[1]},{sfc[2]},0.95);"
            f" border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 4px 0; }}"
            f"QMenu::item {{ padding: 7px 32px 7px 16px; font-size: 12px;"
            f" color: #{txt[0]:02X}{txt[1]:02X}{txt[2]:02X}; }}"
            f"QMenu::item:selected {{ background: #{acc[0]:02X}{acc[1]:02X}{acc[2]:02X};"
            f" color: #FFF; border-radius: 4px; margin: 1px 6px; }}"
            f"QMenu::separator {{ height: 1px;"
            f" background: #{sep[0]:02X}{sep[1]:02X}{sep[2]:02X}; margin: 4px 8px; }}"
        )
        menu = QMenu(self)
        menu.setStyleSheet(menu_css)

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
        self.config["cleanup_on_quit"] = new_cfg.get("cleanup_on_quit", False)

        # 主题切换
        new_theme = new_cfg.get("theme", "light")
        if new_theme != self.theme:
            self.rebuild_theme(new_theme)
            changed = True

        _log().info("应用设置 (preview=%s): size=%s, opacity=%.2f, mode=%s, theme=%s",
                     preview_only, ns, self.config["opacity"], self.config["launch_mode"], self.theme)

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
    # ── 启动日志 ──
    _setup_logger()
    _log().info("=" * 50)
    _log().info("ClaudeFloat v%s 启动 | Frozen=%s | PID=%s", VERSION, _IS_FROZEN, os.getpid())

    # ── 崩溃日志：写入桌面文件便于诊断 ──
    CRASH_LOG = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "ClaudeFloat_crash.log")
    try:
        _main()
        _log().info("ClaudeFloat 正常退出")
    except Exception:
        import traceback
        tb = traceback.format_exc()
        _log().critical("未处理异常导致崩溃:\n%s", tb)
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

    # 退出时清理孤儿 Claude 进程（可配置）
    def _cleanup_on_quit():
        if config.get("cleanup_on_quit", True):
            _log().info("退出清理: taskkill /f /im claude.exe")
            subprocess.run(["taskkill", "/f", "/im", "claude.exe"],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    app.aboutToQuit.connect(_cleanup_on_quit)

    widget = FloatingWidget()

    # ── 设置对话框 ──
    def open_settings():
        _log().debug("打开设置对话框")
        dlg = SettingsDialog(widget.config, parent=widget)
        if dlg.exec_() == QDialog.Accepted and dlg.result_config:
            preview = dlg.result_config.pop("_preview", False)
            widget.apply_settings(dlg.result_config, preview_only=preview)

    def do_launch():
        launch_claude_code(widget.config)

    # ── 系统托盘 ──
    def _build_menu_stylesheet(theme):
        tc = get_colors(theme)
        sfc = tc["SURFACE"]
        txt = tc["TEXT"]
        acc = tc["ACCENT"]
        sep = tc["SEPARATOR"]
        return (
            f"QMenu {{ background: rgba({sfc[0]},{sfc[1]},{sfc[2]},0.95);"
            f" border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 4px 0; }}"
            f"QMenu::item {{ padding: 7px 32px 7px 16px; font-size: 12px;"
            f" color: #{txt[0]:02X}{txt[1]:02X}{txt[2]:02X}; }}"
            f"QMenu::item:selected {{ background: #{acc[0]:02X}{acc[1]:02X}{acc[2]:02X};"
            f" color: #FFF; border-radius: 4px; margin: 1px 6px; }}"
            f"QMenu::separator {{ height: 1px;"
            f" background: #{sep[0]:02X}{sep[1]:02X}{sep[2]:02X}; margin: 4px 8px; }}"
        )

    tray_menu = QMenu()
    tray_menu.setStyleSheet(_build_menu_stylesheet(widget.theme))

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
        tc = get_colors(widget.theme)
        pix.fill(QColor(*tc["ACCENT"]))
        tray_icon.setIcon(QIcon(pix))

    tray_icon.setToolTip("Claude Code 浮窗 — 点击启动 | Ctrl+Alt+C 显示/隐藏")
    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(lambda r: widget.show() if r == QSystemTrayIcon.DoubleClick else None)
    tray_icon.show()
    tray_icon.showMessage("Claude Code 浮窗", "浮窗已启动", QSystemTrayIcon.Information, 2000)

    widget.launch_requested.connect(do_launch)
    widget.quit_requested.connect(app.quit)
    widget.settings_requested.connect(open_settings)
    # 主题切换时同步更新托盘菜单样式
    widget.theme_changed.connect(lambda t: tray_menu.setStyleSheet(_build_menu_stylesheet(t)))
    widget.show()

    if config.get("auto_start") and not is_auto_start_enabled():
        toggle_auto_start(True)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
