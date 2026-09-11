import os
import sys
import subprocess
import platform
import zipfile
import tarfile
import shutil

def bootstrap_venv():
    """Создает виртуальное окружение и устанавливает зависимости, если необходимо."""
    venv_dir = os.path.abspath('.venv')
    if os.name == 'nt':
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python')

    current_python = os.path.abspath(sys.executable)
    if current_python != venv_python:
        if not os.path.exists(venv_python):
            print("Настройка среды: Создание виртуального окружения (.venv)...")
            import venv
            try:
                venv.create(venv_dir, with_pip=True)
            except Exception as e:
                print(f"Ошибка при создании виртуального окружения: {e}")
                sys.exit(1)

            print("Настройка среды: Установка зависимостей (yt-dlp, tqdm)...")
            try:
                subprocess.check_call([venv_python, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
            except Exception as e:
                print(f"Ошибка при установке зависимостей: {e}")
                sys.exit(1)

        # Перезапуск скрипта в виртуальном окружении
        sys.exit(subprocess.call([venv_python] + sys.argv))

# 1. Автоматический bootstrap зависимостей
bootstrap_venv()

# Безопасный импорт сторонних библиотек после проверки окружения
try:
    import argparse
    import urllib.request
    from tqdm import tqdm
    import yt_dlp
except ImportError:
    print("Критическая ошибка: Зависимости не установлены должным образом. Удалите папку .venv и попробуйте снова.")
    sys.exit(1)


def get_ffmpeg_url():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == 'windows':
        return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == 'linux':
        if 'aarch64' in machine or 'arm64' in machine:
            return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
        else:
            return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif system == 'darwin':
        return "https://evermeet.cx/ffmpeg/getrelease/zip"
    return None

def download_with_progress(url, dest_path):
    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)

    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc="Скачивание FFmpeg") as t:
        urllib.request.urlretrieve(url, filename=dest_path, reporthook=t.update_to)

def bootstrap_ffmpeg():
    """Автоматическая доставка FFmpeg."""
    bin_dir = os.path.abspath('bin')
    os.makedirs(bin_dir, exist_ok=True)

    ffmpeg_ext = '.exe' if os.name == 'nt' else ''
    ffmpeg_path = os.path.join(bin_dir, f'ffmpeg{ffmpeg_ext}')

    if os.path.exists(ffmpeg_path) and os.path.isfile(ffmpeg_path):
        return bin_dir

    print(f"FFmpeg не найден. Начинается автоматическое скачивание и распаковка в {bin_dir}...")
    url = get_ffmpeg_url()

    if not url:
        print("Внимание: Автоматическая загрузка FFmpeg не поддерживается для вашей операционной системы.")
        print("Пожалуйста, установите FFmpeg вручную или поместите бинарные файлы в папку bin.")
        return None

    archive_path = os.path.join(bin_dir, "ffmpeg_archive")
    try:
        download_with_progress(url, archive_path)
    except Exception as e:
        print(f"Ошибка при скачивании FFmpeg: {e}")
        return None

    print("\nРаспаковка FFmpeg...")
    try:
        if url.endswith('.zip') or 'zip' in url:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.is_dir(): continue
                    filename = os.path.basename(file_info.filename)
                    if filename in ('ffmpeg', 'ffmpeg.exe', 'ffprobe', 'ffprobe.exe'):
                        source = zip_ref.open(file_info.filename)
                        target_path = os.path.join(bin_dir, filename)
                        target = open(target_path, "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)
                        if os.name != 'nt':
                            os.chmod(target_path, 0o755)
        elif url.endswith('.tar.xz'):
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                for member in tar_ref.getmembers():
                    if member.isdir(): continue
                    filename = os.path.basename(member.name)
                    if filename in ('ffmpeg', 'ffprobe'):
                        source = tar_ref.extractfile(member)
                        target_path = os.path.join(bin_dir, filename)
                        target = open(target_path, "wb")
                        if source:
                            with source, target:
                                shutil.copyfileobj(source, target)
                        if os.name != 'nt':
                            os.chmod(target_path, 0o755)

    except Exception as e:
        print(f"Ошибка при распаковке FFmpeg: {e}")
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)

    if os.path.exists(ffmpeg_path):
        print("FFmpeg успешно установлен!\n")
        return bin_dir
    else:
        print("Не удалось найти бинарный файл ffmpeg в скачанном архиве.")
        return None


class TqdmProgressHook:
    def __init__(self):
        self.pbar = None

    def __call__(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)

            if self.pbar is None and total:
                self.pbar = tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024, desc='Скачивание', ncols=80, leave=True)

            if self.pbar:
                self.pbar.update(downloaded - self.pbar.n)

        elif d['status'] == 'finished':
            if self.pbar:
                if self.pbar.total:
                    self.pbar.update(self.pbar.total - self.pbar.n)
                self.pbar.close()
                self.pbar = None
            print("\nЗагрузка завершена! Сохранение файла (если требуется склейка, это займет немного времени)...")

class MyLogger(object):
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

def download_instagram_video(url, output_path=None):
    ffmpeg_location = bootstrap_ffmpeg()

    # Настройки yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # Наивысшее качество
        'merge_output_format': 'mp4', # Контейнер
        'quiet': True,
        'no_warnings': True,
        'logger': MyLogger(),
        'progress_hooks': [TqdmProgressHook()],
        'outtmpl': '%(title)s_%(id)s.%(ext)s',
    }

    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    if output_path:
        ydl_opts['outtmpl'] = os.path.join(output_path, '%(title)s_%(id)s.%(ext)s')

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Извлечение информации по ссылке: {url}")
            ydl.download([url])
            print("Готово! Контент успешно сохранен.")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'Private video' in error_msg or 'login' in error_msg.lower() or 'empty media response' in error_msg.lower() or 'cookies' in error_msg.lower():
            print("Ошибка: Видео приватное, недоступно без авторизации или удалено.")
        elif 'Name or service not known' in error_msg or 'Connection' in error_msg or 'network' in error_msg.lower():
            print("Ошибка: Проблемы с сетью. Проверьте подключение к интернету.")
        elif 'Unsupported URL' in error_msg or 'invalid url' in error_msg.lower() or 'unavailable' in error_msg.lower():
            print("Ошибка: Неподдерживаемая ссылка или видео недоступно. Убедитесь, что это корректная ссылка.")
        elif '404' in error_msg:
            print("Ошибка: Видео не найдено (ошибка 404). Возможно, оно было удалено.")
        else:
            print(f"Произошла ошибка при скачивании:\n{e}")
    except KeyboardInterrupt:
        print("\nЗагрузка прервана пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Утилита для скачивания видео и Reels из Instagram в максимальном качестве без потерь (Zero-Setup)."
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Ссылка на видео или Reels в Instagram"
    )
    parser.add_argument(
        "-o", "--output",
        help="Путь к папке для сохранения видео (по умолчанию текущая папка)",
        default=None
    )

    args = parser.parse_args()

    url = args.url
    if not url:
        try:
            url = input("Введите ссылку на Instagram (пост, видео или Reels): ").strip()
        except KeyboardInterrupt:
            print("\nОтменено.")
            sys.exit(1)

    if not url:
        print("Ошибка: Ссылка не указана.")
        sys.exit(1)

    download_instagram_video(url, args.output)

if __name__ == "__main__":
    main()
