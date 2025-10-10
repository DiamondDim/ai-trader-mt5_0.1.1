#!/usr/bin/env python3
"""
Контроллер управления AI Trading Robot
Упрощенный скрипт для быстрого управления
"""

import os
import sys
import time
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))


def run_command(command):
    """Выполнение команды"""
    print(f"🚀 Выполнение: {command}")
    os.system(command)


def main():
    """Главная функция контроллера"""
    print("🎮 AI TRADING ROBOT CONTROLLER")
    print("=" * 40)

    while True:
        print("\nДоступные команды:")
        print("1.  📊 Статус робота")
        print("2.  🤖 Обучить модель")
        print("3.  🚀 Запустить торговлю")
        print("4.  🛑 Остановить торговлю")
        print("5.  🚨 АВАРИЙНАЯ ОСТАНОВКА")
        print("6.  🧪 Тест подключения")
        print("7.  📈 Статус MT5")
        print("8.  ❌ Выход")

        choice = input("\nВыберите команду (1-8): ").strip()

        if choice == '1':
            run_command('python main.py --mode status')

        elif choice == '2':
            symbol = input("Введите символ (по умолчанию EURUSDrfd): ").strip() or 'EURUSDrfd'
            run_command(f'python main.py --mode train --symbol {symbol}')

        elif choice == '3':
            symbol = input("Введите символ (по умолчанию EURUSDrfd): ").strip() or 'EURUSDrfd'
            print("🚀 Запуск торговли... Для остановки нажмите Ctrl+C в терминале")
            run_command(f'python main.py --mode trade --symbol {symbol}')

        elif choice == '4':
            run_command('python main.py --mode stop')

        elif choice == '5':
            confirm = input("🚨 ВНИМАНИЕ: Это закроет ВСЕ позиции! Продолжить? (y/N): ")
            if confirm.lower() == 'y':
                run_command('python main.py --mode emergency-stop')
            else:
                print("❌ Отменено")

        elif choice == '6':
            run_command('python main.py --mode test')

        elif choice == '7':
            run_command('python main.py --mode status')

        elif choice == '8':
            print("👋 Выход из контроллера")
            break

        else:
            print("❌ Неверная команда")

        # Пауза перед следующим выводом меню
        time.sleep(1)


if __name__ == "__main__":
    main()
