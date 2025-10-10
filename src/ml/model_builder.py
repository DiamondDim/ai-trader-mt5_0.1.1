import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, f1_score
import joblib
import os
from typing import Optional
import warnings

warnings.filterwarnings('ignore')


class ModelBuilder:
    """Класс для построения и обучения ML моделей"""

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.feature_importance_ = None

    def create_model(self):
        """Создание модели на основе конфигурации"""
        model_config = self.config.get('model', {})
        model_type = model_config.get('model_type', 'GradientBoosting')

        print(f"Создание модели: {model_type}")

        if model_type == "GradientBoosting":
            model_params = model_config.get('model_params', {})
            self.model = GradientBoostingClassifier(
                n_estimators=model_params.get('n_estimators', 100),
                max_depth=model_params.get('max_depth', 3),
                learning_rate=model_params.get('learning_rate', 0.1),
                random_state=model_params.get('random_state', 42)
            )
        else:
            # По умолчанию используем GradientBoosting
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )

        return self.model

    def train_model(self, data: pd.DataFrame, symbol: str, feature_engineer) -> Optional[str]:
        """Обучение модели на исторических данных"""
        try:
            # Подготовка фич
            print("Начало подготовки данных для обучения...")
            features_df = feature_engineer.prepare_features(data, symbol)
            feature_names = feature_engineer.get_feature_names()

            if len(features_df) == 0:
                print("❌ Не удалось подготовить данные для обучения")
                return None

            # Создание целевой переменной (предсказание направления цены)
            features_df = self._create_target(features_df)

            # Удаляем строки с NaN
            features_df = features_df.dropna()

            if len(features_df) < 100:
                print("❌ Недостаточно данных для обучения")
                return None

            # Разделение на признаки и целевую переменную
            X = features_df[feature_names]
            y = features_df['target']

            print(f"✅ Данные для обучения: {len(X)} samples, {len(feature_names)} признаков")

            # Разделение на train/test
            test_size = self.config.get('ml', {}).get('test_size', 0.3)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            print(f"📊 Данные: train={len(X_train)}, test={len(X_test)}")

            # Создание и обучение модели
            model = self.create_model()

            print("Начало обучения модели...")
            model.fit(X_train, y_train)

            # Кросс-валидация
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            print(f"Обучение завершено. CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

            # Оценка на тестовых данных
            y_pred = model.predict(X_test)
            test_accuracy = accuracy_score(y_test, y_pred)
            test_f1 = f1_score(y_test, y_pred, average='weighted')

            print(f"Тестовая точность: {test_accuracy:.4f}")
            print(f"Test F1-Score: {test_f1:.4f}")

            # Сохранение важности признаков
            if hasattr(model, 'feature_importances_'):
                self.feature_importance_ = pd.DataFrame({
                    'feature': feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)

                print("\n🎯 Топ-10 важных признаков:")
                for i, row in self.feature_importance_.head(10).iterrows():
                    print(f"   {row['feature']}: {row['importance']:.4f}")

            # Сохранение модели
            model_path = self.config.get('ml', {}).get('model_path', 'models/trained_model.pkl')
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            joblib.dump(model, model_path)
            print(f"Модель сохранена в: {model_path}")

            self.model = model
            return model_path

        except Exception as e:
            print(f"❌ Ошибка обучения модели: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_target(self, df: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
        """Создание целевой переменной"""
        # Целевая переменная: 1 если цена вырастет через horizon баров, 0 если упадет
        df['future_price'] = df['close'].shift(-horizon)
        df['price_change'] = (df['future_price'] - df['close']) / df['close']

        # Бинарная классификация: 1 если рост > 0, 0 иначе
        df['target'] = (df['price_change'] > 0).astype(int)

        # Удаляем последние horizon строк (у них нет future_price)
        df = df[:-horizon]

        return df

    def load_model(self):
        """Загрузка обученной модели"""
        try:
            model_path = self.config.get('ml', {}).get('model_path', 'models/trained_model.pkl')

            if not os.path.exists(model_path):
                print(f"❌ Файл модели не найден: {model_path}")
                return None

            self.model = joblib.load(model_path)
            print(f"✅ Модель загружена: {model_path}")
            return self.model

        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            return None

    def predict(self, features):
        """Предсказание на новых данных"""
        if self.model is None:
            print("❌ Модель не загружена")
            return None

        try:
            prediction = self.model.predict(features)
            probabilities = self.model.predict_proba(features)
            return prediction, probabilities
        except Exception as e:
            print(f"❌ Ошибка предсказания: {e}")
            return None
