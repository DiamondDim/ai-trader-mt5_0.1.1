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

    def load_current_data(self):
        """
        Загрузка текущих данных для символа
        """
        try:
            data = load_data(
                symbol=self.symbol,
                timeframe_str=self.config['data']['timeframe'],  # ИСПРАВЛЕНО: используем timeframe_str
                bars_count=100  # Для торговли нужно меньше данных
            )

            if data.empty:
                print(f"❌ Не удалось загрузить данные для {self.symbol}")
                return None

            return data

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return None

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

            # Убедимся, что у нас есть данные для предсказания
            if len(features_df) == 0:
                print("❌ Нет данных для предсказания после создания признаков")
                return None

            # Берем последнюю строку для предсказания (исключая целевые колонки)
            exclude_cols = ['target', 'future_close']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            latest_features = features_df[feature_cols].iloc[-1:]

            # Проверяем на NaN
            if latest_features.isnull().any().any():
                print("❌ NaN значения в признаках для предсказания")
                return None

            # Делаем предсказание
            prediction = self.model.predict(latest_features)[0]
            proba = self.model.predict_proba(latest_features)[0]
            confidence = max(proba)

            print(f"🎯 Предсказание: {'BUY' if prediction == 1 else 'SELL'} (уверенность: {confidence:.2f})")

            return {
                'prediction': prediction,
                'confidence': confidence,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"❌ Ошибка при создании предсказания: {e}")
            import traceback
            traceback.print_exc()
            return None

    def should_trade(self, prediction_result, current_bid, current_ask):
        """
        Проверка условий для торговли
        """
        if not prediction_result:
            return False

        confidence = prediction_result['confidence']
        min_confidence = self.config['model'].get('min_confidence', 0.6)

        # Проверка уверенности
        if confidence < min_confidence:
            print(f"⚠️ Слишком низкая уверенность: {confidence:.2f} < {min_confidence}")
            return False

        # Проверка спреда
        spread = current_ask - current_bid
        max_spread = self.symbol_config['max_spread'] * 0.00001  # Конвертируем в цену

        if spread > max_spread:
            print(f"⚠️ Слишком высокий спред: {spread:.5f} > {max_spread:.5f}")
            return False

        return True

    def execute_trade_decision(self, prediction_result):
        """
        Исполнение торгового решения на основе предсказания
        """
        if not prediction_result:
            return

        # Получаем текущие цены
        bid, ask = get_current_price(self.symbol)
        if bid is None or ask is None:
            print("❌ Не удалось получить текущие цены")
            return

        # Проверяем условия для торговли
        if not self.should_trade(prediction_result, bid, ask):
            return

        prediction = prediction_result['prediction']
        confidence = prediction_result['confidence']

        # Конвертируем пипы в цену (для forex 1 пип = 0.0001 для большинства пар)
        pip_value = 0.0001
        stop_loss_pips = self.symbol_config.get('stop_loss_pips', 20)
        take_profit_pips = self.symbol_config.get('take_profit_pips', 30)

        # Определяем тип ордера
        if prediction == 1:  # BUY
            print(f"📈 Сигнал BUY для {self.symbol} (уверенность: {confidence:.2f})")
            success = place_order(
                symbol=self.symbol,
                order_type='buy',
                lot_size=self.symbol_config['lot_size'],
                stop_loss=stop_loss_pips * pip_value,
                take_profit=take_profit_pips * pip_value
            )
        else:  # SELL
            print(f"📉 Сигнал SELL для {self.symbol} (уверенность: {confidence:.2f})")
            success = place_order(
                symbol=self.symbol,
                order_type='sell',
                lot_size=self.symbol_config['lot_size'],
                stop_loss=stop_loss_pips * pip_value,
                take_profit=take_profit_pips * pip_value
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
                    data = self.load_current_data()

                    if data is None:
                        print("❌ Не удалось загрузить данные, повтор через 60 секунд...")
                        time.sleep(60)
                        continue

                    # Создаем предсказание
                    prediction_result = self.make_prediction(data)

                    if prediction_result:
                        # Исполняем торговое решение
                        self.execute_trade_decision(prediction_result)
                    else:
                        print("❌ Не удалось создать предсказание")

                    # Пауза между итерациями
                    print(f"⏳ Ожидание 60 секунд до следующей итерации...")
                    time.sleep(60)

                except Exception as e:
                    print(f"❌ Ошибка в итерации #{iteration}: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n⏹️ Остановка торговли для {self.symbol}")
        except Exception as e:
            print(f"❌ Критическая ошибка в торговом цикле: {e}")
            import traceback
            traceback.print_exc()
