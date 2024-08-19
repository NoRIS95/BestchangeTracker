import asyncio

# from bestchangeapi.api import BestChange
from bestchangeapi.api import BestChange
from currencies import RUB, USDT
from currencies import TON, BTC, XMR, ETH, TRX
from observers import TelegramObserver
from managers import BestChangeManager
from configs import USER_CONDITIONS, BEST_CHANGE_API
from classes import StatusDialog


async def call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx):
    return BestChangeManager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)

async def call_telegram_observer(bot, chat_id):
    return TelegramObserver(bot, chat_id)

async def create_currencies_and_table():
    rub = RUB()
    usdt = USDT()
    ton = TON()
    btc = BTC()
    xmr = XMR()
    eth = ETH()
    trx = TRX()
    return rub, usdt, ton, btc, xmr, eth, trx

async def get_crypt_info(bot, user_id, chat_id):
    global TASK_CHANGE_MANAGER, TASK_TELEGRAM_OBSERVER, CHANGE_MANAGER, TELEGRAM_OBSERVER
    USER_CONDITIONS.data[user_id] = StatusDialog.STATUS_OF_ASK_CRIPT.value
    task_currencies_and_table = asyncio.create_task(create_currencies_and_table())
    rub, usdt, ton, btc, xmr, eth, trx = await task_currencies_and_table

    TASK_CHANGE_MANAGER = asyncio.create_task(call_best_change_manager(BEST_CHANGE_API, rub, usdt, ton, btc, xmr, eth, trx))
    TASK_TELEGRAM_OBSERVER = asyncio.create_task(call_telegram_observer(bot=bot, chat_id=chat_id))
    CHANGE_MANAGER = await TASK_CHANGE_MANAGER
    TELEGRAM_OBSERVER = await TASK_TELEGRAM_OBSERVER

    CHANGE_MANAGER.register_observer(TELEGRAM_OBSERVER)
    message_to_send = await CHANGE_MANAGER.notify_observers()
    return CHANGE_MANAGER, message_to_send