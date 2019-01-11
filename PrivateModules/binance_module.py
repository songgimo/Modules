import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from decimal import *
import asyncio
import time
import aiohttp


class BaseBinance:
    def __init__(self, **kwargs):
        self._endpoint = 'https://api.binance.com'

        if kwargs:
            self.__key = kwargs['key']
            self.__secret = kwargs['secret']

    def private_api(self, method, path, server_time, params=None):
        if params is None:
            params = {}

        params['timestamp'] = server_time
        params['signature'] = hmac.new(self.__secret.encode('utf-8'), urlencode(sorted(params.items())).encode('utf-8'),
                                       hashlib.sha256).hexdigest()

        return self.public_api(method, path, params)

    def public_api(self, method, path, params=None):
        if params is None:
            params = {}

        if method == 'GET':
            rq = requests.get(path, json=params, headers={"X-MBX-APIKEY": self.__key})

        elif method == 'POST':
            rq = requests.post(path, data=params, headers={"X-MBX-APIKEY": self.__key})

        else:
            return False, '', '[{}]Incorrect method'.format(method)

        res = rq.json()

        if 'msg' in res:
            return False, '', res['msg']

        else:
            return True, res, ''

    def get_servertime(self):
        return self.public_api('get', '/api/v1/time')

    def get_exchange_info(self):
        return self.public_api('get', '/api/v1/exchangeInfo')

    def get_step_size(self, stat):
        return {sm['symbol']: sm['symbol']['filters'][1]['stepSize'] for sm in stat['symbols']}

    def service_currencies(self, data):
        return list(data)

    def buy(self, coin, amount, server_time):
        params = {
                    'symbol': coin,
                    'side': 'buy',
                    'quantity': '{0:4f}'.format(amount).strip(),
                    'type': 'MARKET'
                  }

        return self.private_api('POST', '/api/v3/order', server_time, params)

    def sell(self, coin, amount, server_time):
        params = {
                    'symbol': coin,
                    'side': 'sell',
                    'quantity': '{0:4f}'.format(amount).strip(),
                    'type': 'MARKET'
                  }

        self.private_api('POST', '/api/v3/order', server_time, params)

    def get_ticker(self):
        return self.public_api('get', '/api/v1/ticker/24hr')

    def withdraw(self, coin, amount, to_address, server_time, payment_id=None):
        params = {
                    'asset': coin,
                    'address': to_address,
                    'amount': '{}'.format(amount),
                    'name': 'Hello'
                }
        if payment_id:
            params['addresstag'] = payment_id

        return self.private_api('post', '/wapi/v3/withdraw.html', server_time, params)

    def get_candle(self, coin, unit, count):
        # old --> new
        params = {
                    'symbol': coin,
                    'interval': '{}m'.format(unit),
                    'limit': count,
        }
        return self.public_api('get', '/api/v1/klines', params)

    def get_candle_info(self, candle_data):
        candle_list = list(map(float, candle_data[1:7]))
        return {x: candle_list[n] for n, x in enumerate(['open', 'high', 'low', 'close', 'volume', 'timestamp'])}

    def get_uuid_history(self, uuid, symbol, server_time):
        return self.private_api('get', '/api/v3/order', server_time, {'symbol': symbol, 'origClientOrderId': uuid})

    def get_order_history(self, uuid_history):
        total_vol = 0
        for trade_data in uuid_history:
            total_vol += Decimal(trade_data['origQty']).quantize(Decimal(10) ** -8, rounding=ROUND_DOWN)

        return {'market': uuid_history['symbol'], 'volume': total_vol}

    async def async_private_api(self, method, path, server_time, params=None):
        try:
            async with aiohttp.ClientSession(headers={"X-MBX-APIKEY": self.__key}) as s:
                if params is None:
                    params = {}

                params['timestamp'] = server_time
                path = '/'.join([self._endpoint, path])
                if method == 'GET':
                    sig = hmac.new(self.__secret.encode('utf-8'), urlencode(sorted(params.items())).encode('utf-8'),
                                   hashlib.
                                   sha256).hexdigest()

                    query = "{}&signature={}".format(urlencode(sorted(params.items())), sig)
                    rq = await s.get('{}?{}'.format(path, query))
                else:
                    rq = await s.post(path, data=params)

                res = json.loads(await rq.text())

                if 'msg' in res:
                    return False, res, res['msg']

                return True, res, ''

        except Exception as ex:
            return False, '', 'Error[{}]'.format(ex)

    async def async_public_api(self, path, params=None):
        try:
            async with aiohttp.ClientSession() as s:
                if params is None:
                    params = {}

                rq = await s.get('/'.join([self._endpoint, path]), params=params)
                res = json.loads(await rq.text())

                if 'msg' in res:
                    return False, '', res['msg']

                else:
                    return True, res, ''

        except Exception as ex:
            return False, '', 'Error[{}]'.format(ex)

    async def get_deposit_addrs(self, coin_list, server_time):
        try:
            dic_ = {}
            for coin in coin_list:
                suc, data, msg = await self.async_private_api('GET', '/wapi/v3/depositAddress.html', server_time, {'asset': coin})

                if not data['success'] or not suc:
                    continue

                dic_[coin] = data['address']

                if 'addressTag' in data:
                    dic_['{}TAG'.format(coin)] = data['addressTag']

            return True, dic_, ''

        except Exception as ex:
            return False, '', 'Error[{}]'.format(ex)

    async def get_trading_fee(self):
        return True, 0.001, ''

    async def get_transaction_fee(self):
        async with aiohttp.ClientSession() as s:
            fees = {}

            rq = await s.get('https://www.binance.com/assetWithdraw/getAllAsset.html')
            data = json.loads(await rq.text())

            if not data:
                return False, '', 'fail to load data'

        for f in data:
            if f['assetCode'] == 'BCC':
                f['assetCode'] = 'BCH'

            fees[f['assetCode']] = Decimal(f['transactionFee']).quantize(Decimal(10)**-8)

        return True, fees, ''

    async def get_balance(self, server_time):
        return await self.async_private_api('GET', '/api/v3/account', server_time)

    async def get_remain_coin(self, data):
        remaining = {}
        for bal in data['balances']:
            if float(bal['free']) > 0:
                remaining[bal['asset'].upper()] = float(bal['free'])

        return remaining


