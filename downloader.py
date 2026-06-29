
"""
downloader.py
软件下载核心模块
"""

from __future__ import annotations

import os
import time
import requests

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from config import (
    DOWNLOAD_DIR,
    DOWNLOAD_TIMEOUT,
    RETRY_COUNT,
    MAX_WORKERS,
    CHUNK_SIZE,
    USER_AGENT,
)

from logger import logger


class DownloadManager:
    """
    下载管理器
    """

    def __init__(self):

        self.executor = ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        )

        self.lock = Lock()

        self.total_count = 0

        self.finished_count = 0

        self.progress_callback = None

        self.finish_callback = None

        self.log_callback = None

    # --------------------------
    # GUI绑定
    # --------------------------

    def bind_progress(self, func):
        """
        GUI更新函数

        参数：

        func(name,status,percent,speed)
        """

        self.progress_callback = func

    def bind_finish(self, func):
        """
        所有下载结束
        """

        self.finish_callback = func

    def bind_log(self, func):

        self.log_callback = func

    # --------------------------
    # 日志
    # --------------------------

    def log(self, text):

        logger.info(text)

        if self.log_callback:
            self.log_callback(text)

    # --------------------------
    # GUI更新
    # --------------------------

    def update_item(
        self,
        name,
        status,
        percent,
        speed="--"
    ):

        if self.progress_callback:

            self.progress_callback(
                name,
                status,
                percent,
                speed
            )

    # --------------------------
    # 开始下载
    # --------------------------

    def download_all(self, task_list):

        self.total_count = len(task_list)

        self.finished_count = 0

        for task in task_list:

            self.executor.submit(
                self.download_one,
                task
            )

    # --------------------------
    # 下载单个软件
    # --------------------------

    def download_one(self, task):

        name = task["name"]

        url = task["url"]

        folder = task.get("folder", "")

        filename = task.get("save_name", "")

        if folder:

            save_dir = Path(folder)

        else:

            save_dir = DOWNLOAD_DIR

        save_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if not filename:

            filename = url.split("/")[-1]

        save_file = save_dir / filename

        headers = {

            "User-Agent": USER_AGENT

        }

        self.log(f"{name} 开始下载")

        self.update_item(
            name,
            "下载中",
            0,
            "--"
        )

        for retry in range(RETRY_COUNT):

            try:

                self._download(
                    name,
                    url,
                    save_file,
                    headers
                )

                break

            except Exception as e:

                self.log(
                    f"{name} 下载失败：{e}"
                )

                if retry == RETRY_COUNT - 1:

                    self.update_item(
                        name,
                        "失败",
                        0,
                        "--"
                    )

                    return

                time.sleep(2)

    # --------------------------
    # 真正下载文件
    # --------------------------

    def _download(
        self,
        name,
        url,
        save_file,
        headers
    ):

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT
        )

        response.raise_for_status()

        total_size = int(
            response.headers.get(
                "Content-Length",
                0
            )
        )

        downloaded = 0

        last_time = time.time()

        last_size = 0

        if total_size == 0:

            self.log(
                f"{name} 无法获取文件大小"
            )

        with open(save_file, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=CHUNK_SIZE
            ):

                if not chunk:

                    continue

                f.write(chunk)

                downloaded += len(chunk)

                now = time.time()

                elapsed = now - last_time

                # 每0.5秒刷新一次GUI
                if elapsed >= 0.5:

                    speed = (
                        downloaded - last_size
                    ) / elapsed

                    last_size = downloaded

                    last_time = now

                    speed_text = self.format_speed(
                        speed
                    )

                    if total_size > 0:

                        percent = int(
                            downloaded
                            * 100
                            / total_size
                        )

                    else:

                        percent = 0

                    self.update_item(
                        name,
                        "下载中",
                        percent,
                        speed_text
                    )

        self.update_item(
            name,
            "完成",
            100,
            "完成"
        )

        self.log(
            f"{name} 下载完成"
        )

        with self.lock:

            self.finished_count += 1

            if self.finish_callback:

                self.finish_callback(
                    self.finished_count,
                    self.total_count
                )

    # --------------------------
    # 下载速度格式化
    # --------------------------

    @staticmethod
    def format_speed(speed):

        """
        speed 单位 B/s
        """

        if speed < 1024:

            return f"{speed:.0f} B/s"

        elif speed < 1024 * 1024:

            return f"{speed / 1024:.1f} KB/s"

        elif speed < 1024 * 1024 * 1024:

            return f"{speed / 1024 / 1024:.2f} MB/s"

        else:

            return f"{speed / 1024 / 1024 / 1024:.2f} GB/s"

    # --------------------------
    # 获取总体进度
    # --------------------------

    def overall_progress(self):

        if self.total_count == 0:

            return 0

        return int(

            self.finished_count

            * 100

            / self.total_count

        )

    # --------------------------
    # 停止下载（预留）
    # --------------------------

    def stop(self):

        self.executor.shutdown(

            wait=False,

            cancel_futures=True

        )

        self.log("下载任务已停止")