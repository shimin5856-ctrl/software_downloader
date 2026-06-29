"""
logger.py
线程安全日志模块 - 重构版本
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from threading import Lock
from typing import Optional, Callable

from config import LOG_FILE

# 日志级别配置
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# 日志格式器
_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 内部logger实例
_logger = logging.getLogger("software_downloader")
_logger.setLevel(logging.INFO)

# 添加文件处理器
if not _logger.handlers:
    fh = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2 * 1024 * 1024,  # 2MB
        backupCount=3,
        encoding="utf-8"
    )
    fh.setFormatter(_formatter)
    _logger.addHandler(fh)

# 线程锁
_lock = Lock()


class Logger:
    """
    线程安全的日志类
    
    支持同时输出到：
    - 文件日志（使用 Python logging 模块）
    - GUI文本框（Tkinter Text widget）
    """

    def __init__(self):
        """初始化日志实例"""
        self.widget: Optional[object] = None
        self._lock = Lock()

    def bind_text_widget(self, widget: object):
        """
        绑定Tkinter文本小部件
        
        参数：
            widget: Tkinter Text widget 实例
        """
        self.widget = widget

    def _append_gui(self, text: str):
        """
        向GUI文本框追加日志
        
        参数：
            text: 要追加的日志文本
        """
        if self.widget is None:
            return

        try:
            # 使用after()确保在主线程中执行GUI操作
            self.widget.after(
                0,
                self._insert_text_safe,
                text
            )
        except Exception as e:
            _logger.error(f"GUI日志追加失败：{e}")

    def _insert_text_safe(self, text: str):
        """
        安全地将文本插入GUI文本框
        
        参数：
            text: 要插入的文本
        """
        try:
            self.widget.config(state="normal")
            self.widget.insert("end", text + "\n")
            self.widget.see("end")
            self.widget.config(state="disabled")
        except Exception as e:
            _logger.error(f"文本框插入失败：{e}")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%H:%M:%S")

    def log(self, message: str, level: str = "info"):
        """
        记录日志
        
        参数：
            message: 日志消息
            level: 日志级别 ('debug', 'info', 'warning', 'error', 'critical')
        """
        # 获取日志级别
        log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
        
        # 格式化日志文本
        timestamp = self._get_timestamp()
        line = f"{timestamp}  {message}"

        # 线程安全地写入文件日志
        with _lock:
            _logger.log(log_level, message)

        # 追加到GUI
        self._append_gui(line)

    def debug(self, message: str):
        """
        记录调试日志
        
        参数：
            message: 日志消息
        """
        self.log(message, "debug")

    def info(self, message: str):
        """
        记录信息日志
        
        参数：
            message: 日志消息
        """
        self.log(message, "info")

    def warning(self, message: str):
        """
        记录警告日志
        
        参数：
            message: 日志消息
        """
        self.log(message, "warning")

    def error(self, message: str):
        """
        记录错误日志
        
        参数：
            message: 日志消息
        """
        self.log(message, "error")

    def critical(self, message: str):
        """
        记录严重错误日志
        
        参数：
            message: 日志消息
        """
        self.log(message, "critical")

    def set_file_level(self, level: str):
        """
        设置文件日志级别
        
        参数：
            level: 日志级别字符串
        """
        log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
        _logger.setLevel(log_level)

    def get_log_file(self) -> str:
        """
        获取日志文件路径
        
        返回：
            日志文件完整路径
        """
        return str(LOG_FILE)


# 全局logger实例
logger = Logger()


if __name__ == "__main__":
    # 测试日志功能
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    print(f"日志文件位置：{logger.get_log_file()}")
