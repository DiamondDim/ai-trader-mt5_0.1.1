#!/usr/bin/env python3
"""
Тестирование загрузки данных для AI Trading Robot
"""

import sys
import os

# Добавляем путь к src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.mt5_client import initialize_mt5, load_data, get_available_symbols
from utils.config import load_config


def test_data_loading(symbols_to_test=None):
    """
    Тестирование загрузки данных для разных символов
    """
    print("🧪 Тестирование загрузки данных")
    print("=" * 50)

    if not initialize_mt5():
        print("❌ Не удалось инициализировать MT5")
        return False

    if symbols_to_test is None:
        # Тестируем несколько популярных символов
        symbols_to_test = ['EURUSDrfd', 'GBPUSDrfd', 'USDJPYrfd', 'AUDUSDrfd']

    results = {}

    for symbol in symbols_to_test:
        print(f"\n🔍 Тестируем символ: {symbol}")

        # Пробуем разные таймфреймы
        timeframes = ['M1', 'M5', 'M15', 'H1', 'H4']

        for tf in timeframes:
            print(f"  ⏰ Таймфрейм: {tf}")
            data = load_data(symbol, tf, 1000)  # Загружаем 1000 баров

            if not data.empty:
                print(f"    ✅ Успешно: {len(data)} баров")
                results[f"{symbol}_{tf}"] = len(data)

                # Показываем пример данных
                if len(data) > 0:
                    print(f"    📅 Первая дата: {data.index[0]}")
                    print(f"    📅 Последняя дата: {data.index[-1]}")
                    print(f"    📊 Колонки: {list(data.columns)}")
                    break  # Если один таймфрейм сработал, переходим к следующему символу
            else:
                print(f"    ❌ Не удалось загрузить данные")

        if symbol not in [k.split('_')[0] for k in results.keys()]:
            print(f"  💥 Не удалось загрузить данные ни для одного таймфрейма")

    print(f"\n📊 Итоги тестирования:")
    print(f"✅ Успешных загрузок: {len(results)}")
    for key, count in results.items():
        print(f"   {key}: {count} баров")

    return len(results) > 0


def check_available_data():
    """
    Проверка доступных данных в MT5
    """
    print("\n📋 Проверка доступных данных в MT5")
    print("=" * 50)

    if not initialize_mt5():
        return

    import MetaTrader5 as mt5

    # Получаем список символов
    symbols = get_available_symbols()
    print(f"📈 Доступно символов: {len(symbols)}")

    # Проверяем несколько символов
    test_symbols = symbols[:5]  # Первые 5 символов

    for symbol in test_symbols:
        print(f"\n🔍 Символ: {symbol}")

        # Проверяем информацию о символе
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            print(f"  ✅ Доступен: {symbol_info.name}")
            print(f"  💰 Bid: {symbol_info.bid}, Ask: {symbol_info.ask}")

            # Пробуем загрузить небольшое количество данных
            rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, datetime.now(), 10)
            if rates is not None and len(rates) > 0:
                print(f"  📊 Данные доступны: {len(rates)} баров")
            else:
                print(f"  ❌ Данные недоступны")
        else:
            print(f"  ❌ Символ не найден")


if __name__ == "__main__":
    from datetime import datetime

    print("🤖 AI Trading Robot - Тестирование загрузки данных")

    # Тестируем загрузку данных
    success = test_data_loading()

    if success:
        print("\n✅ Тестирование завершено успешно")
    else:
        print("\n❌ Тестирование завершено с ошибками")
        print("\n💡 Рекомендации:")
        print("1. Убедитесь, что MT5 запущен и подключен к демо-счету")
        print("2. Проверьте, что выбранный символ доступен для торговли")
        print("3. Убедитесь, что есть исторические данные для выбранного символа")
        print("4. Попробуйте другой символ из списка доступных")
