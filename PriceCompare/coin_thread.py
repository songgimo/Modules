from PyQt5.QtCore import *
from decimal import Decimal
import os
import sys

# append parent path
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# import binace_module for get ticker.
from PrivateModules import binance_module


class ProcessingCoin(QThread):
    return_signal = pyqtSignal(dict)

    def __init__(self, data_q, command_q, driver, index):
        super().__init__()
        self.data_q = data_q
        self.command_q = command_q
        self.driver = driver
        self.index = index

        self.binance = binance_module()

    def run(self):
        while True:
            self.command_q.put(1)
            data = self.data_q.get()  # {name: name, price: price}

            upbit_price = profit = binance_set = {}

            for key in data:
                if data[key]['name'] == self.index:
                    upbit_price[key] = Decimal(data[key]['price'][1]).quantize(Decimal(10) ** -8)
                    break
                else:
                    upbit_price[key] = 0

            suc, data, msg = self.binance.get_ticker()

            if not suc:
                # logger.debug(msg)
                continue

            for info in data:
                symbol_price = Decimal(info['price']).quantize(Decimal(10) ** -8)
                symbol_slice = info['symbol'][-3:]

                if symbol_slice == 'BTC':
                    binance_set['BTC'] = symbol_price
                    profit['BTC'] = Decimal((symbol_price / upbit_price['BTC'] - 1) * 100).quantize(Decimal(10) ** -8)

                elif symbol_slice == 'ETH':
                    binance_set['ETH'] = symbol_price
                    profit['ETH'] = Decimal((symbol_price / upbit_price['ETH'] - 1) * 100).quantize(Decimal(10) ** -8)

                else:  # symbol_slice == 'USDT':
                    binance_set['USDT'] = symbol_price
                    profit['USDT'] = Decimal((symbol_price / upbit_price['USDT'] - 1) * 100).quantize(Decimal(10) ** -8)

            price_list = [self.index]
            price_list += [[binance_set[base], profit[base]] for base in ['BTC', 'ETH', 'USDT']]


if __name__ == '__main__':
    os.path.dirname(os.path.abspath(os.path.dirname(__file__)))