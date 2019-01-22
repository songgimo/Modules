import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from datetime import datetime
from decimal import *
import base64
import time
import aiohttp

SIGNATURE_VER = 2


class Huobi:
    def __init__(self, **kwargs):
        self._endpoint = 'https://api.huobi.pro'

        if kwargs:
            self._key = kwargs['key']
            self._secret = kwargs['secret']
            self._account_id = kwargs['account_id']

        self.transaction_list = [
            'USDT', 'BTC', 'ETH', 'HT', 'BCH', 'XRP',
            'LTC', 'ADA', 'EOS', 'XEM', 'DASH', 'TRX',
            'LSK', 'ICX', 'QTUM', 'ETC', 'OMG', 'HSR',
            'ZEC', 'BTS', 'SNT', 'SALT', 'GNT', 'CMT',
            'BTM', 'PAY', 'KNC', 'POWR', 'BAT', 'DGD',
            'VEN', 'QASH', 'ZRX', 'GAS', 'MANA', 'ENG',
            'CVC', 'MCO', 'MTL', 'RDN', 'STORJ', 'SRN',
            'CHAT', 'LINK', 'ACT', 'TNB', 'QSP', 'REQ',
            'RPX', 'APPC', 'RCN', 'ADX', 'TNT', 'OST',
            'ITC', 'LUN', 'GNX', 'AST', 'EVX', 'MDS',
            'SNC', 'PROPY', 'EKO', 'NAS', 'WAX', 'WICC',
            'TOPC', 'SWFTC', 'DBC', 'ELF', 'AIDOC', 'QUN',
            'IOST', 'YEE', 'DAT', 'THETA', 'LET', 'DTA', 'UTK',
            'MEET', 'ZIL', 'SOC', 'RUFF', 'OCN', 'ELA', 'ZLA',
            'STK', 'WPR', 'MTN', 'MTX', 'EDU', 'BLZ', 'ABT', 'ONT', 'CTXC'
        ]

        self.get_headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
        }

        self.post_headers = {
            "Accept": "application/json",
            'Content-Type': 'application/json'
        }

    def get_account_id(self):
        return self.api_request('get', '/'.join(['v1', 'account', 'accounts']))

    def get_all_history(self, symbol):
        return self.api_request('get', '/v1/order/orders', {'symbol': symbol,
                                                            'type': 'buy-market', 'states': 'filled'})

    def get_uuid_history(self, uuid):
        return self.api_request('get', '/v1/order/orders/{}'.format(uuid), {'order-id': uuid})

    def encrypto(self, method, path, params, sign_data):
        if method == 'GET':
            params.update(sign_data)
            encode_qry = urlencode(sorted(params.items()))

        else:
            encode_qry = urlencode(sorted(sign_data.items()))

        payload = [method, 'api.huobi.pro', path, encode_qry]
        payload = '\n'.join(payload)

        sign = hmac.new(self._secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).digest()

        return base64.b64encode(sign).decode()

    def api_request(self, method, path, params=None):
        if params is None:
            params = {}
        method = method.upper()

        sign_data = {
                    'AccessKeyId': self._key,
                    'SignatureMethod': 'HmacSHA256',
                    'SignatureVersion': SIGNATURE_VER,
                    'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                     }

        sign = self.encrypto(method, path, params, sign_data)
        url = self._endpoint + path

        if method == 'GET':
            params['Signature'] = sign

        else:
            sign_data['Signature'] = sign
            url += '?' + urlencode(sign_data)

        return self.http_request(method, url, params)

    def http_request(self, method, path, params=None):
        if params is None:
            params = {}

        method = method.upper()
        try:
            if method == 'GET':
                postdata = urlencode(params)
                rq = requests.request(method, path, params=postdata, headers=self.get_headers)

            else:
                postdata = json.dumps(params)
                rq = requests.request(method, path, data=postdata, headers=self.post_headers)

            rqj = rq.json()

            if rqj['status'] in 'error':
                return False, '', rqj['err-msg'], 1
            else:
                return True, rqj, '', 0
        except Exception as ex:
            return False, '', '서버와 통신에 실패하였습니다 = [{}]'.format(ex), 1

    def buy(self, coin, amount):
        params = {
                    'account-id': self._account_id,
                    'symbol': coin,
                    'amount': '{}'.format(amount).strip(),
                    'type': 'buy-market'
                  }

        return self.api_request('POST', '/v1/order/orders/place', params)

    def sell(self, coin, amount):
        params = {
                    'account-id': str(self._account_id),
                    'symbol': coin,
                    'amount': '{}'.format(amount).strip(),
                    'type': 'sell-market'
                  }
        return self.api_request('POST', '/v1/order/orders/place', params)

    def withdraw(self, coin, amount, to_address, payment_id=None):
        params = {
                    'currency': coin.lower(),
                    'address': to_address,
                    'amount': '{}'.format(amount)
        }
        if payment_id:
            tag_dic = {'addr-tag': payment_id}
            params.update(tag_dic)

        return self.api_request('POST', '/v1/dw/withdraw/api/create', params)

    def get_available_coin(self):
        return self.http_request('GET', self._endpoint + '/v1/common/currencys')

    def get_candle_history(self, data):
        history = {x: [] for x in ['open', 'high', 'low', 'close', 'volume', 'timestamp']}

        for info in data['data']:
            for key in ['open', 'high', 'low', 'close', 'volume', 'timestamp']:
                # 최신 -> 과거
                if key == 'volume':
                    history[key].append(info['vol'])
                elif key == 'timestamp':
                    history[key].append(info['id'])
                else:
                    history[key].append(info[key])

        return history

    def get_candle(self, coin, unit, count):
        path = '/'.join(['market', 'history', 'kline'])

        params = {
            'symbol': coin,
            #  period = 1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year
            'period': '{}min'.format(unit),
            'size': count
        }
        return self.http_request('GET', path, params)

    async def async_api_request(self, s, method, path, params=None):
        sign_data = {
                    'AccessKeyId': self._key,
                    'SignatureMethod': 'HmacSHA256',
                    'SignatureVersion': SIGNATURE_VER,
                    'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
                     }

        sign = self.encrypto(method, path, params, sign_data)
        url = self._endpoint + path

        if method == 'GET':
            params['Signature'] = sign
        else:
            sign_data['Signature'] = sign
            url += '?' + urlencode(sign_data)

        suc, data, msg, times = await self.async_http_request(s, method, url, params)

        return suc, data, msg, times

    async def async_http_request(self, s, method, path, params=None):
        if params is None:
            params = {}

        try:
            if method == 'GET':
                postdata = urlencode(params)
                rq = await s.get(path, params=postdata)
            else:
                postdata = json.dumps(params)
                rq = await s.post(path, data=postdata)

            rq = await rq.text()
            rqj = json.loads(rq)

            if rqj['status'] in 'error':
                return False, '', rqj['status'], 1
            else:
                return True, rqj, '', 0

        except Exception as ex:
            return False, '', '서버와 통신에 실패하였습니다 = [{}]'.format(ex), 1

    async def get_deposit_addrs(self):
        gac_suc, gac_data, gac_msg, gac_times = self.get_available_coin()

        if gac_suc:
            try:
                coins = gac_data['data']
                coin_addrs = {}
                async with aiohttp.ClientSession(headers=self.get_headers) as s:

                    for coin in coins:
                        suc, data, msg, times = await self.async_api_request(s, "GET", '/v1/query/deposit-withdraw',
                                                                             {"currency": coin, "type": "deposit",
                                                                              "from": "0", "size": "100"})
                        upper_coin = coin.upper()

                        if suc:
                            if data['data']:
                                coin_info = data['data'][0]
                                coin_addrs[upper_coin] = coin_info['address']

                                if coin_info['currency'] == 'xrp' or coin_info['currency'] == 'xmr' or coin_info['currency'] == 'eos':
                                    coin_addrs[upper_coin + 'TAG'] = coin_info['address-tag']

                            else:
                                coin_addrs[upper_coin] = ''

                    return True, coin_addrs, '', 0
            except Exception as ex:
                return False, '', '[Huobi]주소를 가져오는데 실패했습니다. [{}]'.format(ex), 1
        else:
            return False, '', '[Huobi]사용가능한 코인을 가져오는데 실패했습니다. [{}]'.format(gac_msg), 1

    async def balance(self):
        async with aiohttp.ClientSession(headers=self.get_headers) as sync:
            params = {'account-id': self._account_id}

            suc, data, msg, times = await self.async_api_request(
                                            sync,
                                            'GET',
                                            '/v1/account/accounts/{}/balance'.format(self._account_id),
                                            params)

            if suc:
                balance = {}
                for info in data['data']['list']:
                    if info['type'] == 'trade':

                        if float(info['balance']) > 0:
                            balance[info['currency'].upper()] = float(info['balance'])

                return suc, balance, msg, times

            else:
                return False, '', '[Huobi]지갑 값을 가져오는데 실패했습니다. [{}]'.format(msg)

