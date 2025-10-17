#!/usr/bin/env python3
"""
AI Trading Robot v0.1.1
Главный управляющий скрипт с поддержкой множества символов
"""

import argparse
import sys
import os
import time
from datetime import datetime

# Добавляем путь к src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Проверяем наличие MetaTrader5
try:
    import MetaTrader5 as mt5

    HAS_MT5 = True
except ImportError as e:
    print(f"❌ MetaTrader5 не установлен: {e}")
    print("💡 Установите: pip install MetaTrader5")
    HAS_MT5 = False

try:
    from utils.config import load_config
    from core.trader import Trader
    from core.mt5_client import initialize_mt5, close_all_orders, get_symbol_info, get_available_symbols
    from ml.model_builder import train_model, load_model_for_symbol, get_available_models
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Проверьте структуру папок и наличие необходимых файлов")
    sys.exit(1)

# Импортируем symbol_selector отдельно, так как он в корне
try:
    sys.path.append(current_dir)
    from symbol_selector import SymbolSelector
except ImportError as e:
    print(f"❌ Ошибка импорта SymbolSelector: {e}")
    SymbolSelector = None


def test_connection():
    """Тестирование подключения к MT5"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    print("🔍 Тестирование подключения к MT5...")

    if not initialize_mt5():
        print("❌ Подключение к MT5 не удалось")
        return False

    # Проверяем доступные символы
    symbols = get_available_symbols()

    print(f"✅ Подключение к MT5 успешно")
    print(f"📊 Доступно основных пар: {len(symbols)}")
    if symbols:
        print("📈 Примеры доступных пар:", symbols[:5])

    return True


def train_mode(symbol=None):
    """Режим обучения модели"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    config = load_config()

    # Определяем символ для обучения
    training_symbol = symbol or config['trading']['symbol']

    print(f"🎯 Режим обучения для символа: {training_symbol}")

    # Проверяем подключение
    if not initialize_mt5():
        return False

    # Проверяем доступность символа
    symbol_info = get_symbol_info(training_symbol)
    if not symbol_info:
        print(f"❌ Символ {training_symbol} недоступен")
        return False

    print(f"✅ Символ {training_symbol} доступен для торговли")
    print(f"   Bid: {symbol_info['bid']:.5f}, Ask: {symbol_info['ask']:.5f}, Spread: {symbol_info['spread']:.5f}")

    # Запускаем обучение
    return train_model(training_symbol)


def trade_mode(symbol=None):
    """Режим торговли"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    config = load_config()

    # Определяем символ для торговли
    trading_symbol = symbol or config['trading']['symbol']

    print(f"🚀 Запуск режима торговли для символа: {trading_symbol}")

    # Проверяем подключение
    if not initialize_mt5():
        return False

    # Проверяем наличие модели
    model = load_model_for_symbol(trading_symbol)
    if not model:
        print(f"❌ Модель для {trading_symbol} не найдена")
        print(f"💡 Выполните обучение: python main.py --mode train --symbol {trading_symbol}")
        return False

    # Проверяем доступность символа
    symbol_info = get_symbol_info(trading_symbol)
    if not symbol_info:
        print(f"❌ Символ {trading_symbol} недоступен")
        return False

    print(f"✅ Символ {trading_symbol} доступен")
    print(f"💰 Текущая цена: Bid={symbol_info['bid']:.5f}, Ask={symbol_info['ask']:.5f}")

    # Запускаем торговлю
    try:
        trader = Trader(config)
        trader.trade_loop()
        return True
    except KeyboardInterrupt:
        print("\n⏹️ Торговля остановлена пользователем")
        return True
    except Exception as e:
        print(f"❌ Ошибка в торговом режиме: {e}")
        import traceback
        traceback.print_exc()
        return False


def status_mode():
    """Режим статуса системы"""
    config = load_config()

    print("\n" + "=" * 60)
    print("           СТАТУС AI TRADING ROBOT")
    print("=" * 60)

    # Статус MT5
    print("\n🔌 Подключение MT5:")
    if HAS_MT5 and initialize_mt5():
        print("   ✅ Подключено")

        # Информация о текущем символе
        current_symbol = config['trading']['symbol']
        symbol_info = get_symbol_info(current_symbol)
        if symbol_info:
            print(f"   📊 Текущий символ: {current_symbol}")
            print(f"   💰 Цена: Bid={symbol_info['bid']:.5f}, Ask={symbol_info['ask']:.5f}")
            print(f"   📏 Спред: {symbol_info['spread']:.5f}")
        else:
            print(f"   ❌ Символ {current_symbol} недоступен")
    else:
        print("   ❌ Не подключено (MetaTrader5 не установлен или недоступен)")

    # Статус модели
    print("\n🤖 ML Модель:")
    model_info = config['model']
    current_model_path = model_info.get('current_model', '')
    if current_model_path and os.path.exists(current_model_path):
        print(f"   ✅ Модель: {os.path.basename(current_model_path)}")
        print(f"   🎯 Точность: {model_info.get('accuracy', 'N/A')}")
        print(f"   🔧 Признаков: {model_info.get('features_count', 'N/A')}")
        print(f"   📅 Обучена: {model_info.get('last_trained', 'N/A')}")
    else:
        print("   ❌ Модель не обучена или файл не найден")

    # Доступные модели
    print("\n📚 Доступные модели:")
    models = get_available_models()
    if models:
        for i, model in enumerate(models[:5], 1):  # Показываем первые 5
            print(f"   {i}. {model['symbol']} - {model['date']}")
        if len(models) > 5:
            print(f"   ... и еще {len(models) - 5} моделей")
    else:
        print("   ❌ Нет доступных моделей")

    # Настройки торговли
    print("\n⚙️ Настройки торговли:")
    trading_config = config['trading']
    print(f"   📈 Символ: {trading_config['symbol']}")
    print(f"   📦 Лот: {trading_config['lot_size']}")
    print(f"   📏 Макс. спред: {trading_config['max_spread']}")

    print("\n" + "=" * 60)

    return True


def select_symbol_mode(auto_train=True):
    """Режим выбора символа"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    if SymbolSelector is None:
        print("❌ SymbolSelector не доступен")
        return False

    try:
        selector = SymbolSelector()
        return selector.run_selection_flow(auto_train=auto_train)
    except Exception as e:
        print(f"❌ Ошибка в режиме выбора символа: {e}")
        import traceback
        traceback.print_exc()
        return False


def stop_mode(symbol=None):
    """Режим остановки торговли"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    print("🛑 Остановка торговли...")

    if not initialize_mt5():
        return False

    success = close_all_orders(symbol)

    if success:
        print("✅ Все ордера закрыты")
    else:
        print("❌ Не удалось закрыть все ордера")

    return success


def emergency_stop_mode():
    """Аварийная остановка"""
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    print("🚨 АВАРИЙНАЯ ОСТАНОВКА!")

    if not initialize_mt5():
        return False

    success = close_all_orders()

    if success:
        print("✅ Аварийная остановка выполнена")
    else:
        print("❌ Ошибка при аварийной остановке")

    return success


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='AI Trading Robot v0.1.1')
    parser.add_argument('--mode', type=str, required=True,
                        choices=['test', 'train', 'trade', 'status', 'stop',
                                 'emergency-stop', 'select-symbol'],
                        help='Режим работы')
    parser.add_argument('--symbol', type=str, help='Торговый символ (например, EURUSD)')
    parser.add_argument('--no-train', action='store_true',
                        help='Пропустить автообучение при выборе символа')

    args = parser.parse_args()

    print(f"\n🤖 AI Trading Robot v0.1.1")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎮 Режим: {args.mode}")

    # Проверяем наличие MT5 для режимов, которые его требуют
    mt5_required_modes = ['test', 'train', 'trade', 'select-symbol', 'stop', 'emergency-stop']
    if args.mode in mt5_required_modes and not HAS_MT5:
        print(f"❌ Режим '{args.mode}' требует установки MetaTrader5")
        print("💡 Установите: pip install MetaTrader5")
        return False

    try:
        if args.mode == 'test':
            success = test_connection()
        elif args.mode == 'train':
            success = train_mode(args.symbol)
        elif args.mode == 'trade':
            success = trade_mode(args.symbol)
        elif args.mode == 'status':
            success = status_mode()
        elif args.mode == 'select-symbol':
            success = select_symbol_mode(auto_train=not args.no_train)
        elif args.mode == 'stop':
            success = stop_mode(args.symbol)
        elif args.mode == 'emergency-stop':
            success = emergency_stop_mode()
        else:
            print(f"❌ Неизвестный режим: {args.mode}")
            success = False

        if success:
            print(f"\n✅ Режим '{args.mode}' завершен успешно")
        else:
            print(f"\n❌ Режим '{args.mode}' завершен с ошибками")

        return success

    except KeyboardInterrupt:
        print(f"\n⏹️ Программа прервана пользователем")
        return False
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
