from selenium import webdriver
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os, random
import csv
from selenium.webdriver.support.select import *
import re
import logging
from datetime import datetime
import configparser
import sys
from selenium.webdriver.common.keys import *
from urllib.parse import urlencode
from selenium.common.exceptions import *


cfg = configparser.ConfigParser()
cfg.read('./Settings.ini')

class NaverSelenium:
    def __init__(self, driver):
        self.driver = driver

    def reopen_chrome(self, proxy):
        self.driver.quit()

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--silent")
        self.chrome_options.add_argument("--disable-logging")
        self.chrome_options.add_argument("--log-level=3")

        if proxy:
            next(proxy)

        self.driver = webdriver.Chrome(driver_path, chrome_options=self.chrome_options)

        self.driver.set_page_load_timeout(60)
        self.driver.implicitly_wait(30)

    def set_options(self):


    def import_proxies(self, proxy_path):
        with open(proxy_path, 'r') as f:
            try:
                self.__proxy_list = f.read().split('\n')  # 프록시목록
                return True, self.__proxy_list, 'Successfully load proxy list.'
            except Exception as e:
                return False, '', 'invalid proxy list [{}]'.format(e)

    def proxy_set(self):
        while True:
            for proxy in self.__proxy_list:
                self.chrome_options.add_argument('--proxy-server={}'.format(proxy))
                yield




if __name__ == '__main__':
    driver = webdriver.Chrome(cfg['Settings']['driver path'])
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(cfg['Settings']['driver path'], chrome_options=chrome_options)



    if proxy:

