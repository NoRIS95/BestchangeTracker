from decimal import Decimal

from observers import IObserver, BestChangeUnit
from currencies import Currency, RUB, USDT, BTC, ETH
from configs import EXCHANGES, EX_SOVA, EX_NETEX24, EX_SHAHTA, EX_FERMA

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

class Sova(BestChangeUnit):
    def __init__(self, list_currencies):
        super().__init__(list_currencies)
        self.name = EXCHANGES[EX_SOVA]


class NetEx24(BestChangeUnit):
    def __init__(self, list_currencies):
        super().__init__(list_currencies)
        self.name = EXCHANGES[EX_NETEX24]


class Shahta(BestChangeUnit):
    def __init__(self, list_currencies):
        super().__init__(list_currencies)
        self.name = EXCHANGES[EX_SHAHTA]


class Ferma(BestChangeUnit):
    def __init__(self, list_currencies):
        super().__init__(list_currencies)
        self.name = EXCHANGES[EX_FERMA]

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