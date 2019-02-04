import requests
import json
from urllib.parse import urlencode
from decimal import *
import time
import aiohttp
import jwt
import numpy as np
import asyncio

DEBUG = True


class BaseUpbit:
    def __init__(self, **kwargs):
        '''
        :param key: input your upbit key
        :param secret: input your upbit secret
        '''

        self._endpoint = 'https://api.upbit.com/v1'

        if kwargs:
            self._key = kwargs['key']
            self._secret = kwargs['secret']

    def _public_api(self, method, path, extra=None, header=None):
        try:
            if header is None:
                header = {}

            if extra is None:
                extra = {}

            method = method.upper()
            path = '/'.join([self._endpoint, path])
            if method == 'GET':
                rq = requests.get(path, params=extra, headers=header)
            elif method == 'POST':
                rq = requests.post(path, data=extra, headers=header)
            else:
                return False, '', '[Upbit]incorrect method[{}]'.format(method), 1

            if rq.status_code > 200:
                return False, '', '[Upbit]Request Fail[{}], [{}]'.format(rq.status_code, rq.text), 5

            res = rq.json()

            if 'error' in res:
                return False, '', res['error']['message'], 1

            else:
                return True, res, '', 0
        except Exception as ex:
            return False, '', '[Upbit]Unexpected Error[{}]'.format(ex), 1

    def _private_api(self, method, path, extra=None):
        payload = {
            'access_key': self._key,
            'nonce': int(time.time() * 1000),
        }

        if extra is not None:
            payload.update({'query': urlencode(extra)})

        header = self.get_jwt_token(payload)

        return self._public_api(method, path, extra, header)

    def get_jwt_token(self, payload):
        # _private_api, _async_private_api에 쓰인다.
        return {'Authorization': 'Bearer {}'.format(jwt.encode(payload, self._secret,).decode('utf8'))}

    def get_ticker(self, market):
        # ticker 값을 가져온다.
        # [{key:value}, {}...] 형태로 반환된다.
        return self._public_api('get', 'ticker', {'markets': market})

    def _currencies(self):
        # get_currencies와 service_currencies에 사용하기 위한 내부 함수.
        return self._public_api('get', '/'.join(['market', 'all']))

    def get_available_coin(self):
        s, currencies, m, t = self._currencies()
        if not s:
            return False, '', m, t

        return True, [data['market'].replace('-', '_') for data in currencies], '', 0

    def service_currencies(self):
        # Transaction_fee 값을 구할 때 사용 된다.
        # [BTC, ETH, ...]와 같은 형태가 반환된다.
        s, currencies, m, t = self._currencies()
        if not s:
            return False, '', m, t

        res = []
        for data in currencies:
            data = data['market'].split('-')[1]
            if data not in res:
                res.append(data)

        return True, res, '', 0

    def get_order_history(self, uuid):
        return self._private_api('get', 'order', {'uuid': uuid})

    def withdraw(self, coin, amount, to_address, payment_id=None):
        # todo 확인

        params = {
                    'currency': coin,
                    'address': to_address,
                    'amount': str(amount),
                }

        if payment_id:
            params.update({'secondary_address': payment_id})

        return self._private_api('post', '/'.join(['withdraws', 'coin']), params)

    def buy(self, coin, amount):
        # todo 확인

        s, price, m, t = self.get_ticker(coin)

        if not s:
            return False, '', m, t

        if DEBUG:
            return True, '', 'DEBUG 상태입니다.', 0

        amount, price = map(str, (amount, price * 1.05))

        params = {
            'market': coin,
            'side': 'bid',
            'volume': amount,
            'price': price,
            'ord_type': 'limit'
        }

        return self._private_api('POST', 'orders', params)

    def sell(self, coin, amount):
        # todo 확인
        s, price, m, t = self.get_ticker(coin)

        if not s:
            return False, '', m, t

        if DEBUG:
            return True, '', 'DEBUG 상태입니다.', 0

        amount, price = map(str, (amount, price * 0.95))

        params = {
            'market': coin,
            'side': 'ask',
            'volume': amount,
            'price': price,
            'ord_type': 'limit'
        }

        return self._private_api('POST', 'orders', params)

    async def _async_public_api(self, method, path, extra=None, header=None):
        if header is None:
            header = {}

        if extra is None:
            extra = {}
        try:
            async with aiohttp.ClientSession(headers=header) as s:
                method = method.upper()
                path = '/'.join([self._endpoint, path])

                if method == 'GET':
                    rq = await s.get(path, params=extra)
                elif method == 'POST':
                    rq = await s.post(path, data=extra)
                else:
                    return False, '', '[{}]incorrect method'.format(method), 1

                res = json.loads(await rq.text())

                if 'error' in res:
                    return False, '', res['error']['message'], 1

                else:
                    return True, res, '', 0
        except Exception as ex:
            return False, '', 'Error [{}]'.format(ex), 1

    async def _async_private_api(self, method, path, extra=None):
        payload = {
            'access_key': self._key,
            'nonce': int(time.time() * 1000),
        }

        if extra is not None:
            payload.update({'query': urlencode(extra)})

        header = self.get_jwt_token(payload)

        return await self._async_public_api(method, path, extra, header)

    async def _get_deposit_addrs(self):
        return await self._async_private_api('get', '/'.join(['deposits', 'coin_addresses']))

    async def get_deposit_addrs(self, coin_list=None):
        # 입금 주소를 반환하기 위해 사용되는 함수.
        # [{'currency': 'BTC', 'deposit_address': '주소', 'secondary_address': None}, {}...]
        # 과 같은 형식이 반환 된다.
        s, d, m, t = await self._get_deposit_addrs()

        if not s:
            return False, d, m, t

        dic_ = {}
        for data in d:
            dic_[data['currency']] = data['deposit_address']

            if data['secondary_address']:
                dic_['{}TAG'.format(data['currency'])] = data['secondary_address']

        return True, dic_, '', 0

    async def _get_balance(self):
        # blance를 갖기 위한 내부 함수.
        # Upbit의 Balance API를 호출한다.
        s, d, m, t = await self._async_private_api('get', 'accounts')
        return (False, d, m, t) if not s else (True, d, m, 10)

    async def balance(self):
        # 밸런스 값을 가져오고, Dic형태로 반환한다.
        # [{'currency': 'BTC', 'balance': '0.00223264' ...}, {}] 형태가 반환 된다.
        s, d, m, t = await self._get_balance()

        if not s:
            return False, '', m, t

        else:
            return True, {bal['currency']: bal['balance'] for bal in d}, '', 0

    async def get_orderbook(self, market):
        # [{orderbook_units:[{}, {}, ...], {}...}] 과 같은 형식이 반환된다.
        return await self._async_public_api('get', 'orderbook', {'markets': market})

