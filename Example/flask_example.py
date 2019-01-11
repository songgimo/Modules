import datetime
import logging
from flask import Flask
from flask import request
import json
import pymysql
import configparser

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.addHandler(logging.FileHandler('ServerLog.log'))

cfg = configparser.ConfigParser()
cfg.read('APISettings.ini')


def fetch_all_data(qry):
    cursor.execute(qry)

    fetch_ = cursor.fetchall()

    if not fetch_:
        return False, '', '값이 존재하지 않습니다.'

    else:
        list_ = []

        for fet in fetch_:
            dic_ = {}
            for index, j in enumerate(cursor.description):

                if isinstance(fet[index], datetime.datetime):
                    dic_[j[0]] = fet[index].isoformat()

                else:
                    dic_[j[0]] = fet[index]
            list_.append(dic_)

        return True, list_, ''


@app.route('/url_path', methods=['GET', 'POST', 'DELETE'])
def controller():
    try:
        res = json.loads(request.get_data().decode())
        if request.method == 'GET':
            return get_data(res)

        elif request.method == 'POST':
            return insert_data(res)

        elif request.method == 'DELETE':
            return delete_data(res)

        else:
            return json.dumps({'suc': False, 'data': '', 'msg': '올바른 Method를 통한 접근이 아닙니다.', 'time': 5})

    except Exception as ex:
        return json.dumps({'suc': False, 'data': '', 'msg': 'api값을 가져오는 중 에러가 발생했습니다. [{}]'.format(ex), 'time': 1})


def get_data(res):
    qry = 'SELECT select_data from data_table WHERE id_="{}"'.format(res['id_'])

    fet_suc, fet_data, fet_msg = fetch_all_data(qry)

    if not fet_suc:
        logger.debug(fet_msg)
        return json.dumps({'suc': False, 'data': '', 'msg': fet_msg, 'time': 1})

    return json.dumps({'suc': True, 'data': fet_data, 'msg': '성공적으로 데이터를 가져왔습니다.', 'time': 0})


def insert_data(res):
    qry = 'SELECT select_data from data_table WHERE id_="{}" and select_data="{}"'.format(res['id_'], res['select_data']
                                                                                            )

    fet_suc, fet_data, fet_msg = fetch_all_data(qry)

    if fet_suc:
        # fetch_data가 존재하는 경우엔 post가 되지 않는다. 오류메세지 출력.
        fet_msg = '현재 데이터 값은 DB에 존재하고 있습니다. userid[{}], select_data[{}], market[{}]'.format(res['id_'], res['select_data']
                                                                                     )

        logger.debug(fet_msg)
        return json.dumps({'suc': False, 'data': '', 'msg': fet_msg, 'time': 1})

    qry = '''
            INSERT INTO data_table
            VALUES ("{}", "{}", "{}")
          '''.format(res['id_'], res['select_data'])

    cursor.execute(qry)
    con.commit()

    return json.dumps({'suc': True, 'data': '', 'msg': '성공적으로 Insert 되었습니다.', 'time': 0})


def delete_data(res):
    qry = 'SELECT select_data from data_table WHERE id_="{}"'.format(res['id_'])

    fet_suc, fet_data, fet_msg = fetch_all_data(qry)

    if not fet_suc:
        logger.debug(fet_msg)
        return json.dumps({'suc': False, 'data': '', 'msg': fet_msg, 'time': 1})

    qry = 'DELETE FROM data_table WHERE id_="{}"'.format(res['id_'])
    cursor.execute(qry)
    con.commit()

    return json.dumps({'suc': True, 'data': '', 'msg': '성공적으로 Delete 되었습니다.', 'time': 0})


con = pymysql.connect(host=cfg['Settings']['host'], user=cfg['Settings']['user'], password=cfg['Settings']['password'],
                      db=cfg['Settings']['DB'], charset='utf8')
cursor = con.cursor()

app.run(port=8081)
