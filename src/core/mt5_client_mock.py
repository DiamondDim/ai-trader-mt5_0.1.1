
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MT5ClientMock:
    def __init__(self, config):
        self.config = config
        self.connected = True

    def connect(self) -> bool:
        print("✅ Mock: Подключение к MT5 (тестовый режим)")
        return True

    def disconnect(self):
        print("✅ Mock: Отключение от MT5")
        self.connected = False

    def get_historical_data(self, symbol: str, timeframe: str, bars: int = 1000) -> pd.DataFrame:
        """Генерация тестовых данных"""
        print(f"📊 Mock: Генерация {bars} тестовых баров для {symbol} ({timeframe})")

        # Создаем тестовые данные
        dates = pd.date_range(end=datetime.now(), periods=bars, freq='15min')

        # Генерируем реалистичные ценовые данные
        np.random.seed(42)
        prices = []
        current_price = 1.1000  # Начальная цена EURUSD

        for i in range(bars):
            # Добавляем случайное движение
            change = np.random.normal(0, 0.0005)
            current_price += change

            # Создаем свечу
            open_price = current_price
            high_price = open_price + abs(np.random.normal(0, 0.001))
            low_price = open_price - abs(np.random.normal(0, 0.001))
            close_price = open_price + np.random.normal(0, 0.0003)

            # Обеспечиваем корректность high/low
            high_price = max(open_price, close_price, high_price)
            low_price = min(open_price, close_price, low_price)

            prices.append({
                'time': dates[i].timestamp(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'tick_volume': np.random.randint(100, 1000),
                'spread': np.random.randint(1, 10),
                'real_volume': np.random.randint(1000, 10000)
            })

        df = pd.DataFrame(prices)
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('datetime', inplace=True)

        return df

    def get_current_price(self, symbol: str) -> float:
        return 1.1050  # Фиктивная цена

    def place_order(self, symbol: str, order_type: str, volume: float,
                    stop_loss: float = None, take_profit: float = None) -> bool:
        print(f"✅ Mock: Ордер {order_type} {volume} {symbol}")
        return True

    def get_account_info(self):
        class AccountInfo:
            def __init__(self):
                self.login = 123456
                self.server = "TestServer"
                self.balance = 10000.0
                self.equity = 10000.0
                self.margin = 0.0
                self.currency = "USD"

        return AccountInfo()
