import time

from api import BestChange

from currencies import RUB, USDT
from currencies import TON, BTC, XMR, ETH, TRX
from observers import TelegramObserver
from managers import BestChangeManager


async def call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx):
    return BestChangeManager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)

async def call_telegram_observer(bot, chat_id):
    return TelegramObserver(bot, chat_id)

async def get_bestchangeapi():
    start = time.time()
    best_change_api = BestChange(cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=30)
    end = time.time()
    print(f'Время выполнения get_bestchangeapi: {(end - start) * 1000:.2f} мс')  # Время в миллисекундах
    return best_change_api

async def create_currencies_and_table():
    rub = RUB()
    usdt = USDT()
    ton = TON()
    btc = BTC()
    xmr = XMR()
    eth = ETH()
    trx = TRX()
    return rub, usdt, ton, btc, xmr, eth, trx