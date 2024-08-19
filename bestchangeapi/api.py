import os
import time
import asyncio
import aiohttp
import aiofiles

from io import TextIOWrapper
from zipfile import ZipFile
from itertools import groupby
from .function_create_date import * 

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
    __filename = 'info.zip'
    __url = 'http://api.bestchange.ru/info.zip'
    __enc = 'windows-1251'

    __file_currencies = 'bm_cy.dat'
    __file_exchangers = 'bm_exch.dat'
    __file_rates = 'bm_rates.dat'
    __file_cities = 'bm_cities.dat'
    __file_top = 'bm_top.dat'

    def __init__(self, cache=True, cache_seconds=15, cache_path='./', exchangers_reviews=False, ssl=True):
        self.__cache = cache
        self.__cache_seconds = cache_seconds
        self.__cache_path = cache_path + self.__filename
        self.__exchangers_reviews = exchangers_reviews
        self.__ssl = ssl
        self.__is_error = False

    async def fetch(self, session, url, file_path):
        async with session.get(url, ssl=self.__ssl) as response:
            if response.status == 200:
                data = await response.read()
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(data)
            else:
                raise Exception(f"Failed to download file from {url}, status code: {response.status}")

    async def load(self):
        if os.path.isfile(self.__cache_path) and time.time() - os.path.getmtime(self.__cache_path) < self.__cache_seconds:
            filename = self.__cache_path
        else:
            async with aiohttp.ClientSession() as session:
                await self.fetch(session, self.__url, self.__cache_path)
            filename = self.__cache_path

        await self._extract_files(filename)

    async def _extract_files(self, filename):
        try:
            with ZipFile(filename) as zipfile:
                tasks = []
                tasks.append(self._process_file(zipfile, self.__file_rates))
                tasks.append(self._process_file(zipfile, self.__file_currencies))
                tasks.append(self._process_file(zipfile, self.__file_exchangers))
                tasks.append(self._process_file(zipfile, self.__file_cities))
                tasks.append(self._process_file(zipfile, self.__file_top))

                await asyncio.gather(*tasks)

                if not self.__cache:
                    os.remove(filename)
        except Exception as e:
            self.__is_error = str(e)

    async def _process_file(self, zipfile, file_name):
        with zipfile.open(file_name) as f:
            content = TextIOWrapper(f, encoding=self.__enc).read()
            # Обработка данных: например, сохранение в атрибуты класса
            if file_name == self.__file_rates:
                self.__rates = Rates(content, split_reviews=False)
            elif file_name == self.__file_currencies:
                self.__currencies = Currencies(content)
            elif file_name == self.__file_exchangers:
                self.__exchangers = Exchangers(content)
            elif file_name == self.__file_cities:
                self.__cities = Cities(content)
            elif file_name == self.__file_top:
                self.__top = Top(content)

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

    def top(self):
        return self.__top


async def main():
    api = BestChange(cache_seconds=30, ssl=False)
    await api.load()

    if api.is_error():
        return

    currencies = api.currencies().get()
    top = api.top().get()

    for val in top:
        currencies[val['give_id']]['name'], '->', currencies[val['get_id']]['name'], ':', round(val['perc'], 2)

if __name__ == '__main__':
    asyncio.run(main())


#     start = time.time()
#     best_change_api = BestChange(cache=True, ssl=False, cache_path='./', exchangers_reviews=False, cache_seconds=30)
#     end = time.time()
#     print(f'Время выполнения get_bestchangeapi: {(end - start) * 1000:.2f} мс')  # Время в миллисекундах