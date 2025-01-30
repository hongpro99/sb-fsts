import sys
import os
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from st_aggrid import AgGrid
import pandas as pd
from datetime import datetime, date, timedelta
import pytz

from streamlit_lightweight_charts import renderLightweightCharts
import json
import numpy as np

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db, get_db_session


def draw_lightweight_chart(data_df):

    # 차트 color
    COLOR_BULL = 'rgba(38,166,154,0.9)' # #26a69a
    COLOR_BEAR = 'rgba(239,83,80,0.9)'  # #ef5350

    # Some data wrangling to match required format
    data_df = data_df.reset_index()
    data_df.columns = [col.lower() for col in data_df.columns]

    buy_signal_df = data_df[data_df['buy_signal'].notna()]
    sell_signal_df = data_df[data_df['sell_signal'].notna()]

    # export to JSON format
    temp_df = data_df
    candles = json.loads(temp_df.to_json(orient = "records"))

    temp_df = data_df
    temp_df = temp_df.dropna(subset=['upper'])
    bollinger_band_upper = json.loads(temp_df.rename(columns={"upper": "value",}).to_json(orient = "records"))

    temp_df = data_df
    temp_df = temp_df.dropna(subset=['middle'])
    bollinger_band_middle = json.loads(temp_df.rename(columns={"middle": "value",}).to_json(orient = "records"))

    temp_df = data_df
    temp_df = temp_df.dropna(subset=['lower'])
    bollinger_band_lower = json.loads(temp_df.rename(columns={"lower": "value",}).to_json(orient = "records"))

    temp_df = data_df
    temp_df['color'] = np.where(temp_df['open'] > temp_df['close'], COLOR_BEAR, COLOR_BULL)  # bull or bear
    volume = json.loads(temp_df.rename(columns={"volume": "value",}).to_json(orient = "records"))

    # 매매 마커 추가
    markers = []
    for _, row in buy_signal_df.iterrows():
        marker = {
            "time": row['time'],  # 'date' 열을 'time' 키로 변환
            "position": "belowBar",  # 'position_type' 열을 'position' 키로 변환
            "color": "rgba(0, 0, 0, 1)",  # 'marker_color' 열을 'color' 키로 변환
            "shape": "arrowUp",  # 'marker_shape' 열을 'shape' 키로 변환
            "text": "B",  # 'type' 열을 'text' 키로 변환
            "size": 1  # 'size' 열을 'size' 키로 변환
        }
        markers.append(marker)

    for _, row in sell_signal_df.iterrows():
        marker = {
            "time": row['time'],  # 'date' 열을 'time' 키로 변환
            "position": "aboveBar",  # 'position_type' 열을 'position' 키로 변환
            "color": "rgba(0, 0, 0, 1)",  # 'marker_color' 열을 'color' 키로 변환
            "shape": "arrowDown",  # 'marker_shape' 열을 'shape' 키로 변환
            "text": "S",  # 'type' 열을 'text' 키로 변환
            "size": 1  # 'size' 열을 'size' 키로 변환
        }
        markers.append(marker)

    markers.sort(key=lambda marker: marker['time'])

    chartMultipaneOptions = [
        {
            # "width": 200, # 자동 너비 설정
            "height": 400,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": 'white'
                },
                "textColor": "black"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                    },
                "horzLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                }
            },
            "crosshair": {
                "mode": 0
            },
            "priceScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)"
            },
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,             # 왼쪽 가장자리 고정 여부
                "fixRightEdge": True,
                "visible": True
            },
        },
        {
            # "width": 1000,
            "height": 150,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": 'white'
                },
                "textColor": "black"
            },
            "grid": {
                "vertLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                    },
                "horzLines": {
                    "color": "rgba(197, 203, 206, 0.5)"
                }
            },
            "crosshair": {
                "mode": 0
            },
            "priceScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)"
            },
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,             # 왼쪽 가장자리 고정 여부
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(171, 71, 188, 0.7)',
                "text": 'Volume',
            }
        }
    ]

    seriesCandlestickChart = [
        {
            "type": 'Line',
            "data": bollinger_band_upper,  # 중앙선 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Line',
            "data": bollinger_band_middle,  # 상단 밴드 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Line',
            "data": bollinger_band_lower,  # 하단 밴드 데이터
            "options": {
                "color": 'rgba(0, 0, 0, 1)',  # 노란색
                "lineWidth": 1,
                "priceScaleId": "right",
                "lastValueVisible": False, # 가격 레이블 숨기기
                "priceLineVisible": False, # 가격 라인 숨기기
            },
        },
        {
            "type": 'Candlestick',
            "data": candles,
            "options": {
                "upColor": COLOR_BULL,
                "downColor": COLOR_BEAR,
                "borderVisible": False,
                "wickUpColor": COLOR_BULL,
                "wickDownColor": COLOR_BEAR
            },
            "markers": markers
        },
    ]

    seriesVolumeChart = [
        {
            "type": 'Histogram',
            "data": volume,
            "options": {
                "priceFormat": {
                    "type": 'volume',
                },
                "priceScaleId": "" # set as an overlay setting,
            },
            "priceScale": {
                "scaleMargins": {
                    "top": 0.1,
                    "bottom": 0,
                },
                "alignLabels": False
            },
        }
    ]

    renderLightweightCharts([
        {
            "chart": chartMultipaneOptions[0],
            "series": seriesCandlestickChart
        },
        {
            "chart": chartMultipaneOptions[1],
            "series": seriesVolumeChart
        },
        
    ], 'multipane')

def rename_tradingLogic(trade_history):
    for entry in trade_history:
        if entry.get('trading_logic') == 'rsi_trading':  # history에 있는 로직 이름 변경
            entry['trading_logic'] = 'rsi 확인'
        elif entry.get('trading_logic') == 'check_wick':
            entry['trading_logic'] = '꼬리 확인'
        elif entry.get('trading_logic') == 'penetrating':
            entry['trading_logic'] = '관통형'
        elif entry.get('trading_logic') == 'morning_star':
            entry['trading_logic'] = '샛별형'
        elif entry.get('trading_logic') == 'doji_star':
            entry['trading_logic'] = '상승도지스타'
        elif entry.get('trading_logic') == 'harami':
            entry['trading_logic'] = '상승잉태형'
        elif entry.get('trading_logic') == 'engulfing':
            entry['trading_logic'] = '상승장악형'
        elif entry.get('trading_logic') == 'engulfing2':
            entry['trading_logic'] = '상승장악형2'
        elif entry.get('trading_logic') == 'counterattack':
            entry['trading_logic'] = '상승반격형'
        elif entry.get('trading_logic') == 'down_engulfing':
            entry['trading_logic'] = '하락장악형'
        elif entry.get('trading_logic') == 'down_engulfing2':
            entry['trading_logic'] = '하락장악형2'    
        elif entry.get('trading_logic') == 'down_counterattack':
            entry['trading_logic'] = '하락반격형'
        elif entry.get('trading_logic') == 'down_harami':
            entry['trading_logic'] = '하락잉태형'
        elif entry.get('trading_logic') == 'down_doji_star':
            entry['trading_logic'] = '하락도지스타'
        elif entry.get('trading_logic') == 'evening_star':
            entry['trading_logic'] = '석별형'
        elif entry.get('trading_logic') == 'dark_cloud':
            entry['trading_logic'] = '흑운형'
        elif entry.get('trading_logic') == 'mfi_trading':
            entry['trading_logic'] = 'mfi 확인'
        
def setup_sidebar(sql_executer):
    """
    공통적으로 사용할 사이드바 UI를 설정하는 함수
    """
    
    st.sidebar.header("Simulation Settings")

    user_name = '홍석문'

    # AutoTradingBot 및 SQLExecutor 객체 생성
    sql_executor = SQLExecutor()
    auto_trading_stock = AutoTradingBot(user_name=user_name, virtual=True)
    current_date_kst = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    # 사용자 입력
    # user_name = st.sidebar.text_input("User Name", value="홍석문")
    start_date = st.sidebar.date_input("Start Date", value=date(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=current_date_kst)
    target_trade_value_krw = st.sidebar.number_input("Target Trade Value (KRW)", value=1000000, step=100000)

    query = """
            SELECT 종목코드, 종목이름 FROM fsts.kospi200 ORDER BY 종목이름 COLLATE "ko_KR";
        """

    params = {}

    with get_db_session() as db:
        result = sql_executor.execute_select(db, query, params)

    # Dropdown 메뉴를 통해 데이터 선택
    symbol_options = {
        # "삼성전자": "352820",
        # "대한항공": "003490",
    }

    for stock in result:
        key = stock['종목이름']  # 'a' 값을 키로
        value = stock['종목코드']  # 'b' 값을 값으로
        symbol_options[key] = value  # 딕셔너리에 추가
            
    # interval 설정
    interval_options = {
        "DAY": "day",
        "WEEK": "week",
        "MONTH": "month",
    }

    # 매수/매도 로직 설정
    # JSON 파일 읽기
    file_path = "./dashboard_web/trading_logic.json"
    with open(file_path, "r", encoding="utf-8") as file:
        trading_logic = json.load(file)

    # 사용 예시
    available_buy_logic = trading_logic["available_buy_logic"]
    available_sell_logic = trading_logic["available_sell_logic"]
    
    selected_stock = st.sidebar.selectbox("Select a Stock", list(symbol_options.keys()))
    selected_interval = st.sidebar.selectbox("Select Chart Interval", list(interval_options.keys()))
    selected_buy_logic = st.sidebar.multiselect("Select Buy Logic(s):", list(available_buy_logic.keys()))
    selected_sell_logic = st.sidebar.multiselect("Select Sell Logic(s):", list(available_sell_logic.keys()))
    
    # 3% 매수 조건 체크박스 (체크하면 'Y', 체크 해제하면 'N')
    buy_condition_enabled = st.sidebar.checkbox("매수 제약 조건 활성화")  # True / False 반환
    buy_condition_yn = "Y" if buy_condition_enabled else "N"
    
    # 사용자가 직접 매수 퍼센트 (%) 입력 (기본값 3%)
    if buy_condition_yn == 'Y':
        buy_percentage = st.sidebar.number_input("퍼센트 (%) 입력", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
    else:
        buy_percentage = None
        
    symbol = symbol_options[selected_stock]
    interval = interval_options[selected_interval]
    
    selected_buyTrading_logic = [available_buy_logic[logic] for logic in selected_buy_logic] if selected_buy_logic else []
    selected_sellTrading_logic = [available_sell_logic[logic] for logic in selected_sell_logic] if selected_sell_logic else []


    # ✅ 설정 값을 딕셔너리 형태로 반환
    return {
        "user_name": user_name,
        "start_date": start_date,
        "end_date": end_date,
        "target_trade_value_krw": target_trade_value_krw,
        "kospi200": symbol_options,
        "symbol": symbol,
        "interval": interval,
        "buy_trading_logic": selected_buyTrading_logic,
        "sell_trading_logic": selected_sellTrading_logic,
        "buy_condition_yn": buy_condition_yn,
        "buy_percentage": buy_percentage,
    }
            
def main():
    
    # for DB
    sql_executor = SQLExecutor()

    st.set_page_config(layout="wide")
    
    # ✅ 공통 사이드바 설정 함수 실행 후 값 가져오기
    sidebar_settings = setup_sidebar(sql_executor)
    
    # 탭 생성
    tabs = st.tabs(["🏠 거래 내역", "📈 시뮬레이션 그래프", "📊 Data Analysis Page", "📊 KOSPI200 Simulation"])

    # 각 탭의 내용 구성
    with tabs[0]:
        st.header("🏠 트레이딩 봇 거래 내역")
        
        data = {
            "Trading Bot Name": [],
            "Trading Logic": [],
            "Trade Date": [],
            "Symbol Name": [],
            "Symbol": [],
            "Position": [],
            "Price": [],
            "Quantity": []
        }

        query = """
            select
                trading_bot_name,
                trading_logic,
                trade_date,
                symbol_name,
                symbol,
                position,
                price,
                quantity
            from fsts.trading_history
            order by trading_logic, trade_date, symbol_name;
        """

        params = {}

        with get_db_session() as db:
            result = sql_executor.execute_select(db, query, params)

        for row in result:
            data["Trading Bot Name"].append(row['trading_bot_name'])
            data["Trading Logic"].append(row['trading_logic'])
            data["Trade Date"].append(row['trade_date'])
            data["Symbol Name"].append(row['symbol_name'])
            data["Symbol"].append(row['symbol'])
            data["Position"].append(row['position'])
            data["Price"].append(row['price'])
            data["Quantity"].append(row['quantity'])

        # 데이터 생성
        # data = {
        #     "Name": ["Alice", "Bob", "Charlie"],
        #     "Age": [25, 30, 35],
        #     "City": ["New York", "San Francisco", "Los Angeles"]
        # }
        df = pd.DataFrame(data)
        
        # AgGrid로 테이블 표시
        grid_response = AgGrid(
            df,
            editable=True,  # 셀 편집 가능
            sortable=True,  # 정렬 가능
            filter=True,    # 필터링 가능
            resizable=True, # 크기 조절 가능
            theme='streamlit',   # 테마 변경 가능 ('light', 'dark', 'blue', 등)
            fit_columns_on_grid_load=True  # 열 너비 자동 조정
        )

    with tabs[1]:
        st.header("📈 종목 시뮬레이션")
        
        if st.sidebar.button("개별 종목 시뮬레이션 실행", key = 'simulation_button'):
            auto_trading_stock = AutoTradingBot(user_name=sidebar_settings["user_name"], virtual=True)

            with st.container():
                st.write(f"📊 {sidebar_settings['symbol']} 시뮬레이션 실행 중...")
                
                #시뮬레이션 실행
                data_df, trading_history = auto_trading_stock.simulate_trading(
                    symbol=sidebar_settings["symbol"],
                    start_date=sidebar_settings["start_date"],
                    end_date=sidebar_settings["end_date"],
                    target_trade_value_krw=sidebar_settings["target_trade_value_krw"],
                    buy_trading_logic=sidebar_settings["buy_trading_logic"],
                    sell_trading_logic=sidebar_settings["sell_trading_logic"],
                    interval=sidebar_settings["interval"],
                    buy_percentage=sidebar_settings["buy_percentage"]
                )
        
                # tradingview chart draw
                draw_lightweight_chart(data_df)

                # # DB에서 trading_history 결과 조회
                # query = """
                #     SELECT *
                #     FROM fsts.simulation_history
                #     WHERE symbol = :symbol
                #     ORDER BY created_at DESC
                #     LIMIT 1
                # """
                # params = {"symbol": symbol}
                
                # with get_db_session() as db:
                #     trade_history = sql_executor.execute_select(db, query, params)
                
                if not trading_history:
                    st.write("No trading history available.")
                    return

                # 기본 거래 내역을 DataFrame으로 변환
                history_df = pd.DataFrame([trading_history])

                # 실현 수익률/미실현 수익률 컬럼이 존재하면 % 포맷 적용
                for column in ["realized_roi", "unrealized_roi"]:
                    if column in history_df.columns:
                        history_df[column] = history_df[column].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
                        
                # 🎯 trading_history에 symbol 변수 추가
                stock_name = next((company for company, code in st.session_state.items() if code == sidebar_settings["symbol"]), "해당 종목 없음")
                history_df["symbol"] = stock_name
                # 원하는 컬럼 순서 지정
                reorder_columns = [
                    "symbol", "average_price",
                    "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi", "total_cost",
                    "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity", "history", "created_at"
                ]
                
                # 재정렬된 컬럼만 선택
                history_df = history_df[[col for col in reorder_columns if col in history_df.columns]]

                # 데이터의 행과 열 전환 (Transpose) 후 테이블 표시
                history_df_transposed = history_df.transpose().reset_index()
                history_df_transposed.columns = ["Field", "Value"]

                # Streamlit에서 표시
                st.subheader("📊 Trading History Summary")
                st.dataframe(history_df_transposed, use_container_width=True)
                
                # 상세 거래 내역 처리
                if "history" in trading_history and isinstance(trading_history["history"], list) and trading_history["history"]:
                    # 트레이딩 로직명을 변환 (필요시)
                    rename_tradingLogic(trading_history["history"])  

                    # 상세 거래 내역을 DataFrame으로 변환
                    trade_history_df = pd.DataFrame(trading_history["history"])

                    # Streamlit에서 표시
                    st.subheader("📋 Detailed Trade History")
                    st.dataframe(trade_history_df, use_container_width=True)
                else:
                    st.write("No detailed trade history found.")


    with tabs[2]:
        st.header("📊 데이터 분석 페이지")
        
        # 데이터
        data = sns.load_dataset('penguins')

        # 히스토그램
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data, x='flipper_length_mm', hue='species', multiple='stack', ax=ax)
        ax.set_title("Seaborn 히스토그램")
        st.pyplot(fig)
        
        #새로 추가된 코스피 200 시뮬레이션 탭
    with tabs[3]:
        st.header("📊 코스피 200 종목 시뮬레이션 결과")

        # ✅ 시뮬레이션 실행 버튼
        if st.sidebar.button("코스피 200 시뮬레이션 실행"):
            st.write("🔄 코스피 200 전체 종목에 대해 시뮬레이션을 실행합니다.")

            # ✅ 진행률 바 추가
            progress_bar = st.progress(0)
            progress_text = st.empty()  # 진행 상태 표시

            all_trading_results = []
            failed_stocks = []
            total_stocks = len(sidebar_settings["kospi200"])
            
            for i, (stock_name, symbol) in enumerate(sidebar_settings["kospi200"].items()):
                try:
                    with st.spinner(f"📊 {stock_name} ({i+1}/{total_stocks}) 시뮬레이션 실행 중..."):
                        auto_trading_stock = AutoTradingBot(user_name=sidebar_settings["user_name"], virtual=True)

                        _, trading_history = auto_trading_stock.simulate_trading(
                            symbol=symbol,
                            start_date=sidebar_settings["start_date"],
                            end_date=sidebar_settings["end_date"],
                            target_trade_value_krw=sidebar_settings["target_trade_value_krw"],
                            buy_trading_logic=sidebar_settings["buy_trading_logic"],
                            sell_trading_logic=sidebar_settings["sell_trading_logic"],
                            interval="day",
                            buy_percentage=sidebar_settings["buy_percentage"]
                        )

                        if trading_history:
                            trading_history["symbol"] = stock_name
                            all_trading_results.append(trading_history)

                    # ✅ 진행률 업데이트
                    progress = (i + 1) / total_stocks
                    progress_bar.progress(progress)
                    progress_text.text(f"{int(progress * 100)}% 완료 ({i+1}/{total_stocks})")

                except Exception as e:
                    st.write(f"⚠️ {stock_name} 시뮬레이션 실패: {str(e)}")
                    failed_stocks.append(stock_name)

            st.success("✅ 코스피 200 시뮬레이션 완료!")
            
            # ✅ 시뮬레이션 결과를 `st.session_state`에 저장!
            st.session_state["kospi200_trading_results"] = all_trading_results

            # ✅ 시뮬레이션 결과를 `st.session_state`에서 가져와 사용
            if "kospi200_trading_results" in st.session_state and st.session_state["kospi200_trading_results"]:
                df_results = pd.DataFrame(st.session_state["kospi200_trading_results"])

                # 수익률 컬럼이 존재하면 % 형식 변환
                for col in ["realized_roi", "unrealized_roi"]:
                    if col in df_results.columns:
                        df_results[col] = df_results[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

                # ✅ 평균 수익률 계산
                avg_realized_pnl = df_results["realized_pnl"].mean()
                avg_unrealized_pnl = df_results["unrealized_pnl"].mean()

                # ✅ 평균 수익률 요약 표시
                st.subheader("📊 전체 종목 평균 수익률")
                st.write(f"**💰 평균 실현 손익:** {avg_realized_pnl:,.2f} KRW")
                st.write(f"**📈 평균 미실현 손익:** {avg_unrealized_pnl:,.2f} KRW")

                # ✅ 개별 종목별 결과 표시
                st.subheader("📋 종목별 시뮬레이션 결과")
                AgGrid(
                    df_results,
                    editable=True,
                    sortable=True,
                    filter=True,
                    resizable=True,
                    theme='streamlit',
                    fit_columns_on_grid_load=True
                )

                # ✅ 실패한 종목이 있다면 표시
                if failed_stocks:
                    st.warning(f"⚠️ 시뮬레이션 실패 종목 ({len(failed_stocks)}개): {', '.join(failed_stocks)}")

            else:
                st.write("⚠️ 시뮬레이션 결과가 없습니다.")
    

if __name__ == "__main__":
    main()