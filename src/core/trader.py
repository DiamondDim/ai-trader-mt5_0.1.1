import pandas as pd
import numpy as np
import time
from datetime import datetime
from typing import Dict, Optional
import MetaTrader5 as mt5


class Trader:
    """Класс для управления торговыми операциями с исправлениями"""

    def __init__(self, config: Dict, mt5_client, risk_manager):
        self.config = config
        self.mt5_client = mt5_client
        self.risk_manager = risk_manager
        self.is_trading = False
        self.current_symbol = None
        self.stop_requested = False

    def start_trading(self, symbol: str, model, feature_engineer) -> bool:
        """Запуск автоматической торговли с улучшенной обработкой ошибок"""
        print(f"🎯 Запуск торговли для {symbol}")

        self.current_symbol = symbol
        self.is_trading = True
        self.stop_requested = False

        # Счетчик попыток для избежания бесконечных ошибок
        error_count = 0
        max_errors = 5

        try:
            while self.is_trading and not self.stop_requested and error_count < max_errors:
                current_data = self.mt5_client.get_current_data(symbol, bars=50)
                if current_data is None or current_data.empty:
                    print("❌ Не удалось получить текущие данные")
                    error_count += 1
                    time.sleep(30)
                    continue

                try:
                    features_df = feature_engineer.prepare_features(current_data, symbol)
                    feature_names = feature_engineer.get_feature_names()

                    if len(features_df) == 0:
                        print("❌ Не удалось подготовить фичи")
                        error_count += 1
                        time.sleep(30)
                        continue

                    latest_features = features_df[feature_names].iloc[-1:]

                    prediction = model.predict(latest_features)[0]
                    probability = model.predict_proba(latest_features)[0]

                    print(f"📊 Предсказание: {prediction}, Вероятности: [{probability[0]:.3f}, {probability[1]:.3f}]")

                    # Сбрасываем счетчик ошибок при успешном предсказании
                    error_count = 0

                    # Принимаем торговое решение только при высокой уверенности
                    self._make_trading_decision(symbol, prediction, probability, current_data)

                except Exception as e:
                    print(f"❌ Ошибка обработки данных: {e}")
                    error_count += 1

                # Проверяем флаг остановки перед ожиданием
                if not self.stop_requested:
                    print("⏳ Ожидание 60 секунд...")
                    for i in range(60):
                        if self.stop_requested:
                            break
                        time.sleep(1)

            if error_count >= max_errors:
                print(f"🛑 Превышено максимальное количество ошибок ({max_errors}). Торговля остановлена.")
            elif self.stop_requested:
                print("🛑 Торговля остановлена по запросу пользователя.")

            return True

        except Exception as e:
            print(f"❌ Критическая ошибка в торговом цикле: {e}")
            return False

    def _make_trading_decision(self, symbol: str, prediction: int,
                               probability: np.ndarray, data: pd.DataFrame):
        """Принятие торгового решения с улучшенной логикой"""
        # Получаем текущие цены bid и ask
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print("❌ Не удалось получить текущие цены")
            return

        current_price = tick.ask if prediction == 1 else tick.bid

        if not self.risk_manager.check_risk(symbol, current_price):
            print("⚠️ Торговля приостановлена due to risk management")
            return

        # Повышаем порог уверенности для торговли
        confidence_threshold = 0.7  # 70% уверенности вместо 60%

        if prediction == 1 and probability[1] > confidence_threshold:
            print(f"✅ Сигнал на ПОКУПКУ (уверенность: {probability[1]:.1%})")
            self._open_position(symbol, mt5.ORDER_TYPE_BUY, current_price)
        elif prediction == 0 and probability[0] > confidence_threshold:
            print(f"✅ Сигнал на ПРОДАЖУ (уверенность: {probability[0]:.1%})")
            self._open_position(symbol, mt5.ORDER_TYPE_SELL, current_price)
        else:
            print(f"🤷 Нет четкого сигнала (макс. уверенность: {max(probability):.1%})")

    def _open_position(self, symbol: str, order_type: int, price: float):
        """Открытие позиции с улучшенной обработкой ошибок"""
        volume = self.risk_manager.calculate_position_size(symbol, price)

        if volume <= 0:
            print("⚠️ Объем позиции слишком мал")
            return

        # Безопасный расчет стоп-лосса и тейк-профита
        stop_loss = self.risk_manager.calculate_stop_loss(symbol, order_type, price)
        take_profit = self.risk_manager.calculate_take_profit(symbol, order_type, price)

        print(f"💡 Параметры ордера:")
        print(f"   Символ: {symbol}")
        print(f"   Тип: {'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL'}")
        print(f"   Объем: {volume}")
        print(f"   Текущая цена: {price:.5f}")
        print(f"   Стоп-лосс: {stop_loss:.5f}")
        print(f"   Тейк-профит: {take_profit:.5f}")

        result = self.mt5_client.place_order(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        if result:
            print(f"✅ Позиция открыта: {symbol}")
        else:
            print(f"❌ Ошибка открытия позиции: {symbol}")

    def stop_trading(self):
        """Остановка торговли"""
        self.stop_requested = True
        self.is_trading = False
        print("🛑 Запрошена остановка торговли...")

    def emergency_stop(self):
        """Аварийная остановка - закрытие всех позиций и остановка торговли"""
        print("🚨 АВАРИЙНАЯ ОСТАНОВКА АКТИВИРОВАНА!")
        self.stop_trading()

        # Закрываем все позиции
        print("🔻 Закрытие всех открытых позиций...")
        success = self.mt5_client.close_all_positions()

        if success:
            print("✅ Все позиции закрыты")
        else:
            print("⚠️ Не все позиции удалось закрыть")

        return success

    def get_trading_status(self) -> Dict:
        """Получить статус торговли"""
        positions = self.mt5_client.get_open_positions()
        positions_info = []

        for pos in positions:
            positions_info.append({
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

        return {
            'is_trading': self.is_trading,
            'stop_requested': self.stop_requested,
            'current_symbol': self.current_symbol,
            'open_positions_count': len(positions),
            'open_positions': positions_info
        }
