import pandas as pd
import numpy as np
from typing import List
import warnings

warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Класс для создания и подготовки признаков"""

    def __init__(self, config: dict):
        self.config = config
        self.feature_names = []

    def prepare_features(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Подготовка признаков из рыночных данных"""
        print("Начало подготовки фич...")

        try:
            df = data.copy()

            # Создание расширенного набора фич
            df = self._create_basic_technical_indicators(df)
            df = self._create_statistical_features(df)
            df = self._create_time_features(df)
            df = self._create_lagged_features(df)

            # Удаляем строки с NaN значениями
            df = df.dropna()

            print(f"Подготовка фич завершена. Создано {len(self.feature_names)} признаков")
            return df

        except Exception as e:
            print(f"❌ Ошибка подготовки фич: {e}")
            return pd.DataFrame()

    def _create_basic_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание базовых технических индикаторов"""
        print("Добавление базовых технических индикаторов...")

        # Простые скользящие средние
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        # Экспоненциальные скользящие средние
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()

        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], window=14)

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        # ATR (Average True Range)
        df['atr'] = self._calculate_atr(df, window=14)

        # Volume-based features
        df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['tick_volume'] / df['volume_sma']

        return df

    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание статистических признаков"""
        print("Добавление статистических фич...")

        # Волатильность
        df['volatility_5'] = df['close'].pct_change().rolling(window=5).std()
        df['volatility_10'] = df['close'].pct_change().rolling(window=10).std()
        df['volatility_20'] = df['close'].pct_change().rolling(window=20).std()

        # Процентные изменения
        df['returns_1'] = df['close'].pct_change(1)
        df['returns_5'] = df['close'].pct_change(5)
        df['returns_10'] = df['close'].pct_change(10)

        # Статистические моменты
        df['rolling_skew_10'] = df['returns_1'].rolling(window=10).skew()
        df['rolling_skew_20'] = df['returns_1'].rolling(window=20).skew()
        df['rolling_kurtosis_10'] = df['returns_1'].rolling(window=10).kurt()
        df['rolling_kurtosis_20'] = df['returns_1'].rolling(window=20).kurt()

        return df

    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание временных признаков"""
        print("Добавление временных фич...")

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Временные признаки
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['week_of_year'] = df.index.isocalendar().week

        # Циклические кодирования для времени
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        return df

    def _create_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Создание лаггированных признаков"""
        print("Добавление лаггированных фич...")

        # Лаги цен
        for lag in [1, 2, 3, 5]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['tick_volume'].shift(lag)

        # Лаги доходностей
        for lag in [1, 2, 3]:
            df[f'returns_lag_{lag}'] = df['returns_1'].shift(lag)

        return df

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Расчет RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Расчет ATR (Average True Range)"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=window).mean()
        return atr

    def get_feature_names(self) -> List[str]:
        """Получение списка имен признаков"""
        if not self.feature_names:
            # Базовые ценовые признаки
            base_features = ['open', 'high', 'low', 'close', 'tick_volume']

            # Технические индикаторы
            technical_features = [
                'sma_10', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_hist', 'rsi',
                'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'atr',
                'volume_sma', 'volume_ratio'
            ]

            # Статистические признаки
            statistical_features = [
                'volatility_5', 'volatility_10', 'volatility_20',
                'returns_1', 'returns_5', 'returns_10',
                'rolling_skew_10', 'rolling_skew_20',
                'rolling_kurtosis_10', 'rolling_kurtosis_20'
            ]

            # Временные признаки
            time_features = [
                'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
            ]

            # Лаггированные признаки
            lagged_features = [
                'close_lag_1', 'close_lag_2', 'close_lag_3', 'close_lag_5',
                'volume_lag_1', 'volume_lag_2', 'volume_lag_3', 'volume_lag_5',
                'returns_lag_1', 'returns_lag_2', 'returns_lag_3'
            ]

            self.feature_names = (base_features + technical_features +
                                  statistical_features + time_features + lagged_features)

        return self.feature_names
