"""
main.py
软件批量下载器启动入口
"""

from __future__ import annotations

import sys
import traceback
import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, APP_VERSION
from logger import logger
from gui import DownloadGUI


class Application:
    """
    应用程序入口
    """

    def __init__(self):

        self.gui = None

    # ----------------------------
    # 初始化
    # ----------------------------

    def initialize(self):

        logger.info(
            f"{APP_NAME} {APP_VERSION} 启动"
        )

        self.gui = DownloadGUI()

    # ----------------------------
    # 启动
    # ----------------------------

    def run(self):

        try:

            self.initialize()

            self.gui.run()

        except KeyboardInterrupt:

            logger.warning(
                "用户终止程序"
            )

        except Exception:

            error = traceback.format_exc()

            logger.error(error)

            self.show_error(error)

    # ----------------------------
    # 错误窗口
    # ----------------------------

    @staticmethod
    def show_error(msg):

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(

            "程序异常",

            msg

        )

        root.destroy()


# ----------------------------
# 主入口
# ----------------------------

def main():

    app = Application()

    app.run()


if __name__ == "__main__":

    main()