"""
logger.py
线程安全日志模块
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from queue import Queue
from threading import Lock

from config import LOG_FILE

_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_logger = logging.getLogger("software_downloader")
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(_formatter)
    _logger.addHandler(fh)

_lock = Lock()


class Logger:
    """同时写入文件和GUI日志"""

    def __init__(self):
        self._queue = Queue()

    def bind_text_widget(self, widget):
        self.widget = widget

    def _append_gui(self, text: str):
        if hasattr(self, "widget"):
            self.widget.after(
                0,
                lambda: (
                    self.widget.insert("end", text + "\n"),
                    self.widget.see("end"),
                ),
            )

    def log(self, message: str, level="info"):
        now = datetime.now().strftime("%H:%M:%S")
        line = f"{now}  {message}"

        with _lock:
            if level == "error":
                _logger.error(message)
            elif level == "warning":
                _logger.warning(message)
            else:
                _logger.info(message)

        self._append_gui(line)

    def info(self, message):
        self.log(message, "info")

    def warning(self, message):
        self.log(message, "warning")

    def error(self, message):
        self.log(message, "error")


logger = Logger()
