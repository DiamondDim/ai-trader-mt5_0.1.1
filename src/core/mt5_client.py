import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime
import time


class MT5Client:
    """Исправленная версия MT5 клиента с решением ошибки 10030"""

    def __init__(self, config: Dict):
        self.config = config
        self.connected = False

    def connect(self) -> bool:
        """Подключение к MT5"""
        mt5_config = self.config.get('mt5', {})

        print("🔌 Попытка подключения к MT5...")

        # Принудительно отключаем предыдущее подключение
        mt5.shutdown()

        try:
            if not mt5.initialize(
                    path=mt5_config.get('path', ""),
                    server=mt5_config.get('server', ""),
                    login=mt5_config.get('login', 0),
                    password=mt5_config.get('password', ""),
                    timeout=mt5_config.get('timeout', 60000)
            ):
                error = mt5.last_error()
                print(f"❌ Ошибка инициализации MT5: {error}")
                return False

            self.connected = True

            # Проверяем реальное подключение
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Не удалось получить информацию о счете")
                mt5.shutdown()
                self.connected = False
                return False

            print("✅ Подключено к MT5")
            print(f"   Счет: {account_info.login}")
            print(f"   Сервер: {account_info.server}")
            print(f"   Валюта: {account_info.currency}")
            print(f"   Баланс: {account_info.balance}")

            return True

        except Exception as e:
            print(f"❌ Исключение при подключении к MT5: {e}")
            return False

    def get_historical_data(self, symbol: str, bars: int = 1000) -> pd.DataFrame:
        """Получение исторических данных"""
        if not self.connected:
            print("❌ Не подключено к MT5")
            return None

        timeframe_str = self.config.get('trading', {}).get('timeframe', 'M15')
        timeframe_mapping = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        timeframe = timeframe_mapping.get(timeframe_str, mt5.TIMEFRAME_M15)

        print(f"📊 Загрузка данных для {symbol} ({bars} баров)")

        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

            if rates is None:
                print(f"❌ Не удалось получить данные для {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'tick_volume',
                'spread': 'spread',
                'real_volume': 'volume'
            }, inplace=True)

            print(f"✅ Загружено {len(df)} баров для {symbol}")
            return df

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return None

    def get_current_data(self, symbol: str, bars: int = 50) -> pd.DataFrame:
        """Получение текущих данных для торговли"""
        if not self.connected:
            print("❌ Не подключено к MT5")
            return None

        timeframe_str = self.config.get('trading', {}).get('timeframe', 'M15')
        timeframe_mapping = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        timeframe = timeframe_mapping.get(timeframe_str, mt5.TIMEFRAME_M15)

        print(f"📊 Получение текущих данных для {symbol}")

        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

            if rates is None:
                print(f"❌ Не удалось получить данные для {symbol}")
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tick_volume': 'tick_volume',
                'spread': 'spread',
                'real_volume': 'volume'
            }, inplace=True)

            print(f"✅ Получено {len(df)} текущих баров для {symbol}")
            return df

        except Exception as e:
            print(f"❌ Ошибка получения текущих данных: {e}")
            return None

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Получение информации о символе"""
        if not self.connected:
            return None

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Не удалось получить информацию о символе {symbol}")
            return None

        return {
            'name': symbol_info.name,
            'bid': symbol_info.bid,
            'ask': symbol_info.ask,
            'point': symbol_info.point,
            'trade_tick_size': symbol_info.trade_tick_size,
            'trade_tick_value': symbol_info.trade_tick_value,
            'trade_contract_size': symbol_info.trade_contract_size,
            'trade_mode': symbol_info.trade_mode,
            'trade_stops_level': symbol_info.trade_stops_level,
            'trade_freeze_level': symbol_info.trade_freeze_level
        }

    def get_open_positions_count(self) -> int:
        """Получение количества открытых позиций"""
        if not self.connected:
            return 0

        positions = mt5.positions_get()
        return len(positions) if positions else 0

    def get_open_positions(self):
        """Получение списка открытых позиций"""
        if not self.connected:
            return []

        positions = mt5.positions_get()
        return positions if positions else []

    def close_all_positions(self):
        """Закрытие всех открытых позиций"""
        if not self.connected:
            return False

        positions = self.get_open_positions()
        if not positions:
            print("✅ Нет открытых позиций для закрытия")
            return True

        print(f"🔻 Закрытие {len(positions)} позиций...")

        success_count = 0
        for position in positions:
            symbol = position.symbol
            volume = position.volume
            position_id = position.ticket

            # Определяем тип закрывающей сделки
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask

            # Закрываем позицию
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "position": position_id,
                "price": price,
                "deviation": 20,
                "magic": 0,
                "comment": "Close by robot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Закрыта позиция {position_id} по {symbol}")
                success_count += 1
            else:
                error = self.get_error_description(result.retcode) if result else "Unknown error"
                print(f"❌ Ошибка закрытия позиции {position_id}: {error}")

        print(f"📊 Результат: закрыто {success_count}/{len(positions)} позиций")
        return success_count == len(positions)

    def place_order(self, symbol: str, order_type: int, volume: float,
                    stop_loss: float = 0, take_profit: float = 0) -> bool:
        """
        Размещение ордера с исправленными параметрами (решение ошибки 10030)
        """
        if not self.connected:
            print("❌ Не подключено к MT5")
            return False

        # Получаем актуальную информацию о символе
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ Символ {symbol} не найден")
            return False

        if not symbol_info.visible:
            print(f"🔧 Активируем символ {symbol}...")
            if not mt5.symbol_select(symbol, True):
                print(f"❌ Не удалось активировать символ {symbol}")
                return False

        # Используем правильные цены
        tick = mt5.symbol_info_tick(symbol)
        if order_type == mt5.ORDER_TYPE_BUY:
            price = tick.ask
        else:
            price = tick.bid

        print(f"💰 Текущие цены для {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")

        # Ключевое исправление: используем FOK вместо IOC и увеличенный deviation
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,  # Увеличенный deviation
            "magic": 0,  # Без magic number
            "comment": "AI Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,  # Ключевое изменение!
        }

        print(f"📤 Отправка ордера:")
        print(f"   Символ: {symbol}")
        print(f"   Тип: {'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL'}")
        print(f"   Объем: {volume}")
        print(f"   Цена: {price:.5f}")
        print(f"   SL: {stop_loss:.5f}")
        print(f"   TP: {take_profit:.5f}")

        # Отправка ордера
        result = mt5.order_send(request)

        if result is None:
            error = mt5.last_error()
            print(f"❌ order_send вернул None. Ошибка: {error}")
            return False

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Ошибка ордера {result.retcode}: {self.get_error_description(result.retcode)}")
            return False

        print(f"✅ Ордер успешно выполнен!")
        print(f"   Номер ордера: {result.order}")
        print(f"   Цена исполнения: {result.price:.5f}")
        print(f"   Объем: {result.volume}")

        # Если ордер выполнен и указаны SL/TP, пытаемся их установить
        if stop_loss > 0 or take_profit > 0:
            self._set_sltp_after_open(symbol, result.order, stop_loss, take_profit)

        return True

    def _set_sltp_after_open(self, symbol: str, order_id: int, stop_loss: float, take_profit: float):
        """Установка SL/TP после открытия позиции"""
        try:
            # Даем время на открытие позиции
            time.sleep(1)

            # Находим позицию по номеру ордера
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                print("⚠️ Не найдено открытых позиций для установки SL/TP")
                return

            # Ищем позицию по этому символу
            position = None
            for pos in positions:
                if pos.ticket == order_id:
                    position = pos
                    break

            # Если не нашли по ticket, берем последнюю позицию по символу
            if position is None and positions:
                position = positions[-1]
                print(f"⚠️ Позиция {order_id} не найдена, используем последнюю: {position.ticket}")

            if position is None:
                print("⚠️ Не найдена позиция для установки SL/TP")
                return

            # Модифицируем позицию
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position.ticket,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 0,
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ SL/TP установлены: SL={stop_loss:.5f}, TP={take_profit:.5f}")
            else:
                error_desc = self.get_error_description(result.retcode) if result else "Unknown error"
                print(f"⚠️ Не удалось установить SL/TP: {error_desc}")

        except Exception as e:
            print(f"⚠️ Ошибка при установке SL/TP: {e}")

    def get_error_description(self, error_code: int) -> str:
        """Расшифровка кодов ошибок"""
        error_descriptions = {
            10004: "Requote",
            10006: "Request rejected",
            10007: "Request canceled by trader",
            10008: "Order placed",
            10009: "Request completed",
            10010: "Only part of the request was completed",
            10011: "Request processing error",
            10012: "Request canceled by timeout",
            10013: "Invalid request",
            10014: "Invalid volume in the request",
            10015: "Invalid price in the request",
            10016: "Invalid stops in the request",
            10017: "Trade is disabled",
            10018: "Market is closed",
            10019: "There are not enough money to complete the request",
            10020: "Prices changed",
            10021: "There are no quotes to process the request",
            10022: "Invalid order expiration date in the request",
            10023: "Order state changed",
            10024: "Too frequent requests",
            10025: "No changes in request",
            10026: "Autotrading disabled by server",
            10027: "Autotrading disabled by client terminal",
            10028: "Request locked for processing",
            10029: "Order or position frozen",
            10030: "Invalid S/L or T/P",
        }
        return error_descriptions.get(error_code, f"Unknown error {error_code}")

    def disconnect(self):
        """Отключение от MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("✅ Отключено от MT5")
