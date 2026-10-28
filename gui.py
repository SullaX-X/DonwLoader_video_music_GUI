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
        self.root.geometry("550x580")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap(resource_path("app.ico"))
        except:
            pass

        self.engine = DownloadEngine(self.yt_dlp_monitor)

        self.format_var = tk.StringVar(value="audio")
        self.save_dir = tk.StringVar(value=os.path.join(
            os.path.expanduser("~"), "Downloads"))
        self.browser_var = tk.StringVar(value="Без авторизации")
        self.cookie_file_path = None
        self.progress_var = tk.DoubleVar()

        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10), padding=5)

        # 1. Блок формата (как в оригинале)
        frame_format = ttk.LabelFrame(
            self.root, text=" 1. Выберите формат ", padding=10)
        frame_format.pack(fill="x", padx=20, pady=5)
        ttk.Radiobutton(frame_format, text="🎵 Аудио (MP3)",
                        variable=self.format_var, value="audio").pack(side="left", padx=20)
        ttk.Radiobutton(frame_format, text="🎬 Видео (MP4)",
                        variable=self.format_var, value="video").pack(side="left", padx=20)

        # 2. Блок авторизации
        frame_browser = ttk.LabelFrame(
            self.root, text=" 2. Авторизация (Куки) ", padding=10)
        frame_browser.pack(fill="x", padx=20, pady=5)
        ttk.Label(frame_browser, text="Для скачивания при открытом браузере выберите 'Файл cookies.txt'").pack(
            anchor="w", padx=5)
        browsers = ["Без авторизации", "Файл cookies.txt...", "chrome",
                    "edge", "firefox", "opera", "brave", "vivaldi", "safari"]
        self.browser_cb = ttk.Combobox(
            frame_browser, textvariable=self.browser_var, values=browsers, state="readonly", width=30)
        self.browser_cb.pack(anchor="w", padx=5, pady=5)
        self.browser_cb.bind("<<ComboboxSelected>>", self.on_browser_select)

        # 3. Блок папки
        frame_dir = ttk.LabelFrame(
            self.root, text=" 3. Куда сохранить? ", padding=10)
        frame_dir.pack(fill="x", padx=20, pady=5)
        ttk.Entry(frame_dir, textvariable=self.save_dir,
                  state="readonly", width=50).pack(side="left", padx=5)
        ttk.Button(frame_dir, text="Обзор...",
                   command=self.choose_directory).pack(side="left", padx=5)

        # 4. Блок ссылок + контекстное меню
        frame_links = ttk.LabelFrame(
            self.root, text=" 4. Что качать? ", padding=10)
        frame_links.pack(fill="x", padx=20, pady=5)
        ttk.Label(
            frame_links, text="Вставьте ОДНУ ссылку (Ctrl+V или Правая кнопка мыши):").pack(anchor="w", padx=5)
        self.url_entry = ttk.Entry(frame_links, width=65)
        self.url_entry.pack(padx=5, pady=5)

        # Возвращаем Shortcuts и Context Menu
        self.bind_shortcuts()
        self.create_context_menu()

        ttk.Label(frame_links, text="--- ИЛИ ---", foreground="gray").pack()
        ttk.Button(frame_links, text="📄 Выбрать .txt файл со списком ссылок",
                   command=self.download_from_file).pack(fill="x", padx=5, pady=5)

        # 5. Кнопка и прогресс
        self.download_btn = ttk.Button(
            self.root, text="🚀 СКАЧАТЬ", command=self.download_single)
        self.download_btn.pack(pady=10, fill="x", padx=20)

        self.status_label = ttk.Label(
            self.root, text="Готов к работе", foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=2)

        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=20, pady=2)
        self.progress_text = ttk.Label(self.root, text="0%", font=("Arial", 9))
        self.progress_text.pack(pady=2)

        # ПОДПИСЬ
        ttk.Label(self.root, text="С любовью от SullaX_X и ParsifalX_X",
                  foreground="gray", font=("Arial", 9, "italic")).pack(side="bottom", pady=5)

    # --- Копипаст твоей оригинальной логики (shortcuts, paste, etc.) ---
    def bind_shortcuts(self):
        self.url_entry.bind("<Control-KeyPress>", self.handle_keypress)
        if platform.system() == "Darwin":
            self.url_entry.bind("<Command-KeyPress>", self.handle_keypress)

    def handle_keypress(self, event):
        keysym = event.keysym.lower()
        char = event.char.lower()
        if keysym == 'v' or char in ['v', 'м']:
            return self.paste_text()
        if keysym == 'a' or char in ['a', 'ф']:
            return self.select_all()

    def select_all(self, event=None):
        self.url_entry.select_range(0, tk.END)
        return "break"

    def paste_text(self, event=None):
        try:
            text = self.root.clipboard_get()
            self.url_entry.insert(tk.INSERT, text)
            return "break"
        except:
            pass

    def on_browser_select(self, event):
        if self.browser_var.get() == "Файл cookies.txt...":
            path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt")])
            if path:
                self.cookie_file_path = path
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

    def choose_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_dir.set(folder)

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
            text="⏳ Идет скачивание...", foreground="blue")
        self.download_btn.config(state="disabled")
        threading.Thread(target=self.run_engine,
                         args=(urls,), daemon=True).start()

    def run_engine(self, urls):
        try:
            opts = self.engine.get_ydl_opts(self.format_var.get(
            ) == "video", self.save_dir.get(), self.browser_var.get(), self.cookie_file_path)
            self.engine.run(urls, opts)
            self.root.after(0, lambda: self.status_label.config(
                text="✅ Готово!", foreground="green"))
            open_folder(self.save_dir.get())
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
        finally:
            self.root.after(
                0, lambda: self.download_btn.config(state="normal"))

    def yt_dlp_monitor(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                percent = (d.get('downloaded_bytes', 0) / total) * 100
                self.root.after(0, lambda: self.update_progress(percent))

    def update_progress(self, p):
        self.progress_var.set(p)
        self.progress_text.config(text=f"{p:.1f}%")
