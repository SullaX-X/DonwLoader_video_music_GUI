import yt_dlp
from yt_dlp.utils import DownloadError
import os
import sys
import shutil
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_ffmpeg_path():
    """Ищет FFmpeg в папке со скриптом, в системе или берет из imageio_ffmpeg."""
    local_dir = resource_path(".")
    exe_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

    # 1. Проверяем папку со скриптом
    if os.path.exists(os.path.join(local_dir, exe_name)):
        return local_dir

    # 2. Проверяем системный PATH
    if shutil.which("ffmpeg"):
        return None

    # 3. Берем из пакета imageio-ffmpeg (если установлен через pip)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    return "NOT_FOUND"


def open_folder(path):
    current_os = platform.system()
    try:
        if current_os == "Windows":
            os.startfile(path)
        elif current_os == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except Exception:
        pass


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Downloader Pro v2.0")
        self.root.geometry("600x680")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap(resource_path("app.ico"))
        except Exception:
            pass

        # Переменные состояния
        self.format_var = tk.StringVar(value="video")
        self.quality_var = tk.StringVar(value="Максимальное (4K/2K/1080p)")
        self.save_dir = tk.StringVar(value=os.path.join(
            os.path.expanduser("~"), "Downloads"))
        self.browser_var = tk.StringVar(value="Без авторизации")
        self.cookie_file_path = None

        self.playlist_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0.0)

        self.cancel_requested = False
        self.last_percent = -1.0
        self.ffmpeg_status = get_ffmpeg_path()

        self.setup_styles()
        self.create_widgets()

        if self.ffmpeg_status == "NOT_FOUND":
            messagebox.showwarning(
                "FFmpeg не найден!",
                "Внимание! FFmpeg не найден ни в папке с программой, ни в системе.\n\n"
                "Без него невозможно:\n"
                "1. Скачивать видео в 1080p / 4K со звуком.\n"
                "2. Конвертировать аудио в MP3.\n\n"
                "Положите ffmpeg.exe в папку со скриптом!"
            )

    def setup_styles(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6)
        style.configure("TLabelframe.Label", font=(
            "Segoe UI", 10, "bold"), foreground="#333333")
        style.configure("Action.TButton", font=(
            "Segoe UI", 10, "bold"), foreground="white", background="#0078D7")
        style.map("Action.TButton", background=[
                  ("active", "#005A9E"), ("disabled", "#A0A0A0")])
        style.configure("Cancel.TButton", font=(
            "Segoe UI", 10, "bold"), foreground="white", background="#D9534F")
        style.map("Cancel.TButton", background=[
                  ("active", "#C9302C"), ("disabled", "#A0A0A0")])

    def create_widgets(self):
        # 1. Формат и Качество
        frame_format = ttk.LabelFrame(
            self.root, text=" 1. Формат и Качество ", padding=10)
        frame_format.pack(fill="x", padx=15, pady=5)

        rb_video = ttk.Radiobutton(frame_format, text="🎬 Видео (MP4)",
                                   variable=self.format_var, value="video", command=self.toggle_quality_state)
        rb_video.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        rb_audio = ttk.Radiobutton(frame_format, text="🎵 Только аудио (MP3 320kbps)",
                                   variable=self.format_var, value="audio", command=self.toggle_quality_state)
        rb_audio.grid(row=0, column=1, padx=10, pady=2, sticky="w")

        ttk.Label(frame_format, text="Качество видео:").grid(
            row=1, column=0, padx=10, pady=8, sticky="w")
        qualities = ["Максимальное (4K/2K/1080p)", "1080p (Full HD)",
                     "720p (HD)", "480p (Экономия трафика)"]
        self.quality_cb = ttk.Combobox(
            frame_format, textvariable=self.quality_var, values=qualities, state="readonly", width=28)
        self.quality_cb.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        # 2. Авторизация и обход блокировок
        frame_browser = ttk.LabelFrame(
            self.root, text=" 2. Авторизация (Для 18+, закрытых видео и обхода ботов) ", padding=10)
        frame_browser.pack(fill="x", padx=15, pady=5)

        ttk.Label(frame_browser, text="Источник куков (Закройте браузер перед скачиванием, либо используйте Firefox/cookies.txt):").pack(anchor="w")
        browsers = ["Без авторизации", "Файл cookies.txt...", "firefox",
                    "chrome", "edge", "opera", "brave", "vivaldi", "safari"]
        self.browser_cb = ttk.Combobox(
            frame_browser, textvariable=self.browser_var, values=browsers, state="readonly", width=35)
        self.browser_cb.pack(anchor="w", pady=5)
        self.browser_cb.bind("<<ComboboxSelected>>", self.on_browser_select)

        # 3. Папка сохранения
        frame_dir = ttk.LabelFrame(
            self.root, text=" 3. Папка сохранения ", padding=10)
        frame_dir.pack(fill="x", padx=15, pady=5)

        self.entry_dir = ttk.Entry(
            frame_dir, textvariable=self.save_dir, state="readonly")
        self.entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(frame_dir, text="📁 Открыть", width=10, command=lambda: open_folder(
            self.save_dir.get())).pack(side="right")
        ttk.Button(frame_dir, text="Обзор...", width=10,
                   command=self.choose_directory).pack(side="right", padx=5)

        # 4. Ссылки и опции
        frame_links = ttk.LabelFrame(
            self.root, text=" 4. Ссылка на контент ", padding=10)
        frame_links.pack(fill="x", padx=15, pady=5)

        url_box = ttk.Frame(frame_links)
        url_box.pack(fill="x", pady=2)

        self.url_entry = ttk.Entry(url_box, font=("Segoe UI", 10))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(url_box, text="📋 Вставить", width=12,
                   command=self.paste_text).pack(side="right")
        ttk.Button(url_box, text="✖", width=3, command=lambda: self.url_entry.delete(
            0, tk.END)).pack(side="right", padx=2)

        opts_box = ttk.Frame(frame_links)
        opts_box.pack(fill="x", pady=5)
        ttk.Checkbutton(opts_box, text="Скачать весь плейлист / канал",
                        variable=self.playlist_var).pack(side="left", padx=(0, 15))
        ttk.Checkbutton(opts_box, text="Вшить субтитры (если есть)",
                        variable=self.subtitles_var).pack(side="left")

        ttk.Separator(frame_links, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(frame_links, text="📄 Загрузить список ссылок из .TXT файла",
                   command=self.download_from_file).pack(fill="x")

        self.bind_shortcuts()
        self.create_context_menu()

        # 5. Кнопки управления
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=15, pady=10)

        self.download_btn = ttk.Button(
            btn_frame, text="🚀 СКАЧАТЬ", style="Action.TButton", command=self.download_single)
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.cancel_btn = ttk.Button(
            btn_frame, text="🛑 ОТМЕНА", style="Cancel.TButton", state="disabled", command=self.cancel_download)
        self.cancel_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # 6. Статус и Прогресс-бар
        frame_status = ttk.LabelFrame(
            self.root, text=" Статус выполнения ", padding=10)
        frame_status.pack(fill="both", expand=True, padx=15, pady=5)

        self.status_label = ttk.Label(
            frame_status, text="Готов к работе", foreground="green", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(anchor="w")

        self.file_name_label = ttk.Label(
            frame_status, text="Ожидание ссылки...", foreground="#555555", wraplength=540)
        self.file_name_label.pack(anchor="w", pady=3)

        self.progress_bar = ttk.Progressbar(
            frame_status, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)

        self.stats_label = ttk.Label(
            frame_status, text="0.0% | Скорость: 0 MB/s | Осталось: --:--", font=("Consolas", 9))
        self.stats_label.pack(anchor="center")

    def toggle_quality_state(self):
        if self.format_var.get() == "audio":
            self.quality_cb.config(state="disabled")
        else:
            self.quality_cb.config(state="readonly")

    # --- Горячие клавиши и буфер ---
    def bind_shortcuts(self):
        self.url_entry.bind("<Control-KeyPress>", self.handle_keypress)
        if platform.system() == "Darwin":
            self.url_entry.bind("<Command-KeyPress>", self.handle_keypress)

    def handle_keypress(self, event):
        char = event.char.lower() if event.char else ""
        keysym = event.keysym.lower() if event.keysym else ""
        if keysym == 'v' or char in ['v', 'м']:
            return self.paste_text()
        if keysym == 'a' or char in ['a', 'ф']:
            self.url_entry.select_range(0, tk.END)
            return "break"

    def paste_text(self, event=None):
        try:
            text = self.root.clipboard_get().strip()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, text)
            return "break"
        except Exception:
            pass

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Вставить", command=self.paste_text)
        self.context_menu.add_command(
            label="Очистить", command=lambda: self.url_entry.delete(0, tk.END))
        self.url_entry.bind(
            "<Button-3>", lambda e: self.context_menu.tk_popup(e.x_root, e.y_root))

    def on_browser_select(self, event):
        if self.browser_var.get() == "Файл cookies.txt...":
            path = filedialog.askopenfilename(
                title="Выберите файл cookies.txt", filetypes=[("Text Files", "*.txt")])
            if path:
                self.cookie_file_path = path
                self.status_label.config(
                    text=f"Выбран куки: {os.path.basename(path)}", foreground="blue")
            else:
                self.browser_var.set("Без авторизации")

    def choose_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_dir.set(folder)

    # --- Управление загрузкой ---
    def cancel_download(self):
        self.cancel_requested = True
        self.status_label.config(
            text="🛑 Отмена загрузки...", foreground="orange")
        self.cancel_btn.config(state="disabled")

    def download_single(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(
                "Внимание", "Пожалуйста, вставьте ссылку на видео!")
            return
        self.start_download_thread([url])

    def download_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            urls = [l.strip() for l in f if l.strip().startswith('http')]
        if urls:
            self.start_download_thread(urls)
        else:
            messagebox.showwarning(
                "Пусто", "В файле не найдено ссылок, начинающихся с http/https.")

    def start_download_thread(self, urls):
        self.cancel_requested = False
        self.status_label.config(
            text="⏳ Получение информации о видео...", foreground="blue")
        self.file_name_label.config(text="Подключение к серверам YouTube...")
        self.download_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_var.set(0)
        self.stats_label.config(
            text="0.0% | Скорость: 0 MB/s | Осталось: --:--")
        self.last_percent = -1.0

        threading.Thread(target=self.process_download,
                         args=(urls,), daemon=True).start()

    def build_format_string(self):
        # Если FFmpeg НЕ найден, качаем только уже склеенные форматы (без знака "+")
        if self.ffmpeg_status == "NOT_FOUND":
            if self.format_var.get() == "audio":
                return "ba/b"
            # Максимальное качество, не требующее склейки (обычно 720p)
            return "b[ext=mp4]/b"

        # Если FFmpeg ЕСТЬ — качаем максимальное качество со склейкой:
        if self.format_var.get() == "audio":
            return "ba/b"

        q = self.quality_var.get()
        if "1080p" in q:
            return "bv*[height<=1080]+ba/b[height<=1080] / bv*+ba/b"
        elif "720p" in q:
            return "bv*[height<=720]+ba/b[height<=720] / bv*+ba/b"
        elif "480p" in q:
            return "bv*[height<=480]+ba/b[height<=480] / bv*+ba/b"
        else:
            return "bv*+ba/b"

    def process_download(self, urls):
        save_path = self.save_dir.get()
        is_video = (self.format_var.get() == "video")
        selected_browser = self.browser_var.get()

        ydl_opts = {
            'format': self.build_format_string(),
            'outtmpl': os.path.join(save_path, '%(title).150B [%(id)s].%(ext)s'),
            'windowsfilenames': True,
            'noplaylist': not self.playlist_var.get(),
            'ignoreerrors': False,
            'nooverwrites': True,
            'concurrent_fragment_downloads': 4,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.yt_dlp_monitor],
            # МЫ УБРАЛИ extractor_args и live_from_start, так как они ломали загрузку с куками!
        }

        if self.ffmpeg_status and self.ffmpeg_status != "NOT_FOUND":
            ydl_opts['ffmpeg_location'] = self.ffmpeg_status

        if selected_browser == "Файл cookies.txt..." and self.cookie_file_path:
            ydl_opts['cookiefile'] = self.cookie_file_path
        elif selected_browser != "Без авторизации":
            ydl_opts['cookiesfrombrowser'] = (selected_browser,)

        postprocessors = []
        if self.ffmpeg_status != "NOT_FOUND":
            if not is_video:
                ydl_opts['writethumbnail'] = True
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320'
                })
                postprocessors.append({'key': 'EmbedThumbnail'})
                postprocessors.append({'key': 'FFmpegMetadata'})
            else:
                ydl_opts['merge_output_format'] = 'mp4'
                if self.subtitles_var.get():
                    ydl_opts['writesubtitles'] = True
                    ydl_opts['subtitleslangs'] = ['ru', 'en']
                    postprocessors.append({'key': 'FFmpegEmbedSubtitle'})

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        success_count = 0
        errors = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                if self.cancel_requested:
                    break
                try:
                    ydl.download([url])
                    success_count += 1
                except DownloadError as e:
                    if "RequestedByUser" in str(e):
                        break
                    errors.append(f"{url}:\n{str(e)}")
                except Exception as e:
                    if "RequestedByUser" in str(e):
                        break
                    errors.append(f"{url}:\n{str(e)}")

        self.root.after(0, lambda: self.finish_download(
            success_count, errors, save_path))

    def finish_download(self, success_count, errors, save_path):
        self.download_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

        if self.cancel_requested:
            self.status_label.config(
                text="🛑 Загрузка отменена пользователем", foreground="orange")
            self.file_name_label.config(
                text="Временные файлы сохранены и могут быть докачаны позже.")
            return

        if errors and success_count == 0:
            self.status_label.config(
                text="❌ Ошибка скачивания!", foreground="red")
            error_msg = "\n\n".join(errors[:3])
            if "Permission denied" in error_msg or "Locked" in error_msg:
                error_msg += "\n\n💡 СОВЕТ: Закройте браузер перед скачиванием или выберите файл cookies.txt!"
            messagebox.showerror("Ошибка скачивания",
                                 f"Не удалось скачать контент:\n\n{error_msg}")
        elif errors and success_count > 0:
            self.status_label.config(
                text=f"⚠️ Скачано: {success_count}, Ошибок: {len(errors)}", foreground="orange")
            open_folder(save_path)
            messagebox.showwarning(
                "Завершено с ошибками", f"Успешно: {success_count}\nОшибок: {len(errors)}\n\nПервая ошибка:\n{errors[0]}")
        else:
            self.status_label.config(
                text="✅ Успешно завершено!", foreground="green")
            self.file_name_label.config(
                text=f"Все файлы ({success_count} шт.) сохранены в папку.")
            self.url_entry.delete(0, tk.END)
            open_folder(save_path)

    def yt_dlp_monitor(self, d):
        if self.cancel_requested:
            raise Exception("RequestedByUser")

        status = d.get('status')
        if status == 'downloading':
            info = d.get('info_dict', {})
            title = info.get('title', 'Медиафайл')

            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed') or 0
            eta = d.get('eta')

            percent = (downloaded / total * 100) if total > 0 else 0
            speed_mb = speed / (1024 * 1024)

            if eta is not None:
                mins, secs = divmod(int(eta), 60)
                eta_str = f"{mins:02d}:{secs:02d}"
            else:
                eta_str = "--:--"

            if percent - self.last_percent >= 0.5 or percent == 100:
                self.last_percent = percent
                stats_text = f"{percent:.1f}% | Скорость: {speed_mb:.2f} MB/s | Осталось: {eta_str}"
                self.root.after(0, lambda t=title, p=percent,
                                s=stats_text: self.update_ui_progress(t, p, s))

        elif status == 'finished':
            self.root.after(0, lambda: self.progress_var.set(100.0))
            self.root.after(0, lambda: self.status_label.config(
                text="⚙️ Обработка FFmpeg (Склейка видео и звука / Конвертация)...", foreground="purple"))

    def update_ui_progress(self, title, percent, stats_text):
        self.status_label.config(
            text="⬇️ Идет загрузка...", foreground="#0078D7")
        self.file_name_label.config(text=f"Файл: {title}")
        self.progress_var.set(percent)
        self.stats_label.config(text=stats_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
