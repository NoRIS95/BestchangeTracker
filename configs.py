from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Dispatcher
from aiogram import Bot, Dispatcher
from simplejsondb import Database

from classes import Tg_bot

BEST_CHANGE_API = None
BOT_TOKEN = Tg_bot().get_bot_token()
# ADMIN_ID = os.getenv('ADMIN_ID')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

TASK_CHANGE_MANAGER = None
TASK_TELEGRAM_OBSERVER = None
CHANGE_MANAGER = None
TELEGRAM_OBSERVER = None

# Создаем хранилище для состояний
storage = MemoryStorage()

# Создаем объект диспетчера и передаем в него хранилище
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

USER_CONDITIONS = Database('user_states.json', default=dict())

LOG_DIR = 'logs'

SLEEP_TIME_LOOP = 30

N_TOP=10

EXCHANGES = ["Сова", 'Alfabit', 'Шахта', 'Ферма']
EX_SOVA = 0
EX_NETEX24 = 1
EX_SHAHTA = 2
EX_FERMA = 3

CRYPTOS_LIST = ['BTC', 'ETH', 'TON', 'USDT', 'XMR', 'TRX']
CRYPTO_BTC = 0
CRYPTO_ETH = 1
CRYPTO_TON = 2
CRYPTO_USDT = 3
CRYPTO_XMR = 4
CRYPTO_TRX = 5

FIATS_LIST = ['RUB']
FIATS_LIST_TOP = ['RUB', 'USDT'] # для нижней части таблицы (там в первой колонке рубли, во второй USDT)
FIATS_LIST_PRICES = FIATS_LIST_TOP[::-1] # для верхней левой части таблицы (там в первой колонке USDT, во второй рубли)
RUB_TYPES = ['CASH', 'CARD']
RUB_CASH_TYPE = 0
RUB_CARD_TYPE = 1
FIAT_RUB = 0


USDT_PROTOCOLS = ['Tether BEP20 (USDT)', 'Tether ERC20 (USDT)', 'Tether TRC20 (USDT)']
FIAT_CARDS_METHODS = ['Visa/MasterCard RUB', 'Альфа-Банк RUB', 'ВТБ RUB', 'Газпромбанк RUB', 'Карта Мир RUB', 'Сбербанк RUB', 'Тинькофф RUB']
USDT_TYPES = ['BEP20', 'ERC20', 'TRC20', 'CARD', 'CASH']
BEP20_TYPE = 0
ERC20_TYPE = 1
TRC20_TYPE = 2
CARD_TYPE = 3
CASH_TYPE = 4

OLD_NEW_TON_NAME = {"TON": "TONCOIN"}
OLD_TON_NAME_NUM = 0
NEW_TON_NAME_NUM = 1


CUR_RUB = 0
CUR_USDT = 1
CUR_TON = 2
CUR_BTC = 3
CUR_XMR = 4
CUR_ETH = 5
CUR_TRX = 6