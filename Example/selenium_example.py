from selenium import webdriver
import random
import configparser
import threading
import os
import sys
import queue

# import personal csv module
from PrivateModules.Etc.csv_module import CSVModule


cfg = configparser.ConfigParser()
cfg.read('./Settings.ini')

ROOT = os.path.dirname(os.path.abspath(__file__))

try:
    driver_path = os.path.join(ROOT, cfg['Setting']['driver path'])
    id_list_path = os.path.join(ROOT, cfg['Setting']['id file path'])
    proxy_path = os.path.join(ROOT, cfg['Setting']['proxy path'])
    thread_num = int(cfg['Setting']['thread_num'])

except:
    os.system("PAUSE")
    sys.exit()


class NaverSelenium(threading.Thread):
    def __init__(self, q):
        super(NaverSelenium, self).__init__()
        self.driver = None
        self.q = q

    def driver_setting(self, proxy_ip):
        self.driver = webdriver.Chrome(driver_path)
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--proxy-server={}'.format(proxy_ip))

        self.driver.implicitly_wait(30)
        self.driver.set_page_load_timeout(60)

    def import_proxies(self):
        with open(proxy_path, 'r') as f:
            proxy_list = f.read().split('\n')  # 프록시목록

        return proxy_list

    def crolling_news(self):
        return 'news_data'

    def run(self):
        proxy_list = self.import_proxies()

        while self.q.qsize():
            proxy = random.choice(proxy_list)

            self.driver_setting(proxy)


if __name__ == '__main__':
    DEBUG = True

    c = CSVModule()

    # [[id, pw], [..., ...]]
    list_ = c.import_csv(id_list_path)

    id_queue = queue.Queue()
    list(map(id_queue.put, list_))

    for _ in range(thread_num):
        t = NaverSelenium(id_queue)
        t.start()


