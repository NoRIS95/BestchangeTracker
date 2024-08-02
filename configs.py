import os
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = 'logs'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 10

handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.handlers[0].doRollover()

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