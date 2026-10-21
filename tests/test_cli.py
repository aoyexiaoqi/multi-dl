import json

import pytest
from yt_dlp.utils import DownloadError

import multi_dl.cli as cli
from conftest import FAKE_INFO


# --- straightforward downloads ---------------------------------------------

def test_download_positional_urls(fake_ydl):
    code = cli.main(["https://a.example/1", "https://b.example/2"])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1", "https://b.example/2"]


def test_download_merges_batch_file(fake_ydl, tmp_path):
    batch = tmp_path / "links.txt"
    batch.write_text("# 注释\nhttps://b.example/2\n", encoding="utf-8")
    code = cli.main(["https://a.example/1", "-a", str(batch)])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1", "https://b.example/2"]


def test_download_batch_file_only(fake_ydl, tmp_path):
    batch = tmp_path / "links.txt"
    batch.write_text("https://a.example/1\nhttps://a.example/2\n", encoding="utf-8")
    code = cli.main(["-a", str(batch)])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1", "https://a.example/2"]


# --- paste mode (default when no URLs and no batch file) --------------------

def _fake_input(monkeypatch, lines):
    it = iter(lines)

    def _input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr("builtins.input", _input)


def test_paste_mode_downloads_pasted_url(fake_ydl, monkeypatch, capsys):
    _fake_input(monkeypatch, ["https://a.example/1", ""])
    code = cli.main([])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1"]
    assert "粘贴视频链接" in capsys.readouterr().out


def test_paste_mode_multiple_urls_and_options_apply(fake_ydl, monkeypatch):
    _fake_input(
        monkeypatch,
        ["  https://a.example/1  ", "https://b.example/2", ""],
    )
    code = cli.main(["--quality", "720p", "--archive", "arc.txt"])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1", "https://b.example/2"]
    assert inst.opts["format"] == "bv*[height<=720]+ba/b[height<=720]"
    assert inst.opts["download_archive"] == "arc.txt"


def test_paste_mode_eof_ends_input(fake_ydl, monkeypatch):
    _fake_input(monkeypatch, ["https://a.example/1"])  # then EOF
    code = cli.main([])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.downloaded == ["https://a.example/1"]


def test_paste_mode_no_links_exit_2(fake_ydl, monkeypatch, capsys):
    _fake_input(monkeypatch, [""])
    code = cli.main([])
    assert code == 2
    assert fake_ydl.instances == []
    assert "no links provided" in capsys.readouterr().err


def test_paste_mode_immediate_eof_exit_2(fake_ydl, monkeypatch, capsys):
    _fake_input(monkeypatch, [])
    code = cli.main([])
    assert code == 2
    assert "no links provided" in capsys.readouterr().err


# --- info mode ---------------------------------------------------------------

def test_info_prints_fields(fake_ydl, capsys):
    code = cli.main(["--info", "https://example.com/watch?v=abc123"])
    assert code == 0
    (inst,) = fake_ydl.instances
    assert inst.info_url == "https://example.com/watch?v=abc123"
    assert inst.downloaded is None
    out = capsys.readouterr().out
    assert FAKE_INFO["title"] in out
    assert FAKE_INFO["uploader"] in out
    assert "12:34" in out  # 754 seconds formatted as mm:ss
    assert FAKE_INFO["webpage_url"] in out
    assert "3" in out  # number of formats


def test_info_json_dumps_raw_dict(fake_ydl, capsys):
    code = cli.main(["--info", "https://example.com/watch?v=abc123", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["title"] == FAKE_INFO["title"]
    assert data["duration"] == 754
    assert len(data["formats"]) == 3


def test_info_download_error_exit_1(fake_ydl, capsys):
    fake_ydl.fail_with = DownloadError("no such video")
    code = cli.main(["--info", "https://example.com/bad"])
    assert code == 1
    assert "no such video" in capsys.readouterr().err


# --- error handling ----------------------------------------------------------

def test_download_error_exit_1_with_message(fake_ydl, capsys):
    fake_ydl.fail_with = DownloadError("HTTP Error 404")
    code = cli.main(["https://a.example/bad"])
    assert code == 1
    assert "HTTP Error 404" in capsys.readouterr().err


def test_missing_batch_file_exit_2(fake_ydl, capsys):
    code = cli.main(["-a", "/nonexistent/links.txt"])
    assert code == 2
    assert capsys.readouterr().err != ""


def test_unknown_option_is_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--definitely-not-an-option"])
    assert excinfo.value.code == 2


def test_help_renders():
    # Regression: the --template help text must escape %(...)s so that
    # argparse's help interpolation does not blow up on --help.
    text = cli.build_parser().format_help()
    assert "multi-dl" in text
    assert "%(title)s" in text


def test_invalid_quality_is_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--quality", "4k", "https://a.example/1"])
    assert excinfo.value.code == 2
