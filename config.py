"""
config.py
软件批量下载器配置文件
"""

from pathlib import Path

APP_NAME = "软件批量下载器"
APP_VERSION = "2.0.0"

MAX_WORKERS = 3
DOWNLOAD_TIMEOUT = 30
RETRY_COUNT = 3
CHUNK_SIZE = 1024 * 128

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)

DOWNLOAD_DIR = Path.home() / "Downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "download.log"

WINDOW_WIDTH = 1050
WINDOW_HEIGHT = 720
TABLE_HEIGHT = 18

FONT = ("微软雅黑", 10)
TITLE_FONT = ("微软雅黑", 11, "bold")

COLUMN_WIDTH = {
    "name": 340,
    "status": 120,
    "progress": 120,
    "speed": 120,
}

STATUS_WAIT = "等待"
STATUS_DOWNLOADING = "下载中"
STATUS_SUCCESS = "完成"
STATUS_FAILED = "失败"
STATUS_CANCEL = "取消"

SUCCESS_COLOR = "#2E8B57"
FAILED_COLOR = "#DC143C"
WARNING_COLOR = "#DAA520"
NORMAL_COLOR = "#333333"
