# Installation Guide

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/DiamondDim/ai-trader-mt5.git
   cd ai-trader-mt5
   Set up virtual environment
   
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   Install dependencies


   pip install -r requirements.txt
 # Configure your MT5 account

  Edit config/settings.yaml

  Add your MT5 login, server, and password

  Adjust trading parameters as needed

# Test the connection

```bash
python main.py --mode test
Train the model


python main.py --mode train
Start trading


python main.py --mode trade
```
# Common Issues
MetaTrader5 Installation

If you have issues with MetaTrader5:

```bash
pip install MetaTrader5 --upgrade
Missing Dependencies

pip install --upgrade -r requirements.txt
```
# Configuration
```bash
Edit config/settings.yaml with your details:

yaml
mt5:
  login: YOUR_MT5_LOGIN
  server: "YOUR_BROKER_SERVER"
  password: "YOUR_PASSWORD"

trading:
  symbol: "EURUSDrfd"
  timeframe: "M15"
  risk_per_trade: 0.02
```
# Risk Warning
⚠️ Always test on demo account first! Never risk more than you can afford to lose.

# Шаг 4: Создаем дополнительные скрипты

## Создаем train_model.py
```bash
cat > scripts/train_model.py << 'EOF'
#!/usr/bin/env python3


#Скрипт для обучения модели

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.config import Config
from src.core.mt5_client import MT5Client
from src.ml.model import TradingModel
from src.ml.feature_engineer import FeatureEngineer

def main():
    config = Config.load_config()
    
    print("🎯 Обучение модели...")
    
    mt5 = MT5Client(config)
    if not mt5.connect():
        return
    
    data = mt5.get_historical_data(
        config['trading']['symbol'],
        config['trading']['timeframe'],
        bars=5000
    )
    
    if data is None:
        print("❌ Не удалось загрузить данные")
        return
    
    feature_engineer = FeatureEngineer()
    model = TradingModel(model_type=config['ml']['model_type'])
    
    model.train(data, feature_engineer)
    model.save_model(config['ml']['model_path'])
    
    mt5.disconnect()
    print("✅ Обучение завершено!")

if __name__ == "__main__":
    main()
EOF
```
# Создаем optimize.py
```bash
cat > scripts/optimize.py << 'EOF'
#!/usr/bin/env python3

#Скрипт для оптимизации гиперпараметров модели


import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

print("⚙️ Оптимизация гиперпараметров в разработке...")
print("Скоро будет доступно!")
```
