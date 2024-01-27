from callbacks import get_actual_price, get_best_rate, get_top
import os
import time
from sheetfu import SpreadsheetApp
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


load_dotenv()
n_top=10
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME')
SLEEP_TIME_LOOP = 120
SLEEP_TIME_REQUEST = 1
EXCHANGES = ["Биржа", "Сова", 'NetEx24', 'Шахта', 'Ферма']
CRIPT_LIST = ['BTC', 'ETH', 'TON', 'USDT', 'XMR', 'TRX']
MONETARY_CUR_LIST = ['USDT', 'RUB']
MONETARY_CUR_LIST_TOP = reversed(MONETARY_CUR_LIST)
ALPHABET = list((''.join([chr(i) for i in range(99, 114)])).upper())
ALPHABET_FOR_TOP = list((''.join([chr(i) for i in range(99, 112)])).upper())
STRING_NUMS_LIST = [i for i in range(5,11)]
STRING_NUMS_LIST_TOP = [i for i in range(26,26 + n_top)]
row_ind = 0
CELL_CALLBACKS = {}


for cript in CRIPT_LIST:
    row = STRING_NUMS_LIST[row_ind] 
    col_ind = 0
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
        top_exchanges = get_top()
        
        row_ind_top = 0
        for exch in top_exchanges:
            row_top = STRING_NUMS_LIST_TOP[row_ind_top]
            let = ALPHABET_FOR_TOP[0]
            cl = let + str(row_top)
            CELL_CALLBACKS[cl] = (lambda x: x, [exch])
            col_ind_top = 1
            for cr in CRIPT_LIST:
                for mon in MONETARY_CUR_LIST_TOP:
                    let = ALPHABET_FOR_TOP[col_ind_top]
                    cl = let + str(row_top)
                    CELL_CALLBACKS[cl] = (get_best_rate, (exch, cr, mon))
                    col_ind_top += 1
            row_ind_top += 1
        
        for cell_id, (fn, args) in CELL_CALLBACKS.items():
            value = fn(*args)
            if value is None:
                value = '-'
            cell = sheet.get_range_from_a1(cell_id)
            cell.set_value(value)
            time.sleep(SLEEP_TIME_REQUEST)


        time.sleep(SLEEP_TIME_LOOP)