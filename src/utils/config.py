import yaml
import os
from typing import Dict, Any


class Config:
    """Класс для работы с конфигурацией"""

    @staticmethod
    def load_config(config_path: str = None) -> Dict[str, Any]:
        """Загрузка конфигурации из YAML файла"""
        if config_path is None:
            # Пробуем разные пути к конфигу
            possible_paths = [
                'config/settings.yaml',
                'config/simple_settings.yaml',
                'config/test_settings.yaml'
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break

            if config_path is None:
                print("❌ Не найден файл конфигурации")
                return None

        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                print(f"✅ Конфигурация загружена из: {config_path}")
                return config

        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации {config_path}: {e}")
            return None

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """Сохранение конфигурации в YAML файл"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
            print(f"✅ Конфигурация сохранена: {config_path}")

        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
