import numpy as np
import logging
import cryptocompare
import asyncio

from abc import ABC, abstractmethod
from collections import defaultdict

from currencies import Currency
from configs import *


class IObserver(ABC):
    @abstractmethod
    def update(self):
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
        self.__all_unit_rates = []
        self.__self_unit_rates = []

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

class TelegramObserver(IObserver):
    def __init__(self, bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.exchangers = None
        self.currencies = None
        self.rates = None
        self.best_rate_cache = {}
        self.message = ''

    async def async_update(self):
        self.message = 'Цена криптовалют на бирже и у проверенных обменников:\n'

        all_currencies_list = [OLD_NEW_TON_NAME.get(c, c) for c in CRYPTOS_LIST] + FIATS_LIST
        actual_prices = await asyncio.to_thread(cryptocompare.get_price, all_currencies_list, all_currencies_list)

        def get_actual_price(get_currency_name, give_currency_name):
            get_currency_name = OLD_NEW_TON_NAME.get(get_currency_name, get_currency_name)
            give_currency_name = OLD_NEW_TON_NAME.get(give_currency_name, give_currency_name)
            actual_price = actual_prices[get_currency_name][give_currency_name]
            return actual_price

        def get_best_rate(exchanger_name: str, get_currency_name: str, give_currency_name: str):
            cache_key = (exchanger_name, get_currency_name, give_currency_name)
            if cache_key in self.best_rate_cache:
                return self.best_rate_cache[cache_key]
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
            except Exception as e:
                logging.error(f'Failed to search getting currency or giving currency of exchanger {exchanger_name} from BestChange API for get best rate: {e}')
                return None
            rates = [r['rate'] for r in self.rates if r['exchange_id'] == exchanger_id and r['give_id'] \
                        in give_cur_ids and r['get_id'] in get_cur_ids]
            if len(rates) == 0:
                return None
            best_rate = min(rates)
            self.best_rate_cache[cache_key] = best_rate
            return best_rate

        async def write_currency_info():
            for cript in CRYPTOS_LIST:
                for exchange in ['Биржа'] + EXCHANGES:
                    for money in FIATS_LIST_PRICES:
                        if exchange == "Биржа":
                            rate = get_actual_price(cript, money)
                        else:
                            rate = get_best_rate(exchange, cript, money)
                        if rate is not None:
                            self.message += f"{cript} ->{exchange}: {rate} {money} \n"
        
        async def get_top(n=10, money_list=['USDT', 'RUB'], cript_list=['BTC', 'ETH', 'TON', 'XMR', 'TRX']):
            try:
                exchangers = {v['id']:v['name'] for v in self.exchangers.get().values()}
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
            list_top_exchangers = list(sorted(exchangers, key=lambda x: exchanger_ranks[x]))[:n]
            return list_top_exchangers
        
        async def write_top_info():
            top_exchanges = await get_top()
            self.message += "Топ 10 продавцов на bestchange:\n"
            for exch in top_exchanges:
                self.message += f"{exch}\n"

        task_currency_info = asyncio.create_task(write_currency_info())
        task_top_info = asyncio.create_task(write_top_info())
        await task_currency_info
        await task_top_info

        await self.bot.send_message(self.chat_id, self.message)


    async def update(self):
        await self.async_update()

    def set_unit_chnges_rates(self, rates):
        self.rates = rates

    def set_exchangers(self, exchangers):
        self.exchangers = exchangers

    def set_currencies(self, currencies):
        self.currencies = currencies