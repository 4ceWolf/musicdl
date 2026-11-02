import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import music_fetch


class MusicFetchTests(unittest.TestCase):
    def test_urls_are_separate_arguments(self):
        url = 'https://example.org/watch?v=music&name=$(touch-owned)'
        arguments = music_fetch.parser().parse_args([url])
        command = music_fetch.build_command(arguments, music_fetch.collect_urls(arguments), ['yt-dlp'])
        self.assertEqual(command[-2:], ['--', url])
        self.assertIn('--ignore-config', command)
        self.assertIn('--no-plugin-dirs', command)

    def test_single_item_default_and_playlist_limit(self):
        arguments = music_fetch.parser().parse_args(['https://example.org/list'])
        command = music_fetch.build_command(arguments, arguments.urls, ['yt-dlp'])
        self.assertEqual(command[command.index('--playlist-items') + 1], '1')
        arguments.playlist = True
        arguments.limit = 8
        command = music_fetch.build_command(arguments, arguments.urls, ['yt-dlp'])
        self.assertEqual(command[command.index('--playlist-items') + 1], '1:8')

    def test_rejects_local_and_invalid_urls(self):
        for url in ['file:///etc/passwd', '--exec=anything', 'https://', 'https://host:invalid/music', 'https://user:password@host/music', 'https://host/a\nb']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                music_fetch.collect_urls(music_fetch.parser().parse_args(['--', url]))

    def test_batch_deduplicates_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / 'urls.txt'
            batch.write_text('# own music\nhttps://example.org/a\n\nhttps://example.org/a\n')
            arguments = music_fetch.parser().parse_args(['--batch', str(batch)])
            self.assertEqual(music_fetch.collect_urls(arguments), ['https://example.org/a'])

    def test_dry_run_never_launches_or_creates_output(self):
        with tempfile.TemporaryDirectory() as directory, patch('music_fetch.subprocess.run') as run, patch('builtins.print'):
            output = Path(directory) / 'not-created'
            self.assertEqual(music_fetch.main(['--dry-run', '--output', str(output), 'https://example.org/audio']), 0)
            run.assert_not_called()
            self.assertFalse(output.exists())

    def test_downloader_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory, patch('music_fetch.downloader', return_value=['yt-dlp']), patch('music_fetch.shutil.which', return_value='/usr/bin/tool'), patch('music_fetch.subprocess.run') as run, patch('builtins.print'):
            run.return_value.returncode = 7
            self.assertEqual(music_fetch.main(['--output', directory, 'https://example.org/audio']), 7)
            self.assertNotIn('shell', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
