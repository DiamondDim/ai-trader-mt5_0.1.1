#!/usr/bin/env python3
"""
Symbol Selector for AI Trading Robot
Интерактивный выбор валютных пар и автоматическое обучение
"""

import sys
import os
import questionary
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.mt5_client import get_available_symbols, get_all_symbols, initialize_mt5
from src.ml.model_builder import train_model
from src.utils.config import load_config, save_config


class SymbolSelector:
    def __init__(self):
        self.config = load_config()
        self.initialize()

    def initialize(self):
        """Инициализация MT5 соединения"""
        if not initialize_mt5():
            print("❌ Ошибка инициализации MT5")
            return False
        return True

    def select_symbol_interactive(self):
        """
        Интерактивный выбор валютной пары с красивым интерфейсом
        """
        print("\n🎯" + "=" * 60)
        print("           ВЫБОР ВАЛЮТНОЙ ПАРЫ ДЛЯ ТОРГОВЛИ")
        print("=" * 60)

        print("🔍 Получение списка доступных символов из MT5...")

        # Получаем символы
        major_pairs = get_available_symbols()
        all_symbols = get_all_symbols()

        if not major_pairs and not all_symbols:
            print("❌ Не удалось получить символы из MT5")
            print("💡 Проверьте подключение к MT5 и доступность демо-счета")
            return None

        print(f"✅ Найдено {len(major_pairs)} основных пар и {len(all_symbols)} всех символов")

        # Создаем варианты выбора
        choices = []

        # Текущий символ (если есть)
        current_symbol = self.config['trading'].get('symbol', '')
        if current_symbol:
            choices.append(
                questionary.Separator(f"=== ТЕКУЩИЙ СИМВОЛ: {current_symbol} ===")
            )
            choices.append(f"🔄 Переобучить текущий ({current_symbol})")

        # Основные валютные пары
        if major_pairs:
            choices.append(
                questionary.Separator("=== ОСНОВНЫЕ ВАЛЮТНЫЕ ПАРЫ ===")
            )
            for pair in major_pairs:
                icon = "💹" if "USD" in pair else "💶"
                choices.append(f"{icon} {pair}")

        # Все символы (ограниченное количество)
        if all_symbols:
            choices.append(
                questionary.Separator("=== ВСЕ СИМВОЛЫ (первые 50) ===")
            )
            for pair in all_symbols[:50]:
                choices.append(f"📊 {pair}")

        # Дополнительные опции
        choices.append(
            questionary.Separator("=== ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ ===")
        )
        choices.append("📝 Ввести символ вручную")
        choices.append("❌ Отмена")

        # Выбор символа
        selected = questionary.select(
            "Выберите валютную пару для торговли:",
            choices=choices,
            style=questionary.Style([
                ('separator', 'fg:#cc5454'),
                ('question', 'bold'),
            ])
        ).ask()

        if not selected or selected == "❌ Отмена":
            return None

        # Обработка выбора
        if selected == "📝 Ввести символ вручную":
            selected = questionary.text(
                "Введите название символа (например, EURUSD):",
                validate=lambda text: len(text) > 0
            ).ask()
            return selected.upper() if selected else None

        elif selected.startswith("🔄 Переобучить текущий"):
            return current_symbol

        else:
            # Извлекаем символ из строки с эмодзи
            return selected.split(" ")[-1]

    def configure_symbol(self, symbol):
        """
        Настраивает конфигурацию для выбранного символа
        """
        if not symbol:
            print("❌ Символ не выбран")
            return False

        print(f"\n⚙️  Настройка конфигурации для символа: {symbol}")

        # Обновляем конфигурацию
        self.config['trading']['symbol'] = symbol
        self.config['model']['symbol'] = symbol

        # Настройки по умолчанию для разных типов символов
        symbol_type = self._detect_symbol_type(symbol)
        self._apply_symbol_specific_settings(symbol, symbol_type)

        # Сохраняем обновленную конфигурацию
        save_config(self.config)

        print(f"✅ Конфигурация успешно обновлена для {symbol}")
        print(f"   Тип символа: {symbol_type}")
        print(f"   Лот: {self.config['trading']['lot_size']}")
        print(f"   Таймфрейм: {self.config['data']['timeframe']}")

        return True

    def _detect_symbol_type(self, symbol):
        """Определяет тип символа для применения специфичных настроек"""
        symbol_upper = symbol.upper()

        if any(x in symbol_upper for x in ['EUR', 'GBP', 'AUD', 'NZD', 'USD']):
            return 'forex_major'
        elif any(x in symbol_upper for x in ['JPY', 'CHF', 'CAD']):
            return 'forex_minor'
        elif any(x in symbol_upper for x in ['XAU', 'XAG']):
            return 'metals'
        elif any(x in symbol_upper for x in ['#', '.']):
            return 'stocks'
        else:
            return 'other'

    def _apply_symbol_specific_settings(self, symbol, symbol_type):
        """Применяет специфичные настройки для типа символа"""
        symbol_settings = self.config['symbol_specific'].get(symbol, {})

        if symbol_settings:
            # Используем настройки для конкретного символа
            for key, value in symbol_settings.items():
                if key in self.config['trading']:
                    self.config['trading'][key] = value
        else:
            # Применяем настройки по типу символа
            type_settings = {
                'forex_major': {'lot_size': 0.01, 'max_spread': 2.0},
                'forex_minor': {'lot_size': 0.01, 'max_spread': 3.0},
                'metals': {'lot_size': 0.01, 'max_spread': 5.0},
                'stocks': {'lot_size': 0.1, 'max_spread': 10.0},
                'other': {'lot_size': 0.01, 'max_spread': 5.0}
            }

            settings = type_settings.get(symbol_type, type_settings['other'])
            for key, value in settings.items():
                if key in self.config['trading']:
                    self.config['trading'][key] = value

    def auto_train_symbol(self, symbol):
        """
        Автоматическое обучение модели для выбранного символа
        """
        if not symbol:
            print("❌ Символ не указан для обучения")
            return False

        print(f"\n🤖 ЗАПУСК АВТОМАТИЧЕСКОГО ОБУЧЕНИЯ")
        print(f"🎯 Символ: {symbol}")
        print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        try:
            # Запускаем обучение
            success = train_model(symbol)

            if success:
                print(f"\n✅ Обучение успешно завершено для {symbol}")
                print(f"💾 Модель сохранена в папке models/")
                return True
            else:
                print(f"\n❌ Ошибка обучения для {symbol}")
                return False

        except Exception as e:
            print(f"\n💥 Критическая ошибка при обучении: {e}")
            return False

    def run_selection_flow(self, auto_train=True):
        """
        Полный процесс выбора и настройки символа
        """
        if not self.initialize():
            return False

        # Выбор символа
        symbol = self.select_symbol_interactive()

        if not symbol:
            print("❌ Выбор символа отменен")
            return False

        # Настройка конфигурации
        if not self.configure_symbol(symbol):
            return False

        # Автоматическое обучение
        if auto_train:
            return self.auto_train_symbol(symbol)
        else:
            print(f"\n🎯 Символ {symbol} настроен. Обучение не запущено.")
            print(f"💡 Для обучения выполните: python main.py --mode train --symbol {symbol}")
            return True


def main():
    """
    Основная функция для выбора символа и автоматического обучения
    """
    import argparse

    parser = argparse.ArgumentParser(description='Symbol Selector for AI Trading Robot')
    parser.add_argument('--no-train', action='store_true', help='Skip auto training after selection')

    args = parser.parse_args()

    selector = SymbolSelector()
    success = selector.run_selection_flow(auto_train=not args.no_train)

    if success:
        print("\n🎉" + "=" * 50)
        print("          НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 50)
        current_symbol = selector.config['trading']['symbol']
        print(f"💡 Для запуска торговли выполните:")
        print(f"   python main.py --mode trade --symbol {current_symbol}")
    else:
        print("\n⚠️ Настройка завершена с ошибками")


if __name__ == "__main__":
    main()
