import asyncio

from bestchangeAPI.api import BestChange

from logger import setup_logger
from callbacks import call_best_change_manager, call_googlesheetsobserver, create_currencies_and_table

async def run_programm():
    best_change_api = BestChange(cache_seconds=45, exchangers_reviews=False, split_reviews=False, ssl=False, daemon=True)
    await best_change_api.load()
    setup_logger()
    task_currencies_and_table = asyncio.create_task(create_currencies_and_table())
    rub, usdt, ton, btc, xmr, eth, trx, table = await task_currencies_and_table
    change_manager, google_sheets_observer = await asyncio.gather(call_best_change_manager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx),\
                                                                  call_googlesheetsobserver(sheet_name=table.get_sheet_name(),\
                                                   spreadsheet_id=table.get_spreadsheet_id(), credentials_file=table.get_credentials_file()))
    change_manager.register_observer(google_sheets_observer)
    # change_manager.notify_observers() # Single update
    updates_daemon = await change_manager.start_updates() # Continuous update 
    # await updates_daemon.join()
    updates_daemon.join()


if __name__ == "__main__":
    asyncio.run(run_programm())