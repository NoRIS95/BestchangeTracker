import cryptocompare
from abc import ABC, abstractmethod
import time
import threading
from decimal import Decimal
from bestchange_api import BestChange
from sheetfu import SpreadsheetApp
from dotenv import load_dotenv
from collections import defaultdict
import numpy as np
import os
import logging

load_dotenv()

#TODO удали файл, он больше не нужен

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'secret.json')
SLEEP_TIME_LOOP = 30

N_TOP=10

EXCHANGES = ["Сова", 'NetEx24', 'Шахта', 'Ферма']
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


class Currency(ABC):    #Валюта
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'),
                 decimality: int = 2):
        self.name = ""             # Официальное сокращенное имя крипты
        self.__id_names_list = []  # Список названий валют в файле от BestChange
        self.zero = Decimal('0.0') # для быстрого сравнения с нулем

        """Цену на продажу и покупку понимаем в отношении нас или того объекта, которой ей торгует"""
        self.__price_rub_sell:  Decimal = Decimal("0.0")    # Цена в рублях на продажу
        self.__price_rub_buy:   Decimal = Decimal("0.0")    # Цена в рублях на покупку

        self.__price_usdt_sell: Decimal = Decimal("0.0")    # Цена в USDT на продажу
        self.__price_usdt_buy:  Decimal = Decimal("0.0")    # Цена в USDT на покупку

        self.__naked_price_rub:  Decimal = naked_price_rub  # Голая цена валюты в рублях на бирже
        self.__naked_price_usdt: Decimal = naked_price_usdt # Голая цена валюты в USDT на бирже

        self.__decimality: int = decimality # размерность конкретной валюты
        self.__comission_for_sell_usdt: Decimal = Decimal("1.0") # Комиссия на продажу в usdt
        self.__comission_for_buy_usdt:  Decimal = Decimal("1.0") # Комиссия на покупку в usdt
        self.__comission_for_sell_rub:  Decimal = Decimal("1.0") # Комиссия на продажу в usdt
        self.__comission_for_buy_rub:   Decimal = Decimal("1.0") # Комиссия на покупку в usdt

        self.currency_list = [] # Список {'id':int(val[0]), 'pos_id':int(val[1]), 'name':val[2]}
        self.currency_ids =  [] # int(val[0])

    def update_naked_prices(self):    
        self.__naked_price_usdt = Decimal(
            cryptocompare.get_price(self.name, currency=CRYPTOS_LIST[CRYPTO_USDT])[self.name][
                CRYPTOS_LIST[CRYPTO_USDT]])

        self.__naked_price_rub = Decimal(
            cryptocompare.get_price(self.name, currency=FIATS_LIST[FIAT_RUB])[self.name][
                FIATS_LIST[FIAT_RUB]])

        # Quantize the raw prices to the specified decimal places
        self.__naked_price_usdt = self.__naked_price_usdt.quantize(Decimal('0.0001').normalize())
        self.__naked_price_rub = self.__naked_price_rub.quantize(Decimal('0.01').normalize())

    def compute_comissions(self):   #расчёт комиссии
        if self.__naked_price_usdt != self.zero:
            self.__comission_for_sell_usdt = (self.__price_usdt_sell / self.__naked_price_usdt)

            # Compute the buy commission for USDT
        if self.__naked_price_usdt != self.zero:
            self.__comission_for_buy_usdt = (self.__price_usdt_buy / self.__naked_price_usdt)

            # Compute the sell commission for RUB
        if self.__naked_price_rub != self.zero:
            self.__comission_for_sell_rub = (self.__price_rub_sell / self.__naked_price_rub)

            # Compute the buy commission for RUB
        if self.__naked_price_rub != self.zero:
            self.__comission_for_buy_rub = (self.__price_rub_buy / self.__naked_price_rub)

    def compute_prices(self):  #расчёт цены
        self.__price_usdt_sell = self.__naked_price_usdt * self.__comission_for_sell_usdt
        self.__price_usdt_buy = self.__naked_price_usdt * self.__comission_for_buy_usdt

        self.__price_rub_sell = self.__naked_price_rub * self.__comission_for_sell_rub
        self.__price_rub_buy = self.__naked_price_rub * self.__comission_for_buy_rub

    def set_currency_list(self, cur_list): # сеттер списка валют
        self.currency_list = cur_list
        self.currency_ids = [cur['id'] for cur in cur_list if cur['name'] in self.__id_names_list]

    def get_currency_list(self):
        return self.currency_list

    def set_currency_ids(self, cur_ids):
        self.currency_ids = cur_ids

    def get_currency_ids(self): 
        return self.currency_ids

    def get_naked_price_rub(self):
        return self.__naked_price_rub

    def set_naked_price_rub(self, naked_price_rub: Decimal):
        self.__naked_price_rub = naked_price_rub

    def get_naked_price_usdt(self):
        return self.__naked_price_usdt

    def set_naked_price_usdt(self, naked_price_usdt: Decimal):
        self.__naked_price_usdt = naked_price_usdt

    def get_decimality(self):
        return self.__decimality

    def set_decimality(self, decimality: int):
        self.__decimality = decimality

    def set_price_rub_sell(self, price_rub_sell):
        self.__price_rub_sell = price_rub_sell

    def set_price_rub_buy(self, price_rub_buy):
        self.__price_rub_buy = price_rub_buy

    def set_price_usdt_sell(self, price_usdt_sell):
        self.__price_usdt_sell = price_usdt_sell

    def set_price_usdt_buy(self, price_usdt_buy):
        self.__price_usdt_buy = price_usdt_buy

    def get_price_rub_sell(self):
        return self.__price_rub_sell

    def get_price_rub_buy(self):
        return self.__price_rub_buy

    def get_price_usdt_sell(self):
        return self.__price_usdt_sell

    def get_price_usdt_buy(self):
        return self.__price_usdt_buy

    def set_comission_for_sell_usdt(self, coms:Decimal):
        self.__comission_for_sell_usdt = coms

    def set_comission_for_buy_usdt(self):
        return self.__comission_for_buy_usdt

    def get_comission_for_sell_usdt(self):
        return self.__comission_for_sell_usdt

    def get_comission_for_buy_usdt(self, coms: Decimal):
        self.__comission_for_buy_usdt = coms

    def set_comission_for_sell_rub(self, coms:Decimal):
        self.__comission_for_sell_rub = coms

    def set_comission_for_buy_rub(self):
        return self.__comission_for_buy_rub

    def get_comission_for_sell_rub(self):
        return self.__comission_for_sell_rub

    def get_comission_for_buy_rub(self, coms: Decimal):
        self.__comission_for_buy_rub = coms

    def __str__(self):
        return f"currency:{self.name}\nUSDT_naked:{self.__naked_price_usdt}\t||\tRUB_naked:{self.__naked_price_rub}\t||\n"

class RUB_cash(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_rub=naked_price_rub, decimality=decimality)
        self.__id_names_list = ['Наличные RUB']

class RUB_cards(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_rub=naked_price_rub, decimality=decimality)
        self.__id_names_list = FIAT_CARDS_METHODS

class RUB(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_rub=naked_price_rub, decimality=decimality)
        self.name = FIATS_LIST[FIAT_RUB]
        self.__cash = RUB_cash()
        self.__cards = RUB_cards()

        self.types_dicts = {
            RUB_TYPES[RUB_CASH_TYPE]: self.__cash,
            RUB_TYPES[RUB_CARD_TYPE]: self.__cards
        }

    def set_currency_list(self, cur_list):
        self.currency_list = cur_list
        self.__cash.set_currency_list(cur_list)
        self.__cards.set_currency_list(cur_list)

# Блок кода с USDT
class USD_cash(Currency):
    def __init__(self, naked_price_usdt: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.__id_names_list = ['Наличные USD']

class  USDT_TRC20(Currency):
    def __init__(self, naked_price_usdt: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.__id_names_list = ['Tether TRC20 (USDT)']

class  USDT_ERC20(Currency):
    def __init__(self, naked_price_usdt: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.__id_names_list = ['Tether ERC20 (USDT)']

class  USDT_BEP20(Currency):
    def __init__(self, naked_price_usdt: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.__id_names_list = ['Tether BEP20 (USDT)']

class USDT(Currency):
    def __init__(self, naked_price_usdt: Decimal = Decimal('1.0'), decimality: int = 2):
        super().__init__(naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_USDT]
        self.__trc20 = USDT_TRC20()
        self.__erc20 = USDT_ERC20()
        self.__bep20 = USDT_BEP20()
        self.__cash = USD_cash()

        self.types_dicts = {
            USDT_TYPES[TRC20_TYPE]:self.__trc20,
            USDT_TYPES[ERC20_TYPE]:self.__erc20,
            USDT_TYPES[BEP20_TYPE]:self.__bep20,
            USDT_TYPES[CASH_TYPE]:self.__cash
        }

    def set_currency_list(self, cur_list):
        self.currency_list = cur_list
        self.__cash.set_currency_list(cur_list)
        self.__bep20.set_currency_list(cur_list)
        self.__bep20.set_currency_list(cur_list)
        self.__erc20.set_currency_list(cur_list)
        self.__trc20.set_currency_list(cur_list)


class TON(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'), decimality: int = 9):
        super().__init__(naked_price_rub=naked_price_rub, naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_TON]

class BTC(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'),
                 decimality: int = 8):
        super().__init__(naked_price_rub=naked_price_rub, naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_BTC]

class XMR(Currency): #Monero
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'),
                 decimality: int = 12):
        super().__init__(naked_price_rub=naked_price_rub, naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_XMR]

class TRX(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'),
                 decimality: int = 6):
        super().__init__(naked_price_rub=naked_price_rub, naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_TRX]

class ETH(Currency):
    def __init__(self, naked_price_rub: Decimal = Decimal('0.0'), naked_price_usdt: Decimal = Decimal('0.0'),
                 decimality: int = 18):
        super().__init__(naked_price_rub=naked_price_rub, naked_price_usdt=naked_price_usdt, decimality=decimality)
        self.name = CRYPTOS_LIST[CRYPTO_ETH]


class IObserver(ABC):
    @abstractmethod
    def update(self):
        pass


class ISubject(ABC):
    @abstractmethod
    def register_observer(self, observer: IObserver):
        pass

    @abstractmethod
    def remove_observer(self, observer: IObserver):
        pass

    @abstractmethod
    def notify_observers(self):
        pass


class BestChangeUnit(IObserver):
    def __init__(self):
        self.name = ""
        self.changer_id = -1 # Уникальный айди обменника

        self.__rub  = RUB()         # Список валют, которые мы меняем.
        self.__usdt = USDT()        #
        self.__ton  = TON()         #
        self.__btc  = BTC()         #
        self.__xmr  = XMR()         #
        self.__eth  = ETH()         #
        self.__trx  = TRX()         #
        self.__all_unit_rates = []  # Список всех состояний обмена со всех обменников
        self.__self_unit_rates = [] # Cписок состояний обмена, только данного обменника

        self.currencies_dict = {
            CRYPTOS_LIST[CRYPTO_USDT]: self.__usdt,
            CRYPTOS_LIST[CRYPTO_TON]:  self.__ton,
            CRYPTOS_LIST[CRYPTO_ETH]:  self.__eth,
            CRYPTOS_LIST[CRYPTO_XMR]:  self.__xmr,
            CRYPTOS_LIST[CRYPTO_BTC]:  self.__btc,
            CRYPTOS_LIST[CRYPTO_TRX]:  self.__trx,
            FIATS_LIST[FIAT_RUB]:      self.__rub,
        }

    def set_changer_id(self, id):
        self.changer_id = id

    def set_unit_chnges_rates(self, rates):
        self.__all_unit_rates = rates
        self.__self_unit_rates = [r for r in self.__all_unit_rates if r['exchange_id'] == self.changer_id]

    def update_rates(self, currencies):
        for currency in currencies:
            currency: Currency
            cur: Currency = self.currencies_dict[currency.name]
            cur.set_naked_price_rub(currency.get_naked_price_rub())
            cur.set_naked_price_usdt(currency.get_naked_price_usdt())

    def __str__(self):
        ret_str = f"{self.name}\n"
        for cur in self.currencies_dict.items():
            ret_str += (cur[1].__str__() + "\n")
        return ret_str

    def update(self):
        pass

    def get_rate(self, curr_client_give:str, cur_client_get:str):
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

        rate = [rate['rate'] for rate in self.__self_unit_rates if rate['get_id'] in cur_get.currency_ids\
                and rate['give_id'] in cur_give.currency_ids]


# Example child class
class Sova(BestChangeUnit):
    def __init__(self):
        super().__init__()
        self.name = EXCHANGES[EX_SOVA]


class NetEx24(BestChangeUnit):
    def __init__(self):
        super().__init__()
        self.name = EXCHANGES[EX_NETEX24]


class Shahta(BestChangeUnit):
    def __init__(self):
        super().__init__()
        self.name = EXCHANGES[EX_SHAHTA]


class Ferma(BestChangeUnit):
    def __init__(self):
        super().__init__()
        self.name = EXCHANGES[EX_FERMA]





class GoogleSheetsObserver(IObserver):
    def __init__(self, sheet_name=SHEET_NAME, spreadsheet_id=SPREADSHEET_ID, credentials_file=CREDENTIALS_FILE):
        self.sheet_name = sheet_name
        self.spreadsheet_id = spreadsheet_id
        self.sheet = SpreadsheetApp(credentials_file).open_by_id(spreadsheet_id=spreadsheet_id).get_sheet_by_name(sheet_name)
        self.exchangers = None
        self.currencies = None
        self.rates = None


    def update(self):
        cell_callbacks = {}

        all_currencies_list = [OLD_NEW_TON_NAME.get(c,c) for c in CRYPTOS_LIST] + FIATS_LIST

        actual_prices = cryptocompare.get_price(all_currencies_list, all_currencies_list)

        def get_actual_price(get_currency_name, give_currency_name):
            get_currency_name = OLD_NEW_TON_NAME.get(get_currency_name, get_currency_name)
            give_currency_name = OLD_NEW_TON_NAME.get(give_currency_name, give_currency_name)
            return actual_prices[get_currency_name][give_currency_name]
        
        def get_best_rate(exchanger_name: str, get_currency_name: str, give_currency_name: str):
            get_currency_name = OLD_NEW_TON_NAME.get(get_currency_name, get_currency_name)
            give_currency_name = OLD_NEW_TON_NAME.get(give_currency_name, give_currency_name)
            exchanger_search_result = self.exchangers.search_by_name(exchanger_name)
            if exchanger_search_result:
                exchanger_id = list(self.exchangers.search_by_name(exchanger_name).keys())[0]
            else:
                return
            get_cur_ids = {cur['id'] for cur in self.currencies.search_by_name(get_currency_name).values() \
                        if (get_currency_name in cur['name'])}
            give_cur_ids = {cur['id'] for cur in self.currencies.search_by_name(give_currency_name).values() \
                        if (give_currency_name in cur['name'])}
            rates = [r['rate'] for r in self.rates if r['exchange_id'] == exchanger_id and r['give_id'] \
                        in give_cur_ids and r['get_id'] in get_cur_ids]
            if len(rates) == 0:
                return
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


        data_range = self.sheet.get_range_from_a1('C5:P35')
        backgrounds = data_range.get_backgrounds()
        values = data_range.get_values()
        
        def get_top(n=10, money_list=['USDT', 'RUB'], cript_list=['BTC', 'ETH', 'TON', 'XMR', 'TRX']):
            exchangers = {v['id']:v['name'] for v in self.exchangers.get().values()}

            normalized_prices = defaultdict(list)
            currencies_dict = self.currencies.get()

            actual_prices = {}
            for m in money_list:
                for c in cript_list:
                    actual_prices[(c,m)] = get_actual_price(c,m)

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
                    normalized_prices[exchanger_name].append(rate['rate']/actual_prices[(cript,money)])

            exchanger_ranks = {exchanger_name:np.mean(exchanger_prices_norm) \
                for exchanger_name, exchanger_prices_norm in normalized_prices.items()}
            exchangers = [e for e in exchanger_ranks]
            return list(sorted(exchangers, key=lambda x: exchanger_ranks[x]))[:n]

        top_exchanges = get_top()


        row_ind_top = 26 - 5  # топ начинается с 26 строчки, а значения нашей таблицы с 5
        for exch in top_exchanges:
            col_ind_top = 0
            cell_callbacks[(row_ind_top, col_ind_top)] = (lambda x: x, [exch])
            for cr in CRYPTOS_LIST:
                for mon in FIATS_LIST_TOP:
                    col_ind_top += 1
                    cell_callbacks[(row_ind_top, col_ind_top)] = (get_best_rate, (exch, cr, mon))
            row_ind_top += 1
        for (row_ind, col_ind), (fn, args) in cell_callbacks.items():
            value = fn(*args)
            if value is None:
                value = '-'
            values[row_ind][col_ind] = value
        data_range.set_values(values)
        data_range.set_backgrounds(backgrounds)
                
    def set_unit_chnges_rates(self, rates):
        self.rates = rates

    def set_exchangers(self, exchangers):
        self.exchangers = exchangers

    def set_currencies(self, currencies):
        self.currencies = currencies


class BestChangeManager(ISubject):
    def __init__(self):
        self.__bestChangeAPI = BestChange(load=False, cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=1)
        self.__bestChangeAPI.load()

        self.__Sova_unit = Sova()
        self.__Netex_unit = NetEx24()
        self.__Shahta_unit = Shahta()
        self.__Ferma_unit = Ferma()
        self.__observers = [self.__Shahta_unit, self.__Netex_unit, self.__Sova_unit, self.__Ferma_unit]

        self.__rub = RUB()
        self.__usdt = USDT()
        self.__ton = TON()
        self.__btc = BTC()
        self.__xmr = XMR()
        self.__eth = ETH()
        self.__cur_list = [self.__rub, self.__usdt, self.__ton, self.__btc, self.__xmr, self.__eth]

    def register_observer(self, observer: IObserver):
        self.__observers.append(observer)

    def remove_observer(self, observer: IObserver):
        self.__observers.remove(observer)

    def prepare_rub_ids(self):
        rub_ids = [cur['id'] for cur in self.__bestChangeAPI.currencies().search_by_name(FIATS_LIST[FIAT_RUB]).values()\
                   if cur['name'] in FIAT_CARDS_METHODS]
        return rub_ids

    def prepare_usdt_ids(self):
        usdt_ids = [cur['id'] for cur in self.__bestChangeAPI.currencies().search_by_name((CRYPTOS_LIST[CRYPTO_USDT])).values()\
                    if cur['name'] in USDT_PROTOCOLS]
        return usdt_ids
    
    def set_exchangers(self):
        raise NotImplemented

    def set_currencies(self):
        raise NotImplemented

    def notify_observers(self):
        self.__bestChangeAPI.load()
        all_rates = self.__bestChangeAPI.rates().get()
        exchangers, currencies = self.__bestChangeAPI.exchangers(), self.__bestChangeAPI.currencies()
        if exchangers is None or currencies is None:
            logging.error("Failed to load exchangers or currencies from BestChange API.")
            return

        for currency in self.__cur_list:
            cur_list = [cur for cur in currencies.search_by_name(currency.name).values()]
            currency.update_naked_prices()
            currency.set_currency_list(cur_list)

        for observer in self.__observers:
            observer.set_unit_chnges_rates(all_rates)
            if isinstance(observer, GoogleSheetsObserver):
                observer.set_exchangers(exchangers)
                observer.set_currencies(currencies)
            else:
                try:
                    exchanger_id = list(exchangers.search_by_name(observer.name).keys())[0]
                    observer.set_changer_id(exchanger_id)    
                except IndexError:
                    logging.warning(f'This exchanger {observer.name} was not found') 
                    continue
            observer.update()


    def start_updates(self, interval: int = 5):
        def run_updates():
            while True:
                self.notify_observers()
                time.sleep(interval)

        thread = threading.Thread(target=run_updates)
        thread.daemon = True
        thread.start()
        return thread
        
    def __str__(self):
        ret_str = ""
        for b_c_unin in self.__observers:
            ret_str += (b_c_unin.__str__() + "\n")
        return ret_str

    def get_rate(self, curr_client_give:str, cur_client_get:str):
        for changers in self.__observers:
            changers.get_rate(curr_client_give, cur_client_get)


class HiddenExchanger(IObserver):
    """ На данный момент предполагаем, что комиссия указываается в
    классе валюты и счтиается внутри каждой при обновлении """

    def __init__(self):
        self.currencies_list = []
        self.currencies_dict = {}

    def add_currency(self, curr:Currency):
        self.currencies_list.append(curr)
        self.currencies_dict[curr.name] = curr

    def update_rates(self):
        for currency in self.currencies_list:
            currency: Currency
            currency.update_naked_prices()
            currency.compute_prices()

    def update(self):
        pass

class Baronex(HiddenExchanger):
    """Baronex - скрытые челики, в обменник с которыми можно попасть только по приглашению."""

    def __init__(self):
        self.name = "BaronEx"
        self.__rub = RUB()
        self.__usdt.set_comission_for_sell_usdt(Decimal("1.05"))
        self.__usdt.set_comission_for_buy_usdt(Decimal("1.006"))
        self.add_currency(self.__rub)

        self.__usdt = USDT()
        self.__usdt.set_comission_for_sell_rub(Decimal("1.05"))
        self.__usdt.set_comission_for_buy_rub(Decimal("1.006"))
        self.add_currency(self.__usdt)

        self.__btc = BTC()
        self.__btc.set_comission_for_sell_usdt(Decimal("1.002"))
        self.__btc.set_comission_for_buy_usdt(Decimal("0.99969311"))
        self.__btc.set_comission_for_sell_rub(Decimal("1.05"))
        self.__btc.set_comission_for_buy_rub(Decimal("1.0"))
        self.add_currency(self.__btc)

        self.__eth = ETH()
        self.__eth.set_comission_for_sell_usdt(Decimal("1.002"))
        self.__eth.set_comission_for_buy_usdt(Decimal("0.997"))
        self.__eth.set_comission_for_sell_rub(Decimal("1.05"))
        self.__eth.set_comission_for_buy_rub(Decimal("1.0"))
        self.add_currency(self.__eth)

    def __str__(self):
        ret_str = f"{self.name}\n"
        for cur in self.currencies_dict.items():
            ret_str += (cur[1].__str__() + "\n")
        return ret_str

    def update_rates(self):
        for currency in self.currencies_list:
            currency: Currency
            currency.update_naked_prices()
            currency.compute_prices()

    def update(self):
        pass




if __name__ == "__main__":
    change_manager = BestChangeManager()
    google_sheets_observer = GoogleSheetsObserver(sheet_name=SHEET_NAME, spreadsheet_id=SPREADSHEET_ID, credentials_file=CREDENTIALS_FILE)
    change_manager.register_observer(google_sheets_observer)
    ## change_manager.notify_observers() # Single update
    updates_daemon = change_manager.start_updates() # Continuous update
    updates_daemon.join()