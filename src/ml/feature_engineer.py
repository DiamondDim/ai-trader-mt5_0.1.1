import pandas as pd
import numpy as np
from typing import Optional


class FeatureEngineer:
    def __init__(self):
        self.feature_count = 0

    def create_features(self, data: pd.DataFrame, for_training: bool = True) -> pd.DataFrame:
        """
        Создание признаков для ML модели

        Args:
            data: Исходные данные цен
            for_training: Если True, создает целевую переменную для обучения
                         Если False, создает только признаки для предсказания
        """
        try:
            if data.empty:
                return pd.DataFrame()

            df = data.copy()

            # Базовые ценовые фичи
            df['returns'] = df['close'].pct_change()
            df['high_low_ratio'] = df['high'] / df['low']
            df['open_close_ratio'] = df['close'] / df['open']

            # Простые скользящие средние
            for window in [5, 10, 20, 50]:
                df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
                df[f'sma_ratio_{window}'] = df['close'] / df[f'sma_{window}']
                df[f'returns_sma_{window}'] = df['returns'].rolling(window=window).mean()

            # Экспоненциальные скользящие средние
            for span in [8, 13, 21]:
                df[f'ema_{span}'] = df['close'].ewm(span=span).mean()
                df[f'ema_ratio_{span}'] = df['close'] / df[f'ema_{span}']

            # RSI (Relative Strength Index)
            df['rsi_14'] = self.calculate_rsi(df['close'], 14)
            df['rsi_21'] = self.calculate_rsi(df['close'], 21)

            # MACD
            macd, signal = self.calculate_macd(df['close'])
            df['macd'] = macd
            df['macd_signal'] = signal
            df['macd_histogram'] = macd - signal

            # Bollinger Bands
            bb_upper, bb_lower, bb_middle = self.calculate_bollinger_bands(df['close'])
            df['bb_upper'] = bb_upper
            df['bb_lower'] = bb_lower
            df['bb_middle'] = bb_middle
            df['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)

            # Волатильность
            for window in [5, 10, 20]:
                df[f'volatility_{window}'] = df['returns'].rolling(window=window).std()
                df[f'atr_{window}'] = self.calculate_atr(df, window)

            # Объемы
            if 'tick_volume' in df.columns:
                df['volume_sma_5'] = df['tick_volume'].rolling(5).mean()
                df['volume_sma_20'] = df['tick_volume'].rolling(20).mean()
                df['volume_ratio'] = df['tick_volume'] / df['volume_sma_20']

            # Ценовые уровни
            df['resistance'] = df['high'].rolling(20).max()
            df['support'] = df['low'].rolling(20).min()
            df['distance_to_resistance'] = (df['resistance'] - df['close']) / df['close']
            df['distance_to_support'] = (df['close'] - df['support']) / df['close']

            # Статистические фичи
            df['rolling_skew_10'] = df['returns'].rolling(10).skew()
            df['rolling_kurt_10'] = df['returns'].rolling(10).kurt()

            # Временные фичи
            if hasattr(df.index, 'hour'):
                df['hour'] = df.index.hour
                df['day_of_week'] = df.index.dayofweek
                df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

            # Целевая переменная (только для обучения)
            if for_training:
                n_bars = 3
                df['future_close'] = df['close'].shift(-n_bars)
                df['target'] = (df['future_close'] > df['close']).astype(int)
            else:
                # Для предсказания не создаем целевую переменную
                df['target'] = 0  # Заглушка

            # Удаляем NaN значения
            df = df.dropna()

            # Определяем колонки для исключения
            exclude_cols = ['target']
            if for_training:
                exclude_cols.append('future_close')  # Исключаем future_close только при обучении

            # Считаем количество признаков (исключая целевые и временные колонки)
            feature_exclude_cols = exclude_cols + ['hour', 'day_of_week', 'is_weekend']
            feature_cols = [col for col in df.columns if col not in feature_exclude_cols]
            self.feature_count = len(feature_cols)

            print(
                f"✅ Создано признаков: {self.feature_count} (режим: {'обучение' if for_training else 'предсказание'})")
            print(f"✅ Образцов после очистки: {len(df)}")

            return df

        except Exception as e:
            print(f"❌ Ошибка создания признаков: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Расчет RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Расчет MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: int = 2) -> tuple:
        """Расчет Bollinger Bands"""
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band, lower_band, rolling_mean

    def calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Расчет Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = np.maximum(np.maximum(high_low, high_close), low_close)
        atr = true_range.rolling(window=window).mean()
        return atr


# Функция-обертка для обратной совместимости
def create_features(data: pd.DataFrame, for_training: bool = True) -> pd.DataFrame:
    """
    Функция-обертка для создания признаков
    """
    engineer = FeatureEngineer()
    return engineer.create_features(data, for_training)


def get_feature_count() -> int:
    """
    Получение количества созданных признаков
    """
    return FeatureEngineer().feature_count
