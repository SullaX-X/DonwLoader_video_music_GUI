import os
import sys
import platform
import subprocess


def resource_path(relative_path):
    """ Получает абсолютный путь к файлу (работает и в .py, и в собранном .exe) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def open_folder(path):
    """ Кроссплатформенное открытие папки """
    current_os = platform.system()
    try:
        if current_os == "Windows":
            os.startfile(path)
        elif current_os == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except Exception:
        pass  # Безопасное игнорирование без вывода в консоль
