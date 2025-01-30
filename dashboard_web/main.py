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
    candles = json.loads(data_df.to_json(orient = "records"))

    bollinger_band_upper = json.loads(data_df.dropna(subset=['upper']).rename(columns={"upper": "value",}).to_json(orient = "records"))
    bollinger_band_middle = json.loads(data_df.dropna(subset=['middle']).rename(columns={"middle": "value",}).to_json(orient = "records"))
    bollinger_band_lower = json.loads(data_df.dropna(subset=['lower']).rename(columns={"lower": "value",}).to_json(orient = "records"))
    rsi = json.loads(data_df.dropna(subset=['rsi']).rename(columns={"rsi": "value"}).to_json(orient="records"))
    macd = json.loads(data_df.dropna(subset=['macd']).rename(columns={"macd": "value"}).to_json(orient="records"))
    macd_signal = json.loads(data_df.dropna(subset=['macd_signal']).rename(columns={"macd_signal": "value"}).to_json(orient="records"))
    macd_histogram = json.loads(data_df.dropna(subset=['macd_histogram']).rename(columns={"macd_histogram": "value"}).to_json(orient="records"))
    stochastic_k = json.loads(data_df.dropna(subset=['stochastic_k']).rename(columns={"stochastic_k": "value"}).to_json(orient="records"))
    stochastic_d = json.loads(data_df.dropna(subset=['stochastic_d']).rename(columns={"stochastic_d": "value"}).to_json(orient="records"))

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
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'Volume',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'RSI',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'MACD',
            }
        },
        {
            "height": 150,  # RSI 차트 높이 설정
            "layout": {
                "background": {"type": "solid", "color": 'white'},
                "textColor": "black"
            },
            "grid": {
                "vertLines": {"color": "rgba(197, 203, 206, 0.5)"},
                "horzLines": {"color": "rgba(197, 203, 206, 0.5)"}
            },
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "rgba(197, 203, 206, 0.8)"},
            "timeScale": {
                "borderColor": "rgba(197, 203, 206, 0.8)",
                "barSpacing": 15,
                "fixLeftEdge": True,
                "fixRightEdge": True,
                "visible": True
            },
            "watermark": {
                "visible": True,
                "fontSize": 15,
                "horzAlign": 'left',
                "vertAlign": 'top',
                "color": 'rgba(255, 99, 132, 0.7)',
                "text": 'Stocastic',
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
                "priceScaleId": "", # set as an overlay setting,
                "priceLineVisible": False,
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

    # RSI 차트 시리즈 추가
    seriesRsiChart = [
        {
            "type": 'Line',
            "data": rsi,
            "options": {
                "color": 'rgba(0, 0, 0, 1)',
                "lineWidth": 1.5,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
        {
            "type": 'Line',
            "data": [{"time": row["time"], "value": 70} for row in rsi],  # 과매수 라인
            "options": {
                "color": 'rgba(200, 0, 0, 0.5)',  # 빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
        {
            "type": 'Line',
            "data": [{"time": row["time"], "value": 30} for row in rsi],  # 과매도 라인
            "options": {
                "color": 'rgba(200, 0, 0, 0.5)',  # 빨간색
                "lineWidth": 2,
                "priceScaleId": "right",
                "lastValueVisible": True,
                "priceLineVisible": False,
            },
        },
    ]

    seriesMACDChart = [
        {
            "type": 'Line',
            "data": macd,
            "options": {
                "color": 'rgba(0, 150, 255, 1)',
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line',
            "data": macd_signal, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Histogram',
            "data": macd_histogram,
            "options": {
                "priceLineVisible": False,
            }
        }
    ]

    seriesStochasticChart = [
        {
            "type": 'Line', 
            "data": stochastic_k, 
            "options": {
                "color": 'rgba(0, 150, 255, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
        {
            "type": 'Line', 
            "data": stochastic_d, 
            "options": {
                "color": 'rgba(255, 0, 0, 1)', 
                "lineWidth": 1.5,
                "priceLineVisible": False,
            }
        },
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
        {
            "chart": chartMultipaneOptions[2],
            "series": seriesRsiChart
        },
        {
            "chart": chartMultipaneOptions[3],
            "series": seriesMACDChart
        },
        {
            "chart": chartMultipaneOptions[4],
            "series": seriesStochasticChart
        },
    ], 'multipane')


def main():
    
    # for DB
    sql_executor = SQLExecutor()

    st.set_page_config(layout="wide")

    # 탭 생성
    tabs = st.tabs(["🏠 거래 내역", "📈 시뮬레이션 그래프", "📊 Data Analysis Page"])

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
        st.header("📈 시뮬레이션 페이지")
        # 사이드바 설정
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
        
        symbol = symbol_options[selected_stock]
        interval = interval_options[selected_interval]
        # 선택된 로직 처리
        if selected_buy_logic:
            selected_buyTrading_logic = [available_buy_logic[logic] for logic in selected_buy_logic if logic in available_buy_logic]
            # 선택된 로직 처리
        if selected_sell_logic:
            selected_sellTrading_logic = [available_sell_logic[logic] for logic in selected_sell_logic if logic in available_sell_logic]
        
        # 시뮬레이션 실행 버튼
        if st.sidebar.button("시뮬레이션 시작!", 'button'):
            
            with st.container():
                st.write(f"Running simulation for stock: {selected_stock}...")
                
                # 시뮬레이션 실행
                data_df, simulation_plot = auto_trading_stock.simulate_trading(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    target_trade_value_krw=target_trade_value_krw,
                    buy_trading_logic = selected_buyTrading_logic,
                    sell_trading_logic = selected_sellTrading_logic,
                    interval=interval
                )
                
                # tradingview chart draw
                draw_lightweight_chart(data_df)

                # DB에서 trading_history 결과 조회
                query = """
                    SELECT *
                    FROM fsts.simulation_history
                    WHERE symbol = :symbol
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                params = {"symbol": symbol}
                
                with get_db_session() as db:
                    result = sql_executor.execute_select(db, query, params)
                print(result)
                if result:
                    history_df = pd.DataFrame(result)
                    # 순서대로 컬럼 정렬 (없는 컬럼은 무시)
                    
                                    # 실현 손익 관련 컬럼에 % 추가
                if "realized_roi" in history_df.columns:
                    history_df["realized_roi"] = history_df["realized_roi"].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)

                if "unrealized_roi" in history_df.columns:
                    history_df["unrealized_roi"] = history_df["unrealized_roi"].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else x)
                    
                    # 원하는 컬럼 순서 지정
                    reorder_columns = [
                        "symbol", "average_price",
                        "realized_pnl", "unrealized_pnl", "realized_roi", "unrealized_roi", "total_cost",
                        "buy_count", "sell_count", "buy_dates", "sell_dates", "total_quantity","history", "created_at"
                    ]
                    history_df = history_df[[col for col in reorder_columns if col in history_df.columns]]

                    # 데이터의 행과 열 전환 (Transpose)
                    history_df_transposed = history_df.transpose()
                    # 컬럼 이름을 'Field', 'Value'로 변경
                    history_df_transposed = history_df_transposed.rename_axis("Field").reset_index()
                    history_df_transposed.columns = ["Field", "Value"]

                    # 테이블 표시
                    st.subheader("Trading History")
                    st.dataframe(history_df_transposed, use_container_width=True)
                    
                    # history 컬럼에서 데이터 추출
                    if not history_df.empty and "history" in history_df.columns:
                        # history 컬럼의 값 가져오기
                        trade_history = history_df.loc[0, "history"]

                        try:
                            # trade_history가 문자열이면 JSON으로 변환
                            if isinstance(trade_history, str):
                                trade_history = json.loads(trade_history)
                            
                            # trade_history가 리스트인지 확인 후 DataFrame으로 변환
                            if isinstance(trade_history, list):
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
                                

                                trade_history_df = pd.DataFrame(trade_history)
                            
                                # Streamlit 테이블로 표시
                                st.subheader("Detailed Trade History")
                                st.dataframe(trade_history_df, use_container_width=True)
                            else:
                                st.error(f"The 'history' field is not a valid list. Current type: {type(trade_history)}")
                        except json.JSONDecodeError as e:
                            st.error(f"Failed to decode 'history' field as JSON: {e}")
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")
                    else:
                        st.write("No history field found in the result.")
                    
                else:
                    st.write("No trading history found in the database for this stock.")


    with tabs[2]:
        st.header("📊 데이터 분석 페이지")
        
        # 데이터
        data = sns.load_dataset('penguins')

        # 히스토그램
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data, x='flipper_length_mm', hue='species', multiple='stack', ax=ax)
        ax.set_title("Seaborn 히스토그램")
        st.pyplot(fig)
    

if __name__ == "__main__":
    main()