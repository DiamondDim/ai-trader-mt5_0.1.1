

@echo off
echo Установка зависимостей AI Trading Robot...
echo ==========================================

python -m pip install --upgrade pip

echo  Устанавливаю MetaTrader5...
pip install MetaTrader5==5.0.5328

echo  Устанавливаю pandas...
pip install pandas>=2.0.0

echo  Устанавливаю numpy...
pip install numpy>=1.24.0

echo  Устанавливаю scikit-learn...
pip install scikit-learn>=1.3.0

echo  Устанавливаю matplotlib...
pip install matplotlib>=3.7.0

echo  Устанавливаю PyYAML...
pip install PyYAML>=6.0

echo  Устанавливаю joblib...
pip install joblib>=1.3.0

echo  Устанавливаю scipy...
pip install scipy>=1.11.0

echo  Устанавливаю python-dotenv...
pip install python-dotenv>=1.0.0

echo.
echo  Проверяем установку...
python -c "import MetaTrader5 as mt5; print('✅ MetaTrader5: OK')"
python -c "import pandas as pd; print('✅ pandas: OK')"
python -c "import numpy as np; print('✅ numpy: OK')"
python -c "import sklearn; print('✅ scikit-learn: OK')"
python -c "import yaml; print('✅ PyYAML: OK')"

echo.
echo  Установка завершена!
echo  Теперь вы можете запустить:
echo   python main.py --mode test
pause
