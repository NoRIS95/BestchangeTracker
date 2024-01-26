from callbacks import get_actual_price, get_best_rate
import os
import time
from sheetfu import SpreadsheetApp
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


load_dotenv()
SPREADSHEET_ID = os.getenv('ID_TOKEN')
SHEET_NAME = os.getenv('SHEET_NAME')
SLEEP_TIME_SECONDS = 30
EXCHANGES = ["Биржа", "Сова", 'NetEx24', 'Шахта', 'Ферма']
CRIPT_LIST = ['BTC', 'ETH', 'TON', 'USDT', 'XMR', 'TON']
MONETARY_CUR_LIST = ['USDT', 'RUB']
ALPHABET = list((''.join([chr(i) for i in range(99, 114)])).upper())
STRING_NUMS_LIST = [i for i in range(5,11)]           #строка, где записывается цена крипты
row_ind = 0  #индекс строки не в самой таблице, а в списке 
CELL_CALLBACKS = {}


for cript in CRIPT_LIST:
    row = STRING_NUMS_LIST[row_ind] #индекс строки в самой таблице
    col_ind = 0    #индекс колонки не в самой таблице, а под каким индексом она в списке ALPHABET
    for exchange in EXCHANGES:
        for money in MONETARY_CUR_LIST:
            letter = ALPHABET[col_ind]
            cell = letter + str(row)
            if exchange == "Биржа":
               CELL_CALLBACKS[cell] = (get_actual_price, (cript, money))
            else:
                CELL_CALLBACKS[cell] = (get_best_rate, (exchange, cript, money))
            col_ind += 1
        col_ind += 1
    row_ind += 1


if __name__ == '__main__':
    sa = SpreadsheetApp('secret.json')
    spreadsheet = sa.open_by_id(SPREADSHEET_ID)
    sheet = spreadsheet.get_sheet_by_name(SHEET_NAME)
    while True:
        for cell_id, (fn, args) in CELL_CALLBACKS.items():
            value = fn(*args)
            if value is None:
                value = '-'
            cell = sheet.get_range_from_a1(cell_id)
            cell.set_value(value)

        time.sleep(SLEEP_TIME_SECONDS)

