#!/usr/bin/env python3
"""
Скрипт для очистки папки models от некорректных файлов
"""

import os
import shutil


def clean_models_directory():
    """Очистка папки models от файлов неправильного формата"""
    models_dir = 'models'

    if not os.path.exists(models_dir):
        print("✅ Папка models не существует")
        return

    # Список корректных префиксов
    correct_prefixes = ['model_']

    # Файлы для удаления
    files_to_remove = []

    for file in os.listdir(models_dir):
        file_path = os.path.join(models_dir, file)

        # Проверяем формат имени файла
        if file.endswith('.pkl'):
            if not any(file.startswith(prefix) for prefix in correct_prefixes):
                files_to_remove.append(file_path)
                print(f"🗑️ Файл для удаления (неправильный формат): {file}")
            elif file == "model - scaler.pkl":  # Специфичный некорректный файл
                files_to_remove.append(file_path)
                print(f"🗑️ Файл для удаления (некорректное имя): {file}")

    # Удаляем файлы
    if files_to_remove:
        confirm = input(f"Удалить {len(files_to_remove)} файлов? (y/n): ")
        if confirm.lower() == 'y':
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"✅ Удален: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"❌ Ошибка удаления {file_path}: {e}")
        else:
            print("❌ Удаление отменено")
    else:
        print("✅ Нет файлов для удаления")

    # Показываем оставшиеся файлы
    remaining_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    print(f"\n📁 Оставшиеся файлы в models: {len(remaining_files)}")
    for file in remaining_files:
        print(f"   📄 {file}")


if __name__ == "__main__":
    print("🧹 Очистка папки models")
    print("=" * 50)
    clean_models_directory()
