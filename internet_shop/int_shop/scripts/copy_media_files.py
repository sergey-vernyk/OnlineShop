import shutil
import os
import environ
from django.conf import settings
import hashlib
from typing import Callable

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'int_shop.settings')
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(settings.BASE_DIR, 'settings', '.env'))


def update_sha(filepath, sha):
    """
    Функция обновляет хеш после каждого прочитанного файла
    """
    with open(filepath, 'rb') as f:
        while True:
            block = f.read(2 ** 10)  # блок в 1 Мб
            if not block:
                break
            sha.update(block)


def make_hash() -> Callable:
    sha = hashlib.sha1()  # гарантирует, что всегда будет обновляться только один экземпляр
    files_amount = 0

    def wrap(dir_path, *args, **kwargs) -> tuple:
        """
        Функция считает хеш всех файлов и их кол-во, находящихся в каталогах,
        начиная с пути dir_path.
        Возвращает результат в виде кортежа (хеш, кол-во)
        """
        nonlocal sha, files_amount
        for path, dirs, files in os.walk(dir_path):
            for file in sorted(files):  # гарантия, что файлы будут всегда в одном порядке
                update_sha(os.path.join(path, file), sha)
                files_amount += 1
            for directory in sorted(dirs):  # гарантия, что папки будут всегда в одном порядке
                wrap(os.path.join(path, directory))
            break  # нужна только одна итерация - получить все файлы в текущей директории
        return sha.hexdigest(), files_amount

    return wrap


def run(file):
    """
    Функция копирует файлы и папки в новое расположение, если хеш не совпадает
    (т.е. были обновлены файлы или папки в старом расположении)
    """
    # только если запуск происходит в продакшене
    if env('DEV_OR_PROD') == 'prod':
        old_folder_path = os.path.join(settings.BASE_DIR, 'media/')
        new_folder_path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT)

        sha, amount_files = make_hash()(old_folder_path)
        with open(file, 'r', encoding='utf-8') as f:
            current_sha = f.readline().strip()
            current_amount_files = f.readline().strip()
            current_amount_files = int(current_amount_files) if current_amount_files else 0
            if sha == current_sha:
                print('Hashes are the same and the files have not been updated')
                return

        with open(file, 'w', encoding='utf-8') as f:
            f.write(f'{sha}\n')
            f.write(f'{amount_files}\n')
            shutil.copytree(old_folder_path, new_folder_path, dirs_exist_ok=True)
            print(f'{abs(amount_files - current_amount_files)} file(s) have been deleted or added')
            return
