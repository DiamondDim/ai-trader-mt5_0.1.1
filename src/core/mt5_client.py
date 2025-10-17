import pandas as pd
from datetime import datetime, timedelta
import time

# Проверяем наличие MetaTrader5
try:
    import MetaTrader5 as mt5

    HAS_MT5 = True
except ImportError:
    print("❌ MetaTrader5 не установлен. Установите: pip install MetaTrader5")
    HAS_MT5 = False


def initialize_mt5():
    """
    Инициализация подключения к MT5
    """
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return False

    try:
        if not mt5.initialize():
            print("❌ Ошибка инициализации MT5, код ошибки:", mt5.last_error())
            return False

        # Проверяем подключение к серверу
        if not mt5.terminal_info():
            print("❌ Не удалось подключиться к торговому серверу")
            return False

        print("✅ MetaTrader5 успешно инициализирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации MT5: {e}")
        return False


def get_available_symbols():
    """
    Получает список основных валютных пар из MT5
    """
    if not HAS_MT5:
        print("❌ MetaTrader5 не установлен")
        return []

    try:
        symbols = mt5.symbols_get()
        if symbols is None:
            print("❌ Не удалось получить список символов из MT5")
            return []

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
    if not HAS_MT5:
        return []

    try:
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        symbol_names = [s.name for s in symbols]
        return symbol_names
    except Exception as e:
        print(f"❌ Ошибка при получении списка символов: {e}")
        return []


def get_symbol_info(symbol):
    """
    Получает информацию о конкретном символе
    """
    if not HAS_MT5:
        return None

    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Символ {symbol} не найден")
            return None

        # Безопасное получение атрибутов (некоторые могут отсутствовать в разных версиях MT5)
        info_dict = {
            'name': symbol_info.name,
            'bid': getattr(symbol_info, 'bid', 0),
            'ask': getattr(symbol_info, 'ask', 0),
            'spread': getattr(symbol_info, 'spread', 0),
            'digits': getattr(symbol_info, 'digits', 5),
            'trade_mode': getattr(symbol_info, 'trade_mode', 0),
        }

        # Вычисляем спред, если он не доступен напрямую
        if info_dict['spread'] == 0 and info_dict['ask'] > 0 and info_dict['bid'] > 0:
            info_dict['spread'] = info_dict['ask'] - info_dict['bid']

        # Проверяем доступность торговли
        trade_mode = info_dict['trade_mode']
        info_dict['trade_allowed'] = trade_mode != 0  # 0 = SYMBOL_TRADE_MODE_DISABLED

        return info_dict

    except Exception as e:
        print(f"❌ Ошибка получения информации о символе {symbol}: {e}")
        return None


def load_data(symbol, timeframe="M15", bars_count=2000, timeframe_str=None):
    """
    Загрузка исторических данных для указанного символа
    Обратная совместимость: поддерживает оба параметра timeframe и timeframe_str
    """
    if not HAS_MT5:
        return pd.DataFrame()

    try:
        # Обратная совместимость: если передан timeframe_str, используем его
        if timeframe_str is not None:
            timeframe = timeframe_str

        # Конвертируем строковый таймфрейм в числовой
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }

        timeframe_num = timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)

        # Проверяем, что символ доступен
        if not mt5.symbol_select(symbol, True):
            print(f"❌ Символ {symbol} не доступен для торговли")
            return pd.DataFrame()

        print(f"🔍 Загрузка данных для {symbol} (таймфрейм: {timeframe}, баров: {bars_count})")

        # Пробуем разные методы загрузки данных

        # Метод 1: Загрузка по количеству баров (более надежный)
        rates = mt5.copy_rates_from(symbol, timeframe_num, datetime.now(), bars_count)

        if rates is None or len(rates) == 0:
            print(f"⚠️ Метод 1 не сработал, пробуем метод 2...")
            # Метод 2: Загрузка за последние 30 дней
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)
            rates = mt5.copy_rates_range(symbol, timeframe_num, start_time, end_time)

        if rates is None or len(rates) == 0:
            print(f"⚠️ Метод 2 не сработал, пробуем метод 3...")
            # Метод 3: Загрузка с начала года
            start_time = datetime(datetime.now().year, 1, 1)
            rates = mt5.copy_rates_range(symbol, timeframe_num, start_time, datetime.now())

        if rates is None or len(rates) == 0:
            print(f"❌ Все методы загрузки данных для {symbol} не сработали")
            print(f"💡 Проверьте доступность исторических данных в MT5")
            return pd.DataFrame()

        # Конвертируем в DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        print(f"✅ Загружено {len(df)} баров для {symbol}")
        print(f"📅 Период данных: {df.index[0]} - {df.index[-1]}")

        return df

    except Exception as e:
        print(f"❌ Ошибка загрузки данных для {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_current_price(symbol):
    """
    Получает текущую цену для символа
    """
    if not HAS_MT5:
        return None, None

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
    if not HAS_MT5:
        return False

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
    if not HAS_MT5:
        return False

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
