from bestchange_api import BestChange

from currencies import Currency, RUB, USDT
from currencies import TON, BTC, XMR, ETH, TRX
from observers import IObserver, GoogleSheetsObserver
from managers import BestChangeManager
from configs import SHEET_NAME, SPREADSHEET_ID, CREDENTIALS_FILE


#TODO вынеси этот код в отдельную функцию и вызывай ее из main. Это нужно чтобы была едиинай точка входа в проект
if __name__ == "__main__":
    rub = RUB()
    usdt = USDT()
    ton = TON()
    btc = BTC()
    xmr = XMR()
    eth = ETH()
    trx = TRX()
    best_change_api = BestChange(load=False, cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=1)
    change_manager = BestChangeManager(best_change_api, rub, usdt, ton, btc, xmr, eth, trx)
    google_sheets_observer = GoogleSheetsObserver(sheet_name=SHEET_NAME, spreadsheet_id=SPREADSHEET_ID, credentials_file=CREDENTIALS_FILE)
    change_manager.register_observer(google_sheets_observer)
    ## change_manager.notify_observers() # Single update
    updates_daemon = change_manager.start_updates() # Continuous update
    updates_daemon.join()