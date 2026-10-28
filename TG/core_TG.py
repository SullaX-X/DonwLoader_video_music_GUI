import yt_dlp
import os
from utils import resource_path


class DownloadEngine:
    def __init__(self, progress_hook):
        self.progress_hook = progress_hook

    def get_ydl_opts(self, is_video, save_path, browser, cookie_path):
        ffmpeg_folder = resource_path(".")

        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if is_video else 'bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_folder,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
        }

        # Авторизация
        if browser == "Файл cookies.txt..." and cookie_path:
            opts['cookiefile'] = cookie_path
        elif browser not in ["Без авторизации", "Файл cookies.txt..."]:
            opts['cookiesfrombrowser'] = (browser,)

        if not is_video:
            opts['writethumbnail'] = True
            opts['postprocessors'] = [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                    'preferredquality': '192'},
                {'key': 'EmbedThumbnail'}
            ]
        else:
            opts['merge_output_format'] = 'mp4'

        return opts
    
    def download_for_bot(self, url, is_video, save_path):
        """ Специальный метод для бота: скачивает и возвращает путь к файлу """
        # Настройки те же, что и раньше, но без привязки к GUI-прогрессбару
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if is_video else 'bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ffmpeg_location': resource_path("."),
            'quiet': True,
        }

        if not is_video:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Возвращаем путь к скачанному файлу
            return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

    def run(self, urls, opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
