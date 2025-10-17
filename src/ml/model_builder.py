import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from typing import Optional
import warnings

warnings.filterwarnings('ignore')


class ModelBuilder:
    """Улучшенный класс для построения и обучения ML моделей"""

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance_ = None

    def create_model(self):
        """Создание модели на основе конфигурации"""
        model_config = self.config.get('model', {})
        model_type = model_config.get('model_type', 'GradientBoosting')

        print(f"🤖 Создание модели: {model_type}")

        if model_type == "GradientBoosting":
            model_params = model_config.get('model_params', {})
            self.model = GradientBoostingClassifier(
                n_estimators=model_params.get('n_estimators', 200),  # Увеличили
                max_depth=model_params.get('max_depth', 4),  # Увеличили
                learning_rate=model_params.get('learning_rate', 0.05),  # Уменьшили
                min_samples_split=model_params.get('min_samples_split', 50),  # Добавили
                min_samples_leaf=model_params.get('min_samples_leaf', 20),  # Добавили
                subsample=model_params.get('subsample', 0.8),  # Добавили
                random_state=model_params.get('random_state', 42)
            )
        elif model_type == "RandomForest":
            model_params = model_config.get('model_params', {})
            self.model = RandomForestClassifier(
                n_estimators=model_params.get('n_estimators', 200),
                max_depth=model_params.get('max_depth', 6),
                min_samples_split=model_params.get('min_samples_split', 20),
                min_samples_leaf=model_params.get('min_samples_leaf', 10),
                random_state=model_params.get('random_state', 42),
                n_jobs=-1
            )
        else:
            # По умолчанию используем улучшенный GradientBoosting
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                min_samples_split=50,
                min_samples_leaf=20,
                subsample=0.8,
                random_state=42
            )

        return self.model

    def train_model(self, data: pd.DataFrame, symbol: str, feature_engineer) -> Optional[str]:
        """Обучение модели на исторических данных"""
        try:
            # Подготовка фич
            print("📊 Начало подготовки данных для обучения...")
            features_df = feature_engineer.prepare_features(data, symbol)
            feature_names = feature_engineer.get_feature_names()

            if len(features_df) == 0:
                print("❌ Не удалось подготовить данные для обучения")
                return None

            # Создание целевой переменной (предсказание направления цены)
            features_df = self._create_improved_target(features_df)

            # Удаляем строки с NaN
            initial_samples = len(features_df)
            features_df = features_df.dropna()
            final_samples = len(features_df)

            print(f"📈 Данные после очистки: {final_samples}/{initial_samples} samples")

            if len(features_df) < 200:
                print("❌ Недостаточно данных для обучения")
                return None

            # Разделение на признаки и целевую переменную
            X = features_df[feature_names]
            y = features_df['target']

            print(f"✅ Данные для обучения: {len(X)} samples, {len(feature_names)} признаков")

            # Масштабирование признаков
            print("🔧 Масштабирование признаков...")
            X_scaled = self.scaler.fit_transform(X)
            X = pd.DataFrame(X_scaled, columns=feature_names, index=X.index)

            # Разделение на train/test
            test_size = self.config.get('ml', {}).get('test_size', 0.2)  # Уменьшили test_size
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            print(f"📊 Разделение данных: train={len(X_train)}, test={len(X_test)}")

            # Балансировка классов
            class_ratio = y_train.mean()
            print(f"📊 Баланс классов: {class_ratio:.3f} (1) / {1 - class_ratio:.3f} (0)")

            # Создание и обучение модели
            model = self.create_model()

            print("🎯 Начало обучения модели...")
            model.fit(X_train, y_train)

            # Кросс-валидация
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
            print(f"✅ Обучение завершено. CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

            # Оценка на тестовых данных
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)
            test_accuracy = accuracy_score(y_test, y_pred)
            test_f1 = f1_score(y_test, y_pred, average='weighted')

            print(f"🧪 Тестовая точность: {test_accuracy:.4f}")
            print(f"🎯 Test F1-Score: {test_f1:.4f}")

            # Анализ уверенности предсказаний
            confidence_mean = y_pred_proba.max(axis=1).mean()
            confidence_std = y_pred_proba.max(axis=1).std()
            print(f"📊 Средняя уверенность: {confidence_mean:.4f} ± {confidence_std:.4f}")

            # Сохранение важности признаков
            if hasattr(model, 'feature_importances_'):
                self.feature_importance_ = pd.DataFrame({
                    'feature': feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)

                print("\n🏆 Топ-15 важных признаков:")
                for i, row in self.feature_importance_.head(15).iterrows():
                    print(f"   {row['feature']}: {row['importance']:.4f}")

            # Сохранение модели и scaler
            model_path = self.config.get('ml', {}).get('model_path', 'models/trained_model.pkl')
            scaler_path = model_path.replace('.pkl', '_scaler.pkl')
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            joblib.dump(model, model_path)
            joblib.dump(self.scaler, scaler_path)
            print(f"💾 Модель сохранена в: {model_path}")
            print(f"💾 Scaler сохранен в: {scaler_path}")

            self.model = model
            return model_path

        except Exception as e:
            print(f"❌ Ошибка обучения модели: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_improved_target(self, df: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
        """Создание улучшенной целевой переменной"""
        # Уменьшаем горизонт предсказания для большей стабильности
        df['future_price'] = df['close'].shift(-horizon)
        df['price_change'] = (df['future_price'] - df['close']) / df['close']

        # Используем порог для фильтрации слабых движений
        threshold = 0.0005  # 0.05% порог
        df['target'] = 1  # По умолчанию покупать

        # Продавать если падение больше порога
        df.loc[df['price_change'] < -threshold, 'target'] = 0
        # Держать если движение в пределах порога
        df.loc[(df['price_change'] >= -threshold) & (df['price_change'] <= threshold), 'target'] = 2

        # Удаляем последние horizon строк (у них нет future_price)
        df = df[:-horizon]

        # Фильтруем только сильные сигналы (убираем target=2)
        df = df[df['target'] != 2]

        print(f"🎯 Распределение целевой переменной:")
        target_counts = df['target'].value_counts()
        for target_val, count in target_counts.items():
            direction = "BUY" if target_val == 1 else "SELL"
            percentage = count / len(df) * 100
            print(f"   {direction} ({target_val}): {count} samples ({percentage:.1f}%)")

        return df

    def load_model(self):
        """Загрузка обученной модели и scaler"""
        try:
            model_path = self.config.get('ml', {}).get('model_path', 'models/trained_model.pkl')
            scaler_path = model_path.replace('.pkl', '_scaler.pkl')

            if not os.path.exists(model_path):
                print(f"❌ Файл модели не найден: {model_path}")
                return None

            self.model = joblib.load(model_path)

            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print(f"✅ Scaler загружен: {scaler_path}")

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
            # Масштабирование признаков
            features_scaled = self.scaler.transform(features)
            prediction = self.model.predict(features_scaled)
            probabilities = self.model.predict_proba(features_scaled)
            return prediction, probabilities
        except Exception as e:
            print(f"❌ Ошибка предсказания: {e}")
            return None
