import json
import os
import sys
import time
from pathlib import Path
from pypinyin import lazy_pinyin, Style

def chinese_to_pinyin_no_space(text: str) -> str:
    # 获取拼音（无声调）
    pinyins = lazy_pinyin(text, style=Style.NORMAL)
    # 每个拼音首字母大写，然后拼接
    return ''.join(word.capitalize() for word in pinyins)

def load_config():
    try:
        return json.loads(get_config_path().read_text(encoding="utf-8"))
    except Exception as e:
        defalut = {
            "java_path": {
                "value": "",
                "label": "jdk路径",
                "type": "file"
            },
            "plugin_path": {
                "value": "C:/plugins",
                "label": "插件路径",
                "type": "folder"
            }
        }
        return defalut


def save_config(cfg: dict):
    get_config_path().write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def get_base_path() -> str:
    '''
    获取当前执行目录
    :return:
    '''
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.abspath(__file__))


def get_config_path():
    '''
    获取配置文件的路径
    :return:
    '''
    config_path = os.path.join(get_base_path(), 'config.json')
    Path(config_path).touch(exist_ok=True)
    return Path(config_path)


def get_plugins_folder():
    plugins_dir = get_base_path() + "/plugins"
    # 构建plugins文件夹路径
    if load_config().get("plugin_path"):
        plugins_dir = load_config().get("plugin_path").get("value")
    # 如果plugins文件夹不存在，则创建
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)

    return Path(plugins_dir)


def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def sanitize_name(s: str):
    # 简单过滤文件夹名非法字符
    return "".join(c for c in s if c.isalnum() or c in "-_ ").strip()

def get_loggers_path():
    """初始化主程序与插件日志记录器"""
    log_base_path = os.path.join(get_base_path(), 'log/')
    plugin_log_dir = os.path.join(log_base_path, 'plugins/')
    return log_base_path, plugin_log_dir


