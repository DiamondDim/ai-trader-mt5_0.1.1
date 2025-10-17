import time
import pandas as pd
from datetime import datetime
from src.core.mt5_client import load_data, get_current_price, place_order
from src.ml.feature_engineer import create_features
from src.utils.config import get_symbol_specific_config


class Trader:
    def __init__(self, config):
        self.config = config
        self.symbol = config['trading']['symbol']
        self.symbol_config = get_symbol_specific_config(self.symbol, config)

        # Загрузка модели для конкретного символа
        from src.ml.model_builder import load_model_for_symbol
        self.model = load_model_for_symbol(self.symbol)

        if not self.model:
            raise Exception(f"Модель для символа {self.symbol} не найдена")

        print(f"✅ Трейдер инициализирован для {self.symbol}")
        print(f"⚙️ Настройки: Лот={self.symbol_config['lot_size']}, Макс. спред={self.symbol_config['max_spread']}")

    def make_prediction(self, data):
        """
        Создание предсказания на основе текущих данных
        """
        try:
            # Создаем признаки
            features_df = create_features(data)

            if features_df.empty:
                print("❌ Не удалось создать признаки для предсказания")
                return None

            # Берем последнюю строку для предсказания
            latest_features = features_df.drop('target', axis=1).iloc[-1:]

            # Проверяем на NaN
            if latest_features.isnull().any().any():
                print("❌ NaN значения в признаках для предсказания")
                return None

            # Делаем предсказание
            prediction = self.model.predict(latest_features)[0]
            confidence = self.model.predict_proba(latest_features)[0].max()

            print(f"🎯 Предсказание: {prediction} (уверенность: {confidence:.2f})")

            return {
                'prediction': prediction,
                'confidence': confidence,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"❌ Ошибка при создании предсказания: {e}")
            return None

    def execute_trade_decision(self, prediction_result):
        """
        Исполнение торгового решения на основе предсказания
        """
        if not prediction_result:
            return

        prediction = prediction_result['prediction']
        confidence = prediction_result['confidence']

        # Минимальная уверенность для торговли
        min_confidence = self.config['model'].get('min_confidence', 0.6)

        if confidence < min_confidence:
            print(f"⚠️ Слишком низкая уверенность: {confidence:.2f} < {min_confidence}")
            return

        # Получаем текущие цены и спред
        bid, ask = get_current_price(self.symbol)
        if bid is None or ask is None:
            print("❌ Не удалось получить текущие цены")
            return

        spread = ask - bid
        max_spread = self.symbol_config['max_spread']

        if spread > max_spread:
            print(f"⚠️ Слишком высокий спред: {spread:.4f} > {max_spread}")
            return

        # Определяем тип ордера
        if prediction == 1:  # BUY
            print(f"📈 Сигнал BUY для {self.symbol} (уверенность: {confidence:.2f})")
            success = place_order(
                symbol=self.symbol,
                order_type='buy',
                lot_size=self.symbol_config['lot_size'],
                stop_loss=self.symbol_config.get('stop_loss_pips', 20) * 0.0001,
                take_profit=self.symbol_config.get('take_profit_pips', 30) * 0.0001
            )
        else:  # SELL
            print(f"📉 Сигнал SELL для {self.symbol} (уверенность: {confidence:.2f})")
            success = place_order(
                symbol=self.symbol,
                order_type='sell',
                lot_size=self.symbol_config['lot_size'],
                stop_loss=self.symbol_config.get('stop_loss_pips', 20) * 0.0001,
                take_profit=self.symbol_config.get('take_profit_pips', 30) * 0.0001
            )

        if success:
            print("✅ Торговая операция выполнена")
        else:
            print("❌ Ошибка выполнения торговой операции")

    def trade_loop(self):
        """
        Основной цикл торговли для выбранного символа
        """
        print(f"\n📈 ЗАПУСК ТОРГОВОГО ЦИКЛА ДЛЯ {self.symbol}")
        print(f"⏰ Интервал проверки: 60 секунд")
        print(f"🎯 Минимальная уверенность: {self.config['model'].get('min_confidence', 0.6)}")
        print("=" * 50)

        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n🔄 Итерация #{iteration} - {datetime.now().strftime('%H:%M:%S')}")

                try:
                    # Загружаем текущие данные
                    data = load_data(
                        symbol=self.symbol,
                        timeframe=self.config['data']['timeframe'],
                        bars_count=100  # Нужно меньше данных для реальной торговли
                    )

                    if data.empty:
                        print("❌ Не удалось загрузить данные")
                        time.sleep(60)
                        continue

                    # Создаем предсказание
                    prediction_result = self.make_prediction(data)

                    if prediction_result:
                        # Исполняем торговое решение
                        self.execute_trade_decision(prediction_result)

                    # Пауза между итерациями
                    time.sleep(60)

                except Exception as e:
                    print(f"❌ Ошибка в итерации #{iteration}: {e}")
                    time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n⏹️ Остановка торговли для {self.symbol}")
