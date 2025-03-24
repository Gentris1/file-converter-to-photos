import os
import zipfile
import math
from PIL import Image
import numpy as np


def folder_to_zip(folder_path, zip_path):
    """Архивирует папку в ZIP."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arcname=rel_path)


def split_file(file_path, max_size_mb=32):
    """Разбивает файл на части по max_size_mb."""
    max_size = max_size_mb * 1024 * 1024  # 32 МБ в байтах
    file_size = os.path.getsize(file_path)
    num_parts = math.ceil(file_size / max_size)

    parts = []
    with open(file_path, 'rb') as f:
        for i in range(num_parts):
            part_data = f.read(max_size)
            part_path = f"{file_path}.part{i + 1}"
            with open(part_path, 'wb') as part_file:
                part_file.write(part_data)
            parts.append(part_path)
    return parts


def encode_data_to_image(data, output_path):
    """
    Кодирует бинарные данные в изображение (RGB),
    предварительно записав в первые 4 байта длину данных.
    """
    # Если на вход пришла строка, превращаем в байты
    if isinstance(data, str):
        data = data.encode()

    # Добавляем 4 байта с длиной (Network Byte Order / big-endian)
    data_length = len(data)
    length_bytes = data_length.to_bytes(4, byteorder='big')
    new_data = length_bytes + data

    # Рассчитываем размер изображения (квадратное, чтобы вместить все байты)
    total_bytes = len(new_data)
    img_size = math.ceil(math.sqrt(total_bytes / 3.0))  # три канала (R, G, B)

    # Создаём массив пикселей
    img_array = np.zeros((img_size, img_size, 3), dtype=np.uint8)

    # Заполняем пиксели байтами
    byte_pos = 0
    for i in range(img_size):
        for j in range(img_size):
            for k in range(3):  # R, G, B
                if byte_pos < total_bytes:
                    img_array[i, j, k] = new_data[byte_pos]
                    byte_pos += 1
                else:
                    # Если данные закончились, оставляем 0 (черный пиксель)
                    img_array[i, j, k] = 0

    # Сохраняем изображение
    img = Image.fromarray(img_array)
    img.save(output_path)
    print(f"Создано изображение: {output_path}")


def folder_to_images(folder_path, output_folder, max_size_mb=32):
    """
    Основная функция:
    1) Архивирует папку в ZIP,
    2) Разбивает архив на части ≤max_size_mb,
    3) Каждую часть кодирует в PNG-изображение.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Архивируем папку во временный файл
    zip_path = os.path.join(output_folder, "temp_archive.zip")
    folder_to_zip(folder_path, zip_path)

    # 2. Разбиваем архив на части ≤32 МБ
    parts = split_file(zip_path, max_size_mb)
    os.remove(zip_path)  # Удаляем временный архив

    # 3. Кодируем каждую часть в изображение
    for i, part in enumerate(parts, start=1):
        img_path = os.path.join(output_folder, f"encoded_part_{i}.png")
        with open(part, 'rb') as f:
            data = f.read()
        encode_data_to_image(data, img_path)
        os.remove(part)  # Удаляем временную часть

    print(f"Папка успешно закодирована в {len(parts)} изображений!")


import os


def fix_timestamps(folder_path):
    """
    Проходит по всем файлам в folder_path и устанавливает им время модификации
    не раньше 1980-01-01, чтобы избежать ошибок при создании zip-архивов.
    """
    # Таймштамп для 1980-01-01 00:00:00 в UTC
    min_timestamp = 315532800  # Это timestamp для минимальной даты в ZIP-формате

    # Проверяем, существует ли указанная папка
    if not os.path.exists(folder_path):
        print(f"Ошибка: Папка не найдена - {folder_path}")
        return

    # Обрабатываем все файлы в папке и подпапках
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            try:
                # Получаем текущие временные метки файла
                file_stat = os.stat(file_path)

                # Если время модификации раньше 1980 года, исправляем его
                if file_stat.st_mtime < min_timestamp:
                    # Устанавливаем новое время (время доступа и время модификации)
                    os.utime(file_path, (min_timestamp, min_timestamp))
                    print(f"Исправлен таймштамп для: {file_path}")

            except FileNotFoundError:
                print(f"Файл был удален во время обработки: {file_path}")
            except PermissionError:
                print(f"Нет прав доступа к файлу: {file_path}")
            except Exception as e:
                print(f"Неожиданная ошибка при обработке {file_path}: {e}")


# Пример использования
target_folder = "my_secret_files"
#fix_timestamps(target_folder)
print("Обработка завершена")

# Пример использования (раскомментируйте, если нужно):
folder_to_images(
    folder_path="my_secret_files",   # Папка с данными
    output_folder="encoded_images",  # Куда сохранять изображения
    max_size_mb=32                   # Макс. размер изображения (МБ)
)
