import requests
import json
from decimal import Decimal
import logging
import sys
import os
import asyncio
import configparser
from decimal import ROUND_DOWN
import time
import aiohttp
import numpy as np


class Korbit:
    def __init__(self, key_, secret_, id_, pw):
        self.endpoint = 'https://api.korbit.co.kr'

        self.__key = key_
        self.__secret = secret_
        self.__id = id_
        self.__pw = pw

        self.__token = None
        self.token_time = 0

    def public_api(self, method, path, params=None):
        if params is None:
            params = {}

        method = method.upper()
        path = '/'.join([self.endpoint, path])
        if method == 'POST':
            rq = requests.post(method, path, data=params, headers=self.header())
        else:
            rq = requests.request(method, path, params=params, headers=self.header())

        if rq.status_code > 200:
            return False, '', '[{}]Request통신에 실패했습니다.'.format(rq.status_code)

        res = rq.json()

        if 'msg' in res:
            return False, '', res['msg']

        return True, res, ''

    def private_api(self, method, path, params=None):
        if params is None:
            params = {'nonce': int(time.time())}

        return self.public_api(method, path, params)

    def header(self):
        return {'Authorization': "{} {}".format(self.__token['token_type'], self.__token['access_token'])}

    def token_setting(self, params):
        try:
            rq = requests.post('/'.join([self.endpoint, 'v1', 'oauth2', 'access_token']), data=params)
            self.__token = rq.json()
            self.token_time = int(time.time())

            return True, self.__token, ''

        except Exception as ex:
            return False, '', '토큰 생성 실패. [{}]'.format(ex)

    def get_token(self):
        # call before use another functions
        data = {
            'client_id': self.__key,
            'client_secret': self.__secret,
            'username': self.__id,
            'password': self.__pw,
            'grant_type': 'password'
        }
        return self.token_setting(data)

    def refresh_token(self, refresh_token):
        data = {
            'client_id': self.__key,
            'client_secret': self.__secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        return self.token_setting(data)

    def buy(self, coin, amount):
        data = {
            'currency_pair': coin,
            'type': 'market',
            'fiat_amount': amount,
        }
        return self.private_api('post', '/'.join(['v1', 'user', 'orders', 'buy']), data)

    def sell(self, coin, amount):
        data = {
            'currency_pair': coin,
            'type': 'market',
            'coin_amount': amount,
        }

        return self.private_api('post', '/'.join(['v1', 'user', 'orders', 'sell']), data)

    def withdraw(self, coin, amount, to_address, payment_id=None):
        # Korbit API do not support withdraw coin except BTC
        params = {
            'currency': coin,
            'amount': amount,
            'address': to_address,
            'fee_priority': 'normal'

        }

        return self.private_api('POST', '/'.join(['v1', 'user', 'coins', 'out']), params)

    def balance_avaliable(self, data):
        return {coin: float(data[coin]['available']) for coin in data.keys()}

    async def async_public_api(self, method, path, params=None):
        async with aiohttp.ClientSession(headers=self.header()) as s:
            if params is None:
                params = {}

            method = method.upper()
            path = '/'.join([self.endpoint, path])
            if method == 'POST':
                rq = await s.post(path, data=params)
            else:
                rq = await s.request(method, path, params=params)

            if rq.status > 200:
                return False, '', '[{}]Request통신에 실패했습니다.'.format(rq.status_code)

            res = json.loads(await rq.text())

            if 'msg' in res:
                return False, '', res['msg']

            return True, res, ''

    async def async_private_api(self, method, path, params=None):
        if params is None:
            params = {'nonce': int(time.time())}

        return await self.async_public_api(method, path, params)

    async def balance(self):
        return await self.async_private_api('get', '/'.join(['v1', 'user', 'balances']))