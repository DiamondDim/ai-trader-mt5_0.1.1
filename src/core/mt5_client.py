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
            'point': getattr(symbol_info, 'point', 0.00001),
            'trade_stops_level': getattr(symbol_info, 'trade_stops_level', 0),
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


def place_order(symbol, order_type, lot_size, stop_loss=0.0, take_profit=0.0, max_retries=3):
    """
    Размещение ордера с обработкой ошибок и повторными попытками
    """
    if not HAS_MT5:
        return False

    for attempt in range(max_retries):
        try:
            # Получаем текущую цену
            bid, ask = get_current_price(symbol)
            if bid is None or ask is None:
                print(f"❌ Не удалось получить текущие цены для {symbol}")
                time.sleep(1)
                continue

            # Получаем информацию о символе для проверки минимальных расстояний
            symbol_info = get_symbol_info(symbol)
            if not symbol_info:
                print(f"❌ Не удалось получить информацию о символе {symbol}")
                return False

            # Определяем параметры ордера
            if order_type == 'buy':
                price = ask
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                # Для BUY: SL ниже цены, TP выше цены
                sl = price - stop_loss if stop_loss > 0 else 0
                tp = price + take_profit if take_profit > 0 else 0
            else:  # sell
                price = bid
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                # Для SELL: SL выше цены, TP ниже цены
                sl = price + stop_loss if stop_loss > 0 else 0
                tp = price - take_profit if take_profit > 0 else 0

            # Проверяем минимальные расстояния для стоп-лосса и тейк-профита
            point = symbol_info.get('point', 0.00001)
            stops_level = symbol_info.get('trade_stops_level', 10)  # Минимальное расстояние в пунктах

            if stop_loss > 0:
                min_sl_distance = stops_level * point
                if order_type == 'buy' and (price - sl) < min_sl_distance:
                    print(f"⚠️ Стоп-лосс слишком близко к цене. Корректируем...")
                    sl = price - min_sl_distance * 2  # Устанавливаем в 2 раза дальше минимума
                elif order_type == 'sell' and (sl - price) < min_sl_distance:
                    sl = price + min_sl_distance * 2

            if take_profit > 0:
                min_tp_distance = stops_level * point
                if order_type == 'buy' and (tp - price) < min_tp_distance:
                    print(f"⚠️ Тейк-профит слишком близко к цене. Корректируем...")
                    tp = price + min_tp_distance * 2
                elif order_type == 'sell' and (price - tp) < min_tp_distance:
                    tp = price - min_tp_distance * 2

            # Подготавливаем запрос
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type_mt5,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,  # Увеличиваем отклонение
                "magic": 234000,
                "comment": f"AI Trader #{attempt + 1}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            print(f"🔧 Попытка {attempt + 1}: {order_type.upper()} {symbol} {lot_size} лотов")
            print(f"   💰 Цена: {price:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")

            # Отправляем ордер
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Ордер исполнен: {order_type.upper()} {symbol} {lot_size} лотов")
                print(f"   📊 Номер ордера: {result.order}")
                return True
            else:
                error_msg = get_error_description(result.retcode)
                print(f"❌ Ошибка ордера {symbol} (попытка {attempt + 1}): {result.retcode} - {error_msg}")

                # Если это ошибка цены, пробуем с новыми ценами
                if result.retcode in [10008, 10010, 10011, 10012, 10013, 10014, 10015, 10016, 10017, 10018, 10019,
                                      10020, 10021, 10022, 10023, 10024, 10025, 10026, 10027, 10028, 10029, 10030]:
                    print(f"🔄 Получаем новые цены и пробуем снова...")
                    time.sleep(1)
                    continue
                else:
                    # Для других ошибок не повторяем
                    break

        except Exception as e:
            print(f"❌ Исключение при размещении ордера для {symbol}: {e}")
            time.sleep(1)
            continue

    print(f"💥 Не удалось разместить ордер после {max_retries} попыток")
    return False


def get_error_description(error_code):
    """
    Получение описания ошибки MT5 по коду
    """
    error_descriptions = {
        10000: "TRADE_RETCODE_REQUOTE - Требуется перекотировка",
        10001: "TRADE_RETCODE_REJECT - Запрос отклонен",
        10002: "TRADE_RETCODE_CANCEL - Запрос отменен",
        10003: "TRADE_RETCODE_PLACED - Ордер размещен",
        10004: "TRADE_RETCODE_DONE - Сделка исполнена",
        10005: "TRADE_RETCODE_DONE_PARTIAL - Сделка исполнена частично",
        10006: "TRADE_RETCODE_ERROR - Ошибка обработки запроса",
        10007: "TRADE_RETCODE_TIMEOUT - Запрос отменен по таймауту",
        10008: "TRADE_RETCODE_INVALID - Неверный запрос",
        10009: "TRADE_RETCODE_INVALID_VOLUME - Неверный объем",
        10010: "TRADE_RETCODE_INVALID_PRICE - Неверная цена",
        10011: "TRADE_RETCODE_INVALID_STOPS - Неверные стопы",
        10012: "TRADE_RETCODE_TRADE_DISABLED - Торговля запрещена",
        10013: "TRADE_RETCODE_MARKET_CLOSED - Рынок закрыт",
        10014: "TRADE_RETCODE_NO_MONEY - Недостаточно средств",
        10015: "TRADE_RETCODE_PRICE_CHANGED - Цена изменилась",
        10016: "TRADE_RETCODE_PRICE_OFF - Нет котировок",
        10017: "TRADE_RETCODE_INVALID_EXPIRATION - Неверная дата экспирации",
        10018: "TRADE_RETCODE_ORDER_CHANGED - Ордер изменен",
        10019: "TRADE_RETCODE_TOO_MANY_REQUESTS - Слишком много запросов",
        10020: "TRADE_RETCODE_NO_CHANGES - Нет изменений",
        10021: "TRADE_RETCODE_SERVER_DISABLES_AT - Автотрейдинг запрещен сервером",
        10022: "TRADE_RETCODE_CLIENT_DISABLES_AT - Автотрейдинг запрещен клиентом",
        10023: "TRADE_RETCODE_LOCKED - Запрос заблокирован",
        10024: "TRADE_RETCODE_FROZEN - Ордер или позиция заморожены",
        10025: "TRADE_RETCODE_INVALID_FILL - Неверный тип исполнения",
        10026: "TRADE_RETCODE_CONNECTION - Нет соединения с торговым сервером",
        10027: "TRADE_RETCODE_ONLY_REAL - Разрешена только реальная торговля",
        10028: "TRADE_RETCODE_LIMIT_ORDERS - Достигнут лимит ордеров",
        10029: "TRADE_RETCODE_LIMIT_VOLUME - Достигнут лимит объема",
        10030: "TRADE_RETCODE_INVALID_ORDER - Неверный ордер",
        10031: "TRADE_RETCODE_POSITION_CLOSED - Позиция уже закрыта",
        10032: "TRADE_RETCODE_INVALID_CLOSE_VOLUME - Неверный объем для закрытия",
        10033: "TRADE_RETCODE_CLOSE_ORDER_EXIST - Уже есть ордер на закрытие",
        10034: "TRADE_RETCODE_LIMIT_POSITIONS - Достигнут лимит позиций",
    }

    return error_descriptions.get(error_code, f"Неизвестная ошибка: {error_code}")


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
                "deviation": 20,
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
                error_msg = get_error_description(result.retcode)
                print(f"❌ Ошибка закрытия ордера {order.ticket}: {result.retcode} - {error_msg}")

        print(f"📊 Закрыто ордеров: {closed_count}/{len(orders)}")
        return closed_count == len(orders)

    except Exception as e:
        print(f"❌ Ошибка при закрытии ордеров: {e}")
        return False
