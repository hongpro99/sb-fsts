# sb-fsts
family stock trading system

# 참고 사이트
https://github.com/Soju06/python-kis

# 주의
develop branch 사용할 것!!!!!


# 폴더 구조
main.py -> fastapi 실행
app.utils.discord_bot.py -> discord bot 실행. python -m app.utils.discord_bot 명령어로 실행
technical_indicator.py -> 보조 지표 계산하는 로직은 다 이쪽으로 빼도록

ex.
1. 차트 데이터 가져오기 -> auto_trading_stock.py
2. 각종 보조지표 조회 & 계산 -> technical_indicator.py
3. 매수/매도 판단 및 매매 -> auto_trading_stock.py
4. discord notification -> auto_trading_stock.py
