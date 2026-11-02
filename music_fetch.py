#!/usr/bin/env python3
import argparse
import importlib.util
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent


def parser():
    arguments = argparse.ArgumentParser(description='Music Fetch — save audio you own or have permission to download.')
    arguments.add_argument('urls', nargs='*', help='HTTP(S) media or supported page URLs; quote each URL')
    arguments.add_argument('--batch', type=Path, help='Text file with one URL per line; # starts a comment line')
    arguments.add_argument('--output', type=Path, default=ROOT / 'downloads')
    arguments.add_argument('--format', choices=['best', 'mp3', 'm4a', 'opus', 'flac', 'wav'], default='mp3')
    arguments.add_argument('--playlist', action='store_true', help='Allow multiple playlist entries')
    arguments.add_argument('--limit', type=int, default=50, help='Maximum playlist entries to consider (default: 50)')
    arguments.add_argument('--cover', action='store_true', help='Embed cover art when the source and format support it')
    arguments.add_argument('--dry-run', action='store_true', help='Print the command without network access or creating files')
    arguments.add_argument('--check', action='store_true', help='Check installed tools without downloading')
    return arguments


def downloader():
    executable = shutil.which('yt-dlp')
    if executable:
        return [executable]
    if importlib.util.find_spec('yt_dlp'):
        return [sys.executable, '-m', 'yt_dlp']
    return None


def collect_urls(arguments):
    urls = list(arguments.urls)
    if arguments.batch:
        if arguments.batch.stat().st_size > 1_000_000:
            raise ValueError('Batch file must be smaller than 1 MB.')
        urls.extend(line.strip() for line in arguments.batch.read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.lstrip().startswith('#'))
    if not urls:
        raise ValueError('Provide a URL or --batch file. Use --help for examples.')
    if len(urls) > 1000:
        raise ValueError('Use at most 1,000 URLs per run.')
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or any(character.isspace() or ord(character) < 32 for character in url):
            raise ValueError(f'Expected an HTTP(S) URL: {url!r}')
        if parsed.username is not None or parsed.password is not None:
            raise ValueError('Credentials in URLs are not supported.')
        _ = parsed.port
    return list(dict.fromkeys(urls))


def build_command(arguments, urls, executable):
    output = arguments.output.expanduser().resolve()
    command = [*executable, '--ignore-config', '--no-plugin-dirs', '--newline', '--continue', '--no-overwrites',
               '--retries', '3', '--fragment-retries', '3', '--socket-timeout', '30',
               '--format', 'bestaudio/best', '--extract-audio', '--audio-format', arguments.format,
               '--audio-quality', '0', '--embed-metadata', '--windows-filenames', '--trim-filenames', '180',
               '--paths', str(output), '--output', '%(title).140B [%(id)s].%(ext)s',
               '--download-archive', str(output / f'.downloaded-{arguments.format}.txt'),
               '--match-filters', '!is_live', '--playlist-items', f'1:{arguments.limit}' if arguments.playlist else '1',
               '--yes-playlist' if arguments.playlist else '--no-playlist']
    if arguments.cover:
        command += ['--embed-thumbnail']
    if not shutil.which('deno') and shutil.which('node'):
        command += ['--js-runtimes', f'node:{shutil.which("node")}']
    return command + ['--', *urls]


def main(argv=None):
    arguments_parser = parser()
    arguments = arguments_parser.parse_args(argv)
    executable = downloader()
    missing = [tool for tool in ('ffmpeg', 'ffprobe') if not shutil.which(tool)]
    if not executable:
        missing.insert(0, 'yt-dlp')
    if arguments.check:
        for tool in ('yt-dlp', 'ffmpeg', 'ffprobe', 'deno', 'node'):
            available = shutil.which(tool)
            if tool == 'yt-dlp' and executable:
                available = shlex.join(executable)
            print(f'{tool}: {available or "not installed"}')
        if not shutil.which('deno') and not shutil.which('node'):
            print('Some sites also require a supported JavaScript runtime. See README.md.')
        return 1 if missing else 0
    if not 1 <= arguments.limit <= 10000:
        arguments_parser.error('--limit must be between 1 and 10000.')
    try:
        urls = collect_urls(arguments)
    except (OSError, UnicodeError, ValueError) as error:
        arguments_parser.error(str(error))
    command = build_command(arguments, urls, executable or ['yt-dlp'])
    if arguments.dry_run:
        print(shlex.join(command))
        return 0
    if missing:
        print('Missing: ' + ', '.join(missing) + '. See README.md for setup.', file=sys.stderr)
        return 2
    try:
        arguments.output.expanduser().resolve().mkdir(parents=True, exist_ok=True)
        print(f'Saving audio to {arguments.output.expanduser().resolve()}', flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode:
            print('Download or conversion failed. Details are above; unfinished downloads can be resumed by repeating the command.', file=sys.stderr)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    except KeyboardInterrupt:
        print('\nStopped. Repeat the command to resume unfinished downloads.', file=sys.stderr)
        return 130
    except OSError as error:
        print(f'Could not run Music Fetch: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
