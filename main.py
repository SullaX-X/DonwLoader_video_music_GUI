import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import platform

from utils import resource_path, open_folder
from core import DownloadEngine


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Downloader Pro")
        # Увеличили для чекбокса и названия файла
        self.root.geometry("550x610")
        self.root.resizable(False, False)

        try:
            icon_path = resource_path("app.ico")
            if platform.system() == "Windows":
                self.root.iconbitmap(icon_path)
            else:
                img = tk.PhotoImage(file=resource_path("app.png"))
                self.root.iconphoto(True, img)
        except:
            pass

        # Передаем наш UI-обработчик в движок
        self.engine = DownloadEngine(self.progress_callback)

        self.format_var = tk.StringVar(value="audio")
        self.save_dir = tk.StringVar(value=os.path.join(
            os.path.expanduser("~"), "Downloads"))
        self.browser_var = tk.StringVar(value="Без авторизации")
        self.cookie_file_path = None
        self.progress_var = tk.DoubleVar()

        self.playlist_var = tk.BooleanVar(value=False)
        self.last_percent = -1.0  # Для защиты от лагов GUI

        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10), padding=5)

        # 1. Формат
        frame_format = ttk.LabelFrame(
            self.root, text=" 1. Выберите формат ", padding=10)
        frame_format.pack(fill="x", padx=20, pady=5)
        ttk.Radiobutton(frame_format, text="🎵 Аудио (MP3)",
                        variable=self.format_var, value="audio").pack(side="left", padx=20)
        ttk.Radiobutton(frame_format, text="🎬 Видео (MP4)",
                        variable=self.format_var, value="video").pack(side="left", padx=20)

        # 2. Авторизация
        frame_browser = ttk.LabelFrame(
            self.root, text=" 2. Авторизация (Куки) ", padding=10)
        frame_browser.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_browser, text="Для закрытых видео выберите 'Файл cookies.txt'").pack(
            anchor="w", padx=5)
        browsers = ["Без авторизации", "Файл cookies.txt...", "chrome",
                    "edge", "firefox", "opera", "brave", "vivaldi", "safari"]
        self.browser_cb = ttk.Combobox(
            frame_browser, textvariable=self.browser_var, values=browsers, state="readonly", width=30)
        self.browser_cb.pack(anchor="w", padx=5, pady=5)
        self.browser_cb.bind("<<ComboboxSelected>>", self.on_browser_select)

        # 3. Папка (Fix для macOS сохранен)
        frame_dir = ttk.LabelFrame(
            self.root, text=" 3. Куда сохранить? ", padding=10)
        frame_dir.pack(fill="x", padx=20, pady=5)
        btn_browse = ttk.Button(
            frame_dir, text="Обзор...", command=self.choose_directory)
        btn_browse.pack(side="right", padx=(5, 0))
        self.entry_dir = ttk.Entry(
            frame_dir, textvariable=self.save_dir, state="readonly", width=10)
        self.entry_dir.pack(side="left", fill="x", expand=True)

        # 4. Ссылки и Плейлисты
        frame_links = ttk.LabelFrame(
            self.root, text=" 4. Что качать? ", padding=10)
        frame_links.pack(fill="x", padx=20, pady=5)
        ttk.Label(
            frame_links, text="Вставьте ОДНУ ссылку (Ctrl+V / Cmd+V):").pack(anchor="w", padx=5)
        self.url_entry = ttk.Entry(frame_links, width=10)
        self.url_entry.pack(padx=5, pady=5, fill="x", expand=True)

        ttk.Checkbutton(frame_links, text="Скачивать плейлисты целиком",
                        variable=self.playlist_var).pack(anchor="w", padx=5, pady=2)

        self.bind_shortcuts()
        self.create_context_menu()

        ttk.Label(frame_links, text="--- ИЛИ ---", foreground="gray").pack()
        ttk.Button(frame_links, text="📄 Выбрать .txt файл со списком ссылок",
                   command=self.download_from_file).pack(fill="x", padx=5, pady=5)

        # 5. Статус и Прогресс
        self.download_btn = ttk.Button(
            self.root, text="🚀 СКАЧАТЬ", command=self.download_single)
        self.download_btn.pack(pady=10, fill="x", padx=20)

        self.status_label = ttk.Label(
            self.root, text="Готов к работе", foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=2)

        self.file_name_label = ttk.Label(
            self.root, text="", foreground="gray", font=("Arial", 8))
        self.file_name_label.pack()

        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=20, pady=2)
        self.progress_text = ttk.Label(self.root, text="0%", font=("Arial", 9))
        self.progress_text.pack(pady=2)

    # --- Горячие клавиши ---
    def bind_shortcuts(self):
        self.url_entry.bind("<Control-KeyPress>", self.handle_keypress)
        if platform.system() == "Darwin":
            self.url_entry.bind("<Command-KeyPress>", self.handle_keypress)
            self.url_entry.bind("<Command-v>", lambda e: self.paste_text())
            self.url_entry.bind("<Command-a>", lambda e: self.select_all())

    def handle_keypress(self, event):
        keysym = event.keysym.lower() if event.keysym else ""
        char = event.char.lower() if event.char else ""
        if keysym == 'v' or char in ['v', 'м']:
            return self.paste_text()
        if keysym == 'a' or char in ['a', 'ф']:
            return self.select_all()

    def select_all(self, event=None):
        self.url_entry.select_range(0, tk.END)
        self.url_entry.icursor(tk.END)
        return "break"

    def paste_text(self, event=None):
        try:
            text = self.root.clipboard_get()
            try:
                self.url_entry.delete("sel.first", "sel.last")
            except:
                pass
            self.url_entry.insert(tk.INSERT, text)
            return "break"
        except:
            pass

    # --- UI Логика ---
    def on_browser_select(self, event):
        if self.browser_var.get() == "Файл cookies.txt...":
            path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt")])
            if path:
                self.cookie_file_path = path
                self.status_label.config(
                    text=f"Выбран файл: {os.path.basename(path)}", foreground="blue")
            else:
                self.browser_var.set("Без авторизации")

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Вставить", command=self.paste_text)
        self.context_menu.add_command(
            label="Очистить", command=lambda: self.url_entry.delete(0, tk.END))
        self.url_entry.bind(
            "<Button-3>", lambda e: self.context_menu.tk_popup(e.x_root, e.y_root))
        self.url_entry.bind(
            "<Button-2>", lambda e: self.context_menu.tk_popup(e.x_root, e.y_root))

    def choose_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_dir.set(folder)
            self.entry_dir.xview_moveto(1)

    # --- Логика Загрузки ---
    def download_single(self):
        url = self.url_entry.get().strip()
        if url:
            self.start_thread([url])

    def download_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            urls = [l.strip() for l in f if l.strip().startswith('http')]
        if urls:
            self.start_thread(urls)

    def start_thread(self, urls):
        self.status_label.config(
            text="⏳ Подготовка к скачиванию...", foreground="blue")
        self.file_name_label.config(text="")
        self.download_btn.config(state="disabled")
        self.progress_var.set(0)
        self.progress_text.config(text="0%")
        self.last_percent = -1.0

        threading.Thread(target=self.run_engine,
                         args=(urls,), daemon=True).start()

    def run_engine(self, urls):
        success = False
        try:
            is_video = (self.format_var.get() == "video")
            # Передаем параметр плейлиста в core.py
            opts = self.engine.get_ydl_opts(
                is_video, self.save_dir.get(), self.browser_var.get(
                ), self.cookie_file_path, self.playlist_var.get()
            )
            self.engine.run(urls, opts)

            success = True
            self.root.after(0, lambda: self.status_label.config(
                text="✅ Готово!", foreground="green"))
            self.root.after(0, lambda: self.file_name_label.config(
                text="Все файлы успешно сохранены."))
            self.root.after(0, lambda: open_folder(self.save_dir.get()))
        except Exception as e:
            error_str = str(e).lower()
            self.root.after(0, lambda: self.status_label.config(
                text="❌ Ошибка", foreground="red"))

            # Умная обработка популярных ошибок
            if "could not copy chrome cookie database" in error_str or "locked" in error_str:
                msg = "Браузер заблокировал файл с куками!\nИспользуйте расширение 'Get cookies.txt LOCALLY'."
            elif "login required" in error_str or "rate-limit" in error_str:
                msg = "Сайт требует авторизацию. Используйте файл cookies.txt."
            else:
                msg = f"Произошла ошибка:\n{str(e)}"

            self.root.after(0, lambda m=msg: messagebox.showerror("Ошибка", m))
        finally:
            self.root.after(0, lambda s=success: self.finish_download(s))

    def finish_download(self, success):
        self.download_btn.config(state="normal")
        # Очищаем поле только при успехе! Если ошибка - юзер может исправить ссылку.
        if success:
            self.url_entry.delete(0, tk.END)

    def progress_callback(self, status: str, percent: float, filename: str):
        """ Принимает чистые данные из core.py и безопасно обновляет UI """

        # Обновляем имя файла, только если оно изменилось
        if status in ['downloading', 'finished']:
            current_text = self.file_name_label.cget("text")
            if filename not in current_text:
                # Лямбда с захватом переменной f=filename (защита Late Binding)
                self.root.after(0, lambda f=filename: self.file_name_label.config(
                    text=f"Скачивается: {f}"))

        if status == 'downloading':
            # Throttling: обновляем GUI только если разница >= 1%
            if percent - self.last_percent >= 1.0 or percent == 100.0:
                self.last_percent = percent
                self.root.after(0, lambda p=percent: self.update_progress(p))

        elif status == 'finished':
            self.root.after(0, lambda: self.update_progress(100.0))
            self.root.after(0, lambda: self.progress_text.config(
                text="Конвертация/Склейка (подождите)..."))

    def update_progress(self, percent):
        self.progress_var.set(percent)
        self.progress_text.config(text=f"{percent:.1f}%")


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
