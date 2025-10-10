import pandas as pd
import numpy as np
from typing import Dict, Optional
import MetaTrader5 as mt5


class RiskManager:
    """Упрощенный класс для управления рисками"""

    def __init__(self, config: Dict):
        self.config = config
        self.daily_loss_limit = 0
        self.daily_loss_current = 0

    def check_risk(self, symbol: str, price: float) -> bool:
        """Проверка рисков перед торговлей"""
        trading_config = self.config.get('trading', {})

        # Проверка максимального количества позиций
        max_positions = trading_config.get('max_open_positions', 2)
        # Здесь должна быть логика проверки текущих позиций

        # Проверка дневного лимита убытков
        max_daily_loss = trading_config.get('max_daily_loss', 0.03)
        if self.daily_loss_current >= max_daily_loss:
            print(f"⚠️ Достигнут дневной лимит убытков: {self.daily_loss_current:.2%}")
            return False

        return True

    def calculate_position_size(self, symbol: str, price: float) -> float:
        """Расчет размера позиции"""
        trading_config = self.config.get('trading', {})

        # Используем фиксированный лот из конфига
        lot_size = trading_config.get('lot_size', 0.01)

        # Проверяем минимальный и максимальный лот
        min_lot = 0.01
        max_lot = 1.0

        lot_size = max(min_lot, min(lot_size, max_lot))
        return round(lot_size, 2)

    def calculate_stop_loss(self, symbol: str, order_type: int, price: float) -> float:
        """Расчет стоп-лосса с безопасными расстояниями"""
        # Увеличиваем расстояние для избежания ошибки 10030
        # Используем 50 пунктов для EURUSD (0.0050)
        if order_type == mt5.ORDER_TYPE_BUY:
            # Для BUY: стоп-лосс ниже цены открытия
            stop_loss = price - 0.0050
        else:
            # Для SELL: стоп-лосс выше цены открытия
            stop_loss = price + 0.0050

        return round(stop_loss, 5)

    def calculate_take_profit(self, symbol: str, order_type: int, price: float) -> float:
        """Расчет тейк-профита с безопасными расстояниями"""
        # Используем 80 пунктов для EURUSD (0.0080)
        if order_type == mt5.ORDER_TYPE_BUY:
            # Для BUY: тейк-профит выше цены открытия
            take_profit = price + 0.0080
        else:
            # Для SELL: тейк-профит ниже цены открытия
            take_profit = price - 0.0080

        return round(take_profit, 5)

    def update_daily_loss(self, pnl: float):
        """Обновление дневного убытка"""
        self.daily_loss_current += max(0, -pnl)
        print(f"📊 Текущий дневной убыток: {self.daily_loss_current:.2%}")
