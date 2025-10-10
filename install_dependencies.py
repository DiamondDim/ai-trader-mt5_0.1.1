#!/usr/bin/env python3
"""
Скрипт для установки всех необходимых зависимостей
"""

import subprocess
import sys


def run_command(command):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def main():
    print("🔧 Установка зависимостей для AI Trading Robot...")
    print("=" * 50)

    dependencies = [
        "MetaTrader5==5.0.5328",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.7.0",
        "PyYAML>=6.0",
        "joblib>=1.3.0",
        "scipy>=1.11.0",
        "python-dotenv>=1.0.0"
    ]

    for dep in dependencies:
        print(f"📦 Устанавливаю {dep}...")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {dep}")

        if success:
            print(f"✅ {dep} установлен успешно")
        else:
            print(f"❌ Ошибка установки {dep}: {stderr}")

    print("=" * 50)
    print("🧪 Проверка установки...")

    # Проверяем основные импорты
    test_imports = [
        ("MetaTrader5", "mt5"),
        ("pandas", "pd"),
        ("numpy", "np"),
        ("sklearn", "sklearn"),
        ("yaml", "yaml"),
        ("joblib", "joblib")
    ]

    all_imports_ok = True
    for module, alias in test_imports:
        try:
            if module == "sklearn":
                import sklearn
            else:
                __import__(module)
            print(f"✅ {module} импортируется успешно")
        except ImportError as e:
            print(f"❌ Ошибка импорта {module}: {e}")
            all_imports_ok = False

    if all_imports_ok:
        print("🎉 Все зависимости установлены успешно!")
        print("🚀 Теперь вы можете запустить проект:")
        print("   python main.py --mode test")
    else:
        print("⚠️  Некоторые зависимости не установились. Проверьте ошибки выше.")


if __name__ == "__main__":
    main()
