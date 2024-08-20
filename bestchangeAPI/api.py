import os
import time
import ssl as sslib
import concurrent.futures
import asyncio

from io import TextIOWrapper
from zipfile import ZipFile
from urllib.request import urlretrieve, ProxyHandler, build_opener, install_opener
from itertools import groupby


class Rates:
    def __init__(self, text, split_reviews):
        self.__data = []
        for row in text.splitlines():
            val = row.split(';')
            try:
                self.__data.append({
                    'give_id': int(val[0]),
                    'get_id': int(val[1]),
                    'exchange_id': int(val[2]),
                    'rate': float(val[3]) / float(val[4]),
                    'reserve': float(val[5]),
                    'reviews': val[6].split('.') if split_reviews else val[6],
                    'min_sum': float(val[8]),
                    'max_sum': float(val[9]),
                    'city_id': int(val[10]),
                })
            except ZeroDivisionError:
                pass

    def get(self):
        return self.__data

    def filter(self, give_id, get_id):
        data = []
        for val in self.__data:
            if val['give_id'] == give_id and val['get_id'] == get_id:
                val['give'] = 1 if val['rate'] < 1 else val['rate']
                val['get'] = 1 / val['rate'] if val['rate'] < 1 else 1
                data.append(val)
        return sorted(data, key=lambda x: x['rate'])


class Common:
    def __init__(self):
        self.data = {}

    def get(self):
        return self.data

    def get_by_id(self, id, only_name=True):
        if id not in self.data:
            return False
        return self.data[id]['name'] if only_name else self.data[id]

    def search_by_name(self, name):
        return {k: val for k, val in self.data.items() if val['name'].lower().count(name.lower())}


class Currencies(Common):
    def __init__(self, text):
        super().__init__()
        for row in text.splitlines():
            val = row.split(';')
            self.data[int(val[0])] = {
                'id': int(val[0]),
                'pos_id': int(val[1]),
                'name': val[2],
            }
        self.data = dict(sorted(self.data.items(), key=lambda x: x[1]['name']))


class Exchangers(Common):
    def __init__(self, text):
        super().__init__()
        for row in text.splitlines():
            val = row.split(';')
            self.data[int(val[0])] = {
                'id': int(val[0]),
                'name': val[1],
                'wmbl': int(val[3]),
                'reserve_sum': float(val[4]),
            }
        self.data = dict(sorted(self.data.items()))

    def extract_reviews(self, rates):
        for k, v in groupby(sorted(rates, key=lambda x: x['exchange_id']), lambda x: x['exchange_id']):
            if k in self.data.keys():
                self.data[k]['reviews'] = list(v)[0]['reviews']


class Cities(Common):
    def __init__(self, text):
        super().__init__()
        for row in text.splitlines():
            val = row.split(';')
            self.data[int(val[0])] = {
                'id': int(val[0]),
                'name': val[1],
            }
        self.data = dict(sorted(self.data.items(), key=lambda x: x[1]['name']))

'''
class Bcodes(Common):
    def __init__(self, text):
        super().__init__()
        for row in text.splitlines():
            val = row.split(';')
            self.data[int(val[0])] = {
                'id': int(val[0]),
                'code': val[1],
                'name': val[2],
                'source': val[3],
            }

        self.data = dict(sorted(self.data.items(), key=lambda x: x[1]['code']))


class Brates(Common):
    def __init__(self, text):
        super().__init__()
        self.data = []
        for row in text.splitlines():
            val = row.split(';')
            self.data.append({
                'give_id': int(val[0]),
                'get_id': int(val[1]),
                'rate': float(val[2]),
            })
'''

class Top(Common):
    def __init__(self, text):
        super().__init__()
        self.data = []
        for row in text.splitlines():
            val = row.split(';')
            self.data.append({
                'give_id': int(val[0]),
                'get_id': int(val[1]),
                'perc': float(val[2]),
            })
        self.data = sorted(self.data, key=lambda x: x['perc'], reverse=True)


class BestChange:
    __version = None
    __filename = 'info.zip'
    __url = 'http://api.bestchange.ru/info.zip'
    __enc = 'windows-1251'

    __file_currencies = 'bm_cy.dat'
    __file_exchangers = 'bm_exch.dat'
    __file_rates = 'bm_rates.dat'
    __file_cities = 'bm_cities.dat'
    __file_top = 'bm_top.dat'
    # __file_bcodes = 'bm_bcodes.dat'
    # __file_brates = 'bm_brates.dat'

    __currencies = None
    __exchangers = None
    __rates = None
    __cities = None
    # __bcodes = None
    # __brates = None
    __top = None

    def __init__(self,
                 cache=True,
                 cache_seconds=15,
                 cache_path='./',
                 exchangers_reviews=False,
                 split_reviews=False,
                 ssl=False,
                 proxy=None,
                 daemon=False):
        """
        :param load: True (default). Загружать всю базу сразу
        :param cache: True (default). Использовать кеширование
            (в связи с тем, что сервис отдает данные, в среднем, 15 секунд)
        :param cache_seconds: 15 (default). Сколько времени хранятся кешированные данные.
        В поддержке писали, что загружать архив можно не чаще раз в 30 секунд, но я не обнаружил никаких проблем,
        если загружать его чаще
        :param cache_path: './' (default). Папка хранения кешированных данных (zip-архива)
        :param exchangers_reviews: False (default). Добавить в информацию об обменниках количество отзывов. Работает
        только с включенными обменниками и у которых минимум одно направление на BestChange.
        :param split_reviews: False (default). По-умолчанию BestChange отдает отрицательные и положительные отзывы
        одним значением через точку. Так как направлений обмена и обменников огромное количество, то это значение
        по-умолчанию отключено, чтобы не вызывать лишнюю нагрузку
        :param ssl: Использовать SSL соединение для загрузки данных
        :param proxy: Использовать прокси. Пример: {'http': '127.0.0.1', 'https': '127.0.0.1'}
        """
        self.__is_error = False
        self.__cache = cache
        self.__cache_seconds = cache_seconds
        self.__cache_path = cache_path + self.__filename
        self.__exchangers_reviews = exchangers_reviews
        self.__split_reviews = split_reviews
        self.__ssl = ssl
        self.__proxy = proxy
        self.__daemon = daemon
        self.__executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.__ready_for_calls = asyncio.Event()
        if self.__ssl:
            # Отключаем проверку сертификата, так как BC его не выпустил для этой страницы
            # ssl._create_default_https_context = ssl._create_unverified_context
            # self.__url = self.__url.replace('http', 'https')
            sslib._create_default_https_context = sslib._create_unverified_context
            self.__url = self.__url.replace('http', 'https')

    async def load(self):
        if self.__daemon:
            self.__executor.submit(self._run_infinite_load)
            import time; time.sleep(40)
        else:
            future = self.__executor.submit(self._download_and_extract)
            return asyncio.wrap_future(future)

    def _run_infinite_load(self):
        try:
            self._download_and_extract()  # Perform the initial load
            self.__ready_for_calls.set()  # Signal that the initial load is complete
            while True:
                self._download_and_extract()
                time.sleep(self.__cache_seconds)
        except Exception as e:
            self.__is_error = str(e)
        
    def _download_and_extract(self):
        try:
            if os.path.isfile(self.__cache_path) \
                    and time.time() - creation_date(self.__cache_path) < self.__cache_seconds:
                filename = self.__cache_path
            else:

                if self.__proxy is not None:
                    proxy = ProxyHandler(self.__proxy)
                    opener = build_opener(proxy)
                    install_opener(opener)
                filename, headers = urlretrieve(self.__url, self.__cache_path if self.__cache else None)
            
            with ZipFile(filename) as zipfile:
                files = zipfile.namelist()

                if self.__file_rates not in files:
                    raise Exception(f'File "{self.__file_rates}" not found')

                if self.__file_currencies not in files:
                    raise Exception(f'File "{self.__file_currencies}" not found')

                if self.__file_exchangers not in files:
                    raise Exception(f'File "{self.__file_exchangers}" not found')

                if self.__file_cities not in files:
                    raise Exception(f'File "{self.__file_cities}" not found')

                if self.__file_top not in files:
                    raise Exception(f'File "{self.__file_top}" not found')

                with zipfile.open(self.__file_rates) as f:
                    with TextIOWrapper(f, encoding=self.__enc) as r:
                        self.__rates = Rates(r.read(), self.__split_reviews)


                with zipfile.open(self.__file_currencies) as f:
                    with TextIOWrapper(f, encoding=self.__enc) as r:
                        self.__currencies = Currencies(r.read())

                with zipfile.open(self.__file_exchangers) as f:
                    with TextIOWrapper(f, encoding=self.__enc) as r:
                        self.__exchangers = Exchangers(r.read())

                with zipfile.open(self.__file_cities) as f:
                    with TextIOWrapper(f, encoding=self.__enc) as r:
                        self.__cities = Cities(r.read())
                '''
                if self.__file_bcodes in files:
                    text = TextIOWrapper(zipfile.open(self.__file_bcodes), encoding=self.__enc).read()
                    self.__bcodes = Bcodes(text)

                if self.__file_brates in files:
                    text = TextIOWrapper(zipfile.open(self.__file_brates), encoding=self.__enc).read()
                    self.__brates = Brates(text)
                '''
                with zipfile.open(self.__file_top) as f:
                    with TextIOWrapper(f, encoding=self.__enc) as r:
                        self.__top = Top(r.read())
                
                # ...
                if self.__exchangers_reviews:
                    self.__exchangers.extract_reviews(self.__rates.get())

                if not self.__cache:
                    os.remove(filename)
        except Exception as e:
            self.__is_error = str(e)
        

    def is_error(self):
        return self.__is_error

    def rates(self):
        return self.__rates

    def currencies(self):
        return self.__currencies

    def exchangers(self):
        return self.__exchangers

    def cities(self):
        return self.__cities
    
    '''
    def bcodes(self):
        return self.__bcodes

    def brates(self):
        return self.__brates
    '''

    def top(self):
        return self.__top


async def main():
    start = time.time()
    proxy = None
    api = BestChange(cache_seconds=30, exchangers_reviews=False, split_reviews=False, ssl=False, proxy=proxy, daemon=True)
    end = time.time()
    print(f'Время выполнения get_bestchangeapi: {(end - start) * 1000:.2f} мс')  # Время в миллисекундах

    print('Starting download')
    api.load()
    
    print('Download completed')

    if api.is_error():
        print(api.is_error())
        return

    currencies = api.currencies().get()
    top = api.top().get()
    print(top)

    for val in top:
        print(currencies[val['give_id']]['name'], '->', currencies[val['get_id']]['name'], ':', round(val['perc'], 2))
    
    


if __name__ == '__main__':
    asyncio.run(main())


#     start = time.time()
#     best_change_api = BestChange(cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=30)
#     end = time.time()
#     print(f'Время выполнения get_bestchangeapi: {(end - start) * 1000:.2f} мс')  # Время в миллисекундах