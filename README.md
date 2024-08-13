# Телеграм-бот для BestChange.
_С помощью этого телеграмм-бота можно узнать текущие цены криптовалют в определённых обменных пунктах и топ 10 обменных пунктов на BestChange._
## Инструкция по запуску телеграм-бота: ##
_Зарегистрировать бота с помощью телеграм-бота @BotFather._
```
git clone https://github.com/NoRIS95/BestchangeTracker.git
cp .env.template .env
BOT_TOKEN=<вписать сюда токен тг-бота из п.1> # в .env файле
python3 -m venv dev_venv
source ./bin/dev_venv/activate
pip install -r requirements.txt
```
 
### Запуск телеграм-бота ###
 
```
python main.py
```
