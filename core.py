import yt_dlp
import os
from utils import resource_path


class DownloadEngine:
    def __init__(self, progress_callback=None):
        # Callback принимает: status (str), percent (float), filename (str)
        self.progress_callback = progress_callback
        self.ffmpeg_path = resource_path(".")

    def _internal_hook(self, d):
        """ Внутренний обработчик: изолирует yt-dlp от GUI """
        if not self.progress_callback:
            return

        status = d.get('status')
        # Пытаемся достать название скачиваемого файла
        filename = d.get('info_dict', {}).get('title', 'Медиафайл')

        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                percent = (d.get('downloaded_bytes', 0) / total) * 100
                self.progress_callback('downloading', percent, filename)
        elif status == 'finished':
            self.progress_callback('finished', 100.0, filename)

    def get_ydl_opts(self, is_video: bool, save_path: str, browser: str, cookie_file: str, download_playlist: bool) -> dict:
        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if is_video else 'bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': not download_playlist,  # Скачивание плейлистов
            'ignoreerrors': True,                # Пропуск недоступных видео
            'nooverwrites': True,                # Пропуск уже скачанных файлов
            'ffmpeg_location': self.ffmpeg_path,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._internal_hook],
        }

        if browser == "Файл cookies.txt..." and cookie_file:
            opts['cookiefile'] = cookie_file
        elif browser != "Без авторизации":
            opts['cookiesfrombrowser'] = (browser,)

        if not is_video:
            opts['writethumbnail'] = True
            opts['postprocessors'] = [
                # Качество MP3 повышено до 320 kbps
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                    'preferredquality': '320'},
                {'key': 'EmbedThumbnail'}
            ]
        else:
            opts['merge_output_format'] = 'mp4'

        return opts

    def run(self, urls: list, opts: dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
