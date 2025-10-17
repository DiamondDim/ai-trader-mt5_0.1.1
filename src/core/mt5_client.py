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

        # Проверяем информацию о счете
        account_info = mt5.account_info()
        if account_info:
            print(f"✅ Счет: {account_info.login}, Баланс: {account_info.balance:.2f}")
            print(f"💰 Валюта счета: {account_info.currency}")
            print(f"🔧 Торговый режим: {'Демо' if account_info.trade_mode == 1 else 'Реальный'}")
        else:
            print("⚠️ Не удалось получить информацию о счете")

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

        # Безопасное получение атрибутов
        info_dict = {
            'name': symbol_info.name,
            'bid': getattr(symbol_info, 'bid', 0),
            'ask': getattr(symbol_info, 'ask', 0),
            'spread': getattr(symbol_info, 'spread', 0),
            'digits': getattr(symbol_info, 'digits', 5),
            'trade_mode': getattr(symbol_info, 'trade_mode', 0),
            'point': getattr(symbol_info, 'point', 0.00001),
            'trade_stops_level': getattr(symbol_info, 'trade_stops_level', 0),
            'trade_contract_size': getattr(symbol_info, 'trade_contract_size', 100000),
            'currency_base': getattr(symbol_info, 'currency_base', ''),
            'currency_profit': getattr(symbol_info, 'currency_profit', ''),
            'currency_margin': getattr(symbol_info, 'currency_margin', ''),
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

        # Загрузка данных
        rates = mt5.copy_rates_from(symbol, timeframe_num, datetime.now(), bars_count)

        if rates is None or len(rates) == 0:
            print(f"❌ Не удалось загрузить данные для {symbol}")
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


def check_trading_allowed(symbol):
    """
    Проверяет, разрешена ли торговля для символа
    """
    if not HAS_MT5:
        return False

    try:
        # Проверяем информацию о символе
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Символ {symbol} не найден")
            return False

        # Проверяем, разрешена ли торговля
        if symbol_info.trade_mode != 0:  # 0 = SYMBOL_TRADE_MODE_DISABLED
            print(f"✅ Торговля разрешена для {symbol}")
            return True
        else:
            print(f"❌ Торговля запрещена для {symbol}")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки торговли для {symbol}: {e}")
        return False


def place_order_simple(symbol, order_type, lot_size):
    """
    Простое размещение ордера БЕЗ стоп-лосса и тейк-профита
    """
    if not HAS_MT5:
        return False

    try:
        # Проверяем, разрешена ли торговля
        if not check_trading_allowed(symbol):
            return False

        # Получаем текущую цену
        bid, ask = get_current_price(symbol)
        if bid is None or ask is None:
            print(f"❌ Не удалось получить текущие цены для {symbol}")
            return False

        # Определяем параметры ордера
        if order_type == 'buy':
            price = ask
            order_type_mt5 = mt5.ORDER_TYPE_BUY
        else:  # sell
            price = bid
            order_type_mt5 = mt5.ORDER_TYPE_SELL

        # Подготавливаем простой запрос БЕЗ SL/TP
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type_mt5,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Trader Simple",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        print(f"🔧 Отправка ордера: {order_type.upper()} {symbol} {lot_size} лотов")
        print(f"   💰 Цена: {price:.5f}")

        # Отправляем ордер
        result = mt5.order_send(request)

        # Проверяем, что результат не None
        if result is None:
            print(f"❌ MT5 вернул None при отправке ордера")
            print(f"💡 Проверьте подключение к MT5 и настройки счета")
            return False

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Ордер исполнен: {order_type.upper()} {symbol} {lot_size} лотов")
            print(f"   📊 Номер ордера: {result.order}")
            return True
        else:
            error_msg = get_error_description(result.retcode)
            print(f"❌ Ошибка ордера {symbol}: {result.retcode} - {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Исключение при размещении ордера для {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return False


def place_order_with_sltp(symbol, order_type, lot_size, stop_loss_pips, take_profit_pips):
    """
    Размещение ордера со стоп-лоссом и тейк-профитом (в пипсах)
    """
    if not HAS_MT5:
        return False

    try:
        # Проверяем, разрешена ли торговля
        if not check_trading_allowed(symbol):
            return False

        # Получаем текущую цену
        bid, ask = get_current_price(symbol)
        if bid is None or ask is None:
            print(f"❌ Не удалось получить текущие цены для {symbol}")
            return False

        # Получаем информацию о символе
        symbol_info = get_symbol_info(symbol)
        if not symbol_info:
            return False

        # Определяем параметры ордера
        if order_type == 'buy':
            price = ask
            order_type_mt5 = mt5.ORDER_TYPE_BUY
            # Для BUY: SL ниже цены, TP выше цены
            sl = price - (stop_loss_pips * 0.0001) if stop_loss_pips > 0 else 0
            tp = price + (take_profit_pips * 0.0001) if take_profit_pips > 0 else 0
        else:  # sell
            price = bid
            order_type_mt5 = mt5.ORDER_TYPE_SELL
            # Для SELL: SL выше цены, TP ниже цены
            sl = price + (stop_loss_pips * 0.0001) if stop_loss_pips > 0 else 0
            tp = price - (take_profit_pips * 0.0001) if take_profit_pips > 0 else 0

        # Подготавливаем запрос с SL/TP
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type_mt5,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Trader SL/TP",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        print(f"🔧 Отправка ордера: {order_type.upper()} {symbol} {lot_size} лотов")
        print(f"   💰 Цена: {price:.5f}, SL: {sl:.5f}, TP: {tp:.5f}")

        # Отправляем ордер
        result = mt5.order_send(request)

        # Проверяем, что результат не None
        if result is None:
            print(f"❌ MT5 вернул None при отправке ордера")
            return False

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Ордер исполнен: {order_type.upper()} {symbol} {lot_size} лотов")
            print(f"   📊 Номер ордера: {result.order}")
            return True
        else:
            error_msg = get_error_description(result.retcode)
            print(f"❌ Ошибка ордера {symbol}: {result.retcode} - {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Исключение при размещении ордера для {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return False


def place_order(symbol, order_type, lot_size, stop_loss=0.0, take_profit=0.0):
    """
    Универсальная функция размещения ордера
    """
    # Если указаны стоп-лосс и тейк-профит, используем функцию с SL/TP
    if stop_loss > 0 or take_profit > 0:
        # Конвертируем в пипсы (предполагаем, что stop_loss и take_profit в цене)
        stop_loss_pips = int(stop_loss / 0.0001) if stop_loss > 0 else 0
        take_profit_pips = int(take_profit / 0.0001) if take_profit > 0 else 0
        return place_order_with_sltp(symbol, order_type, lot_size, stop_loss_pips, take_profit_pips)
    else:
        # Используем простую функцию без SL/TP
        return place_order_simple(symbol, order_type, lot_size)


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
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                print(f"✅ Закрыт ордер {order.ticket} для {order.symbol}")
            else:
                error_msg = get_error_description(result.retcode) if result else "None result"
                print(f"❌ Ошибка закрытия ордера {order.ticket}: {error_msg}")

        print(f"📊 Закрыто ордеров: {closed_count}/{len(orders)}")
        return closed_count == len(orders)

    except Exception as e:
        print(f"❌ Ошибка при закрытии ордеров: {e}")
        return False
