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
    icon_path = os.path.join(core.get_base_path(), "doc/logo.png")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
