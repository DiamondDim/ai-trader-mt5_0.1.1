import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB

from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


class Model:
    """Базовый класс ML модели"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        self.is_trained = False

    def create_model(self):
        """Создание модели"""
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
        return self.model

    def train(self, X: pd.DataFrame, y: pd.Series):
        """Обучение модели"""
        if self.model is None:
            self.create_model()

        self.model.fit(X, y)
        self.is_trained = True
        return self

    def predict(self, X: pd.DataFrame):
        """Предсказание"""
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame):
        """Вероятностное предсказание"""
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        return self.model.predict_proba(X)


class AdvancedModel:
    """Расширенный класс ML модели"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        self.models = {}
        self.feature_importance = {}
        self.cv_scores = {}
        self.is_trained = False

    def create_model(self, model_type: str = "GradientBoosting", **params):
        """Создание модели по типу"""

        default_params = {
            "GradientBoosting": {
                "n_estimators": 100,
                "max_depth": 3,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "random_state": 42
            },
            "RandomForest": {
                "n_estimators": 100,
                "max_depth": 5,
                "min_samples_split": 10,
                "min_samples_leaf": 4,
                "random_state": 42
            },
            "LogisticRegression": {
                "C": 0.1,
                "penalty": "l2",
                "solver": "liblinear",
                "random_state": 42
            },
            "SVM": {
                "C": 1.0,
                "kernel": "rbf",
                "probability": True,
                "random_state": 42
            },
            "KNN": {
                "n_neighbors": 5,
                "weights": "distance"
            },
            "DecisionTree": {
                "max_depth": 5,
                "min_samples_split": 10,
                "min_samples_leaf": 4,
                "random_state": 42
            }
        }

        model_params = default_params.get(model_type, {}).copy()
        model_params.update(params)

        print(f"Создание модели: {model_type}")

        if model_type == "GradientBoosting":
            self.model = GradientBoostingClassifier(**model_params)
        elif model_type == "RandomForest":
            self.model = RandomForestClassifier(**model_params)
        elif model_type == "LogisticRegression":
            self.model = LogisticRegression(**model_params)
        elif model_type == "SVM":
            self.model = SVC(**model_params)
        elif model_type == "KNN":
            self.model = KNeighborsClassifier(**model_params)
        elif model_type == "DecisionTree":
            self.model = DecisionTreeClassifier(**model_params)
        elif model_type == "NaiveBayes":
            self.model = GaussianNB()
        else:
            raise ValueError(f"Неизвестный тип модели: {model_type}")

        return self.model

    def create_ensemble(self, ensemble_type: str = "Voting", models_config: List[Dict] = None):
        """Создание ансамблевых моделей"""

        if models_config is None:
            models_config = [
                {"name": "gb", "type": "GradientBoosting", "params": {}},
                {"name": "rf", "type": "RandomForest", "params": {}},
                {"name": "lr", "type": "LogisticRegression", "params": {}}
            ]

        estimators = []
        for model_config in models_config:
            model_name = model_config["name"]
            model_type = model_config["type"]
            model_params = model_config.get("params", {})

            model_obj = self.create_model(model_type, **model_params)
            estimators.append((model_name, model_obj))
            self.models[model_name] = model_obj

        print(f"Создание ансамбля типа: {ensemble_type} с {len(estimators)} моделями")

        if ensemble_type == "Voting":
            self.model = VotingClassifier(estimators=estimators, voting='soft')
        elif ensemble_type == "Stacking":
            final_estimator = LogisticRegression(C=0.1, random_state=42)
            self.model = StackingClassifier(estimators=estimators, final_estimator=final_estimator, cv=5)

        return self.model

    def train(self, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict:
        """Обучение модели с кросс-валидацией"""

        if self.model is None:
            raise ValueError("Модель не создана")

        print("Начало обучения модели...")

        tscv = TimeSeriesSplit(n_splits=cv_folds)

        cv_scores = cross_val_score(self.model, X, y, cv=tscv, scoring='accuracy', n_jobs=-1)

        self.model.fit(X, y)
        self.is_trained = True

        self.cv_scores = {
            'mean': cv_scores.mean(),
            'std': cv_scores.std(),
            'scores': cv_scores.tolist()
        }

        self._calculate_feature_importance(X)

        print(f"Обучение завершено. CV Accuracy: {self.cv_scores['mean']:.4f} ± {self.cv_scores['std']:.4f}")

        return self.cv_scores

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Предсказание модели"""
        if not self.is_trained:
            raise ValueError("Модель не обучена")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Вероятностное предсказание"""
        if not self.is_trained:
            raise ValueError("Модель не обучена")

        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            predictions = self.predict(X)
            proba = np.zeros((len(predictions), 2))
            proba[:, 1] = predictions
            proba[:, 0] = 1 - predictions
            return proba

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """Оценка модели"""
        if not self.is_trained:
            raise ValueError("Модель не обучена")

        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)
        class_report = classification_report(y_test, y_pred, output_dict=True)

        precision = class_report['1']['precision'] if '1' in class_report else 0
        recall = class_report['1']['recall'] if '1' in class_report else 0
        f1 = class_report['1']['f1-score'] if '1' in class_report else 0

        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': conf_matrix.tolist(),
            'classification_report': class_report
        }

        print(f"Тестовая точность: {accuracy:.4f}")
        return results

    def _calculate_feature_importance(self, X: pd.DataFrame):
        """Расчет важности фич"""
        feature_names = X.columns.tolist()

        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                self.feature_importance = dict(zip(feature_names, importances))
            elif hasattr(self.model, 'coef_'):
                coef = self.model.coef_[0]
                self.feature_importance = dict(zip(feature_names, np.abs(coef)))
        except Exception as e:
            print(f"Не удалось рассчитать важность фич: {e}")
            self.feature_importance = {}

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Получить топ-N самых важных фич"""
        if not self.feature_importance:
            return pd.DataFrame()

        importance_df = pd.DataFrame(list(self.feature_importance.items()), columns=['feature', 'importance'])
        return importance_df.sort_values('importance', ascending=False).head(top_n)

    def save_model(self, filepath: str):
        """Сохранение модели"""
        import joblib

        if not self.is_trained:
            raise ValueError("Модель не обучена")

        model_data = {
            'model': self.model,
            'feature_importance': self.feature_importance,
            'cv_scores': self.cv_scores,
            'is_trained': self.is_trained
        }

        joblib.dump(model_data, filepath)
        print(f"Модель сохранена в: {filepath}")

    def load_model(self, filepath: str):
        """Загрузка модели"""
        import joblib

        model_data = joblib.load(filepath)

        self.model = model_data['model']
        self.feature_importance = model_data.get('feature_importance', {})
        self.cv_scores = model_data.get('cv_scores', {})
        self.is_trained = model_data.get('is_trained', False)

        print(f"Модель загружена из: {filepath}")


class ModelComparator:
    """Класс для сравнения нескольких моделей"""

    def __init__(self):
        self.models = {}
        self.results = {}

    def add_model(self, name: str, model: AdvancedModel):
        """Добавление модели для сравнения"""
        self.models[name] = model

    def compare_models(self, X_train: pd.DataFrame, y_train: pd.Series,
                       X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
        """Сравнение всех моделей"""

        comparison_results = []

        for name, model in self.models.items():
            print(f"Тестирование модели: {name}")

            try:
                cv_scores = model.train(X_train, y_train)
                test_results = model.evaluate(X_test, y_test)

                result = {
                    'model': name,
                    'cv_mean': cv_scores['mean'],
                    'cv_std': cv_scores['std'],
                    'test_accuracy': test_results['accuracy'],
                    'test_precision': test_results['precision'],
                    'test_recall': test_results['recall'],
                    'test_f1': test_results['f1_score']
                }

                comparison_results.append(result)
                self.results[name] = result

                print(f"Модель {name}: CV={cv_scores['mean']:.4f}, Test={test_results['accuracy']:.4f}")

            except Exception as e:
                print(f"Ошибка при тестировании модели {name}: {e}")

        results_df = pd.DataFrame(comparison_results)
        results_df = results_df.sort_values('test_accuracy', ascending=False)

        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ СРАВНЕНИЯ МОДЕЛЕЙ:")
        print("=" * 50)
        print(results_df.to_string(index=False))

        return results_df
