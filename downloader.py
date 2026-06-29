"""
downloader.py
软件下载核心模块 - 重构版本
"""

from __future__ import annotations

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
import requests

from config import (
    DOWNLOAD_DIR,
    DOWNLOAD_TIMEOUT,
    RETRY_COUNT,
    MAX_WORKERS,
    CHUNK_SIZE,
    USER_AGENT,
)
from logger import logger


class DownloadError(Exception):
    """下载异常基类"""
    pass


class DownloadManager:
    """
    下载管理器 - 支持多线程批量下载
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.lock = Lock()
        self.total_count = 0
        self.finished_count = 0
        self.progress_callback = None
        self.finish_callback = None
        self.log_callback = None
        self._shutdown = False

    # --------------------------
    # GUI绑定
    # --------------------------

    def bind_progress(self, func):
        """GUI更新函数 - func(name, status, percent, speed)"""
        self.progress_callback = func

    def bind_finish(self, func):
        """所有下载结束回调 - func(finished, total)"""
        self.finish_callback = func

    def bind_log(self, func):
        """日志回调 - func(text)"""
        self.log_callback = func

    # --------------------------
    # 日志
    # --------------------------

    def log(self, text):
        """记录日志"""
        logger.info(text)
        if self.log_callback:
            try:
                self.log_callback(text)
            except Exception as e:
                logger.error(f"日志回调异常：{e}")

    # --------------------------
    # GUI更新
    # --------------------------

    def update_item(self, name, status, percent, speed="--"):
        """更新GUI中的下载项"""
        if self.progress_callback:
            try:
                self.progress_callback(name, status, percent, speed)
            except Exception as e:
                logger.error(f"GUI更新失败：{e}")

    # --------------------------
    # 开始下载
    # --------------------------

    def download_all(self, task_list):
        """
        批量下载任务
        
        参数：
            task_list: 任务列表，每个任务包含 name, url, folder(可选), save_name(可选)
        """
        with self.lock:
            self.total_count = len(task_list)
            self.finished_count = 0
            self._shutdown = False

        if self.total_count == 0:
            self.log("没有下载任务")
            return

        self.log(f"开始批量下载，共 {self.total_count} 个任务")

        for task in task_list:
            if self._shutdown:
                break
            self.executor.submit(self.download_one, task)

    # --------------------------
    # 下载单个软件
    # --------------------------

    def download_one(self, task):
        """下载单个软件"""
        name = task.get("name", "未命名")
        url = task.get("url")
        folder = task.get("folder", "")
        filename = task.get("save_name", "")

        if not url:
            self.log(f"{name} 缺少下载链接")
            self._mark_finished()
            return

        try:
            # 确定保存目录
            save_dir = self._prepare_save_dir(folder)

            # 确定保存文件名
            if not filename:
                filename = url.split("/")[-1].split("?")[0]
            
            # 安全验证文件名（防止路径遍历）
            filename = Path(filename).name
            if not filename:
                filename = "download"

            save_file = save_dir / filename

            headers = {"User-Agent": USER_AGENT}

            self.log(f"{name} 开始下载")
            self.update_item(name, "下载中", 0, "--")

            # 重试逻辑
            self._download_with_retry(name, url, save_file, headers)

        except DownloadError as e:
            self.log(f"{name} 下载失败：{e}")
            self.update_item(name, "失败", 0, "--")
        except Exception as e:
            self.log(f"{name} 未预期的错误：{e}")
            self.update_item(name, "失败", 0, "--")
        finally:
            self._mark_finished()

    # --------------------------
    # 重试机制
    # --------------------------

    def _download_with_retry(self, name, url, save_file, headers):
        """带重试机制的下载"""
        last_exception = None

        for retry in range(RETRY_COUNT):
            try:
                self._download(name, url, save_file, headers)
                return  # 成功，退出

            except Timeout:
                last_exception = f"超时（重试 {retry + 1}/{RETRY_COUNT}）"
                self.log(f"{name} 下载超时，正在重试...")

            except ConnectionError:
                last_exception = f"连接错误（重试 {retry + 1}/{RETRY_COUNT}）"
                self.log(f"{name} 连接错误，正在重试...")

            except HTTPError as e:
                status_code = e.response.status_code
                if status_code == 404:
                    raise DownloadError("文件不存在（404）")
                elif status_code == 403:
                    raise DownloadError("无权限访问（403）")
                elif status_code in (301, 302, 303, 307, 308):
                    raise DownloadError("重定向过多或链接已失效")
                else:
                    last_exception = f"HTTP错误 {status_code}"
                    self.log(f"{name} HTTP错误 {status_code}，正在重试...")

            except RequestException as e:
                last_exception = str(e)
                self.log(f"{name} 请求失败：{e}，正在重试...")

            except DownloadError:
                raise  # 不重试的错误直接抛出

            except Exception as e:
                last_exception = str(e)
                self.log(f"{name} 错误：{e}，正在重试...")

            # 如果不是最后一次重试，等待后重试
            if retry < RETRY_COUNT - 1:
                wait_time = 2 ** retry  # 指数退避：2, 4, 8 秒
                time.sleep(wait_time)

        # 所有重试都失败
        raise DownloadError(last_exception or "未知错误")

    # --------------------------
    # 真正下载文件
    # --------------------------

    def _download(self, name, url, save_file, headers):
        """
        执行实际的文件下载
        
        参数：
            name: 软件名称
            url: 下载链接
            save_file: 保存文件路径
            headers: HTTP请求头
        """
        # 使用临时文件，下载完成后原子性移动
        temp_file = save_file.with_suffix(".tmp")

        try:
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=DOWNLOAD_TIMEOUT,
            )
            response.raise_for_status()

            total_size = int(response.headers.get("Content-Length", 0))

            if total_size == 0:
                self.log(f"{name} 警告：无法获取文件大小")

            downloaded = 0
            last_time = time.time()
            last_size = 0

            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue

                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    elapsed = now - last_time

                    # 每0.5秒刷新一次GUI
                    if elapsed >= 0.5:
                        speed = (downloaded - last_size) / elapsed
                        last_size = downloaded
                        last_time = now

                        speed_text = self.format_speed(speed)

                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                        else:
                            percent = 0

                        self.update_item(name, "下载中", percent, speed_text)

            # 验证下载完整性
            if total_size > 0 and downloaded != total_size:
                raise DownloadError(
                    f"文件不完整：已下载 {downloaded}/{total_size} 字节"
                )

            # 原子性移动文件
            temp_file.replace(save_file)

            self.update_item(name, "完成", 100, "完成")
            self.log(f"{name} 下载完成，保存到：{save_file}")

        except Exception as e:
            # 清理临时文件
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as cleanup_error:
                    self.log(f"{name} 清理临时文件失败：{cleanup_error}")
            raise

    # --------------------------
    # 辅助方法
    # --------------------------

    @staticmethod
    def _prepare_save_dir(folder):
        """准备保存目录"""
        if folder:
            save_dir = Path(folder)
        else:
            save_dir = DOWNLOAD_DIR

        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    @staticmethod
    def format_speed(speed):
        """
        格式化下载速度
        
        参数：
            speed: 速度，单位 B/s
            
        返回：
            格式化后的速度字符串
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
    # 进度管理
    # --------------------------

    def _mark_finished(self):
        """标记一个任务完成"""
        with self.lock:
            self.finished_count += 1
            if self.finish_callback:
                try:
                    self.finish_callback(self.finished_count, self.total_count)
                except Exception as e:
                    logger.error(f"完成回调异常：{e}")

    def overall_progress(self):
        """获取总体进度百分比"""
        with self.lock:
            if self.total_count == 0:
                return 0
            return int(self.finished_count * 100 / self.total_count)

    # --------------------------
    # 生命周期管理
    # --------------------------

    def stop(self):
        """停止所有下载任务"""
        with self.lock:
            self._shutdown = True

        self.executor.shutdown(wait=False, cancel_futures=True)
        self.log("下载任务已停止")

    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            if hasattr(self, "executor") and not self.executor._shutdown:
                self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
