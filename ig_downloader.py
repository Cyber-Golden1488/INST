import argparse
import sys
from tqdm import tqdm
import yt_dlp

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
            print("\nЗагрузка завершена! Сохранение файла...")

class MyLogger(object):
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

def download_instagram_video(url, output_path=None):
    # Настройки yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # Наивысшее качество
        'merge_output_format': 'mp4', # Контейнер (без перекодирования потоков)
        'quiet': True,
        'no_warnings': True,
        'logger': MyLogger(),
        'progress_hooks': [TqdmProgressHook()],
        'outtmpl': '%(title)s_%(id)s.%(ext)s',
    }

    if output_path:
        ydl_opts['outtmpl'] = f"{output_path.rstrip('/')}/%(title)s_%(id)s.%(ext)s"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Извлечение информации по ссылке: {url}")
            ydl.download([url])
            print("Готово! Видео успешно сохранено.")

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
        description="Утилита для скачивания видео и Reels из Instagram в максимальном качестве без потерь."
    )
    parser.add_argument(
        "url",
        help="Ссылка на видео или Reels в Instagram"
    )
    parser.add_argument(
        "-o", "--output",
        help="Путь к папке для сохранения видео (по умолчанию текущая папка)",
        default=None
    )

    args = parser.parse_args()
    download_instagram_video(args.url, args.output)

if __name__ == "__main__":
    main()
