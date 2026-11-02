# Music Fetch

A small Python command-line companion for downloading permitted audio with yt-dlp and converting it with FFmpeg. Use it for your own music, public-domain works, or downloads the rights holder permits. It does not bypass DRM or provide paid streaming access.

## Start on your laptop

Python 3.10+, yt-dlp, FFmpeg, and ffprobe are required. Your host already had these installed during testing. Deno or a supported Node version is useful for sites that require JavaScript challenges; availability still depends on the individual site.

```sh
python3 music_fetch.py --check
python3 music_fetch.py 'https://example.org/your-audio-page'
python3 music_fetch.py --format opus --cover 'https://example.org/your-audio-page'
python3 music_fetch.py --playlist --limit 20 --batch urls.txt
python3 music_fetch.py --dry-run 'https://example.org/your-audio-page'
```

Replace the example URL with an actual downloadable media URL. Output defaults to this project's `downloads` folder; change it with `--output /path/to/music`. Point Echo Next's library at that folder to listen.

The default handles one item per URL, including a playlist-only URL. `--playlist` explicitly allows multiple entries (first 50 by default). The limit applies to playlist entries, not a guaranteed number of successful downloads. Batch files contain one URL per line; blank lines and lines beginning with `#` are ignored.

Supported output choices: `best`, `mp3`, `m4a`, `opus`, `flac`, and `wav`. Converting a lossy source to FLAC cannot restore lost quality. Artwork embedding is optional and depends on the output format and source.

Successful downloads are remembered in a separate archive per output format. Existing files are not overwritten; interrupted downloads can resume. Errors are printed and returned as a nonzero exit status. `--dry-run` performs no network requests or file writes. Only run one downloader at a time against a given output directory.

No shell evaluation, browser-cookie import, external plugins, or user yt-dlp configuration is enabled by this wrapper. For tool installation and site-support updates, follow the [official yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#installation). To use a Python virtual environment instead of a system installation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -U 'yt-dlp[default]'
.venv/bin/python music_fetch.py --check
```

Run tests with `python3 -m unittest -v`.
