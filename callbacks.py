import cryptocompare
from bestchange_api import BestChange

api = BestChange(cache=True, ssl=False, cache_seconds=300, cache_path='./', exchangers_reviews=True)

def get_actual_price(get_currency_name, give_currency_name):
    return cryptocompare.get_price(get_currency_name, currency=give_currency_name)[get_currency_name][give_currency_name]

def get_best_rate(exchanger_name, get_currency_name, give_currency_name):
    try:
        exchanger_id = list(api.exchangers().search_by_name(exchanger_name).keys())[0]
    except IndexError:
        return
    get_cur_ids = {cur for cur in api.currencies().search_by_name(get_currency_name)}
    give_cur_ids = {cur for cur in api.currencies().search_by_name(give_currency_name)}
    rates = [r['rate'] for r in api.rates().get() if r['exchange_id'] == exchanger_id and r['give_id'] in give_cur_ids   and r['get_id'] in get_cur_ids]
    if len(rates) == 0:
        return
    best_rate = min(rates)
    return best_rate