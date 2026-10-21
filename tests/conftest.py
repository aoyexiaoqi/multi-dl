import pytest

import multi_dl.cli as cli

FAKE_INFO = {
    "title": "示例视频 Example Video",
    "uploader": "示例作者",
    "duration": 754,
    "webpage_url": "https://example.com/watch?v=abc123",
    "formats": [{"format_id": "1"}, {"format_id": "2"}, {"format_id": "3"}],
}


class FakeYDL:
    """Offline stand-in for yt_dlp.YoutubeDL; records everything."""

    instances = []
    fail_with = None  # set to an exception instance to simulate failures

    def __init__(self, opts):
        self.opts = opts
        self.downloaded = None
        self.info_url = None
        FakeYDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def download(self, urls):
        if FakeYDL.fail_with is not None:
            raise FakeYDL.fail_with
        self.downloaded = list(urls)
        return 0

    def extract_info(self, url, download=False):
        if FakeYDL.fail_with is not None:
            raise FakeYDL.fail_with
        self.info_url = url
        return dict(FAKE_INFO)


@pytest.fixture
def fake_ydl(monkeypatch):
    FakeYDL.instances = []
    FakeYDL.fail_with = None
    monkeypatch.setattr(cli.yt_dlp, "YoutubeDL", FakeYDL)
    return FakeYDL


def parse(argv):
    return cli.build_parser().parse_args(argv)
