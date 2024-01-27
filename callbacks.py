import cryptocompare
from bestchange_api import BestChange
import numpy as np
from collections import defaultdict

api = BestChange(cache=True, ssl=False, cache_seconds=300, cache_path='./', exchangers_reviews=True)

def get_actual_price(get_currency_name, give_currency_name):
    return cryptocompare.get_price(get_currency_name, currency=give_currency_name)[get_currency_name][give_currency_name]

def get_best_rate(exchanger_name, get_currency_name, give_currency_name):
    try:
        exchanger_id = list(api.exchangers().search_by_name(exchanger_name).keys())[0]
    except IndexError:
        return
    get_cur_ids = {cur['id'] for cur in api.currencies().search_by_name(get_currency_name).values() if get_currency_name in cur['name']}
    give_cur_ids = {cur['id'] for cur in api.currencies().search_by_name(give_currency_name).values() if give_currency_name in cur['name']}
    rates = [r['rate'] for r in api.rates().get() if r['exchange_id'] == exchanger_id and r['give_id'] in give_cur_ids and r['get_id'] in get_cur_ids]
    if len(rates) == 0:
        return
    best_rate = min(rates)
    return best_rate

def get_top(n=10, money_list=['USDT', 'RUB'], cript_list=['BTC', 'ETH', 'TON', 'XMR', 'TRX']):
    exchangers = {v['id']:v['name'] for v in api.exchangers().get().values()}
    rates = api.rates().get()

    normalized_prices = defaultdict(list) # exchanger name -> normalized_sell_prices
    currencies_dict = api.currencies().get() # currency_id -> currency info dict

    actual_prices = {}
    for m in money_list:
        for c in cript_list:
            actual_prices[(c,m)] = get_actual_price(c,m)

    for rate in rates:
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


    try:
        exchanger_id = list(api.exchangers().search_by_name(exchanger_name).keys())[0]
    except IndexError:
        return
