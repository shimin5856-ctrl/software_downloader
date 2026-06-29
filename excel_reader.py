"""
excel_reader.py
读取软件下载列表（Excel）- 重构版本
"""

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = ["软件名称", "下载地址"]
OPTIONAL_COLUMNS = ["保存文件名", "保存目录"]


class ExcelReaderError(Exception):
    """Excel读取异常基类"""
    pass


class ExcelReader:
    """
    Excel文件读取器
    
    支持读取包含以下列的Excel文件：
    - 软件名称 (必须)
    - 下载地址 (必须)
    - 保存文件名 (可选)
    - 保存目录 (可选)
    """

    def __init__(self, file_path: str):
        """
        初始化读取器
        
        参数：
            file_path: Excel文件路径
        """
        self.file_path = Path(file_path)

    def _check_file(self):
        """检查文件有效性"""
        if not self.file_path.exists():
            raise ExcelReaderError(f"文件不存在：{self.file_path}")

        if self.file_path.suffix.lower() not in (".xlsx", ".xls"):
            raise ExcelReaderError(
                f"不支持的文件格式：{self.file_path.suffix}，仅支持 .xlsx 或 .xls"
            )

    def _read_excel_file(self) -> pd.DataFrame:
        """读取Excel文件"""
        try:
            df = pd.read_excel(self.file_path)
            return df
        except Exception as e:
            raise ExcelReaderError(f"读取Excel文件失败：{e}")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名（去掉首尾空格）"""
        df.columns = [str(col).strip() for col in df.columns]
        return df

    def _validate_columns(self, df: pd.DataFrame):
        """验证必需的列是否存在"""
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            available_columns = ", ".join(df.columns)
            raise ExcelReaderError(
                f"Excel缺少必须列：{', '.join(missing_columns)}\n"
                f"当前列：{available_columns}"
            )

    def _filter_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """过滤掉名称或链接为空的行"""
        df = df.dropna(subset=["软件名称", "下载地址"])
        
        # 过滤空字符串
        df = df[
            (df["软件名称"].astype(str).str.strip() != "") &
            (df["下载地址"].astype(str).str.strip() != "")
        ]
        
        return df

    def _extract_task(self, row: pd.Series) -> dict:
        """从一行数据提取任务信息"""
        task = {
            "name": str(row["软件名称"]).strip(),
            "url": str(row["下载地址"]).strip(),
            "save_name": self._get_optional_field(row, "保存文件名"),
            "folder": self._get_optional_field(row, "保存目录"),
        }
        return task

    @staticmethod
    def _get_optional_field(row: pd.Series, column_name: str) -> str:
        """获取可选字段，如果不存在或为空则返回空字符串"""
        if column_name not in row.index:
            return ""
        
        value = row.get(column_name)
        
        # 检查是否为NaN或None
        if pd.isna(value):
            return ""
        
        return str(value).strip()

    def read(self) -> list:
        """
        读取并解析Excel文件
        
        返回：
            任务列表，每个任务为dict，包含以下键：
            - name: 软件名称
            - url: 下载链接
            - save_name: 保存文件名（可选）
            - folder: 保存目录（可选）
        
        异常：
            ExcelReaderError: 文件不存在、格式不支持或数据验证失败
        """
        # 1. 检查文件
        self._check_file()

        # 2. 读取Excel文件
        df = self._read_excel_file()

        # 3. 标准化列名
        df = self._normalize_columns(df)

        # 4. 验证必需列
        self._validate_columns(df)

        # 5. 过滤空行
        df = self._filter_empty_rows(df)

        if df.empty:
            raise ExcelReaderError("Excel文件中没有有效的下载任务")

        # 6. 提取任务
        result = [self._extract_task(row) for _, row in df.iterrows()]

        return result


def read_excel(file_path: str) -> list:
    """
    便捷函数：读取Excel文件
    
    参数：
        file_path: Excel文件路径
    
    返回：
        任务列表
    
    异常：
        ExcelReaderError: 读取或解析失败
    """
    return ExcelReader(file_path).read()


if __name__ == "__main__":
    try:
        data = read_excel("软件列表.xlsx")
        
        print(f"成功读取 {len(data)} 个下载任务：")
        print("-" * 80)
        
        for idx, item in enumerate(data, 1):
            print(f"{idx}. 软件名称: {item['name']}")
            print(f"   下载链接: {item['url']}")
            if item.get("save_name"):
                print(f"   保存文件名: {item['save_name']}")
            if item.get("folder"):
                print(f"   保存目录: {item['folder']}")
            print()
            
    except Exception as e:
        print(f"错误：{e}")
