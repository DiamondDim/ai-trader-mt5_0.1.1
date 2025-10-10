#!/usr/bin/env python3
"""
Тестовый скрипт для диагностики проблем с ордерами
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from src.core.mt5_client import MT5Client
from src.utils.config import Config
import MetaTrader5 as mt5


def test_symbol_info(symbol: str):
    """Тестирование информации о символе"""
    config = Config.load_config()
    client = MT5Client(config)

    if not client.connect():
        return

    try:
        print(f"🔍 Тестирование символа: {symbol}")

        # Получаем информацию о символе
        symbol_info = client.get_symbol_info(symbol)
        if symbol_info:
            print("✅ Информация о символе:")
            for key, value in symbol_info.items():
                print(f"   {key}: {value}")

        # Пробуем разместить тестовый ордер без SL/TP
        print(f"\n🧪 Тестовый ордер без SL/TP:")
        success = client.place_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_BUY,
            volume=0.01,
            price=0,  # 0 означает использование текущей цены
            stop_loss=0,
            take_profit=0
        )

        if success:
            print("✅ Ордер без SL/TP успешен!")
        else:
            print("❌ Ордер без SL/TP не удался")

        # Пробуем разместить тестовый ордер с SL/TP
        print(f"\n🧪 Тестовый ордер с SL/TP:")
        success = client.place_order(
            symbol=symbol,
            order_type=mt5.ORDER_TYPE_BUY,
            volume=0.01,
            price=0,
            stop_loss=1.15000,  # Далекий SL
            take_profit=1.17000  # Далекий TP
        )

        if success:
            print("✅ Ордер с SL/TP успешен!")
        else:
            print("❌ Ордер с SL/TP не удался")

    except Exception as e:
        print(f"❌ Исключение при тестировании: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = "EURUSDrfd"

    test_symbol_info(symbol)
