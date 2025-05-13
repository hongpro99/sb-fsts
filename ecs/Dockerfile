# 베이스 이미지 설정 (Python 3.11 사용)
FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 코드 복사
# 프로젝트 depth 일치 시키도록 /app/app 설정
COPY ./test.py /app/test.py
# COPY ./dashboard_web/trading_logic.json /app/app/trading_logic.json

EXPOSE 7000

# FastAPI 서버 실행 (Uvicorn 사용)
CMD ["python", "/app/test.py"]