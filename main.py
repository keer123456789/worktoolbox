# main.py
import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication
)

import core
from ui.main_window import MainWindow
from logger_manager import init_logging
import logging

if __name__ == "__main__":
    log_base_path, plugin_log_dir = core.get_loggers_path()
    init_logging(log_dir=log_base_path,main_log_name='app.log')
    icon_path = os.path.join(core.get_base_path(), "doc/logo.png")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    win = MainWindow()
    win.show()

    exec_num=app.exec_()
    logging.info("==系统退出==")
    sys.exit(exec_num)
