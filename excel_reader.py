"""
excel_reader.py
读取软件下载列表（Excel）
"""

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = ["软件名称", "下载地址"]


class ExcelReader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def _check_file(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在：{self.file_path}")

        if self.file_path.suffix.lower() not in (".xlsx", ".xls"):
            raise ValueError("仅支持 .xlsx 或 .xls 文件")

    def read(self):
        self._check_file()

        df = pd.read_excel(self.file_path)

        df.columns = [str(c).strip() for c in df.columns]

        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                raise ValueError(
                    f"Excel缺少必须列：{col}\n"
                    f"当前列：{', '.join(df.columns)}"
                )

        df = df.dropna(subset=["软件名称", "下载地址"])

        result = []

        for _, row in df.iterrows():
            result.append({
                "name": str(row["软件名称"]).strip(),
                "url": str(row["下载地址"]).strip(),
                "save_name": (
                    str(row["保存文件名"]).strip()
                    if "保存文件名" in df.columns and pd.notna(row.get("保存文件名"))
                    else ""
                ),
                "folder": (
                    str(row["保存目录"]).strip()
                    if "保存目录" in df.columns and pd.notna(row.get("保存目录"))
                    else ""
                ),
            })

        return result


def read_excel(file_path):
    return ExcelReader(file_path).read()


if __name__ == "__main__":
    data = read_excel("软件列表.xlsx")

    for item in data:
        print(item)
