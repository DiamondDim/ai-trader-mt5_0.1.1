#!/usr/bin/env python3
"""
Продвинутое тестирование ордеров для AI Trading Robot
"""

import sys
import os
import time

# Добавляем путь к src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.mt5_client import initialize_mt5, place_order, get_symbol_info, close_all_orders, get_error_description
from utils.config import load_config


def test_order_advanced(symbol=None):
    """
    Продвинутое тестирование размещения ордера
    """
    print("🧪 Продвинутое тестирование ордеров...")

    if not initialize_mt5():
        print("❌ Не удалось инициализировать MT5")
        return False

    config = load_config()
    test_symbol = symbol or config['trading']['symbol']

    print(f"🎯 Тестируем символ: {test_symbol}")

    # Проверяем информацию о символе
    symbol_info = get_symbol_info(test_symbol)
    if not symbol_info:
        print(f"❌ Символ {test_symbol} не доступен")
        return False

    print(f"✅ Информация о символе:")
    print(f"   Название: {symbol_info['name']}")
    print(f"   Bid: {symbol_info['bid']:.5f}")
    print(f"   Ask: {symbol_info['ask']:.5f}")
    print(f"   Spread: {symbol_info['spread']:.5f}")
    print(f"   Digits: {symbol_info['digits']}")
    print(f"   Point: {symbol_info.get('point', 'N/A')}")
    print(f"   Trade stops level: {symbol_info.get('trade_stops_level', 'N/A')}")
    print(f"   Trade allowed: {symbol_info['trade_allowed']}")

    # Тестируем BUY ордер с разными настройками
    print(f"\n📈 Тестируем BUY ордер с разными настройками...")

    # Тест 1: Без стоп-лосса и тейк-профита
    print(f"\n🔹 Тест 1: Без SL/TP")
    success1 = place_order(
        symbol=test_symbol,
        order_type='buy',
        lot_size=0.01,
        stop_loss=0.0,
        take_profit=0.0
    )

    time.sleep(2)

    # Тест 2: С умеренными SL/TP
    print(f"\n🔹 Тест 2: С умеренными SL/TP (50/75 пипсов)")
    success2 = place_order(
        symbol=test_symbol,
        order_type='buy',
        lot_size=0.01,
        stop_loss=0.0050,  # 50 пипсов
        take_profit=0.0075  # 75 пипсов
    )

    time.sleep(2)

    # Тест 3: SELL ордер
    print(f"\n🔹 Тест 3: SELL ордер с SL/TP")
    success3 = place_order(
        symbol=test_symbol,
        order_type='sell',
        lot_size=0.01,
        stop_loss=0.0050,
        take_profit=0.0075
    )

    # Закрываем все тестовые ордера
    print(f"\n🛑 Закрываем все тестовые ордера...")
    close_success = close_all_orders(test_symbol)

    # Итоговый результат
    tests_passed = sum([success1, success2, success3])
    print(f"\n📊 Итоги тестирования:")
    print(f"   ✅ Успешных тестов: {tests_passed}/3")
    print(f"   ✅ Закрытие ордеров: {'Успешно' if close_success else 'С ошибками'}")

    if tests_passed >= 2 and close_success:
        print(f"\n🎉 Тестирование пройдено успешно!")
        return True
    else:
        print(f"\n⚠️ Тестирование завершено с проблемами")
        return False


def test_market_conditions():
    """
    Тестирование рыночных условий
    """
    print("\n📊 Тестирование рыночных условий...")

    if not initialize_mt5():
        return False

    import MetaTrader5 as mt5
    from datetime import datetime

    # Проверяем время сервера
    server_time = mt5.symbol_info_tick("AUDUSDrfd").time
    server_time_str = datetime.fromtimestamp(server_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"🕒 Время сервера: {server_time_str}")

    # Проверяем состояние рынка
    symbols_to_check = ["AUDUSDrfd", "EURUSDrfd", "GBPUSDrfd"]

    for symbol in symbols_to_check:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            spread = tick.ask - tick.bid
            print(f"   {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}, Spread={spread:.5f}")
        else:
            print(f"   {symbol}: Нет данных")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Продвинутое тестирование ордеров AI Trading Robot')
    parser.add_argument('symbol', nargs='?', help='Символ для тестирования (например, AUDUSDrfd)')
    parser.add_argument('--market', action='store_true', help='Показать рыночные условия')

    args = parser.parse_args()

    print("🤖 AI Trading Robot - Продвинутое тестирование ордеров")
    print("=" * 60)

    success = True

    if args.market:
        success = test_market_conditions()
    else:
        success = test_order_advanced(args.symbol)

    if success:
        print("\n✅ Тестирование завершено успешно")
    else:
        print("\n❌ Тестирование завершено с ошибками")
        sys.exit(1)
