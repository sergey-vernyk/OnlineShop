import hashlib
import os
import shutil
from typing import Callable

import environ
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'int_shop.settings')
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(settings.BASE_DIR, 'settings', '.env'))  # env file location


def update_sha(filepath, sha):
    """
    Update hash after each read file.
    """
    with open(filepath, 'rb') as f:
        while True:
            block = f.read(2 ** 10)  # block size equal 1 Mb
            if not block:
                break
            sha.update(block)


def make_hash() -> Callable:
    sha = hashlib.sha1()  # guarantee, that only one instance will be updating
    files_amount = 0

    def wrap(dir_path, *args, **kwargs) -> tuple:
        """
        Calculates hash of all available files and their quantity,
        which are located in directories, started from `dir_path`.
        Returns result as tuple (hash, quantity).
        """
        nonlocal sha, files_amount
        for path, dirs, files in os.walk(dir_path):
            for file in sorted(files):  # guarantee, that files will always be in the same order
                update_sha(os.path.join(path, file), sha)
                files_amount += 1
            for directory in sorted(dirs):  # guarantee, that directories will always be in the same order
                wrap(os.path.join(path, directory))
            break  # necessary only one iteration for getting all files in the current directory
        return sha.hexdigest(), files_amount

    return wrap


def run(file) -> None:
    """
    If hash doesn't match (i.e. there were updated files or directories in old location),
    function copies files and directories into new location.
    """
    # action starts only in production server
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
