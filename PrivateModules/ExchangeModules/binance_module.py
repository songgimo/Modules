import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from decimal import *
import asyncio
import time
import aiohttp
import math

DEBUG = True


class BaseBinance:
    def __init__(self, **kwargs):
        self._endpoint = 'https://api.binance.com'
        self._page_endopoint = 'https://www.binance.com'
        self._exchange_info = {}
        # 처음에 무조건 불러와야하는 함수.
        self.get_exchange_info()

        if kwargs:
            self._key = kwargs['key']
            self._secret = kwargs['secret']
            self._default_header = {"X-MBX-APIKEY": self._key}

    def _private_api(self, method, path, params=None):
        if params is None:
            params = {}

        s, nonce, m, t = self._get_servertime()

        if not s:
            return False, '', 'ServerTime을 가져오는데 실패했습니다.[{}]'.format(m), t

        params['timestamp'] = nonce
        sign = hmac.new(self._secret.encode('utf-8'), urlencode(sorted(params.items())).encode('utf-8'),
                        hashlib.sha256).hexdigest()

        query = "{}&signature={}".format(urlencode(sorted(params.items())), sign)
        path = '{}?{}'.format(path, query)

        return self._public_api(method, path, headers=self._default_header)

    def _public_api(self, method, path, params=None, headers=None):
        try:
            if params is None:
                params = {}

            if headers is None:
                headers = {}

            method = method.upper()
            path = '/'.join([self._endpoint, path])

            if method == 'GET':
                rq = requests.get(path, params=params, headers=headers)

            elif method == 'POST':
                rq = requests.post(path, data=params, headers=headers)

            else:
                return False, '', '[Binance]incorrect method[{}]'.format(method), 1

            if rq.status_code > 200:
                return False, '', '[Binance]Request Fail[{}], [{}]'.format(rq.status_code, rq.text), 5

            res = rq.json()

            if 'msg' in res:
                return False, '', res['msg'], 1

            else:
                return True, res, '', 0
        except Exception as ex:
            return False, '', '[Binance]Unexpected Error[{}]'.format(ex), 1

    def _get_servertime(self):
        # 바이낸스는 Nonce를 servertime을 통해 가져와야 한다.
        for _ in range(3):
            s, d, m, t, = self._public_api('get', '/'.join(['api', 'v1', 'time']))
            if s:
                return True, d['serverTime'], '', 0
            time.sleep(1)

        else:
            return False, '', m, 1

    def _get_exchange_info(self):
        # Binance에서 service하는 기본적인 코인들의 정보들이 들어있음.
        # {symbols:[{'symbol':...,}], {etc:}, ... }형태가 리턴 된다.
        return self._public_api('get', '/'.join(['api', 'v1', 'exchangeInfo']))

    def get_currencies(self):
        # Binance에서 service하는 coin값을 가져온다.
        # [BTC, ...] 형태의 값이 반환 됨

        return True, [ables.split('_')[1] for ables in self._exchange_info.keys()] + ['BTC'], '', 0

    def buy(self, coin, amount):
        if DEBUG:
            return True, '', 'DEBUG 상태입니다.', 0
        params = {
                    'symbol': coin,
                    'side': 'buy',
                    'quantity': '{0:4f}'.format(amount).strip(),
                    'type': 'MARKET'
                  }

        return self._private_api('POST', '/'.join(['api', 'v3', 'order']), params)

    def sell(self, coin, amount):
        if DEBUG:
            return True, '', 'DEBUG 상태입니다.', 0

        params = {
                    'symbol': coin,
                    'side': 'sell',
                    'quantity': '{0:4f}'.format(amount).strip(),
                    'type': 'MARKET'
                  }

        return self._private_api('POST', '/'.join(['api', 'v3', 'order']), params)

    def get_ticker(self):
        # [{}, {}]형태의 값이 반환 됨.
        return self._public_api('get', '/'.join(['api', 'v1', 'ticker', '24hr']))

    def withdraw(self, coin, amount, to_address, payment_id=None):
        params = {
                    'asset': coin,
                    'address': to_address,
                    'amount': '{}'.format(amount),
                    'name': 'Hello'
                }
        if payment_id:
            params['addresstag'] = payment_id

        return self._private_api('post', '/'.join(['wapi', 'v3', 'withdraw.html']), params)

    def get_candle(self, coin, unit, count):
        # old --> new
        params = {
                    'symbol': coin,
                    'interval': '{}m'.format(unit),
                    'limit': count,
        }
        return self._public_api('get', '/'.join(['api', 'v1', 'klines']), params)

    def get_exchange_info(self):
        # symbol 정보 값에서 각 코인의 step단위를 구하는 함수.
        # get_step_size 함수, service_currencies에 쓰이는 함수이며 처음에 호출되어야 하는 함수임.
        s, stat, m, t = self._get_exchange_info()

        if not s:
            return False, '', m, 5

        step_size = {}
        for sym in stat['symbols']:
            symbol = sym['symbol']
            market_coin = symbol[-3:]

            if 'BTC' in market_coin:
                trade_coin = symbol[:-3]
                # BNBBTC -> BTC-BNB
                coin = market_coin + '_' + trade_coin

                step_size.update({
                    coin: sym['filters'][2]['stepSize']
                })

        self._exchange_info = step_size

        return True, '', 'ExchangeInfo를 성공적으로 불러왔습니다.', 0

    async def _async_private_api(self, method, path, params=None):
        if params is None:
            params = {}

        s, nonce, m, t = self._get_servertime()

        if not s:
            return False, '', 'ServerTime을 가져오는데 실패했습니다.[{}]'.format(m), t

        params['timestamp'] = nonce
        sign = hmac.new(self._secret.encode('utf-8'), urlencode(sorted(params.items())).encode('utf-8'),
                        hashlib.sha256).hexdigest()

        query = "{}&signature={}".format(urlencode(sorted(params.items())), sign)
        path = '{}?{}'.format(path, query)

        params.pop('timestamp')
        return await self._async_public_api(method, path, params, headers=self._default_header)

    async def _async_public_api(self, method, path, params=None, headers=None, end_point=None):
        # end_point parameter가 추가된 이유는 get_transactionFee는 binance.com을 사용하기 때문.
        method = method.upper()
        if headers is None:
            headers = {}
        if params is None:
            params = {}

        if end_point is None:
            end_point = self._endpoint

        if params and headers and method == 'GET':
            # deposit_addrs같은 경우(path+ ?+query의 경우), params를 넣어선 안됨.
            params = {}

        try:
            async with aiohttp.ClientSession(headers=headers) as s:
                method = method.upper()

                if method == 'GET':
                    rq = await s.get('/'.join([end_point, path]), params=params)

                elif method == 'POST':
                    rq = await s.post('/'.join([end_point, path]), data=params)

                else:
                    return False, '', '[{}]incorrect method'.format(method), 1

                if rq.status > 200:
                    return False, '', '[Binance]Request Fail[{}], [{}]'.format(rq.status, rq.text), 5

                res = json.loads(await rq.text())

                if 'msg' in res:
                    return False, '', res['msg'], 1

                else:
                    return True, res, '', 0

        except Exception as ex:
            return False, '', 'Error[{}]'.format(ex), 1

    async def _get_deposit_addrs(self, coin):
        return await self._async_private_api('GET', '/'.join(['wapi', 'v3', 'depositAddress.html']), {'asset': coin})

    async def get_deposit_addrs(self, coin_list=None):
        if coin_list is None:
            s, coin_list, m, t = self.get_currencies()
        try:
            dic_ = {}
            for coin in coin_list:
                time.sleep(0.1)
                suc, data, msg, time_ = await self._get_deposit_addrs(coin)

                if not data['success'] or not suc:
                    continue

                dic_[coin] = data['address']

                if 'addressTag' in data:
                    if data['addressTag']:
                        dic_['{}TAG'.format(coin)] = data['addressTag']

            return True, dic_, '', 0

        except Exception as ex:
            return False, '', 'Error[{}]'.format(ex), 10

    async def _get_balance(self):
        return await self._async_private_api('GET', '/'.join(['api', 'v3', 'account']))

    async def balance(self):
        # {BTC:float(0.012)} 형태의 값이 반환 된다.

        s, data, m, t = await self._get_balance()

        if not s:
            return False, '', '[Binance]{}'.format(m), 5

        remaining = {bal['asset'].upper(): float(bal['free']) for bal in data['balances'] if float(bal['free']) > 0}

        return True, remaining, '', 0

    async def get_orderbook(self, coin):
        return await self._async_public_api('GET', '/'.join(['api', 'v1', 'depth']), {'symbol': coin})

