import subprocess
import os


def _safe_popen(command, shell=False):
    if os.name != "nt":
        print("Local Windows automation is unavailable on this platform.")
        return False
    try:
        subprocess.Popen(command, shell=shell)
        return True
    except Exception as error:
        print(f"Automation error: {error}")
        return False


def open_file():
    return _safe_popen("notepad.exe")


def open_notepad():
    return _safe_popen("notepad.exe")


def open_calculator():
    return _safe_popen("calc.exe")


def open_chrome():
    return _safe_popen("start chrome", shell=True)


def play_music():
    return _safe_popen("start chrome https://www.youtube.com/results?search_query=music", shell=True)