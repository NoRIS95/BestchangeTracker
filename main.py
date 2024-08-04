import asyncio

from bestchange_api import BestChange

from currencies import RUB, USDT
from currencies import TON, BTC, XMR, ETH, TRX
from observers import GoogleSheetsObserver
from managers import BestChangeManager
from table import Table
from logger import setup_logger


async def call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx):
    return BestChangeManager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)

async def call_googlesheetsobserver(sheet_name, spreadsheet_id, credentials_file):
    return GoogleSheetsObserver(sheet_name, spreadsheet_id, credentials_file)

async def create_currencies_and_table():
    rub = RUB()
    usdt = USDT()
    ton = TON()
    btc = BTC()
    xmr = XMR()
    eth = ETH()
    trx = TRX()
    table = Table()
    return rub, usdt, ton, btc, xmr, eth, trx, table

async def run_programm():
    setup_logger()
    rub, usdt, ton, btc, xmr, eth, trx, table = await create_currencies_and_table()
    table = Table()
    best_change_api = BestChange(load=False, cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=1)
    # change_manager = BestChangeManager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)
    # google_sheets_observer = GoogleSheetsObserver(sheet_name=table.get_sheet_name(),\    #Родной вариант
    #                                                 spreadsheet_id=table.get_spreadsheet_id(), credentials_file=table.get_credentials_file())
    
    change_manager, google_sheets_observer = await asyncio.gather(call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx),\
                                                                  call_googlesheetsobserver(sheet_name=table.get_sheet_name(),\
                                                   spreadsheet_id=table.get_spreadsheet_id(), credentials_file=table.get_credentials_file()))
    
    # change_manager = await call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)
    # google_sheets_observer = await call_googlesheetsobserver(sheet_name=table.get_sheet_name(),\
    #                                                 spreadsheet_id=table.get_spreadsheet_id(), credentials_file=table.get_credentials_file())
    change_manager.register_observer(google_sheets_observer)
    ## change_manager.notify_observers() # Single update
    updates_daemon = await change_manager.start_updates() # Continuous update
    # updates_daemon = asyncio.create_task(change_manager.start_updates())  # Continuous update
    await updates_daemon.join()
    # updates_daemon.join()


if __name__ == "__main__":
    asyncio.run(run_programm())