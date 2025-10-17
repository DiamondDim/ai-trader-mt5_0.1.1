#!/usr/bin/env python3
"""
Диагностика проблем с торговлей в AI Trading Robot
"""

import sys
import os
import time

# Добавляем путь к src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.mt5_client import initialize_mt5, get_symbol_info, check_trading_allowed, place_order_simple, \
    place_order_with_sltp
import MetaTrader5 as mt5


def diagnose_account():
    """
    Диагностика счета и подключения
    """
    print("🔍 Диагностика счета MT5")
    print("=" * 50)

    if not initialize_mt5():
        print("❌ Не удалось инициализировать MT5")
        return False

    # Получаем информацию о счете
    account_info = mt5.account_info()
    if account_info:
        print(f"✅ Информация о счете:")
        print(f"   👤 Логин: {account_info.login}")
        print(f"   💰 Баланс: {account_info.balance:.2f}")
        print(f"   💵 Валюта: {account_info.currency}")
        print(f"   🏦 Компания: {account_info.company}")
        print(f"   🔧 Режим: {'Демо' if account_info.trade_mode == 1 else 'Реальный'}")
        print(f"   📈 Кредитное плечо: 1:{account_info.leverage}")
        print(f"   📊 Свободная маржа: {account_info.margin_free:.2f}")
    else:
        print("❌ Не удалось получить информацию о счете")
        return False

    return True


def diagnose_symbol(symbol):
    """
    Диагностика символа
    """
    print(f"\n🔍 Диагностика символа: {symbol}")
    print("=" * 50)

    symbol_info = get_symbol_info(symbol)
    if not symbol_info:
        print(f"❌ Символ {symbol} не найден")
        return False

    print(f"✅ Информация о символе:")
    print(f"   📛 Название: {symbol_info['name']}")
    print(f"   💰 Bid: {symbol_info['bid']:.5f}")
    print(f"   💵 Ask: {symbol_info['ask']:.5f}")
    print(f"   📏 Спред: {symbol_info['spread']:.5f}")
    print(f"   🔢 Digits: {symbol_info['digits']}")
    print(f"   📍 Point: {symbol_info['point']}")
    print(f"   🛑 Stops Level: {symbol_info['trade_stops_level']}")
    print(f"   📦 Contract Size: {symbol_info['trade_contract_size']}")
    print(f"   💱 Базовая валюта: {symbol_info['currency_base']}")
    print(f"   💵 Валюта прибыли: {symbol_info['currency_profit']}")
    print(f"   🏦 Валюта маржи: {symbol_info['currency_margin']}")
    print(f"   ✅ Торговля разрешена: {symbol_info['trade_allowed']}")

    # Проверяем торговые разрешения
    trading_allowed = check_trading_allowed(symbol)
    if not trading_allowed:
        print(f"❌ Торговля запрещена для {symbol}")
        return False

    return True


def test_simple_orders(symbol):
    """
    Тестирование простых ордеров без SL/TP
    """
    print(f"\n🧪 Тестирование простых ордеров для {symbol}")
    print("=" * 50)

    # Тест 1: BUY ордер
    print(f"\n🔹 Тест 1: BUY ордер (0.01 лот)")
    success_buy = place_order_simple(symbol, 'buy', 0.01)

    time.sleep(2)

    # Тест 2: SELL ордер
    print(f"\n🔹 Тест 2: SELL ордер (0.01 лот)")
    success_sell = place_order_simple(symbol, 'sell', 0.01)

    # Закрываем все ордера
    from core.mt5_client import close_all_orders
    print(f"\n🛑 Закрываем все тестовые ордера...")
    close_success = close_all_orders(symbol)

    print(f"\n📊 Результаты простых ордеров:")
    print(f"   ✅ BUY: {'Успешно' if success_buy else 'Ошибка'}")
    print(f"   ✅ SELL: {'Успешно' if success_sell else 'Ошибка'}")
    print(f"   ✅ Закрытие: {'Успешно' if close_success else 'Ошибка'}")

    return success_buy or success_sell


def test_sltp_orders(symbol):
    """
    Тестирование ордеров со SL/TP
    """
    print(f"\n🧪 Тестирование ордеров со SL/TP для {symbol}")
    print("=" * 50)

    # Тест 1: BUY ордер с SL/TP
    print(f"\n🔹 Тест 1: BUY ордер с SL/TP (0.01 лот, SL=20, TP=30)")
    success_buy = place_order_with_sltp(symbol, 'buy', 0.01, 20, 30)

    time.sleep(2)

    # Тест 2: SELL ордер с SL/TP
    print(f"\n🔹 Тест 2: SELL ордер с SL/TP (0.01 лот, SL=20, TP=30)")
    success_sell = place_order_with_sltp(symbol, 'sell', 0.01, 20, 30)

    # Закрываем все ордера
    from core.mt5_client import close_all_orders
    print(f"\n🛑 Закрываем все тестовые ордера...")
    close_success = close_all_orders(symbol)

    print(f"\n📊 Результаты ордеров с SL/TP:")
    print(f"   ✅ BUY: {'Успешно' if success_buy else 'Ошибка'}")
    print(f"   ✅ SELL: {'Успешно' if success_sell else 'Ошибка'}")
    print(f"   ✅ Закрытие: {'Успешно' if close_success else 'Ошибка'}")

    return success_buy or success_sell


def check_mt5_version():
    """
    Проверка версии MT5
    """
    print(f"\n🔍 Проверка версии MT5")
    print("=" * 50)

    try:
        version = mt5.version()
        print(f"✅ Версия MT5: {version}")

        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"✅ Терминал: {terminal_info.name}")
            print(f"✅ Путь: {terminal_info.path}")
            print(f"✅ Данные: {terminal_info.data_path}")
            print(f"✅ Коммунити: {terminal_info.community_account}")
            print(f"✅ Коммунити соединение: {terminal_info.community_connection}")

        return True
    except Exception as e:
        print(f"❌ Ошибка проверки версии: {e}")
        return False


def main():
    """
    Главная функция диагностики
    """
    import argparse

    parser = argparse.ArgumentParser(description='Диагностика проблем с торговлей AI Trading Robot')
    parser.add_argument('symbol', nargs='?', default='EURUSDrfd', help='Символ для диагностики')

    args = parser.parse_args()

    print("🤖 AI Trading Robot - Диагностика торговли")
    print("=" * 60)

    # Запускаем диагностику
    success = True

    # 1. Проверяем версию MT5
    success &= check_mt5_version()

    # 2. Диагностируем счет
    success &= diagnose_account()

    # 3. Диагностируем символ
    success &= diagnose_symbol(args.symbol)

    # 4. Тестируем простые ордера
    simple_success = test_simple_orders(args.symbol)

    # 5. Тестируем ордера с SL/TP (только если простые работают)
    if simple_success:
        sltp_success = test_sltp_orders(args.symbol)
    else:
        print(f"\n⚠️ Пропускаем тест SL/TP из-за ошибок простых ордеров")
        sltp_success = False

    print(f"\n🎯 Итоги диагностики:")
    print(f"   ✅ Базовая диагностика: {'Успешно' if success else 'С ошибками'}")
    print(f"   ✅ Простые ордера: {'Успешно' if simple_success else 'Ошибка'}")
    print(f"   ✅ Ордера с SL/TP: {'Успешно' if sltp_success else 'Ошибка'}")

    if simple_success:
        print(f"\n💡 Рекомендация: Используйте простые ордера (без SL/TP) для торговли")
    else:
        print(f"\n💡 Проблема: Не удается разместить даже простые ордера")
        print(f"   🔧 Возможные причины:")
        print(f"   - Демо-счет не разрешает торговлю")
        print(f"   - Проблемы с подключением к брокеру")
        print(f"   - Ограничения на счете")

    return simple_success


if __name__ == "__main__":
    success = main()

    if success:
        print(f"\n✅ Диагностика завершена успешно")
        print(f"💡 Теперь можно запустить торговлю: python main.py --mode trade")
    else:
        print(f"\n❌ Диагностика выявила проблемы")
        sys.exit(1)
