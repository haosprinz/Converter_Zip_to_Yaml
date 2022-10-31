import shutil
import zipfile
from math import ceil
from os import path, listdir, chdir, mkdir
from typing import List

import yaml

CURRENT_DIR = path.dirname(path.abspath(__file__))


def zip_converter(filename: str,
                  validation_size: float = 1.0,
                  ):
    """
    Конвертер zip-архива выгрузки размеченного набора данных из CVAT

    :param filename: имя zip-архива в текущей директории
    :param validation_size: размер валидационной выборки в диапазоне 0..1.0(по умолчанию 1.0)
    :return: None
    """
    create_directories()

    archive_dir_name = "archive"
    archive_dir = path.join(CURRENT_DIR, archive_dir_name)
    with zipfile.ZipFile(filename, 'r') as zipFile:
        zipFile.extractall(archive_dir_name)

    with open(path.join(archive_dir, 'obj.names')) as obj_data:
        list_class = obj_data.read().strip().split('\n')

    obj_train_data_path = path.join(archive_dir, 'obj_train_data')
    chdir(path.join(archive_dir, 'obj_train_data'))

    # Распределение изображений и файлов разметки
    file_sorting(listdir(), obj_train_data_path, validation_size)

    # Создание кофигурационного файла
    create_yaml_config(list_class)


def file_sorting(files: List[str],
                 content_path: str,
                 validation_size: float,
                 root_dir_name: str = "sorted",
                 ):
    """
    Распределение файлов с выгрузки разметки в необходимой для yolov5 иерархии каталогов

    :param files: список имен файлов
    :param content_path: путь до каталога исходных файлов разметки obj_train_data
    :param validation_size: размер валидационной выборки
    :param root_dir_name: имя корневого каталога (по умолчанию "sorted")
    :return: None
    """
    # Разбор файлов на изображения и txt-файлы разметки
    images = []
    texts = []
    for name in files:
        if name.__contains__('.jpg'):
            images.append(name)
        elif name.__contains__('.txt'):
            texts.append(name)

    sorted_images_train = path.join(CURRENT_DIR, f"{root_dir_name}/images/train")
    sorted_images_val = path.join(CURRENT_DIR, f"{root_dir_name}/images/val")
    sorted_labels_train = path.join(CURRENT_DIR, f"{root_dir_name}/labels/train")
    sorted_labels_val = path.join(CURRENT_DIR, f"{root_dir_name}/labels/val")

    val_text_list = []
    val_count = ceil(len(images) * validation_size)
    if val_count == len(images):
        val_count = 0

    i = 1
    for image in images:
        if i <= val_count:
            shutil.copyfile(path.join(content_path, image), path.join(sorted_images_val, image))
            val_text_list.append(image[:-4] + '.txt')
        else:
            shutil.copyfile(path.join(content_path, image), path.join(sorted_images_train, image))
        i += 1

    for txt in texts:
        if val_text_list.__contains__(txt):
            shutil.copyfile(path.join(content_path, txt), path.join(sorted_labels_val, txt))
        else:
            shutil.copyfile(path.join(content_path, txt), path.join(sorted_labels_train, txt))


def create_yaml_config(class_names: List[str],
                       filename: str = "sorted",
                       ):
    """
    Создать конфигурационный yaml-файл

    :param class_names: список имен классов
    :param filename: имя конфигурационного файла (по умолчанию "sorted")
    :return: None
    """
    chdir(CURRENT_DIR)
    config_data = {"train": "/sorted/images/train",
                   "val": "/sorted/images/val",
                   "nc": len(class_names),
                   "names": class_names,
                   }

    with open(f"{filename}.yaml", "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)


def create_directories(root_dir_name: str = "sorted"):
    """
    Создать иерархию каталогов для yolov5 формата датасета

    :param root_dir_name: имя корневого каталога (по умолчанию "sorted")
    :return: None
    """
    mkdir(f"{root_dir_name}")
    mkdir(f"{root_dir_name}/images")
    mkdir(f"{root_dir_name}/images/train")
    mkdir(f"{root_dir_name}/images/val")
    mkdir(f"{root_dir_name}/labels")
    mkdir(f"{root_dir_name}/labels/train")
    mkdir(f"{root_dir_name}/labels/val")


if __name__ == '__main__':
    print(f"Current directory сontent: {listdir()}")
    source_filename = input("Write source zip-filename from current directory: ")
    val_size = float(input('Validation size (float value of 0..1): '))
    zip_converter(source_filename, validation_size=val_size)
