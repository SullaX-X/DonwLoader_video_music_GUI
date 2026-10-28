import os
import sys
import platform
import subprocess


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def open_folder(path):
    current_os = platform.system()
    try:
        if current_os == "Windows":
            os.startfile(path)
        elif current_os == "Darwin":
            subprocess.run(["open", path], check=True)
        elif current_os == "Linux":
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        print(f"Не удалось открыть папку: {e}")
