# multi-dl

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

多平台流媒体视频下载命令行工具，基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp)。主打最简单的用法：**复制视频链接 → 运行 `multi-dl` → 粘贴 → 回车 → 空行开始下载**。同时支持画质预设、批量下载、只下音频、字幕、播放列表和下载档案去重。

[English](#english)

## 快速开始

在任意视频页面复制链接，然后：

```bash
multi-dl
```

程序会提示：

```text
粘贴视频链接后回车，可连续粘贴多条，空行开始下载
Paste a video link and press Enter; paste more links, or an empty line to start downloading.
```

把链接粘贴进去回车，可以继续粘贴更多条；按一次空行（直接回车）就开始下载。就这么简单。

## 环境要求

- Python 3.9 及以上
- [ffmpeg](https://ffmpeg.org/)（**建议安装**）：以下功能需要它
  - 合并分别下载的视频流和音频流（`best` / `1080p` 等预设默认是分开的流，需要合并成一个文件）
  - `--quality audio` 把音频提取/转码为 mp3
  - 部分字幕格式转换
  - 没有 ffmpeg 时，请使用平台提供的合并好的单一文件格式（可用 `-f` 指定），否则可能只下到单独的视频或音频流

## 安装

```bash
pip install git+https://github.com/aoyexiaoqi/multi-dl.git
```

从源码安装：

```bash
git clone https://github.com/aoyexiaoqi/multi-dl.git
cd multi-dl
pip install .
```

## 用法

### 直接传链接

```bash
multi-dl https://example.com/watch?v=xxxx
multi-dl https://a.example/1 https://b.example/2     # 一次多个
```

### 批量文件

把链接存成文本文件（一行一个，空行和 `#` 开头的行会被忽略）：

```bash
multi-dl -a links.txt
multi-dl https://a.example/1 -a links.txt            # 参数链接与文件链接会合并
```

### 画质预设

| 预设 | 说明 | yt-dlp 格式字符串 |
| --- | --- | --- |
| `best`（默认） | 最佳画质 | `bv*+ba/b` |
| `1080p` | 最高 1080p | `bv*[height<=1080]+ba/b[height<=1080]` |
| `720p` | 最高 720p | `bv*[height<=720]+ba/b[height<=720]` |
| `480p` | 最高 480p | `bv*[height<=480]+ba/b[height<=480]` |
| `audio` | 只下音频并转 mp3 192k | `ba/b` + FFmpegExtractAudio 后处理 |

```bash
multi-dl --quality 720p https://example.com/watch?v=xxxx
multi-dl --quality audio https://example.com/watch?v=xxxx
multi-dl -f "bv[height<=720]+ba" https://example.com/watch?v=xxxx   # -f 原生格式串，覆盖预设
```

### 字幕

```bash
multi-dl --subs https://example.com/watch?v=xxxx                    # 中英字幕（含自动字幕）
multi-dl --subs --sub-langs "ja.*,en.*" https://example.com/watch?v=xxxx
```

字幕格式为 `srt/best`，同时下载普通字幕和自动生成字幕。

### 播放列表

默认只下载单个视频（即使链接里带着播放列表参数）。加 `--playlist` 才下整个列表：

```bash
multi-dl --playlist https://example.com/playlist?list=xxxx
multi-dl --playlist --limit 5 https://example.com/playlist?list=xxxx   # 只下前 5 个
```

### 下载档案（去重/续传）

```bash
multi-dl --archive archive.txt -a links.txt
```

档案文件会记录已下载完成的视频 ID，下次再跑同样的链接会自动跳过，适合长期分批下载、断点续跑。

### 输出目录与文件名

```bash
multi-dl -o ~/Videos https://example.com/watch?v=xxxx
multi-dl --template "%(uploader)s/%(title)s.%(ext)s" https://example.com/watch?v=xxxx
```

默认模板是 `%(title)s [%(id)s].%(ext)s`，文件保存在 `-o` 指定目录（默认当前目录）下。

### 查看信息（不下载）

```bash
multi-dl --info https://example.com/watch?v=xxxx
multi-dl --info https://example.com/watch?v=xxxx --json   # 输出原始信息 JSON
```

输出标题、作者、时长（mm:ss）、页面链接和可用格式数量。

### 其他选项

```bash
multi-dl --dry-run https://example.com/watch?v=xxxx   # 试运行，不真正写文件
multi-dl --retries 3 https://example.com/watch?v=xxxx # 覆盖默认重试次数（10）
```

粘贴模式下同样可以使用 `--quality`、`--subs`、`--archive` 等全部选项，它们会作用于粘贴进来的链接。

退出码：`0` 成功；`1` 下载/获取信息失败；`2` 用法错误（参数错误、没有任何链接、批量文件读不到）。

## 注意事项（权利与条款）

- 本工具只是一个下载前端，基于公开的 yt-dlp；**它不破解 DRM，不绕过任何付费、登录或其他访问控制**。
- 请只下载你有权下载的内容，遵守各平台的服务条款和当地版权法律。下载受版权保护的内容仅限个人合理使用等法律允许的情形，请勿传播或商用。
- This tool does not bypass DRM or circumvent any access control. Only download content you have the right to, and respect each platform's terms of service and copyright law.

## English

**multi-dl** is a friendly multi-platform video downloader CLI powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp). The primary flow is copy & paste:

```bash
multi-dl          # then paste one or more links, empty line to start
```

```bash
pip install git+https://github.com/aoyexiaoqi/multi-dl.git
multi-dl https://example.com/watch?v=xxxx                  # direct URL(s)
multi-dl -a links.txt                                      # batch file (one URL per line, # = comment)
multi-dl --quality 720p URL                                # presets: best | 1080p | 720p | 480p | audio
multi-dl --quality audio URL                               # audio only, extracted to mp3 192k
multi-dl -f "bv[height<=720]+ba" URL                        # raw yt-dlp format string (overrides preset)
multi-dl --subs URL                                        # subtitles + auto-captions (zh.*,en.*)
multi-dl --playlist --limit 5 URL                          # playlist (default: single video only)
multi-dl --archive archive.txt -a links.txt                # download archive: dedupe / resume
multi-dl -o ~/Videos --template "%(title)s.%(ext)s" URL    # output dir / filename template
multi-dl --info URL                                        # metadata only; add --json for raw JSON
multi-dl --dry-run URL                                     # simulate, write nothing
```

- Requires Python 3.9+. **ffmpeg is recommended**: merging separate video/audio streams, mp3 extraction and some subtitle conversions need it.
- Exit codes: `0` ok, `1` download/info failure, `2` usage error (bad args, no links, unreadable batch file).
- multi-dl does **not** bypass DRM or circumvent access controls. Only download content you have the right to, respecting platform terms and copyright law.

## License

[MIT](LICENSE) © aoyexiaoqi
