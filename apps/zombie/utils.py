import os

from apps.zombie.models import Zombie
from os.path import join as join_path

from config import settings


def save_file_to_zombie(zombie: Zombie):
    media_folder = join_path("media")
    zombie_folder = zombie.ip_address.replace('.', '') + zombie.os_name
    if not os.path.isdir(zombie_folder):
        os.makedirs(zombie_folder)
    else:
        pass
