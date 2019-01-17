from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import *
import queue
import sys
import time
import os
from selenium import webdriver

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from PriceCompare.coin_thread import ProcessingCoin


class Widget(QWidget):
    def __init__(self, coins):
        super().__init__()
        self.setupUi(self)

        self.flag = True

        data_q = queue.Queue()
        command_q = queue.Queue()

        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)

        ud = UpbitDriver(data_q, command_q, driver)
        ud.start()

        for coin in coins:
            ct = ProcessingCoin(data_q, command_q, driver, coin)
            ct.return_signal.connect(self.table_widget)
            ct.start()

            time.sleep(0.2)

    def table_widget(self, val):
        if self.flag:
            self.model = ManageTableModel()
            self.coin_table.setModel(self.model)
            self.coin_table.show()

            self.flag = False

        else:
            oc = self.Coin_Table_view_model.rowCount()
            self.Coin_Table_view_model.insertRow(oc, None, data=val)

        self.CoinTable.show()


class UpbitDriver(QThread):
    def __init__(self, data_q, command_q, driver):
        super().__init__()
        self.data_q = data_q # 데이터를 보낼 큐
        self.command_q = command_q  # 몇개의 데이터가 필요한지 확인하는 명령큐
        self.driver = driver

    def run(self):
        base_currency = ['KRW', 'BTC', 'ETH', 'USDT']
        count, payment = 0, {}
        payment_path = self.driver.find_elements_by_xpath('//ul[@class="ty05"]/li')
        while True:
            if self.command_q.empty():
                for n, pay in enumerate(base_currency):
                    payment_path[n].click()

                    name = [
                        self.driver.execute_script("return arguments[0].textContent", val).split('/')[0] for val in
                        self.driver.find_elements_by_xpath('//table[@class="highlight"]/tbody//td[@class="tit"]/em')
                    ]

                    price = [
                        self.driver.execute_script("return arguments[0].textContent", val).replace(",", "") for val in
                        self.driver.find_elements_by_xpath('//table[@class="highlight"]/tbody//td/strong')
                    ]

                    payment[pay] = {'name': name, 'price': price}

                    time.sleep(0.1)

            else:
                count += self.command_q.get()

            for _ in range(count):
                self.data_q.put(payment)

            count = 0
