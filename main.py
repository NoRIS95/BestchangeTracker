import os
import time
from datetime import datetime
from sheetfu import SpreadsheetApp
from dotenv import load_dotenv, find_dotenv
from callbacks import get_actual_price, get_best_rate, get_top


load_dotenv()
n_top=10
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME')
SLEEP_TIME_LOOP = 120
EXCHANGES = ["Биржа", "Сова", 'NetEx24', 'Шахта', 'Ферма']
CRIPT_LIST = ['BTC', 'ETH', 'TON', 'USDT', 'XMR', 'TRX']
MONETARY_CUR_LIST = ['USDT', 'RUB']
MONETARY_CUR_LIST_TOP = ['RUB', 'USDT']
row_ind = 0
CELL_CALLBACKS = {}


for cript in CRIPT_LIST:
    col_ind = 0
    for exchange in EXCHANGES:
        for money in MONETARY_CUR_LIST:
            if exchange == "Биржа":
                CELL_CALLBACKS[(row_ind, col_ind)] = (get_actual_price, (cript, money))
            else:
                CELL_CALLBACKS[(row_ind, col_ind)] = (get_best_rate, (exchange, cript, money))
            col_ind += 1
        col_ind += 1
    row_ind += 1


if __name__ == '__main__':
    sheet = SpreadsheetApp('secret.json').open_by_id(spreadsheet_id=SPREADSHEET_ID).get_sheet_by_name(SHEET_NAME)
    while True:
        data_range = sheet.get_range_from_a1('C5:P35')
        backgrounds = data_range.get_backgrounds()
        values = data_range.get_values()
        top_exchanges = get_top()
        
        row_ind_top = 26 - 5  # топ начинается с 26 строчки, а значения нашей таблицы с 5
        for exch in top_exchanges:
            col_ind_top = 0
            CELL_CALLBACKS[(row_ind_top, col_ind_top)] = (lambda x: x, [exch])
            for cr in CRIPT_LIST:
                for mon in MONETARY_CUR_LIST_TOP:
                    col_ind_top += 1
                    CELL_CALLBACKS[(row_ind_top, col_ind_top)] = (get_best_rate, (exch, cr, mon))
            row_ind_top += 1
        
        for (row_ind, col_ind), (fn, args) in CELL_CALLBACKS.items():
            value = fn(*args)
            if value is None:
                value = '-'
            values[row_ind][col_ind] = value
        data_range.set_values(values)
        data_range.set_backgrounds(backgrounds)
        # data_range.commit()
        time.sleep(SLEEP_TIME_LOOP)