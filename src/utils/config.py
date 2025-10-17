import yaml
import os
from datetime import datetime


def load_config(config_path=None):
    """
    Загрузка конфигурации из YAML файла
    """
    if config_path is None:
        config_path = os.path.join('config', 'settings.yaml')

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        # Добавляем значения по умолчанию если их нет
        defaults = {
            'trading': {
                'symbol': 'EURUSD',
                'lot_size': 0.01,
                'max_spread': 2.0,
                'magic_number': 234000
            },
            'model': {
                'symbol': 'EURUSD',
                'current_model': '',
                'last_trained': '',
                'accuracy': 0.0,
                'features_count': 0,
                'training_samples': 0
            },
            'data': {
                'timeframe': 'M15',
                'bars_count': 2000
            },
            'symbol_specific': {}
        }

        # Рекурсивное обновление конфига значениями по умолчанию
        def update_config(current, default):
            for key, value in default.items():
                if key not in current:
                    current[key] = value
                elif isinstance(value, dict) and isinstance(current[key], dict):
                    update_config(current[key], value)

        update_config(config, defaults)

        return config

    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        # Возвращаем конфиг по умолчанию
        return defaults


def save_config(config, config_path=None):
    """
    Сохранение конфигурации в YAML файл
    """
    if config_path is None:
        config_path = os.path.join('config', 'settings.yaml')

    try:
        # Создаем папку если её нет
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"✅ Конфигурация сохранена: {config_path}")
        return True

    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False


def create_multi_symbol_config():
    """
    Создание конфигурации для работы с несколькими символами
    """
    config = {
        'trading': {
            'symbol': 'EURUSD',
            'lot_size': 0.01,
            'max_spread': 2.0,
            'magic_number': 234000,
            'max_orders': 5,
            'daily_loss_limit': 50.0
        },
        'model': {
            'symbol': 'EURUSD',
            'current_model': '',
            'last_trained': '',
            'accuracy': 0.0,
            'features_count': 0,
            'training_samples': 0,
            'min_confidence': 0.6
        },
        'data': {
            'timeframe': 'M15',
            'bars_count': 2000,
            'train_test_split': 0.8
        },
        'symbol_specific': {
            'EURUSD': {
                'lot_size': 0.01,
                'max_spread': 2.0,
                'stop_loss_pips': 20,
                'take_profit_pips': 30
            },
            'GBPUSD': {
                'lot_size': 0.01,
                'max_spread': 2.5,
                'stop_loss_pips': 25,
                'take_profit_pips': 35
            },
            'USDJPY': {
                'lot_size': 0.01,
                'max_spread': 2.0,
                'stop_loss_pips': 25,
                'take_profit_pips': 40
            },
            'XAUUSD': {
                'lot_size': 0.01,
                'max_spread': 5.0,
                'stop_loss_pips': 50,
                'take_profit_pips': 80
            }
        }
    }

    config_path = os.path.join('config', 'multi_symbol_config.yaml')
    save_config(config, config_path)
    return config


def get_symbol_specific_config(symbol, config=None):
    """
    Получение специфичных настроек для символа
    """
    if config is None:
        config = load_config()

    symbol_config = config['symbol_specific'].get(symbol, {})

    # Возвращаем объединенные настройки (общие + специфичные)
    trading_config = config['trading'].copy()
    trading_config.update(symbol_config)

    return trading_config
