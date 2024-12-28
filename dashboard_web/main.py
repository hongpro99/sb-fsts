import sys
import os

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.stock_auto_trading import AutoTradingStock
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from st_aggrid import AgGrid
import pandas as pd



def main():
    
    st.set_page_config(layout="wide")

    # 탭 생성
    tabs = st.tabs(["🏠 Home", "📈 Graph Page", "📊 Data Analysis Page"])

    # 각 탭의 내용 구성
    with tabs[0]:
        st.header("🏠 홈 페이지")
        # 데이터 생성
        data = {
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [25, 30, 35],
            "City": ["New York", "San Francisco", "Los Angeles"]
        }
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
        st.header("📈 그래프 페이지")
        
        # Dropdown 메뉴를 통해 데이터 선택
        symbol_options = {
            "삼성전자": "352820",
            "대한항공": "003490",
        }
        
        # Dropdown 메뉴 생성
        selected_symbol = st.selectbox("주식 종목을 선택하세요:", list(symbol_options.keys()))
        symbol = symbol_options[selected_symbol]

        # 그래프 생성
        # fig, ax = plt.subplots(figsize=(16, 9))
        # ax.plot(x, y, marker='o', label=selected_dataset)
        # ax.set_title(f"Graph for {selected_dataset}")
        # ax.set_xlabel("X-axis")
        # ax.set_ylabel("Y-axis")
        # ax.legend()
        
        auto_trading_stock = AutoTradingStock()

        # symbol = '352820'

        data_interval='15m'
        data_count = 1200 # 최대 1500
        target_trade_value_krw = 1000000  # 매수 목표 거래 금액

        simulation_plot, realized_pnl, current_pnl = auto_trading_stock.simulate_trading(symbol, data_interval, data_count, target_trade_value_krw)

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