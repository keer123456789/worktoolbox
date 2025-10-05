# main.py
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from PyQt5.QtCore import Qt, QProcess, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox, QFormLayout,
    QLineEdit, QPlainTextEdit, QSplitter, QComboBox, QSpacerItem, QSizePolicy,
    QHBoxLayout, QDialog, QScrollArea
)

BASE_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = BASE_DIR / "plugins"
PLUGINS_DIR.mkdir(exist_ok=True)


def load_config():
    try:
        return json.loads(get_config_path().read_text(encoding="utf-8"))
    except Exception as e:
        return {}


def save_config(cfg: dict):
    get_config_path().write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建plugins文件夹路径
    config_path = os.path.join(base_dir, 'config.json')
    Path(config_path).touch(exist_ok=True)
    return Path(config_path)


def get_plugins_folder():
    # 获取exe所在目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建plugins文件夹路径
    plugins_dir = os.path.join(base_dir, 'plugins')

    # 如果plugins文件夹不存在，则创建
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)

    return Path(plugins_dir)


def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def sanitize_name(s: str):
    # 简单过滤文件夹名非法字符
    return "".join(c for c in s if c.isalnum() or c in "-_ ").strip()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("办公百宝箱")
        icon_path = os.path.join(os.path.dirname(__file__), "doc/logo.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 600)
        self.process = None
        self.current_plugin = None
        self.arg_widgets = []  # list of dicts: {'spec':spec, 'widget': widget}
        self.config = load_config()
        self.init_ui()
        self.load_plugins()

    def init_ui(self):
        # 左侧：上传 + 插件列表
        left_box = QVBoxLayout()
        left_box.setSpacing(8)
        left_box.setContentsMargins(8, 8, 8, 8)

        title = QLabel("插件管理")
        title.setFont(QFont("", 12, QFont.Bold))
        left_box.addWidget(title)

        up_btn_row = QHBoxLayout()
        self.upload_btn = QPushButton("上传新插件")
        self.refresh_btn = QPushButton("刷新列表")
        self.setting_btn = QPushButton("设置")
        up_btn_row.addWidget(self.upload_btn)
        up_btn_row.addWidget(self.refresh_btn)
        up_btn_row.addWidget(self.setting_btn)
        left_box.addLayout(up_btn_row)

        self.plugin_list = QListWidget()
        self.plugin_list.setSelectionMode(QListWidget.SingleSelection)
        left_box.addWidget(self.plugin_list, 1)

        left_footer = QLabel("插件目录： " + str(get_plugins_folder()))
        left_footer.setStyleSheet("color: #666; font-size: 11px;")
        left_box.addWidget(left_footer)

        left_widget = QWidget()
        left_widget.setLayout(left_box)
        left_widget.setMinimumWidth(260)
        left_widget.setMaximumWidth(420)
        left_widget.setStyleSheet("background: #f7f8fa;")

        # 右侧 上半：插件信息 + 参数表单 + 按钮
        right_top_v = QVBoxLayout()
        right_top_v.setContentsMargins(8, 8, 8, 8)
        right_top_v.setSpacing(10)

        self.plugin_title = QLabel("未选择插件")
        self.plugin_title.setFont(QFont("", 14, QFont.Bold))
        right_top_v.addWidget(self.plugin_title)

        self.plugin_desc = QLabel("")
        self.plugin_desc.setWordWrap(True)
        self.plugin_desc.setStyleSheet("color:#333;")
        right_top_v.addWidget(self.plugin_desc)

        # 参数区域放在 GroupBox 里并可滚动（若需再改为 QScrollArea）
        self.args_group = QGroupBox("参数")
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        form_container = QWidget()
        self.args_form = QFormLayout(form_container)
        self.args_form.setLabelAlignment(Qt.AlignRight)
        self.args_form.setSpacing(8)

        scroll_area.setWidget(form_container)

        vbox = QVBoxLayout(self.args_group)
        vbox.addWidget(scroll_area)
        right_top_v.addWidget(self.args_group)

        # 执行按钮区域
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("执行")
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        right_top_v.addLayout(btn_row)

        right_top = QWidget()
        right_top.setLayout(right_top_v)
        right_top.setMinimumHeight(240)

        # 右侧 下半：日志
        right_bottom_v = QVBoxLayout()
        right_bottom_v.setContentsMargins(8, 0, 8, 8)
        log_label = QLabel("运行日志")
        log_label.setFont(QFont("", 11, QFont.Bold))
        right_bottom_v.addWidget(log_label)

        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Courier", 10))
        right_bottom_v.addWidget(self.log_area, 1)
        self.clear_log_btn = QPushButton("清空日志")
        right_bottom_v.addWidget(self.clear_log_btn)
        right_bottom = QWidget()
        right_bottom.setLayout(right_bottom_v)

        # 右侧整体布局（上下）
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(right_top)
        right_splitter.addWidget(right_bottom)
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)

        # 左右主分割
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        main_layout = QHBoxLayout()
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        # 事件绑定
        self.upload_btn.clicked.connect(self.upload_plugin)
        self.refresh_btn.clicked.connect(self.load_plugins)
        self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selected)
        self.run_btn.clicked.connect(self.on_run_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.setting_btn.clicked.connect(self.on_setting_clicked)
        self.clear_log_btn.clicked.connect(self.on_clear_log_clicked)
        # 样式（简单美化）
        self.setStyleSheet("""
            QPushButton { padding:6px 10px; }
            QGroupBox { font-weight: bold; }
            QListWidget { background: white; }
        """)

    # ---------------- 插件管理 ----------------
    def load_plugins(self):
        """扫描 plugins 目录，加载 plugin.json 信息"""
        self.plugin_list.clear()
        count = 0
        for p in sorted(get_plugins_folder().iterdir()):
            if p.is_dir():
                j = p / "plugin.json"
                if j.exists():
                    try:
                        meta = json.loads(j.read_text(encoding="utf-8"))
                        meta['path'] = str(p)
                        item = QListWidgetItem(str(count + 1) + '. ' + meta.get("name", p.name))
                        item.setData(Qt.UserRole, meta)
                        item.setToolTip(meta.get("description", ""))
                        self.plugin_list.addItem(item)
                        count += 1
                    except Exception as e:
                        print("load plugin failed", p, e)
        self.append_log(f"已加载 {count} 个插件")

    def on_plugin_selected(self):
        item = self.plugin_list.currentItem()
        if not item:
            return
        meta = item.data(Qt.UserRole)
        self.show_plugin_meta(meta)

    def show_plugin_meta(self, meta: dict):
        """展示插件信息并动态生成参数表单"""
        self.current_plugin = meta
        name = meta.get("name", "未命名插件")
        desc = meta.get("description", "")
        self.plugin_title.setText(name)
        self.plugin_desc.setText(desc)
        # 清空旧控件
        while self.args_form.rowCount():
            self.args_form.removeRow(0)
        self.arg_widgets = []

        args = meta.get("args", [])
        for spec in args:
            label = spec.get("label") or spec.get("name")
            atype = spec.get("type", "string")
            default = spec.get("default", "")
            widget = None

            if atype == "string":
                widget = QLineEdit()
                widget.setText(str(default))
            elif atype == "int":
                widget = QLineEdit()
                widget.setText(str(default))
                widget.setPlaceholderText("整数")
            elif atype == "file":
                # file: QLineEdit + Browse
                w = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                le = QLineEdit()
                le.setText(str(default))
                btn = QPushButton("选择文件")

                def _choose():
                    fn, _ = QFileDialog.getOpenFileName(self, "选择文件")
                    if fn:
                        le.setText(fn)

                btn.clicked.connect(_choose)
                h.addWidget(le)
                h.addWidget(btn)
                w.setLayout(h)
                widget = w
                widget._value_widget = le
            elif atype == "folder":
                w = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                le = QLineEdit()
                le.setText(str(default))
                btn = QPushButton("选择文件夹")

                def _choose_dir():
                    d = QFileDialog.getExistingDirectory(self, "选择文件夹")
                    if d:
                        le.setText(d)

                btn.clicked.connect(_choose_dir)
                h.addWidget(le)
                h.addWidget(btn)
                w.setLayout(h)
                widget = w
                widget._value_widget = le
            elif atype == "choice":
                cb = QComboBox()
                for o in spec.get("options", []):
                    cb.addItem(str(o))
                idx = 0
                try:
                    idx = spec.get("options", []).index(default)
                except:
                    idx = 0
                cb.setCurrentIndex(idx)
                widget = cb
            else:
                widget = QLineEdit()
                widget.setText(str(default))

            self.arg_widgets.append({"spec": spec, "widget": widget})
            self.args_form.addRow(QLabel(label + ":"), widget)

        # 如果没有 args，显示占位
        if not args:
            self.args_form.addRow(QLabel("提示:"), QLabel("该插件不需要参数"))

    # ---------------- 上传插件 ----------------
    def upload_plugin(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择插件 zip 包", str(BASE_DIR), "Zip files (*.zip)")
        if not file_path:
            return
        try:
            tmp = Path(tempfile.mkdtemp(prefix="plugin_"))
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(str(tmp))
            # 在 tmp 中寻找 plugin.json
            found = None
            for root, dirs, files in os.walk(str(tmp)):
                if "plugin.json" in files:
                    found = Path(root) / "plugin.json"
                    break
            if not found:
                QMessageBox.warning(self, "上传失败", "zip 包中未包含 plugin.json")
                shutil.rmtree(tmp)
                return
            meta = json.loads(found.read_text(encoding="utf-8"))
            plugin_name = sanitize_name(meta.get("folder", meta.get("name", Path(file_path).stem)))
            dest = get_plugins_folder() / plugin_name
            if dest.exists():
                # 提示覆盖或改名
                ret = QMessageBox.question(self, "插件已存在", f"插件目录 {dest} 已存在，是否覆盖？",
                                           QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if ret == QMessageBox.Cancel:
                    shutil.rmtree(tmp)
                    return
                elif ret == QMessageBox.No:
                    # 尝试创建新名字
                    idx = 1
                    while True:
                        cand = get_plugins_folder() / f"{plugin_name}_{idx}"
                        if not cand.exists():
                            dest = cand
                            break
                        idx += 1
            shutil.move(str(found.parent), str(dest))
            # 如果 tmp 下还有其它残留，尝试删除
            try:
                shutil.rmtree(tmp)
            except:
                pass
            QMessageBox.information(self, "上传成功", f"已安装到：{dest}")
            self.load_plugins()
        except Exception as e:
            QMessageBox.critical(self, "上传失败", str(e))

    # ---------------- 执行插件 ----------------
    def on_run_clicked(self):
        item = self.plugin_list.currentItem()
        if not item:
            QMessageBox.information(self, "提示", "请先选择一个插件")
            return
        meta = item.data(Qt.UserRole)
        # collect args in order
        args = []
        for aw in self.arg_widgets:
            spec = aw['spec']
            widget = aw['widget']
            val = ""
            if isinstance(widget, QLineEdit):
                val = widget.text()
            else:
                # file/folder widgets have attribute _value_widget pointing to QLineEdit
                if hasattr(widget, "_value_widget"):
                    val = widget._value_widget.text()
                elif isinstance(widget, QComboBox):
                    val = widget.currentText()
                else:
                    # fallback try find QLineEdit child
                    le = widget.findChild(QLineEdit)
                    val = le.text() if le else ""
            args.append(str(val))
        self.start_process(meta, args)

    def append_log(self, text: str):
        for line in str(text).splitlines():
            self.log_area.appendPlainText(f"[{ts()}] {line}")

    def clear_log(self):
        self.log_area.clear()

    def start_process(self, meta: dict, args: list):
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "警告", "已有插件在运行，请先停止")
            return
        entry = meta.get("entry")
        ptype = meta.get("type", "").lower()
        plugin_path = Path(meta.get("path", ""))
        if not entry:
            # default mapping
            if ptype == "bat":
                entry = "run.bat"
            elif ptype == "python":
                entry = "run.py"
            else:
                # try guess
                if (plugin_path / "run.py").exists():
                    entry = "run.py"
                    ptype = "python"
                elif (plugin_path / "run.bat").exists():
                    entry = "run.bat"
                    ptype = "bat"
                else:
                    QMessageBox.critical(self, "错误", "找不到入口脚本 (run.py/run.bat)，请检查插件目录")
                    return
        script_path = str(plugin_path / entry)
        if not Path(script_path).exists():
            QMessageBox.critical(self, "错误", f"入口文件不存在：{script_path}")
            return

        self.process = QProcess(self)
        # set working directory to plugin path

        self.process.setWorkingDirectory(str(plugin_path))
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.setReadChannel(QProcess.StandardOutput)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)

        # build program / args for QProcess.start(program, args)
        if ptype == "bat" or script_path.lower().endswith(".bat"):
            program = "cmd"
            qargs = ["/c", script_path] + args
        elif ptype == "python" or script_path.lower().endswith(".py"):
            program = sys.executable or "python"
            qargs = [script_path] + args
        elif ptype == "exe" or script_path.lower().endswith(".exe"):
            program = script_path
            qargs = args
        elif ptype == "java" or script_path.lower().endswith(".jar"):
            program = self.config.get("java_path")
            if not program or not Path(program).exists():
                QMessageBox.warning(self, "警告", "未配置 Java 路径，请先在设置中配置 JDK！")
                return
            qargs = ["-Dfile.encoding=UTF-8", "-jar", str(script_path)] + args
        else:
            # try make executable
            program = script_path
            qargs = args

        # start
        try:
            self.append_log("******************************")
            self.append_log(f"启动：{program} {' '.join(qargs)}")
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.process.start(program, qargs)
            # slight timeout to check start success
            QTimer.singleShot(800, self._check_started)
        except Exception as e:
            self.append_log("启动失败：" + str(e))
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _check_started(self):
        if not self.process:
            return
        if self.process.state() == QProcess.NotRunning:
            # failed to start, read error
            err = bytes(self.process.readAllStandardError()).decode(errors="ignore")
            self.append_log("进程未启动. 错误: " + err)
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def on_stdout(self):
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        if data.strip():
            self.append_log(data.strip())

    def on_stderr(self):
        if not self.process:
            return
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        if data.strip():
            self.append_log("[ERR] " + data.strip())

    def on_finished(self, exitCode, exitStatus):
        self.append_log(f"进程结束，退出码：{exitCode}")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        # clear self.process after short delay
        QTimer.singleShot(200, self._clear_process)

    def _clear_process(self):
        try:
            self.process = None
        except:
            self.process = None

    def on_stop_clicked(self):
        if not self.process:
            return
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.append_log("已发送 kill 信号")
            self.stop_btn.setEnabled(False)

    def on_setting_clicked(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self.config = dlg.config
            self.append_log("配置已更新")

    def on_clear_log_clicked(self):
        self.clear_log();


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(400, 120)
        self.config = config.copy()

        self.form_layout = QFormLayout(self)

        self.java_input = QLineEdit(self.config.get("java_path", ""))
        self.choose_btn = QPushButton("选择...")
        self.choose_btn.clicked.connect(self.choose_java)

        hbox = QHBoxLayout()
        hbox.addWidget(self.java_input)
        hbox.addWidget(self.choose_btn)

        self.form_layout.addRow("Java路径：", hbox)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save)
        self.form_layout.addRow(self.save_btn)

    def choose_java(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 java.exe", "", "Executable (*.exe)")
        if file_path:
            self.java_input.setText(file_path)

    def save(self):
        self.config["java_path"] = self.java_input.text().strip()
        save_config(self.config)
        QMessageBox.information(self, "成功", "设置已保存")
        self.accept()


if __name__ == "__main__":
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS  # PyInstaller 临时路径
    else:
        base_path = os.path.abspath(".")
    icon_path = os.path.join(base_path, "logo.ico")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
