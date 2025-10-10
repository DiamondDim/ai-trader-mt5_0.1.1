#!/usr/bin/env python3
"""
Упрощенный запуск AI Trading Robot
"""

import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def main():
    print("🤖 AI Trading Robot - Быстрый запуск")
    print("=====================================")
    print("1. Тестирование подключения")
    print("2. Обучение модели")
    print("3. Запуск торговли")
    print("4. Просмотр символов")
    print("5. Выход")

    choice = input("\nВыберите действие (1-5): ").strip()

    if choice == "1":
        symbol = input("Введите символ (или Enter для выбора): ").strip()
        if symbol:
            os.system(f"python main.py --mode test --symbol {symbol}")
        else:
            os.system("python main.py --mode test")
    elif choice == "2":
        symbol = input("Введите символ (или Enter для выбора): ").strip()
        if symbol:
            os.system(f"python main.py --mode train --symbol {symbol}")
        else:
            os.system("python main.py --mode train")
    elif choice == "3":
        symbol = input("Введите символ (или Enter для выбора): ").strip()
        if symbol:
            os.system(f"python main.py --mode trade --symbol {symbol}")
        else:
            os.system("python main.py --mode trade")
    elif choice == "4":
        os.system("python main.py --mode symbols")
    elif choice == "5":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()

