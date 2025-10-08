# main.py
import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication
)

import core
from ui.main_window import MainWindow

if __name__ == "__main__":
    dirs = core.get_plugins_folder().iterdir()
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
