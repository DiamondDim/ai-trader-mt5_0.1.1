#!/usr/bin/env python3
"""
AI Trading Robot for MetaTrader 5
Главный управляющий скрипт
"""

import argparse
import sys
import os
import signal
import time
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from src.core.mt5_client import MT5Client  # ИСПРАВЛЕНО: импорт из mt5_client.py
from src.core.trader import Trader
from src.ml.model_builder import ModelBuilder
from src.ml.feature_engineer import FeatureEngineer
from src.utils.risk_manager import RiskManager
from src.utils.config import Config

# Глобальные переменные для управления роботом
trader_instance = None
mt5_client = None


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    print(f"\n🛑 Получен сигнал {signum}. Останавливаем робота...")
    if trader_instance:
        trader_instance.stop_trading()
    if mt5_client:
        mt5_client.disconnect()
    sys.exit(0)


def setup_signal_handlers():
    """Настройка обработчиков сигналов"""
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command


def train_model(config, symbol):
    """Режим обучения модели"""
    print("🤖 Режим обучения модели...")

    client = MT5Client(config)  # ИСПРАВЛЕНО: используем MT5Client
    if not client.connect():
        print("❌ Не удалось подключиться к MT5")
        return False

    try:
        # Загрузка данных
        print(f"📊 Загрузка данных для {symbol}...")
        data = client.get_historical_data(symbol, bars=1000)
        if data is None or data.empty:
            print("❌ Не удалось загрузить данные")
            return False

        # Создание и обучение модели
        model_builder = ModelBuilder(config)
        feature_engineer = FeatureEngineer(config)

        print("🎯 Обучение модели...")
        model_path = model_builder.train_model(data, symbol, feature_engineer)

        if model_path:
            print(f"✅ Модель обучена и сохранена: {model_path}")
            return True
        else:
            print("❌ Ошибка обучения модели")
            return False

    finally:
        client.disconnect()


def trade_mode(config, symbol):
    """Режим торговли"""
    global trader_instance, mt5_client

    print("💰 Запуск торгового режима...")

    # Подключение к MT5
    mt5_client = MT5Client(config)  # ИСПРАВЛЕНО: используем MT5Client
    if not mt5_client.connect():
        print("❌ Не удалось подключиться к MT5")
        return False

    try:
        # Загрузка модели
        model_builder = ModelBuilder(config)
        feature_engineer = FeatureEngineer(config)

        model = model_builder.load_model()
        if model is None:
            print("❌ Не удалось загрузить модель. Сначала обучите модель.")
            return False

        # Создание менеджера рисков и трейдера
        risk_manager = RiskManager(config)
        trader_instance = Trader(config, mt5_client, risk_manager)

        print("🚀 Запуск автоматической торговли...")
        print("💡 Для остановки нажмите Ctrl+C")

        # Запуск торговли
        success = trader_instance.start_trading(symbol, model, feature_engineer)

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в торговом режиме: {e}")
        return False
    finally:
        if mt5_client:
            mt5_client.disconnect()


def status_mode(config):
    """Режим статуса"""
    global trader_instance, mt5_client

    print("📊 Получение статуса робота...")

    mt5_client = MT5Client(config)  # ИСПРАВЛЕНО: используем MT5Client
    if not mt5_client.connect():
        print("❌ Не удалось подключиться к MT5")
        return False

    try:
        # Если трейдер запущен, получаем его статус
        if trader_instance:
            status = trader_instance.get_trading_status()
        else:
            # Иначе базовый статус
            positions = mt5_client.get_open_positions()
            status = {
                'is_trading': False,
                'stop_requested': False,
                'current_symbol': None,
                'open_positions_count': len(positions),
                'open_positions': []
            }

            for pos in positions:
                status['open_positions'].append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp
                })

        # Вывод статуса
        print("\n" + "=" * 50)
        print("🤖 СТАТУС AI TRADING ROBOT")
        print("=" * 50)
        print(f"📈 Торговля активна: {'✅ ДА' if status['is_trading'] else '❌ НЕТ'}")
        print(f"🛑 Остановка запрошена: {'✅ ДА' if status['stop_requested'] else '❌ НЕТ'}")
        print(f"🎯 Текущий символ: {status['current_symbol'] or 'Нет'}")
        print(f"📊 Открыто позиций: {status['open_positions_count']}")

        if status['open_positions']:
            print("\n💼 ОТКРЫТЫЕ ПОЗИЦИИ:")
            for pos in status['open_positions']:
                profit_color = "🟢" if pos['profit'] >= 0 else "🔴"
                print(f"   {pos['ticket']} | {pos['symbol']} | {pos['type']} | "
                      f"Объем: {pos['volume']} | Цена: {pos['open_price']:.5f} | "
                      f"Прибыль: {profit_color} {pos['profit']:.2f}")

        print("=" * 50)
        return True

    finally:
        mt5_client.disconnect()


def stop_mode(config):
    """Режим остановки"""
    global trader_instance, mt5_client

    print("🛑 Запрос остановки торговли...")

    if trader_instance:
        trader_instance.stop_trading()
        print("✅ Команда остановки отправлена")
        return True
    else:
        print("⚠️ Трейдер не запущен")
        return False


def emergency_stop_mode(config):
    """Режим аварийной остановки"""
    global trader_instance, mt5_client

    print("🚨 АВАРИЙНАЯ ОСТАНОВКА!")

    mt5_client = MT5Client(config)  # ИСПРАВЛЕНО: используем MT5Client
    if not mt5_client.connect():
        print("❌ Не удалось подключиться к MT5")
        return False

    try:
        if trader_instance:
            success = trader_instance.emergency_stop()
            if success:
                print("✅ Аварийная остановка выполнена")
            else:
                print("⚠️ Аварийная остановка выполнена с ошибками")
            return success
        else:
            # Если трейдер не запущен, просто закрываем все позиции
            print("🔻 Закрытие всех открытых позиций...")
            success = mt5_client.close_all_positions()
            if success:
                print("✅ Все позиции закрыты")
            else:
                print("⚠️ Не все позиции удалось закрыть")
            return success

    finally:
        mt5_client.disconnect()


def test_connection(config):
    """Тестирование подключения"""
    print("🧪 Тестирование подключения к MT5...")

    client = MT5Client(config)  # ИСПРАВЛЕНО: используем MT5Client
    if client.connect():
        print("✅ Подключение успешно")

        # Тестируем базовые функции
        symbol = config.get('trading', {}).get('symbol', 'EURUSDrfd')
        print(f"🔍 Тестирование символа {symbol}...")

        symbol_info = client.get_symbol_info(symbol)
        if symbol_info:
            print("✅ Информация о символе:")
            print(f"   Bid: {symbol_info['bid']:.5f}")
            print(f"   Ask: {symbol_info['ask']:.5f}")
            print(f"   Point: {symbol_info['point']}")
            print(f"   Stops Level: {symbol_info['trade_stops_level']}")
        else:
            print("❌ Не удалось получить информацию о символе")

        client.disconnect()
        return True
    else:
        print("❌ Ошибка подключения")
        return False


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='AI Trading Robot for MetaTrader 5')
    parser.add_argument('--mode', choices=['train', 'trade', 'status', 'stop', 'emergency-stop', 'test'],
                        required=True, help='Режим работы')
    parser.add_argument('--symbol', help='Торговый символ (например: EURUSDrfd)')
    parser.add_argument('--config', help='Путь к файлу конфигурации')

    args = parser.parse_args()

    # Загрузка конфигурации
    if args.config:
        config = Config.load_config(args.config)
    else:
        config = Config.load_config()

    if config is None:
        print("❌ Не удалось загрузить конфигурацию")
        return

    # Настройка обработчиков сигналов
    setup_signal_handlers()

    # Определение символа
    symbol = args.symbol or config.get('trading', {}).get('symbol', 'EURUSDrfd')

    # Выполнение выбранного режима
    try:
        if args.mode == 'train':
            train_model(config, symbol)
        elif args.mode == 'trade':
            trade_mode(config, symbol)
        elif args.mode == 'status':
            status_mode(config)
        elif args.mode == 'stop':
            stop_mode(config)
        elif args.mode == 'emergency-stop':
            emergency_stop_mode(config)
        elif args.mode == 'test':
            test_connection(config)

    except KeyboardInterrupt:
        print("\n🛑 Программа остановлена пользователем")
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
