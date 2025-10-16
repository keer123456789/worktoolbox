#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/10/16 21:36
# @Author  : 我的名字
# @File    : logger_manager.py
# @Description : 这个函数是用来balabalabala自己写
import os
import sys
import logging
import threading
import traceback
from datetime import datetime


def init_logging(
    log_dir: str = "./logs",
    main_log_name: str = "app.log",
    level: int = logging.INFO,
    console: bool = True,
):
    """
    初始化日志系统（系统日志 + 全局异常捕获）

    参数:
        log_dir: 日志存放目录
        main_log_name: 主系统日志文件名
        level: 日志等级
        console: 是否在控制台同步输出
    """

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, main_log_name)

    # 设置 logging 配置
    handlers = [logging.FileHandler(log_file, encoding="utf-8")]
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
        handlers=handlers,
    )

    logging.info("=== 系统启动 ===")
    logging.info(f"日志文件位置: {os.path.abspath(log_file)}")

    # 捕获全局未处理异常
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    # 捕获线程中的未处理异常（Python 3.8+ 支持）
    def threading_exception_handler(args):
        logging.error(f"线程异常: {args.thread.name}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    if hasattr(threading, "excepthook"):
        threading.excepthook = threading_exception_handler

    # 捕获 print 输出重定向
    class StreamToLogger:
        def __init__(self, level):
            self.level = level

        def write(self, message):
            message = message.strip()
            if message:
                self.level(message)

        def flush(self):
            pass

    sys.stdout = StreamToLogger(logging.info)
    sys.stderr = StreamToLogger(logging.error)

    logging.info("日志系统初始化完成")
    return logging


def get_logger(name=None):
    """获取子模块日志记录器"""
    return logging.getLogger(name or __name__)


def get_plugin_logger(plugin_name: str, log_dir: str = "./plugin_logs"):
    """
    获取插件专用日志对象（文件独立保存）
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(
        log_dir,
        f"{plugin_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    plugin_logger = logging.getLogger(plugin_name)
    plugin_logger.setLevel(logging.INFO)

    # 防止重复添加 handler
    if not plugin_logger.handlers:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        plugin_logger.addHandler(fh)

    plugin_logger.info(f"插件日志启动：{log_path}")
    return plugin_logger
