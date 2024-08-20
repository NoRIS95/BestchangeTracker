import cryptocompare

from abc import ABC
from decimal import Decimal

from configs import *


# def make_cript_dict_cryptocompare(): 
#     cript_list = []
#     for i in CRYPTOS_LIST:
#         if i == list(OLD_NEW_TON_NAME.keys())[OLD_TON_NAME_NUM]:
#             i = OLD_NEW_TON_NAME[i]
#         cript_list.append(i)
#     crypt_exch_prices = cryptocompare.get_price(cript_list, FIATS_LIST + ['USDT'])
#     return crypt_exch_prices

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