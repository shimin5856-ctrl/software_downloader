"""
gui.py
软件批量下载器 GUI
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import *

from excel_reader import read_excel

from downloader import DownloadManager

from logger import logger


class DownloadGUI:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(APP_NAME)

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.minsize(900, 600)

        self.file_path = ""

        self.tasks = []

        self.manager = DownloadManager()

        self.manager.bind_progress(
            self.update_item
        )

        self.manager.bind_finish(
            self.update_total
        )

        self.create_widgets()

    # ====================================
    # 创建界面
    # ====================================

    def create_widgets(self):

        self.create_toolbar()

        self.create_table()

        self.create_progress()

        self.create_log()

    # ====================================
    # 工具栏
    # ====================================

    def create_toolbar(self):

        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        ttk.Label(
            frame,
            text="Excel文件："
        ).pack(
            side="left"
        )

        self.path_var = tk.StringVar()

        self.entry = ttk.Entry(
            frame,
            textvariable=self.path_var,
            state="readonly",
            width=80
        )

        self.entry.pack(
            side="left",
            padx=5,
            fill="x",
            expand=True
        )

        self.btn_open = ttk.Button(

            frame,

            text="浏览...",

            command=self.open_excel

        )

        self.btn_open.pack(
            side="left",
            padx=5
        )

        self.btn_start = ttk.Button(

            frame,

            text="开始下载",

            command=self.start_download

        )

        self.btn_start.pack(
            side="left"
        )

    # ====================================
    # 软件列表
    # ====================================

    def create_table(self):

        frame = ttk.Frame(self.root)

        frame.pack(
            fill="both",
            expand=True,
            padx=10
        )

        columns = (

            "name",

            "status",

            "progress",

            "speed"

        )

        self.tree = ttk.Treeview(

            frame,

            columns=columns,

            show="headings",

            height=18

        )

        self.tree.heading(
            "name",
            text="软件名称"
        )

        self.tree.heading(
            "status",
            text="状态"
        )

        self.tree.heading(
            "progress",
            text="进度"
        )

        self.tree.heading(
            "speed",
            text="下载速度"
        )

        self.tree.column(
            "name",
            width=350
        )

        self.tree.column(
            "status",
            width=120,
            anchor="center"
        )

        self.tree.column(
            "progress",
            width=120,
            anchor="center"
        )

        self.tree.column(
            "speed",
            width=150,
            anchor="center"
        )

        vs = ttk.Scrollbar(

            frame,

            orient="vertical",

            command=self.tree.yview

        )

        self.tree.configure(
            yscrollcommand=vs.set
        )

        self.tree.pack(

            side="left",

            fill="both",

            expand=True

        )

        vs.pack(

            side="right",

            fill="y"

        )

"""
gui.py
软件批量下载器 GUI
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import *

from excel_reader import read_excel

from downloader import DownloadManager

from logger import logger


class DownloadGUI:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(APP_NAME)

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.minsize(900, 600)

        self.file_path = ""

        self.tasks = []

        self.manager = DownloadManager()

        self.manager.bind_progress(
            self.update_item
        )

        self.manager.bind_finish(
            self.update_total
        )

        self.create_widgets()

    # ====================================
    # 创建界面
    # ====================================

    def create_widgets(self):

        self.create_toolbar()

        self.create_table()

        self.create_progress()

        self.create_log()

    # ====================================
    # 工具栏
    # ====================================

    def create_toolbar(self):

        frame = ttk.Frame(
            self.root,
            padding=10
        )

        frame.pack(
            fill="x"
        )

        ttk.Label(
            frame,
            text="Excel文件："
        ).pack(
            side="left"
        )

        self.path_var = tk.StringVar()

        self.entry = ttk.Entry(
            frame,
            textvariable=self.path_var,
            state="readonly",
            width=80
        )

        self.entry.pack(
            side="left",
            padx=5,
            fill="x",
            expand=True
        )

        self.btn_open = ttk.Button(

            frame,

            text="浏览...",

            command=self.open_excel

        )

        self.btn_open.pack(
            side="left",
            padx=5
        )

        self.btn_start = ttk.Button(

            frame,

            text="开始下载",

            command=self.start_download

        )

        self.btn_start.pack(
            side="left"
        )

    # ====================================
    # 软件列表
    # ====================================

    def create_table(self):

        frame = ttk.Frame(self.root)

        frame.pack(
            fill="both",
            expand=True,
            padx=10
        )

        columns = (

            "name",

            "status",

            "progress",

            "speed"

        )

        self.tree = ttk.Treeview(

            frame,

            columns=columns,

            show="headings",

            height=18

        )

        self.tree.heading(
            "name",
            text="软件名称"
        )

        self.tree.heading(
            "status",
            text="状态"
        )

        self.tree.heading(
            "progress",
            text="进度"
        )

        self.tree.heading(
            "speed",
            text="下载速度"
        )

        self.tree.column(
            "name",
            width=350
        )

        self.tree.column(
            "status",
            width=120,
            anchor="center"
        )

        self.tree.column(
            "progress",
            width=120,
            anchor="center"
        )

        self.tree.column(
            "speed",
            width=150,
            anchor="center"
        )

        vs = ttk.Scrollbar(

            frame,

            orient="vertical",

            command=self.tree.yview

        )

        self.tree.configure(
            yscrollcommand=vs.set
        )

        self.tree.pack(

            side="left",

            fill="both",

            expand=True

        )

        vs.pack(

            side="right",

            fill="y"

        )
    # ====================================
    # 更新单个软件状态
    # ====================================

    def update_item(
        self,
        name,
        status,
        percent,
        speed
    ):

        def update():

            if not self.tree.exists(name):
                return

            self.tree.item(
                name,
                values=(
                    name,
                    status,
                    f"{percent}%",
                    speed
                )
            )

        self.root.after(
            0,
            update
        )

    # ====================================
    # 更新总体进度
    # ====================================

    def update_total(
        self,
        finished,
        total
    ):

        def update():

            percent = 0

            if total > 0:

                percent = int(
                    finished * 100 / total
                )

            self.total_progress["value"] = percent

            self.total_label.config(

                text=f"{percent}%"

            )

            # 全部完成

            if finished == total:

                self.btn_open.config(

                    state="normal"

                )

                self.btn_start.config(

                    state="normal"

                )

                logger.info(

                    "全部软件下载完成"

                )

                messagebox.showinfo(

                    "完成",

                    "全部软件下载完成！"

                )

        self.root.after(
            0,
            update
        )

    # ====================================
    # 清空日志
    # ====================================

    def clear_log(self):

        self.log_text.delete(

            "1.0",

            tk.END

        )

    # ====================================
    # 清空列表
    # ====================================

    def clear_table(self):

        self.tree.delete(

            *self.tree.get_children()

        )

        self.total_progress["value"] = 0

        self.total_label.config(

            text="0%"

        )

    # ====================================
    # 退出程序
    # ====================================

    def on_close(self):

        try:

            self.manager.stop()

        except Exception:

            pass

        self.root.destroy()

    # ====================================
    # 启动GUI
    # ====================================

    def run(self):

        self.root.protocol(

            "WM_DELETE_WINDOW",

            self.on_close

        )

        self.root.mainloop()


# ====================================
# 调试运行
# ====================================

if __name__ == "__main__":

    app = DownloadGUI()

    app.run()

    # ====================================
    # 更新单个软件状态
    # ====================================

    def update_item(
        self,
        name,
        status,
        percent,
        speed
    ):

        def update():

            if not self.tree.exists(name):
                return

            self.tree.item(
                name,
                values=(
                    name,
                    status,
                    f"{percent}%",
                    speed
                )
            )

        self.root.after(
            0,
            update
        )

    # ====================================
    # 更新总体进度
    # ====================================

    def update_total(
        self,
        finished,
        total
    ):

        def update():

            percent = 0

            if total > 0:

                percent = int(
                    finished * 100 / total
                )

            self.total_progress["value"] = percent

            self.total_label.config(

                text=f"{percent}%"

            )

            # 全部完成

            if finished == total:

                self.btn_open.config(

                    state="normal"

                )

                self.btn_start.config(

                    state="normal"

                )

                logger.info(

                    "全部软件下载完成"

                )

                messagebox.showinfo(

                    "完成",

                    "全部软件下载完成！"

                )

        self.root.after(
            0,
            update
        )

    # ====================================
    # 清空日志
    # ====================================

    def clear_log(self):

        self.log_text.delete(

            "1.0",

            tk.END

        )

    # ====================================
    # 清空列表
    # ====================================

    def clear_table(self):

        self.tree.delete(

            *self.tree.get_children()

        )

        self.total_progress["value"] = 0

        self.total_label.config(

            text="0%"

        )

    # ====================================
    # 退出程序
    # ====================================

    def on_close(self):

        try:

            self.manager.stop()

        except Exception:

            pass

        self.root.destroy()

    # ====================================
    # 启动GUI
    # ====================================

    def run(self):

        self.root.protocol(

            "WM_DELETE_WINDOW",

            self.on_close

        )

        self.root.mainloop()


# ====================================
# 调试运行
# ====================================

if __name__ == "__main__":

    app = DownloadGUI()

    app.run()