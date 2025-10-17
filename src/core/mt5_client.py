import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time


def initialize_mt5():
    """
    Инициализация подключения к MT5
    """
    if not mt5.initialize():
        print("❌ Ошибка инициализации MT5, код ошибки:", mt5.last_error())
        return False

    # Проверяем подключение к серверу
    if not mt5.terminal_info():
        print("❌ Не удалось подключиться к торговому серверу")
        return False

    print("✅ MetaTrader5 успешно инициализирован")
    return True


def get_available_symbols():
    """
    Получает список основных валютных пар из MT5
    """
    try:
        symbols = mt5.symbols_get()
        symbol_names = [s.name for s in symbols]

        # Основные forex пары
        forex_majors = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
            'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP',
            'EURJPY', 'EURCHF', 'GBPJPY', 'AUDJPY'
        ]

        # Ищем доступные основные пары
        available_majors = [s for s in symbol_names if s in forex_majors]

        # Также добавляем популярные пары с постфиксами
        for symbol in symbol_names:
            if any(major in symbol for major in forex_majors) and symbol not in available_majors:
                # Проверяем, что это действительно forex пара
                if any(postfix in symbol for postfix in ['', 'rfd', 'micro', 'mini']):
                    available_majors.append(symbol)

        # Сортируем для удобства
        available_majors.sort()
        return available_majors

    except Exception as e:
        print(f"❌ Ошибка при получении списка символов: {e}")
        return []


def get_all_symbols():
    """
    Получает все символы без фильтрации
    """
    try:
        symbols = mt5.symbols_get()
        symbol_names = [s.name for s in symbols]
        return symbol_names
    except Exception as e:
        print(f"❌ Ошибка при получении списка символов: {e}")
        return []


def get_symbol_info(symbol):
    """
    Получает информацию о конкретном символе
    """
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Символ {symbol} не найден")
            return None

        return {
            'name': symbol_info.name,
            'bid': symbol_info.bid,
            'ask': symbol_info.ask,
            'spread': symbol_info.ask - symbol_info.bid,
            'digits': symbol_info.digits,
            'trade_mode': symbol_info.trade_mode,
            'trade_allowed': symbol_info.trade_allowed
        }
    except Exception as e:
        print(f"❌ Ошибка получения информации о символе {symbol}: {e}")
        return None


def load_data(symbol, timeframe=mt5.TIMEFRAME_M15, bars_count=2000):
    """
    Загрузка исторических данных для указанного символа
    """
    try:
        # Проверяем, что символ доступен
        if not mt5.symbol_select(symbol, True):
            print(f"❌ Символ {symbol} не доступен для торговли")
            return pd.DataFrame()

        # Получаем текущее время
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)  # Загружаем данные за 30 дней

        # Загружаем бары
        rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)

        if rates is None or len(rates) == 0:
            print(f"❌ Не удалось загрузить данные для {symbol}")
            return pd.DataFrame()

        # Конвертируем в DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        print(f"✅ Загружено {len(df)} баров для {symbol}")
        return df

    except Exception as e:
        print(f"❌ Ошибка загрузки данных для {symbol}: {e}")
        return pd.DataFrame()


def get_current_price(symbol):
    """
    Получает текущую цену для символа
    """
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None, None

        return tick.bid, tick.ask
    except Exception as e:
        print(f"❌ Ошибка получения цены для {symbol}: {e}")
        return None, None


def place_order(symbol, order_type, lot_size, stop_loss=0.0, take_profit=0.0):
    """
    Размещение ордера
    """
    try:
        # Получаем текущую цену
        bid, ask = get_current_price(symbol)
        if bid is None or ask is None:
            return False

        # Определяем параметры ордера
        if order_type == 'buy':
            price = ask
            order_type_mt5 = mt5.ORDER_TYPE_BUY
            sl = price - stop_loss if stop_loss > 0 else 0
            tp = price + take_profit if take_profit > 0 else 0
        else:  # sell
            price = bid
            order_type_mt5 = mt5.ORDER_TYPE_SELL
            sl = price + stop_loss if stop_loss > 0 else 0
            tp = price - take_profit if take_profit > 0 else 0

        # Подготавливаем запрос
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type_mt5,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": "AI Trader",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Отправляем ордер
        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Ошибка ордера {symbol}: {result.retcode}")
            return False

        print(f"✅ Ордер исполнен: {order_type.upper()} {symbol} {lot_size} лотов")
        return True

    except Exception as e:
        print(f"❌ Ошибка размещения ордера для {symbol}: {e}")
        return False


def close_all_orders(symbol=None):
    """
    Закрытие всех ордеров (для указанного символа или всех)
    """
    try:
        orders = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()

        if orders is None:
            print("✅ Нет открытых ордеров для закрытия")
            return True

        closed_count = 0
        for order in orders:
            # Определяем тип закрывающей сделки
            close_type = mt5.ORDER_TYPE_SELL if order.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": order.ticket,
                "symbol": order.symbol,
                "volume": order.volume,
                "type": close_type,
                "price": mt5.symbol_info_tick(
                    order.symbol).bid if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(order.symbol).ask,
                "deviation": 10,
                "magic": 234000,
                "comment": "Close AI",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                print(f"✅ Закрыт ордер {order.ticket} для {order.symbol}")
            else:
                print(f"❌ Ошибка закрытия ордера {order.ticket}: {result.retcode}")

        print(f"📊 Закрыто ордеров: {closed_count}/{len(orders)}")
        return closed_count == len(orders)

    except Exception as e:
        print(f"❌ Ошибка при закрытии ордеров: {e}")
        return False
