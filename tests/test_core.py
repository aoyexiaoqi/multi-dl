import os

from multi_dl.core import (
    QUALITY_FORMATS,
    build_options,
    collect_urls,
    format_duration,
    read_batch_file,
)
from conftest import parse


# --- quality presets -------------------------------------------------------

def test_preset_best_format():
    opts = build_options(parse([]))
    assert opts["format"] == "bv*+ba/b"


def test_preset_1080p_format():
    opts = build_options(parse(["--quality", "1080p"]))
    assert opts["format"] == "bv*[height<=1080]+ba/b[height<=1080]"


def test_preset_720p_format():
    opts = build_options(parse(["--quality", "720p"]))
    assert opts["format"] == "bv*[height<=720]+ba/b[height<=720]"


def test_preset_480p_format():
    opts = build_options(parse(["--quality", "480p"]))
    assert opts["format"] == "bv*[height<=480]+ba/b[height<=480]"


def test_preset_audio_format():
    opts = build_options(parse(["--quality", "audio"]))
    assert opts["format"] == "ba/b"


def test_all_presets_in_table():
    assert set(QUALITY_FORMATS) == {"best", "1080p", "720p", "480p", "audio"}


# --- audio postprocessor ----------------------------------------------------

def test_audio_postprocessor_present_in_audio_mode():
    opts = build_options(parse(["--quality", "audio"]))
    (pp,) = opts["postprocessors"]
    assert pp["key"] == "FFmpegExtractAudio"
    assert pp["preferredcodec"] == "mp3"
    assert pp["preferredquality"] == "192"


def test_audio_postprocessor_absent_in_video_mode():
    opts = build_options(parse(["--quality", "720p"]))
    assert "postprocessors" not in opts


# --- raw format override ----------------------------------------------------

def test_format_flag_overrides_preset():
    opts = build_options(parse(["--quality", "480p", "-f", "22/18"]))
    assert opts["format"] == "22/18"


def test_format_flag_overrides_audio_postprocessor():
    opts = build_options(parse(["--quality", "audio", "-f", "140"]))
    assert opts["format"] == "140"
    assert "postprocessors" not in opts


# --- output -----------------------------------------------------------------

def test_outtmpl_default_joins_output_dir():
    opts = build_options(parse(["-o", "downloads"]))
    assert opts["outtmpl"] == os.path.join(
        "downloads", "%(title)s [%(id)s].%(ext)s"
    )


def test_outtmpl_custom_template():
    opts = build_options(parse(["-o", "dl", "--template", "%(id)s.%(ext)s"]))
    assert opts["outtmpl"] == os.path.join("dl", "%(id)s.%(ext)s")


# --- playlist ---------------------------------------------------------------

def test_noplaylist_by_default():
    opts = build_options(parse([]))
    assert opts["noplaylist"] is True
    assert "playlistend" not in opts


def test_playlist_flag_and_limit():
    opts = build_options(parse(["--playlist", "--limit", "5"]))
    assert opts["noplaylist"] is False
    assert opts["playlistend"] == 5


# --- archive / retries / dry-run / subs ------------------------------------

def test_archive_passthrough():
    opts = build_options(parse(["--archive", "archive.txt"]))
    assert opts["download_archive"] == "archive.txt"


def test_retries_default_and_custom():
    assert build_options(parse([]))["retries"] == 10
    assert build_options(parse(["--retries", "3"]))["retries"] == 3


def test_dry_run_sets_simulate():
    assert build_options(parse(["--dry-run"]))["simulate"] is True
    assert "simulate" not in build_options(parse([]))


def test_subs_options():
    opts = build_options(parse(["--subs"]))
    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["subtitleslangs"] == ["zh.*", "en.*"]
    assert opts["subtitlesformat"] == "srt/best"


def test_subs_custom_langs():
    opts = build_options(parse(["--subs", "--sub-langs", "ja.*,en.*"]))
    assert opts["subtitleslangs"] == ["ja.*", "en.*"]


def test_no_subs_by_default():
    opts = build_options(parse([]))
    assert "writesubtitles" not in opts


# --- batch file & duration --------------------------------------------------

def _write_batch(tmp_path, text):
    path = tmp_path / "links.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_batch_file_parsing_skips_comments_and_blanks(tmp_path):
    path = _write_batch(
        tmp_path,
        "# 这是注释\n"
        "https://a.example/1\n"
        "\n"
        "   \n"
        "  https://b.example/2  \n"
        "#another comment\n"
        "https://c.example/3\n",
    )
    assert read_batch_file(path) == [
        "https://a.example/1",
        "https://b.example/2",
        "https://c.example/3",
    ]


def test_collect_urls_merges_positional_and_batch(tmp_path):
    path = _write_batch(tmp_path, "https://b.example/2\n")
    urls = collect_urls(["https://a.example/1"], path)
    assert urls == ["https://a.example/1", "https://b.example/2"]


def test_format_duration():
    assert format_duration(754) == "12:34"
    assert format_duration(65) == "01:05"
    assert format_duration(3661) == "1:01:01"
    assert format_duration(None) == "unknown"
