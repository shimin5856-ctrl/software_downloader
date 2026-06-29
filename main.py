"""
main.py
软件批量下载器启动入口 - 重构版本
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
    应用程序主类
    
    负责应用程序的初始化、启动和异常处理
    """

    def __init__(self):
        """初始化应用程序"""
        self.gui: DownloadGUI | None = None

    def initialize(self):
        """
        初始化应用程序
        
        创建GUI实例并记录启动信息
        """
        try:
            logger.info(f"{APP_NAME} {APP_VERSION} 启动")
            self.gui = DownloadGUI()
            logger.info("GUI初始化完成")
        except Exception as e:
            logger.error(f"应用初始化失败：{e}")
            raise

    def run(self):
        """
        运行应用程序
        
        处理各种异常情况：
        - KeyboardInterrupt: 用户按下Ctrl+C
        - Exception: 其他未捕获的异常
        """
        try:
            self.initialize()
            
            if self.gui is None:
                raise RuntimeError("GUI初始化失败")
            
            self.gui.run()

        except KeyboardInterrupt:
            logger.warning("用户中止程序")
            sys.exit(0)

        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(f"程序异常：{error_msg}")
            self._show_error_dialog(error_msg)
            sys.exit(1)

    @staticmethod
    def _show_error_dialog(error_msg: str):
        """
        显示错误对话框
        
        参数：
            error_msg: 错误信息文本
        """
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            messagebox.showerror(
                "程序异常",
                f"程序遇到错误：\n\n{error_msg}"
            )
            
            root.destroy()
        except Exception as e:
            # 如果GUI错误对话框失败，至少打印到控制台
            print(f"显示错误对话框失败：{e}", file=sys.stderr)
            print(f"原始错误：{error_msg}", file=sys.stderr)


def main():
    """
    应用程序主入口
    
    创建并运行Application实例
    """
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
