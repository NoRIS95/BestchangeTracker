import logging
import asyncio
from abc import ABC, abstractmethod
from observers import IObserver, GoogleSheetsObserver, CRYPTOS_LIST, FIATS_LIST, FIAT_RUB
from exchangers import Sova, NetEx24, Shahta, Ferma
from currencies import FIAT_CARDS_METHODS, CRYPTO_USDT, USDT_PROTOCOLS, make_cript_dict_cryptocompare


class ISubject(ABC):
    @abstractmethod
    async def register_observer(self, observer: IObserver):
        pass

    @abstractmethod
    def remove_observer(self, observer: IObserver):
        pass

    @abstractmethod
    async def notify_observers(self):
        pass

class BestChangeManager(ISubject):
    def __init__(self, best_change_api, rub, usdt, ton, btc, xmr, eth, trx):
        self.__bestChangeAPI = best_change_api
        
        self.__Sova_unit = Sova([rub, usdt, ton, btc, xmr, eth, trx])
        self.__Netex_unit = NetEx24([rub, usdt, ton, btc, xmr, eth, trx])
        self.__Shahta_unit = Shahta([rub, usdt, ton, btc, xmr, eth, trx])
        self.__Ferma_unit = Ferma([rub, usdt, ton, btc, xmr, eth, trx])
        self.__observers = [self.__Shahta_unit, self.__Netex_unit, self.__Sova_unit, self.__Ferma_unit]

        self.__rub = rub
        self.__usdt = usdt
        self.__ton = ton
        self.__btc = btc
        self.__xmr = xmr
        self.__eth = eth
        self.__trx = trx
        self.__cur_list = [self.__rub, self.__usdt, self.__ton, self.__btc, self.__xmr, self.__eth, self.__trx]

    async def register_observer(self, observer: IObserver):
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

    async def notify_observers(self):
        await self.__bestChangeAPI.load()
        all_rates = self.__bestChangeAPI.rates().get()
        exchangers, currencies = self.__bestChangeAPI.exchangers(), self.__bestChangeAPI.currencies()
        
        try:
            for currency in self.__cur_list:
                cur_list = [cur for cur in currencies.search_by_name(currency.name).values()]
                currency.update_naked_prices()
                currency.set_currency_list(cur_list)
        except AttributeError:
            logging.error("Failed to load currencies from BestChange API.")
        
        tasks = []
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
                except AttributeError:
                    logging.error(f'Failed to load exchanger {observer.name} from BestChange API')
                    continue
            tasks.append(asyncio.create_task(observer.update()))
        
        await asyncio.gather(*tasks)

    async def start_updates(self, interval: int = 5):
        while True:
            await self.notify_observers()
            await asyncio.sleep(interval)

    def __str__(self):
        ret_str = ""
        for b_c_unin in self.__observers:
            ret_str += (b_c_unin.__str__() + "\n")
        return ret_str

    def get_rate(self, curr_client_give: str, cur_client_get: str):
        for changers in self.__observers:
            changers.get_rate(curr_client_give, cur_client_get)