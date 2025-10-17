import joblib
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings

warnings.filterwarnings('ignore')


def train_model(symbol=None):
    """
    Обучение модели для конкретного символа
    """
    try:
        from src.utils.config import load_config
        from src.core.mt5_client import load_data
        from src.ml.feature_engineer import create_features

        config = load_config()

        # Используем переданный символ или из конфига
        if symbol:
            trading_symbol = symbol
        else:
            trading_symbol = config['trading']['symbol']

        print(f"📊 Обучение модели для символа: {trading_symbol}")

        # Загрузка данных для конкретного символа
        data = load_data(
            symbol=trading_symbol,
            timeframe_str=config['data']['timeframe'],
            bars_count=config['data']['bars_count']
        )

        if data.empty:
            print(f"❌ Не удалось загрузить данные для {trading_symbol}")
            return False

        print(f"✅ Загружено {len(data)} баров")

        # Создание признаков ДЛЯ ОБУЧЕНИЯ (с целевой переменной)
        print("🔧 Создание признаков для обучения...")
        features_df = create_features(data, for_training=True)

        if features_df.empty or features_df.isnull().all().all():
            print("❌ Не удалось создать признаки или все признаки NaN")
            return False

        # Подготовка данных для обучения
        # ИСКЛЮЧАЕМ future_close из признаков!
        exclude_cols = ['target', 'future_close']
        X = features_df.drop(exclude_cols, axis=1)
        y = features_df['target']

        # Удаляем строки с NaN
        valid_indices = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[valid_indices]
        y = y[valid_indices]

        if len(X) == 0:
            print("❌ Нет валидных данных для обучения после очистки NaN")
            return False

        print(f"✅ Валидных образцов для обучения: {len(X)}")
        print(f"✅ Количество признаков: {X.shape[1]}")
        print(f"✅ Признаки: {list(X.columns)}")

        # Разделение на тренировочную и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        # Обучение модели
        print("🎯 Обучение GradientBoosting модели...")
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42
        )

        model.fit(X_train, y_train)

        # Оценка модели
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"📈 Точность модели: {accuracy:.4f} ({accuracy * 100:.2f}%)")
        print("\n📊 Отчет по классификации:")
        print(classification_report(y_test, y_pred))

        # Важность признаков
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\n🔝 Топ-10 важных признаков:")
        print(feature_importance.head(10).to_string(index=False))

        # Создаем папку models если её нет
        os.makedirs('models', exist_ok=True)

        # Сохранение модели с именем включающим символ и дату
        model_filename = f"model_{trading_symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}.pkl"
        model_path = os.path.join('models', model_filename)

        joblib.dump(model, model_path)

        # Сохраняем информацию о последней модели в конфиг
        config['model']['last_trained'] = datetime.now().isoformat()
        config['model']['current_model'] = model_path
        config['model']['symbol'] = trading_symbol
        config['model']['accuracy'] = float(accuracy)
        config['model']['features_count'] = int(X.shape[1])
        config['model']['training_samples'] = int(len(X))

        from src.utils.config import save_config
        save_config(config)

        print(f"✅ Модель сохранена: {model_path}")
        print(f"💾 Размер модели: {os.path.getsize(model_path) / 1024 / 1024:.2f} MB")

        return True

    except Exception as e:
        print(f"❌ Ошибка при обучении модели: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_model_for_symbol(symbol):
    """
    Загрузка модели для конкретного символа
    """
    try:
        models_dir = 'models'

        if not os.path.exists(models_dir):
            print(f"❌ Папка {models_dir} не существует")
            return None

        # Ищем модели для символа (правильный формат: model_SYMBOL_YYYYMMDD_HHMM.pkl)
        model_files = [f for f in os.listdir(models_dir)
                       if f.startswith(f'model_{symbol}_') and f.endswith('.pkl')]

        if not model_files:
            print(f"❌ Не найдена модель для символа {symbol}")
            print(f"💡 Доступные модели: {[f for f in os.listdir(models_dir) if f.endswith('.pkl')]}")
            return None

        # Берем самую свежую модель (последнюю по времени)
        latest_model = sorted(model_files, reverse=True)[0]
        model_path = os.path.join(models_dir, latest_model)

        model = joblib.load(model_path)

        # Получаем информацию о модели
        from src.utils.config import load_config
        config = load_config()

        model_info = {
            'path': model_path,
            'symbol': symbol,
            'accuracy': config['model'].get('accuracy', 'N/A'),
            'features': config['model'].get('features_count', 'N/A'),
            'trained': config['model'].get('last_trained', 'N/A')
        }

        print(f"✅ Загружена модель: {latest_model}")
        print(f"   📊 Точность: {model_info['accuracy']}")
        print(f"   🔧 Признаков: {model_info['features']}")
        print(f"   ⏰ Обучена: {model_info['trained'][:16]}")

        return model

    except Exception as e:
        print(f"❌ Ошибка загрузки модели для {symbol}: {e}")
        return None


def get_available_models():
    """
    Получает список всех доступных моделей (только правильного формата)
    """
    try:
        models_dir = 'models'
        if not os.path.exists(models_dir):
            return []

        # Фильтруем только файлы правильного формата: model_SYMBOL_YYYYMMDD_HHMM.pkl
        model_files = [f for f in os.listdir(models_dir)
                       if f.startswith('model_') and f.endswith('.pkl')
                       and len(f.split('_')) >= 3]  # Должен быть символ и дата

        models_info = []
        for model_file in model_files:
            try:
                # Парсим информацию из имени файла
                # Формат: model_SYMBOL_YYYYMMDD_HHMM.pkl
                base_name = model_file.replace('.pkl', '')
                parts = base_name.split('_')

                if len(parts) >= 3:
                    symbol = parts[1]
                    date_str = parts[2]
                    # Проверяем, что date_str похож на дату (YYYYMMDD)
                    if len(date_str) == 8 and date_str.isdigit():
                        models_info.append({
                            'symbol': symbol,
                            'file': model_file,
                            'date': date_str,
                            'path': os.path.join(models_dir, model_file)
                        })
            except Exception as e:
                print(f"⚠️ Не удалось обработать файл модели {model_file}: {e}")
                continue

        return sorted(models_info, key=lambda x: x['date'], reverse=True)

    except Exception as e:
        print(f"❌ Ошибка получения списка моделей: {e}")
        return []


def delete_old_models(symbol, keep_count=3):
    """
    Удаление старых моделей, оставляя только указанное количество самых свежих
    """
    try:
        models = get_available_models()
        symbol_models = [m for m in models if m['symbol'] == symbol]

        if len(symbol_models) <= keep_count:
            return

        # Сортируем от старых к новым и удаляем старые
        old_models = sorted(symbol_models, key=lambda x: x['date'])[:-keep_count]

        for old_model in old_models:
            try:
                os.remove(old_model['path'])
                print(f"🗑️ Удалена старая модель: {old_model['file']}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить модель {old_model['file']}: {e}")

    except Exception as e:
        print(f"❌ Ошибка при удалении старых моделей: {e}")


def delete_model(model_path):
    """
    Удаление модели
    """
    try:
        if os.path.exists(model_path):
            os.remove(model_path)
            print(f"✅ Модель удалена: {model_path}")
            return True
        else:
            print(f"❌ Файл модели не найден: {model_path}")
            return False
    except Exception as e:
        print(f"❌ Ошибка удаления модели: {e}")
        return False
