import os
import numpy as np
from PIL import Image
import zipfile


def decode_image_to_data(image_path):
    """
    Извлекает бинарные данные из изображения,
    учитывая первые 4 байта (big-endian) как длину полезной нагрузки.
    """
    img = Image.open(image_path)
    img_array = np.array(img)

    # Собираем все байты в один массив
    data_bytes = bytearray()
    height, width, _ = img_array.shape

    for i in range(height):
        for j in range(width):
            # Извлекаем R, G, B
            pixel = img_array[i, j]
            data_bytes.extend(pixel)

    # Превращаем в bytes
    all_data = bytes(data_bytes)

    # Первые 4 байта – это длина (big-endian)
    if len(all_data) < 4:
        raise ValueError("Изображение слишком маленькое или повреждено (не хватает хотя бы 4 байт).")
    data_length = int.from_bytes(all_data[:4], byteorder='big')

    # Проверяем корректность длины
    if data_length > (len(all_data) - 4):
        raise ValueError("Некорректная длина данных или файл поврежден.")

    # Извлекаем ровно data_length байт
    real_data = all_data[4:4 + data_length]
    return real_data


def restore_from_images(input_folder, output_folder):
    """
    Восстанавливает ZIP-архив из набора PNG-изображений
    и распаковывает его в output_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Получаем все файлы-изображения, сортируем по номеру части
    image_files = sorted(
        [f for f in os.listdir(input_folder) if f.startswith("encoded_part_") and f.endswith(".png")],
        key=lambda x: int(x.split("_")[-1].split(".")[0])
    )

    if not image_files:
        print("❌ Нет закодированных изображений в папке:", input_folder)
        return

    print("🔍 Декодирую изображения...")
    parts_data = []
    for img_file in image_files:
        img_path = os.path.join(input_folder, img_file)
        try:
            decoded = decode_image_to_data(img_path)
            parts_data.append(decoded)
            print(f"   → Обработано: {img_file}")
        except Exception as e:
            print(f"   ❌ Ошибка при декодировании {img_file}: {e}")
            return

    # Объединяем все части в один ZIP-файл
    zip_path = os.path.join(output_folder, "restored.zip")
    with open(zip_path, "wb") as f:
        for part in parts_data:
            f.write(part)

    # Проверяем, является ли результат действительно ZIP-архивом
    if not zipfile.is_zipfile(zip_path):
        print("❌ Ошибка: Неверный формат ZIP. Возможные причины:")
        print("   1. Изображения были повреждены или изменены.")
        print("   2. Использован другой метод кодирования (не текущая версия).")
        print(f"   Данные сохранены как '{zip_path}'. Попробуйте распаковать вручную.")
        return

    # Распаковываем архив
    print("📦 Распаковываю архив...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_folder)
        print(f"✅ Успешно! Файлы восстановлены в: {output_folder}")
    except Exception as e:
        print(f"❌ Ошибка при распаковке: {e}")
    finally:
        # Если хотите сохранить сам ZIP, просто закомментируйте строчку ниже
        os.remove(zip_path)


if __name__ == "__main__":
    # Пример использования (раскомментируйте, если нужно):
    restore_from_images(
        input_folder="encoded_images",
        output_folder="restored_files"
    )
    pass
