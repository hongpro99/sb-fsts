# sb-fsts: 자동 주식 트레이딩 시스템

사람의 감정을 배제한 자동 봇 트레이딩 실현을 목표로 한 자동 주식 데이터 수집, 보조지표 계산, 자동 매매, 실시간 알림(Discord), 웹 대시보드, LLM 기반 질의응답 등 다양한 기능을 제공하는 통합 트레이딩 플랫폼입니다.

---

# 목차
1. [기술스택 / 요구사항](#기술스택--요구사항)
2. [실행 방법](#실행-방법)
3. [주요 기능/ 사용 예시](#주요-기능-사용-예시)
4. [아키텍처/ 폴더 구조](#아키텍처-폴더-구조)
5. [Contributing](#contributing)

---

# 기술스택 / 요구사항

- **Python 3.8+**
- **FastAPI**: 백엔드 API 서버
- **Streamlit**: 웹 대시보드 프론트엔드
- **Discord**: 실시간 알림 및 메시징
- **AWS ECS, EC2, S3, DynamoDB**: 클라우드 인프라 및 데이터 저장
- **ChatGPT/OpenAI API**: 자연어 기반 질의응답
- **Vector DB**: LLM RAG(질의응답) 데이터 저장

---

# 실행 방법

## 1. 로컬 개발 환경

1. Python 3.8 이상 설치
2. 가상환경 생성 및 활성화
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```
3. 패키지 설치
   ```sh
   pip install -r requirements.txt
   ```
4. FastAPI 서버 실행
   ```sh
   python main.py
   ```
5. Discord 봇 실행
   ```sh
   python -m app.utils.discord_bot
   ```
6. 웹 대시보드 실행
   ```sh
   ./local_run_web.sh
   ```

## 2. AWS ECS 환경

- 각 서비스는 Docker 이미지로 빌드되어 ECS에 배포됩니다.
- 환경 변수 및 AWS IAM 권한을 통해 S3 접근 및 데이터 저장이 가능합니다.
- 로그 및 트레이딩 데이터는 S3 버킷에 저장됩니다.

---

# 주요 기능/ 사용 예시

- **자동 트레이딩**: 실시간 데이터 수집, 보조지표 기반 매수/매도 판단, 자동 주문
- **보조지표 계산**: 이동평균선, RSI 등 다양한 기술적 지표 지원
- **Discord 알림**: 트레이딩 결과 및 이벤트 실시간 알림
- **웹 대시보드**: 트레이딩 현황, 수익률, 로그 등 시각화
- **S3 연동**: 데이터 및 로그 백업, 분석 지원
- **스케줄러 기반 자동화**: scheduler.py를 통해 트레이딩, 데이터 수집, 알림 등 반복 작업을 자동화합니다.
- **LLM 질의응답**: ChatGPT와 연동하여 자연어 기반 질의 및 데이터 조회

---

# 아키텍처/ 폴더 구조

## 아키텍처 다이어그램

- **ECS/EC2**: FastAPI 기반 트레이딩 봇, 웹 백엔드, Streamlit 웹 프론트엔드가 컨테이너로 실행
- **S3**: 트레이딩 데이터, 로그, 백업 저장
- **RDS**: 계좌/종목 정보, 트레이딩 로그 저장
- **한국투자증권 API**: 실시간 주식 데이터 및 주문 처리
- **Discord**: 실시간 알림 및 메시징
- **scheduler**: 트레이딩 봇, 데이터 수집, 알림 전송 등 주요 작업을 주기적으로 실행합니다.  
  예를 들어, 일정 시간마다 `auto_trading_stock.py`의 트레이딩 로직을 호출하여 자동 매매가 이루어지도록 합니다.
- **ChatGPT**: 자연어 기반 질의응답 및 데이터 조회
- **Vector DB**: LLM RAG(질의응답) 데이터 저장
- **GitHub Actions**: CI/CD 자동 배포

## 주요 폴더 구조

```
main.py                  # FastAPI 서버 실행
app/utils/discord_bot.py # Discord 봇 실행 (알림 전송)
technical_indicator.py   # 보조지표 계산 로직
auto_trading_stock.py    # 데이터 수집, 매매 판단, 알림, S3 저장
scheduler.py             # 트레이딩 봇 및 주요 작업 스케줄링 (주기적 실행)
dashboard_web/           # 웹 대시보드 코드 (Streamlit)
llm/                     # LLM(대형 언어 모델) 관련 코드
```

---

# Contributing

- 개발은 반드시 **develop 브랜치**에서 진행합니다.
- 기능 개발 시 feature 브랜치에서 작업 후, develop 브랜치로 Pull Request를 생성합니다.
- 코드 리뷰 및 테스트 후 master 브랜치로 병합되며, CI/CD를 통해 자동 배포됩니다.

---

> 참고:  
> - [python-kis](https://github.com/Soju06/python-kis)  
> - 문의 및 피드백은 Discord 또는 GitHub Issues를 통해 주시기 바랍니다.