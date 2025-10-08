from PyQt5.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QMessageBox, QFormLayout,
    QLineEdit, QComboBox, QHBoxLayout, QDialog
)

import core


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(600, 200)
        self.config = config.copy()
        self.id_form_map = {}
        self.form_layout = QFormLayout(self)
        self.load_params()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save)
        self.form_layout.addRow(self.save_btn)

    def load_params(self):

        for param in self.config.keys():
            o = self.config.get(param)
            label = o.get("label", "")
            value = o.get("value", "")
            atype = o.get("type", "")
            if atype == "string":
                widget = QLineEdit()
                widget.setText(str(value))
                self.id_form_map[param] = widget
            elif atype == "int":
                widget = QLineEdit()
                widget.setText(str(value))
                widget.setPlaceholderText("整数")
                self.id_form_map[param] = widget
            elif atype == "file":
                # file: QLineEdit + Browse
                w = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                le = QLineEdit()
                le.setText(str(value))
                btn = QPushButton("选择文件")

                def _choose(_checked=False, _le=le):
                    fn, _ = QFileDialog.getOpenFileName(self, "选择文件")
                    if fn:
                        _le.setText(fn)

                btn.clicked.connect(_choose)
                h.addWidget(le)
                h.addWidget(btn)
                w.setLayout(h)
                widget = w
                widget._value_widget = le
                self.id_form_map[param] = le
            elif atype == "folder":
                w = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                fle = QLineEdit()
                fle.setText(str(value))
                fbtn = QPushButton("选择文件夹")

                def _choose_dir(_checked=False, _fle=fle):
                    d = QFileDialog.getExistingDirectory(self, "选择文件夹")
                    if d:
                        _fle.setText(d)

                fbtn.clicked.connect(_choose_dir)
                h.addWidget(fle)
                h.addWidget(fbtn)
                w.setLayout(h)
                widget = w
                widget._value_widget = fle
                self.id_form_map[param] = fle

            elif atype == "choice":
                cb = QComboBox()
                for os in o.get("options", []):
                    cb.addItem(str(os))
                idx = 0
                try:
                    idx = o.get("options", []).index(value)
                except:
                    idx = 0
                cb.setCurrentIndex(idx)
                widget = cb
                self.id_form_map[param] = widget

            else:
                widget = QLineEdit()
                widget.setText(str(value))
                self.id_form_map[param] = widget
            self.form_layout.addRow(label, widget)

    def save(self):
        for key in self.id_form_map:
            widget = self.id_form_map[key]
            if isinstance(widget, QLineEdit):
                value = widget.text()
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            self.config[key]["value"] = value
        core.save_config(self.config)
        QMessageBox.information(self, "成功", "设置已保存")
        self.accept()
