import requests

class TradingLogic:
    def __init__(self, auto_trading):
        """
        TradingLogic 초기화
        Args:
            auto_trading (AutoTradingStock): AutoTradingStock 객체
        """
        self.auto_trading = auto_trading

    # 체결강도 로직에 따라 매매 대상인지 확인하고 거래 실행
    def get_volume_power_ranking_and_trade(self, input_market="2001"):
        """
        체결강도 순위를 조회하고 조건에 따라 매수/매도 실행
        Args:
            input_market (str): 조회할 시장 코드
        Returns:
            bool: 매수/매도 신호가 발생했는지 여부
        """
        
        try:
            # 기존 코드 유지
            kis = self.auto_trading.kis
            appkey = self.auto_trading.appkey
            secretkey = self.auto_trading.secretkey
            
            url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/ranking/volume-power"
            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": str(self.kis.token),
                "appkey": self.appkey,
                "appsecret": self.secretkey,
                "tr_id": "FHPST01680000",
                "custtype": "P"
            }
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

            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                rankings = result.get("output", [])

                if rankings:
                    # 상위 종목으로 매매 실행
                    top_stock = rankings[0]
                    stock_code = top_stock['stck_shrn_iscd']
                    stock_name = top_stock['hts_kor_isnm']
                    volume_power = float(top_stock['tday_rltv'])

                    # 매수 실행
                    buy_qty = 1
                    buy_price = None  # 시장가
                    order_result = self.place_order(stock_code, buy_qty, buy_price, order_type="buy")

                    if order_result:
                        print(f"✅ 매수 완료: 종목명 {stock_name}, 수량 {buy_qty}")
                        return True
                    else:
                        print(f"❌ 매수 실패: 종목명 {stock_name}")
                        return False
                else:
                    print("⚠️ 체결강도 데이터가 없습니다.")
                    return False
            else:
                print(f"❌ 체결강도 조회 실패: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            print(f"❌ 체결강도 로직 실행 중 오류 발생: {e}")
            return False
