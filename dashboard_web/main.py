import sys
import os
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from st_aggrid import AgGrid
import pandas as pd
from datetime import datetime, date, timedelta 

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.auto_trading_bot import AutoTradingBot
from app.utils.crud_sql import SQLExecutor
from app.utils.database import get_db, get_db_session


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
        st.header("📈 시뮬레이션 그래프")

        # 화면을 2개의 열로 나누기 for selectbox
        col1, col2 = st.columns(2)

        query = """
            SELECT 종목코드, 종목이름 FROM fsts.kospi200 ORDER BY 종목이름;
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

        trading_logic_options = ["윗꼬리_아랫꼬리", "관통형"]
            
        # Dropdown 메뉴 생성
        with col1:
            selected_trading_logic = st.selectbox("매매 로직을 선택하세요:", trading_logic_options)
        with col2:
            selected_symbol = st.selectbox("주식 종목을 선택하세요:", list(symbol_options.keys()))
            symbol = symbol_options[selected_symbol]

        # 그래프 생성
        # fig, ax = plt.subplots(figsize=(16, 9))
        # ax.plot(x, y, marker='o', label=selected_dataset)
        # ax.set_title(f"Graph for {selected_dataset}")
        # ax.set_xlabel("X-axis")
        # ax.set_ylabel("Y-axis")
        # ax.legend()
        
        user_name = "홍석형"

        auto_trading_bot = AutoTradingBot(user_name=user_name)

        # symbol = '352820'

        # 당일로부터 1년전 기간으로 차트 분석
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        target_trade_value_krw = 1000000  # 매수 목표 거래 금액

        simulation_plot = auto_trading_bot.simulate_trading(symbol, start_date, end_date, target_trade_value_krw)

        fig, ax = simulation_plot

        # 그래프 출력
        # st.pyplot(fig)
        
        # 그래프 이미지를 메모리에 저장
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)  # 메모리 절약을 위해 그래프 닫기
        
        image = buf
        
        # 이미지 표시
        st.image(image, caption=f"Graph for {selected_symbol}", use_container_width=True)

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