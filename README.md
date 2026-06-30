# 软件批量下载器 (software_downloader)

这是一个用于批量下载软件安装包的简单 GUI 工具（基于 Tkinter）。本次提交添加了自动解析“下载页面”的功能：当 Excel 中填写的是产品的下载页面（而非直接的文件链接）时，程序会尝试解析页面并自动选取最新的安装包进行下载。

主要特性

- 从 Excel 文件读取下载任务（软件名称、下载地址、可选保存文件名、保存目录）
- 多线程并发下载（可配置最大线程数）
- 支持从“下载页面”自动解析真实安装包链接（新增 page_parser.py）
- 简单的版本/大小优先策略：优先选择文件名中带版本号的最大版本，或 Content-Length 最大的文件
- GUI 日志与文件日志（RotatingFileHandler）

安装（推荐虚拟环境）

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

或者手动安装依赖：

```bash
pip install requests beautifulsoup4 packaging pandas openpyxl
```

运行

```bash
python main.py
```

使用说明

1. 在 Excel 文件中准备下载列表，至少包含两列：
   - 软件名称（列名：软件名称）
   - 下载地址（列名：下载地址）

   可选列：
   - 保存文件名（列名：保存文件名）
   - 保存目录（列名：保存目录）

2. 在 GUI 中选择 Excel 文件，加载任务后点击“开始下载”。

自动解析下载页面说明

- 如果 Excel 中填写的是指向产品下载页面的链接（例如厂商下载页或 GitHub Release 页面），程序会在尝试下载前用 page_parser.py 解析页面，提取候选的安装包链接并选出“最佳”一个进行下载。
- 解析策略：
  - 从页面的 a[href] 中找到带常见安装包扩展名的链接（.exe/.msi/.zip/.tar.gz/.dmg/.deb 等）
  - 若文件名包含版本号（例如 v1.2.3 或 1.2.3），优先选择最大版本
  - 否则按 Content-Length（HEAD）选择最大文件
  - 如仍无法判定，按链接文本中包含 latest/download/installer 等关键词优先
- 对于需要 JavaScript 渲染或点击按钮才会触发下载的页面（AJAX/POST），静态解析可能失败，请参考“高级：使用 Playwright”部分进行处理

安全与注意事项

- 自动解析第三方页面并下载文件存在风险，请仅对可信来源使用此功能。
- 如果你希望更严格的安全控制，可以在 GUI 中显示解析出的真实下载 URL 并要求用户确认，或在程序中加入域名白名单/黑名单。

高级：使用 Playwright（可选）

某些网站通过 JavaScript 动态生成下载链接或需要点击按钮触发下载。若需要支持这些站点，可以使用 Playwright（额外依赖，体积较大）：

```bash
pip install playwright
python -m playwright install
```

然后可以在 page_parser.py 中添加一个基于 Playwright 的渲染分支，用浏览器渲染后的 page.content() 交给 BeautifulSoup 解析。

开发与测试

- 代码组织：
  - main.py: 启动入口
  - gui.py: Tkinter GUI
  - downloader.py: 下载管理器（现在已集成 page_parser）
  - page_parser.py: 新增的下载页面解析器
  - excel_reader.py: 从 Excel 读取任务
  - logger.py: 线程安全日志

- 单元测试：建议为 page_parser 写单元测试，使用静态 HTML 样例覆盖常见页面结构。

依赖

见 requirements.txt。

如果你希望我把 Playwright 回退解析或 README 中的示例扩展为针对你的常用下载站点（例如某些厂商或 GitHub Release 的示例），我可以继续补充。