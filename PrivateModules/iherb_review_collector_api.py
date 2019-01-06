import requests
import time


class IherbApiModule:
    def __init__(self):
        self._endpoint = 'https://www.iherb.com'
        self.__proxy = {}
        self.__proxy_list = []

        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
            'content-type': 'application/json'
        }

    def import_proxies(self, path):
        with open(path, 'r') as f:
            try:
                self.__proxy_list = f.read().split('\n')
                return True, self.__proxy_list, 'successfully loaded proxy list.'

            except Exception as e:
                return False, '', 'Error . [{}]'.format(e)

    def proxy_set(self):
        while True:
            for num in range(len(self.__proxy_list)):
                self.__proxy = {
                    'http': self.__proxy_list[num],
                    'https': self.__proxy_list[num]
                }
                yield

    def request(self, method, path, extra=None):
        try:
            if extra is None:
                extra = {}

            url = '/'.join([self._endpoint, path])
            method = method.upper()

            if method == 'POST':
                rq = requests.request(method, url, data=extra, headers=self.headers, proxies=self.__proxy)
            else:
                rq = requests.request(method, url, params=extra, headers=self.headers, proxies=self.__proxy)

            if rq.status_code == 403:
                return False, '', 'change proxy list.'

            res = rq.json()

            return True, res, ''

        except Exception as ex:
            return False, '', 'fail to http Request. [{}]'.format(ex)

    def iherb_api(self, pid, num):
        params = {
            'pid': pid,
            'limit': 1000,
            'page': num,
            'lc': '',
            'translations': 'ko-KR',
            '_': int(time.time() * 1000)
        }
        return self.request('get', '/'.join(['ugc', 'api', 'review']), params)

