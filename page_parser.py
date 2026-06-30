"""
page_parser.py
解析“下载页面”以自动找到真实的安装包下载链接
"""

from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Tuple, Dict
import requests
from bs4 import BeautifulSoup
from packaging.version import parse as parse_version

# 可以识别的安装包扩展名（按需扩展）
FILE_EXTS = (
    ".exe", ".msi", ".zip", ".tar.gz", ".tgz", ".7z",
    ".rar", ".pkg", ".dmg", ".deb", ".rpm", ".AppImage",
)

# 简单缓存，避免重复解析同一页面（进程内，短 TTL）
_CACHE: Dict[str, Tuple[float, str]] = {}
CACHE_TTL = 60 * 10  # 10 分钟缓存


def _looks_like_file_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in FILE_EXTS)


def _extract_urls_from_text(text: str, base_url: str) -> List[str]:
    # 简单正则搜索可能的文件链接（包含 query）
    pattern = re.compile(r'https?://[^\s"\'"<>]+(?:' + r'|'.join([re.escape(e) for e in FILE_EXTS]) + r')(?:\?[^\s"\'"<>]*)?', re.IGNORECASE)
    found = pattern.findall(text)
    # 也 try relative links with BeautifulSoup separately
    return [urljoin(base_url, u) for u in found]


def find_candidate_links(page_url: str, session: Optional[requests.Session] = None, timeout: int = 10) -> List[Tuple[str, str]]:
    """
    解析页面，返回候选下载链接列表：[(abs_url, link_text), ...]
    """
    # 缓存
    now = time.time()
    if page_url in _CACHE:
        ts, resolved = _CACHE[page_url]
        if now - ts < CACHE_TTL:
            return [(resolved, "cached")]

    s = session or requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = s.get(page_url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    candidates: List[Tuple[str, str]] = []

    # 1) 通过 a[href] 收集显式链接
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        abs_url = urljoin(page_url, href)
        if _looks_like_file_url(abs_url):
            text = a.get_text(strip=True) or href
            candidates.append((abs_url, text))

    # 2) 从页面文本用正则寻找直接出现的链接（某些站点会写明完整下载链接）
    if not candidates:
        for u in _extract_urls_from_text(resp.text, page_url):
            if _looks_like_file_url(u):
                candidates.append((u, "found_by_regex"))

    # 3) 某些页面通过 meta refresh 指向下载
    if not candidates:
        meta = soup.find("meta", attrs={"http-equiv": lambda v: v and v.lower() == "refresh"})
        if meta and "content" in meta.attrs:
            m = meta["content"]
            murl = m.split("url=")[-1]
            murl = urljoin(page_url, murl)
            if _looks_like_file_url(murl):
                candidates.append((murl, "meta_refresh"))

    # 记录缓存（如果只有一个候选，缓存最终结果；否则缓存 first)
    if candidates:
        _CACHE[page_url] = (now, candidates[0][0])

    # 去重并返回
    seen = set()
    uniq = []
    for u, t in candidates:
        if u not in seen:
            seen.add(u)
            uniq.append((u, t))
    return uniq


def _head_size(url: str, session: Optional[requests.Session] = None, timeout: int = 8) -> int:
    s = session or requests.Session()
    try:
        h = s.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        cl = h.headers.get("Content-Length")
        if cl and cl.isdigit():
            return int(cl)
    except Exception:
        # 有些站点不允许 HEAD，尝试用 GET 只请求一小段（带 stream）
        try:
            r = s.get(url, stream=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            cl = r.headers.get("Content-Length")
            if cl and cl.isdigit():
                return int(cl)
        except Exception:
            pass
    return 0


VERSION_RE = re.compile(r"v?(\d+(?:\.\d+){1,})", re.IGNORECASE)


def _extract_version_from_filename(url: str) -> Optional[str]:
    name = urlparse(url).path.split("/")[-1]
    m = VERSION_RE.search(name)
    if m:
        return m.group(1)
    return None


def choose_best_link(candidates: List[Tuple[str, str]], session: Optional[requests.Session] = None) -> str:
    """
    在候选链接中选择最佳的一个：
    - 优先有版本号的，使用 packaging.version 比较
    - 然后按 Content-Length 最大
    - 然后按 link text 含 'latest'/'download' 优先
    - 最后返回第一个
    """
    if not candidates:
        raise ValueError("未找到候选下载链接")

    parsed = []
    for url, text in candidates:
        ver = _extract_version_from_filename(url)
        size = _head_size(url, session=session)
        parsed.append({"url": url, "text": text, "version": ver, "size": size})

    # 1) 有版本的按版本号排序
    versioned = [p for p in parsed if p["version"]]
    if versioned:
        try:
            versioned.sort(key=lambda p: parse_version(p["version"]), reverse=True)
            return versioned[0]["url"]
        except Exception:
            pass

    # 2) 按文件大小选择最大
    parsed.sort(key=lambda p: p["size"], reverse=True)
    if parsed[0]["size"] > 0:
        return parsed[0]["url"]

    # 3) 按关键词排序
    keyword = ("latest", "download", "installer", "setup")
    for p in parsed:
        txt = (p["text"] or "").lower()
        if any(k in txt for k in keyword):
            return p["url"]

    # 4) 最后返回第一个
    return parsed[0]["url"]


def resolve_download_url(page_url: str, session: Optional[requests.Session] = None, timeout: int = 10) -> str:
    """
    给定一个下载页面，解析并返回最终的安装包 URL（如果找不到则抛出异常）
    """
    candidates = find_candidate_links(page_url, session=session, timeout=timeout)
    if not candidates:
        # 再尝试直接从文本抽取
        raise ValueError(f"在页面中未找到可识别的安装包链接：{page_url}")
    return choose_best_link(candidates, session=session)
