import requests
import json
from urllib.parse import urlencode
from decimal import *
import time
import aiohttp
import jwt


class BaseUpbit:
    def __init__(self, **kwargs):
        '''
        :param key: input your upbit key
        :param secret: input your upbit secret
        '''

        self._endpoint = 'https://api.upbit.com/v1'

        if kwargs:
            self.__key = kwargs['key']
            self.__secret = kwargs['secret']

    def public_api(self, method, path, extra=None, header=None):
        if header is None:
            header = {}

        if extra is None:
            extra = {}

        method = method.upper()
        path = '/'.join([self._endpoint, path])
        if method == 'GET':
            rq = requests.get(path, headers=header, json=extra)
        elif method == 'POST':
            rq = requests.post(path, headers=header, params=extra)
        else:
            return False, '', '[{}]incorrect method'.format(method)

        try:
            res = rq.json()

            if 'error' in res:
                return False, '', res['error']['message']

            else:
                return True, res, ''

        except Exception as ex:
            return False, '', 'Error [{}]'.format(ex)

    def private_api(self, method, path, extra=None):
        payload = {
            'access_key': self.__key,
            'nonce': int(time.time() * 1000),
        }

        if extra is not None:
            payload.update({'query': urlencode(extra)})

        header = self.get_jwt_token(payload)

        return self.public_api(method, path, extra, header)

    def get_jwt_token(self, payload):
        return 'Bearer {}'.format(jwt.encode(payload, self.__secret,).decode('utf8'))

    def get_ticker(self, market):
        return self.public_api('get', 'ticker', market)

    def currencies(self):
        # using get_currencies, service_currencies
        return self.public_api('get', '/'.join(['market', 'all']))

    def get_currencies(self, currencies):
        res = []
        return [res.append(data['market']) for data in currencies if not currencies['market'] in res]

    def service_currencies(self, currencies):
        # using deposit_addrs
        res = []
        return [res.append(data.split('-')[1]) for data in currencies if currencies['market'].split('-')[1] not in res]

    def get_orderbook(self, market):
        return self.public_api('get', 'orderbook', {'markets': market})

    def get_order_history(self, uuid):
        return self.private_api('get', 'order', {'uuid': uuid})

    def get_balance(self):
        return self.private_api('get', 'accounts')

    def withdraw(self, coin, amount, to_address, payment_id=None):
        params = {
                    'currency': coin,
                    'address': to_address,
                    'amount': str(amount),
                }

        if payment_id:
            params.update({'secondary_address': payment_id})

        return self.private_api('post', '/'.join(['withdraws', 'coin']), params)

    def buy(self, coin, amount, price):
        amount, price = map(str, (amount, price * 1.05))

        params = {
            'market': coin,
            'side': 'bid',
            'volume': amount,
            'price': price,
            'ord_type': 'limit'
        }

        return self.private_api('POST', 'orders', params)

    def sell(self, coin, amount, price):
        amount, price = map(str, (amount, price * 0.95))

        params = {
            'market': coin,
            'side': 'ask',
            'volume': amount,
            'price': price,
            'ord_type': 'limit'
        }

        return self.private_api('POST', 'orders', params)

    async def async_public_api(self, method, path, extra=None, header=None):
        if header is None:
            header = {}

        if extra is None:
            extra = {}
        try:
            async with aiohttp.ClientSession(headers=header) as s:
                method = method.upper()
                path = '/'.join([self._endpoint, path])

                if method == 'GET':
                    rq = await s.get(path, headers=header, json=extra)
                elif method == 'POST':
                    rq = await s.post(path, headers=header, params=extra)
                else:
                    return False, '', '[{}]incorrect method'.format(method)

                res = json.loads(await rq.text())

                if 'error' in res:
                    return False, '', res['error']['message']

                else:
                    return True, res, ''
        except Exception as ex:
            return False, '', 'Error [{}]'.format(ex)

    async def async_private_api(self, method, path, extra=None):
        payload = {
            'access_key': self.__key,
            'nonce': int(time.time() * 1000),
        }

        if extra is not None:
            payload.update({'query': urlencode(extra)})

        header = self.get_jwt_token(payload)

        return await self.async_public_api(method, path, extra, header)

