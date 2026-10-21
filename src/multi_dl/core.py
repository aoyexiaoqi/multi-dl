"""Pure helpers for multi-dl: yt-dlp option building, batch files, formatting.

Everything in this module is side-effect free (except reading a batch file)
so it can be unit-tested without network access or a real yt-dlp run.
"""

from __future__ import annotations

import os
from typing import List, Optional

DEFAULT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
DEFAULT_SUB_LANGS = "zh.*,en.*"

#: Quality preset name -> yt-dlp format string.
QUALITY_FORMATS = {
    "best": "bv*+ba/b",
    "1080p": "bv*[height<=1080]+ba/b[height<=1080]",
    "720p": "bv*[height<=720]+ba/b[height<=720]",
    "480p": "bv*[height<=480]+ba/b[height<=480]",
    "audio": "ba/b",
}

AUDIO_POSTPROCESSOR = {
    "key": "FFmpegExtractAudio",
    "preferredcodec": "mp3",
    "preferredquality": "192",
}


def read_batch_file(path: str) -> List[str]:
    """Read URLs from a text file: one per line.

    Blank lines and lines starting with ``#`` are ignored; surrounding
    whitespace is stripped.
    """
    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def collect_urls(positional: List[str], batch_file: Optional[str]) -> List[str]:
    """Merge URLs from positional args and an optional batch file."""
    urls = list(positional)
    if batch_file:
        urls.extend(read_batch_file(batch_file))
    return urls


def format_duration(seconds) -> str:
    """Format a duration in seconds as mm:ss (or h:mm:ss for >= 1 hour)."""
    if seconds is None:
        return "unknown"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return "%d:%02d:%02d" % (hours, minutes, secs)
    return "%02d:%02d" % (minutes, secs)


def build_options(args) -> dict:
    """Build the yt-dlp options dict from parsed CLI args.

    ``args`` is the argparse namespace produced by :mod:`multi_dl.cli`
    (any object with the same attributes works).
    """
    opts: dict = {}

    # Format selection: an explicit -f/--format string always wins.
    if getattr(args, "format", None):
        opts["format"] = args.format
    else:
        opts["format"] = QUALITY_FORMATS[args.quality]
    # Audio preset: extract to mp3 after downloading the best audio stream.
    if args.quality == "audio" and not getattr(args, "format", None):
        opts["postprocessors"] = [dict(AUDIO_POSTPROCESSOR)]

    # Output location / naming.
    template = getattr(args, "template", None) or DEFAULT_TEMPLATE
    opts["outtmpl"] = os.path.join(args.output_dir, template)

    # Playlist handling: single video unless explicitly asked otherwise.
    opts["noplaylist"] = not getattr(args, "playlist", False)
    if getattr(args, "limit", None):
        opts["playlistend"] = args.limit

    # Download archive for dedupe / resume across runs.
    if getattr(args, "archive", None):
        opts["download_archive"] = args.archive

    opts["retries"] = args.retries

    if getattr(args, "dry_run", False):
        opts["simulate"] = True

    # Subtitles (manual + automatic captions).
    if getattr(args, "subs", False):
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        langs = getattr(args, "sub_langs", None) or DEFAULT_SUB_LANGS
        opts["subtitleslangs"] = [s.strip() for s in langs.split(",") if s.strip()]
        opts["subtitlesformat"] = "srt/best"

    return opts
