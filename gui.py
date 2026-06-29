"""
gui.py
软件批量下载器 GUI - 重构版本
"""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from config import (
    APP_NAME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FONT,
    TITLE_FONT,
    COLUMN_WIDTH,
    STATUS_WAIT,
    STATUS_DOWNLOADING,
    STATUS_SUCCESS,
    STATUS_FAILED,
    SUCCESS_COLOR,
    FAILED_COLOR,
    WARNING_COLOR,
    NORMAL_COLOR,
)
from excel_reader import read_excel
from downloader import DownloadManager
from logger import logger


class DownloadGUI:
    """软件批量下载器 GUI 主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(900, 600)

        self.file_path = ""
        self.tasks = []
        self.task_items = {}  # 存储任务ID与Treeview项的映射

        # 初始化下载管理器
        self.manager = DownloadManager()
        self.manager.bind_progress(self.update_item)
        self.manager.bind_finish(self.update_total)
        self.manager.bind_log(self.append_log)

        # 创建界面
        self.create_widgets()

    # ====================================
    # 创建界面
    # ====================================

    def create_widgets(self):
        """创建所有界面组件"""
        self.create_toolbar()
        self.create_table()
        self.create_progress()
        self.create_log()

    # ====================================
    # 工具栏
    # ====================================

    def create_toolbar(self):
        """创建工具栏"""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="x")

        # 标签
        ttk.Label(frame, text="Excel文件：").pack(side="left")

        # 文件路径输入框
        self.path_var = tk.StringVar()
        self.entry = ttk.Entry(
            frame,
            textvariable=self.path_var,
            state="readonly",
            width=80
        )
        self.entry.pack(side="left", padx=5, fill="x", expand=True)

        # 浏览按钮
        self.btn_open = ttk.Button(
            frame,
            text="浏览...",
            command=self.open_excel
        )
        self.btn_open.pack(side="left", padx=5)

        # 开始下载按钮
        self.btn_start = ttk.Button(
            frame,
            text="开始下载",
            command=self.start_download,
            state="disabled"
        )
        self.btn_start.pack(side="left", padx=2)

        # 停止下载按钮
        self.btn_stop = ttk.Button(
            frame,
            text="停止下载",
            command=self.stop_download,
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=2)

        # 清空列表按钮
        self.btn_clear = ttk.Button(
            frame,
            text="清空列表",
            command=self.clear_table
        )
        self.btn_clear.pack(side="left", padx=2)

    # ====================================
    # 软件列表
    # ====================================

    def create_table(self):
        """创建软件列表表格"""
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 定义列
        columns = ("name", "status", "progress", "speed")
        
        # 创建Treeview
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=18
        )

        # 设置列标题
        self.tree.heading("name", text="软件名称")
        self.tree.heading("status", text="状态")
        self.tree.heading("progress", text="进度")
        self.tree.heading("speed", text="下载速度")

        # 设置列宽
        self.tree.column("name", width=COLUMN_WIDTH["name"])
        self.tree.column("status", width=COLUMN_WIDTH["status"], anchor="center")
        self.tree.column("progress", width=COLUMN_WIDTH["progress"], anchor="center")
        self.tree.column("speed", width=COLUMN_WIDTH["speed"], anchor="center")

        # 创建滚动条
        vs = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)

        # 布局
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

    # ====================================
    # 进度条
    # ====================================

    def create_progress(self):
        """创建总体进度条"""
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="总体进度：", font=FONT).pack(side="left")

        self.total_progress = ttk.Progressbar(
            frame,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.total_progress.pack(side="left", padx=10, fill="x", expand=True)

        self.total_label = ttk.Label(frame, text="0%", font=TITLE_FONT, width=5)
        self.total_label.pack(side="left")

    # ====================================
    # 日志输出
    # ====================================

    def create_log(self):
        """创建日志输出区域"""
        frame = ttk.LabelFrame(self.root, text="日志输出", padding=5)
        frame.pack(fill="both", padx=10, pady=5)

        # 创建文本框
        self.log_text = tk.Text(
            frame,
            height=6,
            width=80,
            font=("Courier", 9),
            state="disabled"
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 绑定日志小部件
        logger.bind_text_widget(self.log_text)

    # ====================================
    # 文件操作
    # ====================================

    def open_excel(self):
        """打开Excel文件对话框"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            # 读取Excel文件
            self.tasks = read_excel(file_path)
            self.file_path = file_path

            # 更新UI
            self.path_var.set(file_path)
            self.clear_table()
            self._load_tasks_to_table()
            self.btn_start.config(state="normal")

            logger.info(f"成功加载 {len(self.tasks)} 个下载任务")

        except Exception as e:
            logger.error(f"读取Excel文件失败：{e}")
            messagebox.showerror("错误", f"读取文件失败：{e}")
            self.path_var.set("")

    def _load_tasks_to_table(self):
        """将任务加载到表格"""
        self.task_items.clear()
        for idx, task in enumerate(self.tasks):
            name = task.get("name", "未命名")
            item_id = self.tree.insert(
                "",
                "end",
                iid=name,
                values=(name, STATUS_WAIT, "0%", "--")
            )
            self.task_items[name] = item_id

    # ====================================
    # 下载控制
    # ====================================

    def start_download(self):
        """开始下载"""
        if not self.tasks:
            messagebox.showwarning("警告", "请先选择Excel文件")
            return

        # 禁用按钮
        self.btn_open.config(state="disabled")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_clear.config(state="disabled")

        # 重置进度
        self.total_progress["value"] = 0
        self.total_label.config(text="0%")

        # 在后台线程启动下载
        thread = threading.Thread(
            target=self.manager.download_all,
            args=(self.tasks,),
            daemon=True
        )
        thread.start()

        logger.info("开始批量下载...")

    def stop_download(self):
        """停止下载"""
        self.manager.stop()
        self.btn_stop.config(state="disabled")
        logger.warning("用户停止下载")

    def clear_table(self):
        """清空列表"""
        self.tree.delete(*self.tree.get_children())
        self.total_progress["value"] = 0
        self.total_label.config(text="0%")
        self.task_items.clear()

    # ====================================
    # 日志处理
    # ====================================

    def append_log(self, text):
        """追加日志到日志文本框"""
        def _append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", text + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

        self.root.after(0, _append)

    # ====================================
    # 更新UI
    # ====================================

    def update_item(self, name, status, percent, speed):
        """更新单个下载项的状态"""
        def _update():
            if name not in self.task_items:
                return

            item_id = self.task_items[name]
            
            # 更新数值
            self.tree.item(
                item_id,
                values=(name, status, f"{percent}%", speed)
            )

            # 根据状态设置颜色
            if status == STATUS_SUCCESS:
                self.tree.item(item_id, tags=("success",))
            elif status == STATUS_FAILED:
                self.tree.item(item_id, tags=("failed",))
            elif status == STATUS_DOWNLOADING:
                self.tree.item(item_id, tags=("downloading",))

        self.root.after(0, _update)

    def update_total(self, finished, total):
        """更新总体进度"""
        def _update():
            if total > 0:
                percent = int(finished * 100 / total)
            else:
                percent = 0

            self.total_progress["value"] = percent
            self.total_label.config(text=f"{percent}%")

            # 全部完成
            if finished == total and total > 0:
                self.btn_open.config(state="normal")
                self.btn_start.config(state="normal")
                self.btn_stop.config(state="disabled")
                self.btn_clear.config(state="normal")

                logger.info("全部软件下载完成")
                messagebox.showinfo("完成", "全部软件下载完成！")

        self.root.after(0, _update)

    # ====================================
    # 程序生命周期
    # ====================================

    def on_close(self):
        """关闭程序"""
        try:
            self.manager.stop()
        except Exception as e:
            logger.error(f"停止下载管理器失败：{e}")

        self.root.destroy()

    def run(self):
        """启动GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()


# ====================================
# 主函数
# ====================================

if __name__ == "__main__":
    app = DownloadGUI()
    app.run()
