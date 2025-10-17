#!/usr/bin/env python3
"""
Тестирование ордеров для AI Trading Robot
"""

import sys
import os

# Добавляем путь к src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from core.mt5_client import initialize_mt5, place_order, get_symbol_info, close_all_orders
    from utils.config import load_config
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


def test_order(symbol=None):
    """
    Тестирование размещения ордера
    """
    print("🧪 Тестирование ордеров...")

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
    print(f"   Trade allowed: {symbol_info['trade_allowed']}")

    # Тестируем BUY ордер
    print(f"\n📈 Тестируем BUY ордер...")
    success_buy = place_order(
        symbol=test_symbol,
        order_type='buy',
        lot_size=0.01,
        stop_loss=0.0020,
        take_profit=0.0030
    )

    if success_buy:
        print("✅ BUY ордер успешно размещен")
    else:
        print("❌ Ошибка размещения BUY ордера")

    # Небольшая пауза
    import time
    time.sleep(2)

    # Тестируем SELL ордер
    print(f"\n📉 Тестируем SELL ордер...")
    success_sell = place_order(
        symbol=test_symbol,
        order_type='sell',
        lot_size=0.01,
        stop_loss=0.0020,
        take_profit=0.0030
    )

    if success_sell:
        print("✅ SELL ордер успешно размещен")
    else:
        print("❌ Ошибка размещения SELL ордера")

    # Закрываем все тестовые ордера
    print(f"\n🛑 Закрываем все тестовые ордера...")
    close_success = close_all_orders(test_symbol)

    if close_success:
        print("✅ Все тестовые ордера закрыты")
    else:
        print("❌ Ошибка закрытия ордеров")

    # Итоговый результат
    if success_buy and success_sell and close_success:
        print(f"\n🎉 Все тесты пройдены успешно!")
        return True
    else:
        print(f"\n⚠️ Некоторые тесты не пройдены")
        return False


def test_market_info():
    """
    Тестирование информации о рынке
    """
    print("\n📊 Тестирование рыночной информации...")

    if not initialize_mt5():
        return False

    from core.mt5_client import get_available_symbols, get_all_symbols

    # Получаем списки символов
    major_pairs = get_available_symbols()
    all_symbols = get_all_symbols()

    print(f"✅ Основных валютных пар: {len(major_pairs)}")
    print(f"✅ Всего символов: {len(all_symbols)}")

    if major_pairs:
        print("\n📈 Основные пары:")
        for i, pair in enumerate(major_pairs[:10], 1):
            print(f"   {i}. {pair}")
        if len(major_pairs) > 10:
            print(f"   ... и еще {len(major_pairs) - 10} пар")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Тестирование ордеров AI Trading Robot')
    parser.add_argument('symbol', nargs='?', help='Символ для тестирования (например, EURUSD)')
    parser.add_argument('--market-info', action='store_true', help='Показать рыночную информацию')

    args = parser.parse_args()

    print("🤖 AI Trading Robot - Тестирование ордеров")
    print("=" * 50)

    success = True

    if args.market_info:
        success = test_market_info()
    else:
        success = test_order(args.symbol)

    if success:
        print("\n✅ Тестирование завершено успешно")
    else:
        print("\n❌ Тестирование завершено с ошибками")
        sys.exit(1)
