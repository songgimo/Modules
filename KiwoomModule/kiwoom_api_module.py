import time
import asyncio


class KiwoomApiModule:
    def __init__(self, kh_regist):
        self.kh_regist = kh_regist
        self._received = []
        self._set_flag = '0'

    def _set_input_value(self, name, value):
        return self.kh_regist.dynamicCall('SetInputValue(QString, QString)', name, value)

    def _request_common_data(self, rq_name, tx_code, scn_no, repeat=False):
        if repeat:
            repeat = 2
        else:
            repeat = 0

        res = self.kh_regist.dynamicCall('CommRqData(QString, QString, int, QString)',
                                          [rq_name, tx_code, repeat, scn_no])

        return res

    def _set_real_reg(self, stock_code, field):
        self.kh_regist.dynamicCall('SetRealReg(QString, QString, QString, QString)',
                                   '5005', stock_code, field, self._set_flag)

        if self._set_flag == '0':
            self._set_flag = '1'

    def _request_default_info(self, stock_code, rq_name, repeat):
        # 주식 기본정보요청을 하는 함수
        # 시작가격, 현재 가격을 가져오는데 사용한다.

        tx_code = 'opt10001'
        # 싱글 데이터이기 때문에 index는 0으로 설정한다.
        scn_no = stock_code

        self._set_input_value('종목코드', stock_code)
        self._request_common_data(rq_name, tx_code, scn_no, repeat)

    def _request_repeat_info(self, stock_code, rq_name, repeat):
        # 주식 기본정보요청을 하는 함수
        # 시작가격, 현재 가격을 가져오는데 사용한다.

        tx_code = 'opt10007'
        # 싱글 데이터이기 때문에 index는 0으로 설정한다.
        scn_no = stock_code

        self._set_input_value('종목코드', stock_code)
        self._request_common_data(rq_name, tx_code, scn_no, repeat)

    def _send_order(self, rq_name, scn_no, account, order_type, stock_code, qty, price, trade_type, ogn_order_no=''):
        # 매매 주문을 하는 함수
        '''
              SendOrder(
              BSTR sRQName, // 사용자 구분명
              BSTR sScreenNo, // 화면번호
              BSTR sAccNo,  // 계좌번호 10자리
              LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
              BSTR sCode, // 종목코드
              LONG nQty,  // 주문수량
              LONG nPrice, // 주문가격
              BSTR sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
              BSTR sOrgOrderNo  // 원주문번호입니다. 신규주문에는 공백, 정정(취소)주문할 원주문번호를 입력합니다.
              )
        '''

        if ogn_order_no:
            pass
            # 정정/취소 할때 정정/취소할 주문번호를 입력받는다.

        self.kh_regist.dynamicCall('SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
                                   [rq_name, scn_no, account, order_type, stock_code, qty, price, trade_type,
                                    ogn_order_no])

    def get_common_data(self, tx_code, rc_name, index, item_name):
        return self.kh_regist.dynamicCall('GetCommData(QString, QString, int, QString)',
                                          [tx_code, rc_name, index, item_name]).replace(' ', '')

    def get_common_real_data(self, stock_code, field):
        # self._set_real_reg(stock_code, str(field))
        return self.kh_regist.dynamicCall('GetCommRealData(QSting, int)', [stock_code, field])

    def login_kiwoom_api(self):
        # kiwoom open API를 호출하는 함수.
        self.kh_regist.dynamicCall("CommConnect()")

    def get_account_list(self):
        return self.kh_regist.dynamicCall('GetLoginInfo("ACCLIST")').split(';')

    def get_account_info(self, account, stock_code):
        self._set_input_value('계좌번호', account)
        self._set_input_value('비밀번호', '')
        self._set_input_value('상장폐지조회구분', '0')
        self._set_input_value('비밀번호입력매체구분', '00')

        scn_no = stock_code
        return self._request_common_data('예수금_{}'.format(stock_code), 'OPW00004', scn_no, False)

    def request_current_stock_info(self, account):
        self._set_input_value('계좌번호', account)
        self._set_input_value('비밀번호', '')
        self._set_input_value('상장폐지조회구분', '0')
        self._set_input_value('비밀번호입력매체구분', '00')

        return self._request_common_data('보유수량', 'OPW00004', '0102', False)

    def get_current_stock_info(self):
        # request_current_stock_info로 요청
        # get_repeat_count로 몇개의 데이터가 대기중인지 확인
        # get_current_stock_info로 데이터 값 return
        tx_code = 'OPW00004'
        cnt = self.get_repeat_count(tx_code, '예수금')

        res = {}
        for n in range(cnt):
            # tx_code, rc_name, index, item_name
            stock_name = self.get_common_data(tx_code, '', n, '종목명')
            qty = self.get_common_data(tx_code, '', n, '보유수량')
            res[stock_name] = qty

        return res

    def get_repeat_count(self, tx_code, rc_name):
        return self.kh_regist.dynamicCall('GetRepeatCnt(QString, QSting)', [tx_code, rc_name])

    def get_stock_code_by_market(self, market_code):
        # 주식 종목코드를 시장 구분에 따라 반환한다.
        # 0:장내, 3:ELW, 4:뮤추얼펀드, 5:신주인수권, 6:리츠,
        # 8:ETF, 9:하이일드펀드, 10:코스닥, 30:K-OTC, 50:코넥스(KONEX)
        return self.kh_regist.dynamicCall('GetCodeListByMarket(QString)', market_code).split(';')

    def get_hangul_by_stock_code(self, stock_code):
        # 주식 종목코드를 바탕으로 한글이름을 반환한다.
        return self.kh_regist.dynamicCall('GetMasterCodeName(QString)', stock_code)

    def kiwoom_connect_check(self):
        # 로그인이 정상적으로 되었는지에 대한 Check, 로그인 되어있는 경우 1, 아닌 경우 0을 반환한다.
        return self.kh_regist.dynamicCall("GetConnectState()")

    def get_opening_price(self, stock_code):
        # 시초가 반환 함수
        return self._request_default_info(stock_code, '시가_{}'.format(stock_code), False)

    def get_current_price(self, stock_code):
        # 현재가 반환 함수
        # get_comm_real_data라는 api가 존재하지만 주식 기본 정보요청 함수로도 처리 가능
        return self._request_repeat_info(stock_code, '현재가_{}'.format(stock_code), False)

    def buy_stock(self, account, stock_code, qty, price, trade_type):
        # 매수함수, 신규 매수는 1번임
        order_type = 1
        if trade_type == '지정가':
            trade_type = '00'

        elif trade_type == '시장가':
            trade_type = '03'

        scn_no = stock_code
        return self._send_order('buy_order', scn_no, account, order_type, stock_code, qty, price, trade_type, '')

    def sell_stock(self, account, stock_code, qty, price, trade_type):
        # 매도함수, 신규매도는 2번임
        order_type = 2

        if trade_type == '지정가':
            trade_type = '00'

        elif trade_type == '시장가':
            trade_type = '03'

        scn_no = stock_code
        return self._send_order('sell_order', scn_no, account, order_type, stock_code, qty, price, trade_type, '')


