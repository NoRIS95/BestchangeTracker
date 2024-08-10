import numpy as np
import logging
import cryptocompare
import asyncio
import time
import gspread_asyncio

from google.oauth2.service_account import Credentials
from abc import ABC, abstractmethod
from collections import defaultdict

from currencies import Currency
from configs import *


class IObserver(ABC):
    @abstractmethod
    async def update(self):
        pass

class BestChangeUnit(IObserver):
    def __init__(self, currencies):
        self.name = ""
        self.changer_id = -1  # Уникальный айди обменника

        self.__rub = currencies[CUR_RUB]
        self.__usdt = currencies[CUR_USDT]
        self.__ton = currencies[CUR_TON]
        self.__btc = currencies[CUR_BTC]
        self.__xmr = currencies[CUR_XMR]
        self.__eth = currencies[CUR_ETH]
        self.__trx = currencies[CUR_TRX]
        self.__all_unit_rates = []  # Список всех состояний обмена со всех обменников
        self.__self_unit_rates = []  # Список состояний обмена, только данного обменника

        self.currencies_dict = {
            CRYPTOS_LIST[CRYPTO_USDT]: self.__usdt,
            CRYPTOS_LIST[CRYPTO_TON]: self.__ton,
            CRYPTOS_LIST[CRYPTO_ETH]: self.__eth,
            CRYPTOS_LIST[CRYPTO_XMR]: self.__xmr,
            CRYPTOS_LIST[CRYPTO_BTC]: self.__btc,
            CRYPTOS_LIST[CRYPTO_TRX]: self.__trx,
            FIATS_LIST[FIAT_RUB]: self.__rub,
        }

    def set_changer_id(self, id):
        self.changer_id = id

    def set_unit_chnges_rates(self, rates):
        self.__all_unit_rates = rates
        self.__self_unit_rates = [r for r in self.__all_unit_rates if r['exchange_id'] == self.changer_id]

    async def async_update_rates(self, currencies):
        async def async_set_naked_price_rub(cur, currency):
            return cur.set_naked_price_rub(currency.get_naked_price_rub())

        async def async_set_naked_price_usdt(cur, currency):
            return cur.set_naked_price_usdt(currency.get_naked_price_usdt())

        tasks = []
        for currency in currencies:
            currency: Currency
            cur: Currency = self.currencies_dict[currency.name]
            tasks.append(asyncio.create_task(async_set_naked_price_rub(cur, currency)))
            tasks.append(asyncio.create_task(async_set_naked_price_usdt(cur, currency)))
        await asyncio.gather(*tasks)

    async def update(self):
        await self.async_update_rates(self.currencies_dict.values())

    def __str__(self):
        ret_str = f"{self.name}\n"
        for cur in self.currencies_dict.items():
            ret_str += (cur[1].__str__() + "\n")
        return ret_str

    def get_rate(self, curr_client_give: str, cur_client_get: str):
        cc_give = curr_client_give.split("_")
        if len(cc_give) == 1:
            cur_give = self.currencies_dict[cc_give[0]]
        else:
            cur_give = self.currencies_dict[cc_give[0]].types_dicts[cc_give[1]]

        cc_get = cur_client_get.split("_")
        if len(cc_get) == 1:
            cur_get = self.currencies_dict[cc_get[0]]
        else:
            cur_get = self.currencies_dict[cc_get[0]].types_dicts[cc_get[1]]

        rate = [rate['rate'] for rate in self.__self_unit_rates if rate['get_id'] in cur_get.currency_ids \
                and rate['give_id'] in cur_give.currency_ids]

class GoogleSheetsObserver(IObserver):
    def __init__(self, sheet_name, spreadsheet_id, credentials_file):
        self.sheet_name = sheet_name
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.exchangers = None
        self.currencies = None
        self.rates = None
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(self.get_creds)

    def get_creds(self):
        creds = Credentials.from_service_account_file(self.credentials_file, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return creds

    async def async_update(self):
        agc = await self.agcm.authorize()
        spreadsheet = await agc.open_by_key(self.spreadsheet_id)
        sheet = await spreadsheet.worksheet(self.sheet_name)

        cell_callbacks = {}

        all_currencies_list = [OLD_NEW_TON_NAME.get(c, c) for c in CRYPTOS_LIST] + FIATS_LIST
        actual_prices = await asyncio.to_thread(cryptocompare.get_price, all_currencies_list, all_currencies_list)

        def get_actual_price(get_currency_name, give_currency_name):
            get_currency_name = OLD_NEW_TON_NAME.get(get_currency_name, get_currency_name)
            give_currency_name = OLD_NEW_TON_NAME.get(give_currency_name, give_currency_name)
            actual_price = actual_prices[get_currency_name][give_currency_name]
            return actual_price

        async def get_best_rate(exchanger_name: str, get_currency_name: str, give_currency_name: str):
            get_currency_name = OLD_NEW_TON_NAME.get(get_currency_name, get_currency_name)
            give_currency_name = OLD_NEW_TON_NAME.get(give_currency_name, give_currency_name)
            try:
                exchanger_search_result = self.exchangers.search_by_name(exchanger_name)
            except AttributeError:
                logging.error(f'Failed to search result of exchanger {exchanger_name} from BestChange API for get best rate')
                return None
            if exchanger_search_result:
                exchanger_id = list(self.exchangers.search_by_name(exchanger_name).keys())[0]
            else:
                return None
            try:
                get_cur_ids = {cur['id'] for cur in self.currencies.search_by_name(get_currency_name).values() \
                            if (get_currency_name in cur['name'])}
                give_cur_ids = {cur['id'] for cur in self.currencies.search_by_name(give_currency_name).values() \
                            if (give_currency_name in cur['name'])}
            except:
                logging.error(f'Failed to search getting currency or giving currency of exchanger {exchanger_name} from BestChange API for get best rate')
                return None
            rates = [r['rate'] for r in self.rates if r['exchange_id'] == exchanger_id and r['give_id'] \
                        in give_cur_ids and r['get_id'] in get_cur_ids]
            if len(rates) == 0:
                return None
            best_rate = min(rates)
            return best_rate

        row_ind = 0
        for cript in CRYPTOS_LIST:
            col_ind = 0
            for exchange in ['Биржа'] + EXCHANGES:
                for money in FIATS_LIST_PRICES:
                    if exchange == "Биржа":
                        cell_callbacks[(row_ind, col_ind)] = (get_actual_price, (cript, money))
                    else:
                        cell_callbacks[(row_ind, col_ind)] = (get_best_rate, (exchange, cript, money))
                    col_ind += 1
                col_ind += 1
            row_ind += 1

        data_range = await sheet.range('C5:P35')
        values = await sheet.get('C5:P35')

        async def get_top(n=10, money_list=['USDT', 'RUB'], cript_list=['BTC', 'ETH', 'TON', 'XMR', 'TRX']):
            start = time.time()
            try:
                exchangers = {v['id']: v['name'] for v in self.exchangers.get().values()}
            except AttributeError:
                logging.error('Failed to load exchangers from BestChange API for get top')
                return
            normalized_prices = defaultdict(list)
            try:
                currencies_dict = self.currencies.get()
            except AttributeError:
                logging.error('Failed to load currencies from BestChange API for get top')
                return
            actual_prices = {}
            for m in money_list:
                for c in cript_list:
                    actual_prices[(c, m)] = get_actual_price(c, m)

            for rate in self.rates:
                exchanger_id = rate['exchange_id']
                exchanger_name = exchangers[exchanger_id]

                get_currency_id = rate['get_id']
                get_currency_name = currencies_dict[get_currency_id]['name']

                give_currency_id = rate['give_id']
                give_currency_name = currencies_dict[give_currency_id]['name']

                money = None
                for m in money_list:
                    if m in give_currency_name:
                        money = m
                        break
                cript = None
                for c in cript_list:
                    if c in get_currency_name:
                        cript = c
                        break
                if any([money is None, cript is None]):
                    continue
                else:
                    normalized_prices[exchanger_name].append(rate['rate'] / actual_prices[(cript, money)])

            exchanger_ranks = {exchanger_name: np.mean(exchanger_prices_norm) \
                               for exchanger_name, exchanger_prices_norm in normalized_prices.items()}
            exchangers = [e for e in exchanger_ranks]
            list_top_exchangers = list(sorted(exchangers, key=lambda x: exchanger_ranks[x]))[:n]
            end = time.time()
            print(f'Время загрузки get_top: {(end - start) * 1000:.2f} мс')  # Время в миллисекундах
            return list_top_exchangers

        top_exchanges = await get_top()

        row_ind_top = 26 - 5  # топ начинается с 26 строчки, а значения нашей таблицы с 5
        try:
            for exch in top_exchanges:
                col_ind_top = 0
                cell_callbacks[(row_ind_top, col_ind_top)] = (lambda x: x, [exch])
                for cr in CRYPTOS_LIST:
                    for mon in FIATS_LIST_TOP:
                        col_ind_top += 1
                        cell_callbacks[(row_ind_top, col_ind_top)] = (get_best_rate, (exch, cr, mon))
                row_ind_top += 1
        except TypeError:
            logging.error('Failed to load top of exchanges from BestChange API')
        tasks = []
        for (row_ind, col_ind), (fn, args) in cell_callbacks.items():
            tasks.append(self.update_cell(values, row_ind, col_ind, fn, args))
        await asyncio.gather(*tasks)
        await sheet.update('C5:P35', values)

    async def update_cell(self, values, row_ind, col_ind, fn, args):
        result = fn(*args)
        if asyncio.iscoroutine(result):
            value = await result
        else:
            value = result
        if value is None:
            value = '-'
        if row_ind < len(values) and col_ind < len(values[row_ind]):
            values[row_ind][col_ind] = value
        else:
            logging.error(f"Index out of range: row {row_ind}, col {col_ind}")

    async def update(self):
        await self.async_update()

    def set_unit_chnges_rates(self, rates):
        self.rates = rates

    def set_exchangers(self, exchangers):
        self.exchangers = exchangers

    def set_currencies(self, currencies):
        self.currencies = currencies