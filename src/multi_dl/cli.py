"""Command-line interface for multi-dl.

The default experience is *paste mode*: copy a video link, run ``multi-dl``,
paste, press Enter, then an empty line to start downloading. URLs can also be
passed positionally or via a batch file.

multi-dl is a friendly front-end to yt-dlp. It does not bypass DRM or any
other access control; only download content you have the right to.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

import yt_dlp
from yt_dlp.utils import DownloadError

from .core import build_options, collect_urls, format_duration

PASTE_INSTRUCTION = (
    "粘贴视频链接后回车，可连续粘贴多条，空行开始下载\n"
    "Paste a video link and press Enter; paste more links, "
    "or an empty line to start downloading."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi-dl",
        description="多平台视频下载（基于 yt-dlp）：复制链接、粘贴、回车即可下载。"
        " Multi-platform video downloader powered by yt-dlp.",
    )
    parser.add_argument("urls", nargs="*", metavar="URL", help="一个或多个视频链接")
    parser.add_argument(
        "-a",
        "--batch-file",
        metavar="FILE",
        help="从文本文件读取链接（一行一个，# 开头为注释）",
    )
    parser.add_argument(
        "--quality",
        choices=["best", "1080p", "720p", "480p", "audio"],
        default="best",
        help="画质预设（默认 best；audio 只下载音频并转 mp3）",
    )
    parser.add_argument(
        "-f",
        "--format",
        metavar="FMT",
        help="自定义 yt-dlp 格式字符串（覆盖 --quality）",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        metavar="DIR",
        help="下载目录（默认当前目录）",
    )
    parser.add_argument(
        "--template",
        metavar="TEMPLATE",
        help="yt-dlp 输出文件名模板（默认 '%%(title)s [%%(id)s].%%(ext)s'）",
    )
    parser.add_argument("--subs", action="store_true", help="同时下载字幕与自动字幕")
    parser.add_argument(
        "--sub-langs",
        default="zh.*,en.*",
        metavar="LANGS",
        help="字幕语言（逗号分隔，默认 zh.*,en.*）",
    )
    parser.add_argument(
        "--playlist", action="store_true", help="下载整个播放列表（默认只下单个视频）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="播放列表最多下载前 N 个",
    )
    parser.add_argument(
        "--archive",
        metavar="FILE",
        help="下载档案文件：记录已下载的视频，跨次运行去重/续传",
    )
    parser.add_argument(
        "--retries", type=int, default=10, metavar="N", help="重试次数（默认 10）"
    )
    parser.add_argument(
        "--info",
        metavar="URL",
        help="只查看视频信息（标题/作者/时长/格式数），不下载",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="配合 --info：输出原始信息 JSON",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行：走完整流程但不真正下载文件"
    )
    return parser


def read_pasted_urls() -> List[str]:
    """Interactive paste prompt: read lines until an empty line or EOF."""
    print(PASTE_INSTRUCTION)
    urls: List[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        line = line.strip()
        if not line:
            break
        urls.append(line)
    return urls


def run_download(opts: dict, urls: List[str]) -> int:
    """Download ``urls`` with a YoutubeDL instance. Returns an exit code."""
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
    except DownloadError as exc:
        print("multi-dl: 下载失败 / download failed: %s" % exc, file=sys.stderr)
        return 1
    return 0


def run_info(opts: dict, url: str, as_json: bool) -> int:
    """Extract and print metadata for one URL. Returns an exit code."""
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as exc:
        print("multi-dl: 获取信息失败 / info failed: %s" % exc, file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
        return 0
    print("标题 / Title: %s" % info.get("title"))
    print("作者 / Uploader: %s" % info.get("uploader"))
    print("时长 / Duration: %s" % format_duration(info.get("duration")))
    print("链接 / URL: %s" % info.get("webpage_url"))
    print("可用格式 / Formats: %d" % len(info.get("formats") or []))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    opts = build_options(args)

    # Info mode stands alone.
    if args.info:
        return run_info(opts, args.info, args.json)

    # Collect URLs: positional + batch file, else fall back to paste mode.
    try:
        urls = collect_urls(args.urls, args.batch_file)
    except OSError as exc:
        print("multi-dl: 无法读取批量文件 / cannot read batch file: %s" % exc, file=sys.stderr)
        return 2
    if not urls:
        urls = read_pasted_urls()
    if not urls:
        print(
            "multi-dl: 没有提供任何链接 / no links provided.",
            file=sys.stderr,
        )
        return 2

    return run_download(opts, urls)


if __name__ == "__main__":
    sys.exit(main())
