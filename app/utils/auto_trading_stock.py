import time
import numpy as np
import pandas as pd
import requests
import math
from pykis import PyKis, KisChart, KisStock, KisAuth
from datetime import datetime
import mplfinance as mpf
from dotenv import load_dotenv
import os
import json
from pykis import KisQuote
from pykis import KisBalance
from pykis import KisOrder
from pykis import KisRealtimePrice, KisSubscriptionEventArgs, KisWebsocketClient, PyKis
from pykis import PyKis, KisTradingHours
from pykis import PyKis, KisOrderProfits
from pykis import KisRealtimeExecution, KisSubscriptionEventArgs, KisWebsocketClient
import asyncio

# .env 파일 로드
load_dotenv()



class AutoTradingStock:
    def __init__(self, id, account, real_appkey, real_secretkey, virtual=False, virtual_id=None, virtual_appkey=None, virtual_secretkey=None):
        """
        AutoTradingStock 클래스 초기화
        실전투자와 모의투자를 선택적으로 설정 가능
        """
        # 속성 초기화
        self.virtual = virtual
        self.id = id
        self.account = account  # 계좌 번호 저장
        self.appkey = real_appkey
        self.secretkey = real_secretkey
        self.virtual_id = virtual_id
        self.virtual_appkey = virtual_appkey
        self.virtual_secretkey = virtual_secretkey
        self.ticket = None  # 실시간 체결 구독 티켓
        
        
        if self.virtual:
            # 모의투자용 PyKis 객체 생성
            if not all([id,account, real_appkey, real_secretkey,virtual_id, virtual_appkey, virtual_secretkey]):
                raise ValueError("모의투자 정보를 완전히 제공해야 합니다.")
            
            message = ("모의투자 API 객체를 생성 중입니다...")
            self.send_discord_webhook(message,"trading")
            self.kis = PyKis(
                id=id,
                account=account,
                appkey=real_appkey,
                secretkey=real_secretkey,
                virtual_id=virtual_id,
                virtual_appkey=virtual_appkey,
                virtual_secretkey=virtual_secretkey,
                keep_token=True  # API 접속 토큰 자동 저장
            )
        else:
            # 실전투자용 PyKis 객체 생성
            message = ("실전투자 API 객체를 생성 중입니다...")
            self.send_discord_webhook(message,"trading")
            self.kis = PyKis(
                id=id,
                account=account,
                appkey=real_appkey,
                secretkey=real_secretkey,
                keep_token=True  # API 접속 토큰 자동 저장
            )
            

        print(f"{'모의투자' if self.virtual else '실전투자'} API 객체가 성공적으로 생성되었습니다.")

        
    def get_account_info(self):
        """투자 유형 및 계좌 정보를 반환"""
        account_type = "모의 투자" if self.virtual else "실전 투자"
        return {
            "투자 유형": account_type,
            "계좌 번호": self.account,
            "사용된 ID": self.virtual_id if self.virtual else self.id

        }

    def send_account_info_to_discord(self):
        """계좌 정보를 디스코드 웹훅에 전송"""
        account_info = self.get_account_info()

        # 정보를 문자열로 정리
        message = (
            "📢 투자 계좌 정보:\n" +
            "\n".join([f"{key}: {value}" for key, value in account_info.items()])
        )

        # 디스코드로 전송
        self.send_discord_webhook(message, "trading")

    def get_access_token(self):
        """
        한국투자증권 API에서 액세스 토큰을 발급받는 함수
        """
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {
        "grant_type": "client_credentials",
        "appkey": os.getenv('API_KEY'),  # 본인의 appkey로 변경
        "appsecret": os.getenv('API_SECRET')  # 본인의 appsecret로 변경
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                token_data = response.json()
                print("토큰 발급 성공:", token_data)
                return token_data["access_token"]
            else:
                print(f"토큰 발급 실패: {response.status_code} {response.text}")
                return None
        except Exception as e:
            print(f"토큰 발급 중 오류 발생: {e}")
            return None    
        

    #def get_auth_info(self):
    #    """인증 정보 확인"""
    #    return {
    #        "id": self.id,
    #        "account": self.account,
    #        "virtual": self.virtual
            
            
    #    }

    def send_discord_webhook(self, message, bot_type):
        if bot_type == 'trading':
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # 복사한 Discord 웹훅 URL로 변경
            username = "Stock Trading Bot"

        data = {
            "content": message,
            "username": username,  # 원하는 이름으로 설정 가능
        }
        

        # 요청 보내기
        response = requests.post(webhook_url, json=data)
        
        # 응답 확인
        if response.status_code == 204:
            print("메시지가 성공적으로 전송되었습니다.")
        else:
            print(f"메시지 전송 실패: {response.status_code}, {response.text}")


    def get_stock_quote(self, symbol):
        """주식 시세를 가져와 디스코드로 전달"""
        try:
            # 종목 객체 가져오기
            stock = self.kis.stock(symbol)

            # 시세 가져오기
            quote: KisQuote = stock.quote()
            quote: KisQuote = stock.quote(extended=True) # 주간거래 시세
        # 시세 정보 문자열 생성
            message = (
    f"📊 종목 시세 정보\n"
    f"종목 코드: {quote.symbol}\n"
    f"종목명: {quote.name}\n"
    f"업종: {quote.sector_name}\n"
    f"현재가: {quote.close:,.0f} KRW\n"
    f"시가: {quote.open:,.0f} KRW\n"
    f"고가: {quote.high:,.0f} KRW\n"
    f"저가: {quote.low:,.0f} KRW\n"
    f"전일 대비 가격: {quote.change:,.0f} KRW\n"
    f"등락률: {quote.change / (quote.close - quote.change):.2%}\n"
    f"거래량: {quote.volume:,.0f} 주\n"
    f"거래 대금: {quote.amount:,} KRW\n"
    f"시가총액: {quote.market_cap:,} 억 KRW\n"
    f"52주 최고가: {quote.indicator.week52_high:,.0f} KRW (일자: {quote.indicator.week52_high_date})\n"
    f"52주 최저가: {quote.indicator.week52_low:,.0f} KRW (일자: {quote.indicator.week52_low_date})\n"
    f"EPS (주당순이익): {quote.indicator.eps:,.0f} KRW\n"
    f"BPS (주당순자산): {quote.indicator.bps:,.0f} KRW\n"
    f"PER (주가수익비율): {quote.indicator.per}\n"
    f"PBR (주가순자산비율): {quote.indicator.pbr}\n"
    f"단위: {quote.unit}\n"
    f"호가 단위: {quote.tick:,.0f} KRW\n"
    f"거래 정지 여부: {'정지' if quote.halt else '정상'}\n"
    f"과매수 상태: {'예' if quote.overbought else '아니오'}\n"
    f"위험도: {quote.risk.capitalize()}\n"
    )
            # 디스코드 웹훅 전송
            self.send_discord_webhook(message,"trading")

            # 디버깅용 출력
            print("주식 시세 정보:", message)
        except Exception as e:
            print(f"주식 시세 조회 중 오류 발생: {e}")
            error_message = f"❌ 주식 시세 조회 중 오류 발생: {e}"
            self.send_discord_webhook(error_message,"trading")
            
    def inquire_balance(self):
        """잔고 정보를 디스코드 웹훅으로 전송"""
        
                # 주 계좌 객체를 가져옵니다.
        account = self.kis.account()

        balance: KisBalance = account.balance()

        print(repr(balance)) # repr을 통해 객체의 주요 내용을 확인할 수 있습니다.
        
        try:
            # 기본 잔고 정보
            message = (
                f"📃 주식 잔고 정보\n"
                f"계좌 번호: {balance.account_number}\n"
                f"총 구매 금액: {balance.purchase_amount:,.0f} KRW\n"
                f"현재 평가 금액: {balance.current_amount:,.0f} KRW\n"
                f"총 평가 손익: {balance.profit:,.0f} KRW\n"
                f"총 수익률: {balance.profit_rate/ 100:.2%}\n\n"
            )
            
            
            # 보유 종목 정보 추가
            message += "📊 보유 종목 정보:\n"
            for stock in balance.stocks:
                message += (
                    f"종목명: {stock.symbol} (시장: {stock.market})\n"
                    f"수량: {stock.qty:,}주\n"
                    f"평균 단가: {stock.price:,.0f} KRW\n"
                    f"평가 금액: {stock.amount:,.0f} KRW\n"
                    f"평가 손익: {stock.profit:,.0f} KRW\n"
                    f"수익률: {stock.profit_rate /100:.2%}\n\n"
                )
                
                
            # 예수금 정보 추가
            message += "💰 예수금 정보:\n"
            for currency, deposit in balance.deposits.items():
                message += (
                    f"통화: {currency}\n"
                    f"금액: {deposit.amount:,.0f} {currency}\n"
                    f"환율: {deposit.exchange_rate}\n\n"
                )

            # 디스코드 웹훅으로 메시지 전송
            self.send_discord_webhook(message, "trading")

        except Exception as e:
            # 오류 메시지 처리
            error_message = f"❌ 잔고 정보를 처리하는 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")
    
    def place_order(self, symbol, qty, buy_price=None, sell_price=None, order_type="buy"):
        """주식 매수/매도 주문 함수
        Args:
            symbol (str): 종목 코드
            qty (int): 주문 수량
            price (int, optional): 주문 가격. 지정가 주문 시 필요
            order_type (str): "buy" 또는 "sell"
        """
        try:
            # 종목 객체 가져오기
            stock = self.kis.stock(symbol)

            # 매수/매도 주문 처리
            if order_type == "buy":
                if buy_price:
                    order = stock.buy(price=buy_price, qty=qty)  # price 값이 있으면 지정가 매수
                else:
                    order = stock.buy(qty=qty)  # 시장가 매수
                message = f"📈 매수 주문 완료! 종목: {symbol}, 수량: {qty}, 가격: {'시장가' if not buy_price else buy_price}"
            elif order_type == "sell":
                if sell_price:
                    order = stock.sell(price=sell_price)  # 지정가 매도
                else:
                    order = stock.sell()  # 시장가 매도
                message = f"📉 매도 주문 완료! 종목: {symbol}, 수량: {qty}, 가격: {'시장가' if not sell_price else sell_price}"
            else:
                raise ValueError("Invalid order_type. Must be 'buy' or 'sell'.")

            # 디스코드로 주문 결과 전송
            self.send_discord_webhook(message, "trading")

            return order

        except Exception as e:
            error_message = f"주문 처리 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")

    
    def get_trading_hours(self, country_code):
        """
        특정 국가의 주식 시장 거래 시간을 조회합니다.
        Args:
            country_code (str): 국가 코드 (예: US, KR, JP)
        """
        try:
            # 거래 시간 조회
            trading_hours: KisTradingHours = self.kis.trading_hours(country_code)

            # 메시지 정리
            message = (
                f"📅 **{country_code} 주식 시장 거래 시간**\n"
                f"정규 거래 시작: {trading_hours.open_kst}\n"
                f"정규 거래 종료: {trading_hours.close_kst}\n"
            )

            # 결과 출력 및 웹훅 전송
            print(message)
            self.send_discord_webhook(message, "trading")
            return message
        
        except Exception as e:
            error_message = f"❌ 거래 시간 조회 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")
            return None

#실시간체결 모의투자 불가??
    def start_realtime_execution(self):
        """실시간 체결 구독 시작"""
        account = self.kis.account()

        def on_execution(sender: KisWebsocketClient, e: KisSubscriptionEventArgs[KisRealtimeExecution]):
            """체결 이벤트 처리 함수"""
            execution_data = e.response
            self.send_discord_webhook(self.kis.websocket.subscriptions)  # 디스코드 웹훅 전송

        # 이벤트 구독 시작
        self.ticket = account.on("execution", on_execution)
        print("🚀 실시간 체결 구독을 시작했습니다.")

    def stop_realtime_execution(self):
        """
        실시간 체결 내역 구독 종료
        """
        if self.ticket:
            self.ticket.unsubscribe()
            print("🛑 실시간 체결 구독이 종료되었습니다.")

# #직접 API 호출한 체결강도 순위 조회
#     def get_volume_power_ranking(self, market_code="J", input_market="2001"):
#         """
#         시장별 거래량 순위 조회 메소드
#         Args:
#         market_code (str): 시장 코드 (KOSPI: "J", KOSDAQ: "Q", 전체: "U")
#         """
#         # API 요청 URL
#         url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/volume-power"

#         # 요청 헤더 설정
#         headers = {
#             "Content-Type": "application/json; charset=utf-8",
#             "Authorization": str(self.kis.token),
#             "appkey": self.appkey,
#             "appsecret": self.secretkey,
#             "tr_id": "FHPST01680000",
#             "custtype": "P"
#         }

#         # 요청 파라미터 설정
#         params = {
#             "fid_trgt_exls_cls_code": "0",
#             "fid_cond_mrkt_div_code": market_code,
#             "fid_cond_scr_div_code": "20168",
#             "fid_input_iscd": input_market,
#             "fid_div_cls_code": "0",
#             "fid_input_price_1": "",
#             "fid_input_price_2": "",
#             "fid_vol_cnt": "",
#             "fid_trgt_cls_code": "0"
#         }

#         try:
#             # API 요청
#             response = requests.get(url, headers=headers, params=params)

#             if response.status_code == 200:
#                 result = response.json()
#                 rankings = result.get("output", [])
                
#                 # 조회된 결과를 문자열로 정리
#                 message = "**📊 체결강도 순위 조회 결과:**\n"
#                 for idx, stock in enumerate(rankings[:10]):  # 상위 10개 종목만 표시
#                     message += (
#                         f"{idx+1}. 종목명: {stock['hts_kor_isnm']}\n"
#                         f"종목코드: {stock["stck_shrn_iscd"]}\n"
#                         f"당일 체결강도: {stock['tday_rltv']}\n"
                        
#                     )
#                 print(message)
#                 self.send_discord_webhook(message, "trading")

#             else:
#                 error_message = f"❌ 거래량 순위 조회 실패: {response.status_code} {response.text}"
#                 print(error_message)
#                 self.send_discord_webhook(error_message, "trading")

#         except Exception as e:
#             error_message = f"❌ 거래량 순위 조회 중 오류 발생: {e}"
#             print(error_message)
#             self.send_discord_webhook(error_message, "trading")

    def get_volume_power_ranking_and_trade(self, input_market="2001"):
        """
        체결강도 순위를 조회하고 조건에 따라 종목을 자동으로 매수/매도
        Args:
            market_code (str): 시장 코드 (KOSPI: "J", KOSDAQ: "Q", 전체: "U")
            input_market (str): 조회할 시장 코드
        """
        # API 요청 URL
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/volume-power"

        # 요청 헤더 설정
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "FHPST01680000",
            "custtype": "P"
        }

        # 요청 파라미터 설정
        params = {
            "fid_trgt_exls_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": input_market,
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_trgt_cls_code": "0"
        }

        try:
            # API 요청 보내기
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                rankings = result.get("output", [])

                # 메시지 구성
                message = "**📊 체결강도 상위 종목 조회 및 자동 매수/매도**\n"
                top_stocks = []

                for idx, stock in enumerate(rankings[:5]):  # 상위 5개 종목만 처리
                    stock_name = stock['hts_kor_isnm']
                    stock_code = stock['stck_shrn_iscd']
                    volume_power = float(stock['tday_rltv'])

                    message += (
                        f"{idx+1}. 종목명: {stock_name}\n"
                        f"종목코드: {stock_code}\n"
                        f"체결강도: {volume_power:.2f}\n"
                    )

                # 결과를 디스코드에 전송
                print(message)
                self.send_discord_webhook(message, "trading")


                # 체결강도 1위 종목 선택
                top_stock = rankings[0]
                stock_name = top_stock['hts_kor_isnm']
                stock_code = top_stock['stck_shrn_iscd']
                volume_power = float(top_stock['tday_rltv'])
                


                # 1주 매수 실행 (시장가)
                buy_qty = 1
                buy_price = None  # 시장가
                order_result = self.place_order(stock_code, buy_qty, buy_price, order_type="buy")

                if order_result:
                    self.send_discord_webhook(
                        f"✅ 매수 완료: 종목명: {stock_name}, 수량: {buy_qty}주, 가격: 시장가\n", "trading" 
                    )
                    
                    print(f"✅ 매수 완료: {stock_name} - 수량: {buy_qty}주")

                    # 매수 가격 저장
                    stock = self.kis.stock(stock_code)
                    quote = stock.quote()
                    purchase_price = float(quote.close)  # 매수가격 설정

                    # 5% 상승 시 매도 조건 확인
                    sell_price = round(purchase_price*1.05, 2)  # 매수가 대비 5% 상승
                    self.monitor_and_sell(stock_code, stock_name, buy_qty, purchase_price, sell_price)
                else:
                    self.send_discord_webhook(f"❌ 매수 실패: 종목명: {stock_name}", "trading")
            else:
                error_message = f"❌ 체결강도 조회 실패: {response.status_code}, {response.text}"
                print(error_message)
                self.send_discord_webhook(error_message, "trading")

        except Exception as e:
            error_message = f"❌ 체결강도 조회 및 자동매수 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")


    async def monitor_and_sell(self, stock_code, stock_name, qty, purchase_price, sell_price, timeout=1800, interval = 60):
        """
        매수가 대비 5% 상승 시 자동 매도
        """
        try:
            stock = self.kis.stock(stock_code)
            start_time = time.time()

            while True:
                # 현재 시간과 시작 시간 비교
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout:
                    self.send_discord_webhook(
                        f"⏳ 매도 조건 시간이 초과되었습니다. 목표가: {sell_price}원", "trading"
                    )
                    print("⏳ 매도 조건 시간이 초과되었습니다.")
                    break

                # 현재가 조회
                quote = stock.quote()
                current_price = float(quote.close)

                print(f"[{elapsed_time:.0f}초 경과] 현재가: {current_price}, 목표 매도가: {sell_price}")

                # 목표가 도달 시 매도 실행
                if current_price >= sell_price:
                    order_result = self.place_order(stock_code, qty, sell_price, order_type="sell")

                    if order_result:
                        profit = current_price - purchase_price
                        profit_rate = (profit / purchase_price) * 100

                        message = (
                            f"✅ 자동 매도 완료!\n"
                            f"종목명: {stock_name}\n"
                            f"매수가: {purchase_price}원\n"
                            f"매도가: {current_price}원\n"
                            f"수익률: {profit_rate:.2f}%"
                        )
                        print(message)
                        self.send_discord_webhook(message, "trading")
                    else:
                        self.send_discord_webhook(
                            f"❌ 매도 실패: 종목명: {stock_name}", "trading"
                        )
                    break

                # 일정 시간 대기
                await asyncio.sleep(interval)

        except Exception as e:
            error_message = f"❌ 매도 조건 확인 중 오류 발생: {e}"
            print(error_message)
            self.send_discord_webhook(error_message, "trading")

    # 배당률 상위 조회 함수
    def get_top_dividend_stocks(self):
        # 실전 투자 환경 URL
        url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/dividend-rate"

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            'Authorization': str(self.kis.token),
            "appkey": self.appkey,
            "appsecret": self.secretkey,
            "tr_id": "HHKDB13470100",  # 실전 거래용 TR_ID
            "custtype": "P"
        }

        # 요청 쿼리 파라미터 설정
        params = {
            "CTS_AREA": "",
            "GB1": "2",  # 전체 조회
            "UPJONG": "2001",  # 업종 코드 (예시)
            "GB2": "6",  # 배당률 순서
            'GB3': '2',
            "F_DT": "20240101",  # 시작 날짜
            "T_DT": "20241201",  # 종료 날짜
            "GB4": "1"  # 기타 설정
        }

        # API 요청 보내기
        response = requests.get(url, headers=headers, params=params)

        # 응답 처리
        if response.status_code == 200:
            result = response.json()
            # 상위 5개 항목 추출
            top_stocks = result.get("output", [])[:5]

            # 결과 정리
            message = "📊 KOSPI200 배당률 상위 5:\n"
            for idx, stock in enumerate(top_stocks):
                dividend_rate = float(stock['divi_rate']) / 100
                message +=(
                    f"{idx+1}. 종목명: {stock['isin_name']}\n"
                    f"날짜: {stock['record_date']}\n"
                    f"현금/주식배당금: {stock["per_sto_divi_amt"]}\n"
                    f"배당률: {dividend_rate:.2f}% \n"
                )
        
            # 디스코드 웹훅 전송
            self.send_discord_webhook(message, "trading")
                    
        else:
            error_message = f"❌ 배당률 조회 실패: {response.status_code}, {response.text}"
            self.send_discord_webhook(error_message, "trading")
            print(error_message)

    # 봉 데이터를 가져오는 함수
    def _get_ohlc(self, symbol, start_date, end_date):
        symbol_stock: KisStock = self.kis.stock(symbol)  # SK하이닉스 (코스피)
        chart: KisChart = symbol_stock.chart(
            start=start_date,
            end=end_date,
        ) # 2023년 1월 1일부터 2023년 12월 31일까지의 일봉입니다.
        klines = chart.bars

        # 첫 번째 데이터를 제외하고, 각 항목의 open 값을 전날 close 값으로 변경
        for i in range(1, len(klines)):
            klines[i].open = klines[i - 1].close  # 전날의 close로 open 값을 변경
            
        return klines


    # 볼린저밴드 계산
    def _cal_bollinger_band(self, previous_closes, close_price):
        if len(previous_closes) >= 20:
            sma = np.mean(previous_closes[-20:])
            std = np.std(previous_closes[-20:])
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
        else:
            sma = np.mean(previous_closes) if previous_closes else close_price
            std = np.std(previous_closes) if len(previous_closes) > 1 else 0
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)

        band = {}
        band['upper'] = upper_band
        band['middle'] = sma
        band['lower'] = lower_band

        return band


    # 윗꼬리와 아랫꼬리를 체크하는 함수
    def _check_wick(self, candle, previous_closes, lower_band, sma, upper_band):
        open_price = float(candle.open)
        high_price = float(candle.high)
        low_price = float(candle.low)
        close_price = float(candle.close)

        # 윗꼬리 아랫꼬리 비율
        wick_ratio = 1.3

        # 볼린저 밴드 및 시간 정보
        middle_band = sma
        print(f"시간: {candle.time}, open_price: {open_price:.0f} KRW, low_price: {low_price:.0f} KRW, high_price: {high_price:.0f} KRW, close_price: {close_price:.0f} KRW, 볼린저 밴드 정보: 상단: {upper_band:.0f} KRW, 중단: {middle_band:.0f} KRW, 하단: {lower_band:.0f} KRW")

        # 아랫꼬리 여부 (고가와 저가의 차이가 크고 양봉일 때, 하락 중에만, 볼린저 밴드 하단 근처에서)
        lower_wick = min(open_price, close_price) - low_price # 아랫꼬리
        upper_wick = high_price - max(open_price, close_price) # 윗꼬리

        body = abs(open_price - close_price)
        # body 에 2배한게 꼬리보다 클 때 
        body_ratio = 2

        average_previous_close = sum(previous_closes) / len(previous_closes) if previous_closes else close_price
        
        is_downtrend = close_price < average_previous_close
        is_near_lower_band = low_price <= (lower_band + (lower_band * 0.01)) and open_price < middle_band # 볼린저 밴드 하단 근처 및 하단 이하에서만 인식
        # 아랫꼬리가 윗꼬리보다 클때, 양봉일 때, 하락 중에만, 볼린저 밴드 하단 근처에서, body * n 이 꼬리보다 클 때  
        # has_lower_wick = lower_wick > body * 0.3 and close_price > open_price and is_downtrend and is_near_lower_band
        has_lower_wick = abs(lower_wick) > abs(upper_wick) * wick_ratio and close_price > open_price and is_downtrend and is_near_lower_band and body * body_ratio > abs(upper_wick)

        print(f'윗꼬리 = {upper_wick}, 아랫꼬리 = {lower_wick}, body = {body}')

        if not has_lower_wick:
            reason = []
            if abs(lower_wick) <= abs(upper_wick):
                reason.append("아랫꼬리가 윗꼬리보다 짦음")
            if close_price <= open_price:
                reason.append("종가가 시가보다 높지 않음")
            if not is_downtrend:
                reason.append("하락 추세가 아님")
            if not is_near_lower_band:
                reason.append("볼린저 밴드 하단 근처가 아님")
            if body * body_ratio <= abs(upper_wick):
                reason.append(f"윗꼬리가 바디 * {body_ratio} 보다 김")
            print(f"아랫꼬리 감지 실패: 시간: {candle.time}, 사유: {', '.join(reason)}")

        if has_lower_wick:
            print(f"아랫꼬리 감지: 시간: {candle.time}, close_price: {close_price:.7f} KRW, 볼린저 밴드 상단: {upper_band:.7f} KRW, 중단: {middle_band:.7f} KRW, 하단: {lower_band:.7f} KRW")

        # 윗꼬리 여부 (고가와 저가의 차이가 크고 음봉일 때, 상승 중에만, 볼린저 밴드 상단 근처에서)
        is_uptrend = close_price > average_previous_close
        is_near_upper_band = high_price >= (upper_band - (upper_band * 0.01)) and open_price > middle_band # 볼린저 밴드 상단 근처 및 상단 이상에서만 인식
        # 윗꼬리가 아랫꼬리보다 클 때, 음봉일 때, 상승 중에만, 볼린저 밴드 상단 근처에서, body * n 이 꼬리보다 클 때  
        has_upper_wick = abs(upper_wick) > abs(lower_wick) * wick_ratio and close_price < open_price and is_uptrend and is_near_upper_band and body * body_ratio > abs(lower_wick)

        if not has_upper_wick:
            reason = []
            if abs(upper_wick) <= abs(lower_wick):
                reason.append("윗꼬리가 아랫꼬리보다 짦음")
            if close_price >= open_price:
                reason.append("종가가 시가보다 낮지 않음")
            if not is_uptrend:
                reason.append("상승 추세가 아님")
            if not is_near_upper_band:
                reason.append("볼린저 밴드 상단 근처가 아님")
            if body * body_ratio <= abs(lower_wick):
                reason.append(f"아랫꼬리가 바디 * {body_ratio} 보다 김")
            print(f"윗꼬리 감지 실패: 시간: {candle.time}, 사유: {', '.join(reason)}")

        if has_upper_wick:
            print(f"윗꼬리 감지: 시간: {candle.time}, close_price: {close_price:.7f} KRW, 볼린저 밴드 상단: {upper_band:.7f} KRW, 중단: {middle_band:.7f} KRW, 하단: {lower_band:.7f} KRW")

        return has_upper_wick, has_lower_wick


    def _draw_chart(self, symbol, ohlc, timestamps, buy_signals, sell_signals):

        # 캔들 차트 데이터프레임 생성
        df = pd.DataFrame(ohlc, columns=['Open', 'High', 'Low', 'Close'], index=pd.DatetimeIndex(timestamps))

        # 볼린저 밴드 계산
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['Upper'] = df['SMA'] + (df['Close'].rolling(window=20).std() * 2)
        df['Lower'] = df['SMA'] - (df['Close'].rolling(window=20).std() * 2)

        # 매수 및 매도 시그널 표시를 위한 추가 데이터 (x와 y의 길이 맞추기 위해 NaN 사용)
        df['Buy_Signal'] = np.nan
        df['Sell_Signal'] = np.nan

        for signal in buy_signals:
            df.at[signal[0], 'Buy_Signal'] = signal[1]
        for signal in sell_signals:
            df.at[signal[0], 'Sell_Signal'] = signal[1]

        # 그래프 그리기
        add_plot = [
            mpf.make_addplot(df['Upper'], color='blue', linestyle='-', label='Upper Band'),
            mpf.make_addplot(df['Lower'], color='blue', linestyle='-', label='Lower Band'),
            mpf.make_addplot(df['SMA'], color='orange', label='SMA'),
            mpf.make_addplot(df['Buy_Signal'], type='scatter', markersize=20, marker='^', color='green', label='BUY'),
            mpf.make_addplot(df['Sell_Signal'], type='scatter', markersize=20, marker='v', color='red', label='SELL')
        ]

        simulation_plot = mpf.plot(df, type='candle', style='charles', title=f'{symbol}', addplot=add_plot, ylabel='Price (KRW)', figsize=(20, 9), returnfig=True)

        return simulation_plot


    
    def simulate_trading(self, symbol, start_date, end_date, target_trade_value_krw):
        ohlc_data = self._get_ohlc(symbol, start_date, end_date)
        realized_pnl = 0
        position = 0  # 현재 포지션 수량
        trade_stack = []  # 매수 가격을 저장하는 스택
        previous_closes = []  # 이전 종가들을 저장
        total_invested = 0  # 매수에 사용된 총 금액
        current_cash = target_trade_value_krw  # 초기 잔고
    
    # 그래프 그리기 위한 데이터
        timestamps = []
        ohlc = []
        buy_signals = []
        sell_signals = []

        for i in range(len(ohlc_data) - 1):
            candle = ohlc_data[i]
            next_candle = ohlc_data[i + 1]

            open_price = float(candle.open)
            high_price = float(candle.high)
            low_price = float(candle.low)
            close_price = float(candle.close)
            timestamp = candle.time
            next_open_price = float(next_candle.open)
            next_timestamp = next_candle.time

            timestamps.append(timestamp)
            ohlc.append([open_price, high_price, low_price, close_price])

            previous_closes.append(close_price)

        # 볼린저 밴드 계산
            bollinger_band = self._cal_bollinger_band(previous_closes, close_price)

            upper_wick, lower_wick = self._check_wick(
                candle, previous_closes, bollinger_band['lower'], bollinger_band['middle'], bollinger_band['upper']
        )

            if lower_wick and current_cash >= open_price:  # 매수 조건 및 잔고 확인
                position += 1
                trade_stack.append(open_price)
                buy_signals.append((timestamp, open_price))

                current_cash -= open_price  # 잔고 감소
                total_invested += open_price  # 투자 금액 증가

            # 매수 알림 전송
                message = (
                    f"📈 매수 이벤트 발생!\n"
                    f"종목: {symbol}\n"
                    f"매수가: {open_price:.2f} KRW\n"
                    f"매수 시점: {timestamp}\n"
                    f"총 포지션: {position}\n"
                    f"현재 잔고: {current_cash:.2f} KRW"
            )
                self.send_discord_webhook(message, "trading")

            elif upper_wick and position > 0:  # 매도 조건
                entry_price = trade_stack.pop()  # 매수 가격 가져오기
                exit_price = next_open_price  # 매도가
                pnl = exit_price - entry_price  # 개별 거래 손익
                realized_pnl += pnl  # 총 실현 손익에 추가
                sell_signals.append((next_timestamp, exit_price))
                position -= 1

                current_cash += exit_price  # 매도로 인한 잔고 증가

            # 매도 알림 전송
                message = (
                    f"📉 매도 이벤트 발생!\n"
                    f"종목: {symbol}\n"
                    f"매도가: {exit_price:.2f} KRW\n"
                    f"매도 시점: {next_timestamp}\n"
                    f"거래 손익: {pnl:.2f} KRW\n"
                    f"총 실현 손익: {realized_pnl:.2f} KRW\n"
                    f"현재 잔고: {current_cash:.2f} KRW\n"
                    f"남은 포지션: {position}"
                )
                self.send_discord_webhook(message, "trading")

    # 마지막 종가를 기준으로 평가
        final_close = float(ohlc_data[-1].close)
        if position > 0:
            current_pnl = (final_close - sum(trade_stack) / len(trade_stack)) * position  # 현재 평가 손익
        else:
            current_pnl = 0

    # 결과 출력
        total_assets = current_cash + (final_close * position)  # 총 자산 = 현금 + 보유 자산 평가액
        message = (
            f"📊 시뮬레이션 완료!\n"
            f"종목: {symbol}\n"
            f"기간: {start_date} ~ {end_date}\n"
            f"총 실현 손익: {realized_pnl:.2f} KRW\n"
            f"현재 평가 손익: {current_pnl:.2f} KRW\n"
            f"최종 잔고: {current_cash:.2f} KRW\n"
            f"총 자산 가치: {total_assets:.2f} KRW"
        )
        self.send_discord_webhook(message, "trading")

        # 캔들 차트 데이터프레임 생성
        simulation_plot = self._draw_chart(symbol, ohlc, timestamps, buy_signals, sell_signals)

        return simulation_plot, realized_pnl, current_cash

