from sqlalchemy import create_engine #데이터베이스 연결을 위한 엔진 생성
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

DATABASE_URL = "postgresql://coupleof:coupleof123@coupleof-rds.cp9lsfxv5if3.ap-northeast-2.rds.amazonaws.com/auto_trading"
# postgresql 데이터베이스에 연결하기 위한 URL

# 엔진 설정
engine = create_engine(DATABASE_URL)

# 세션을 생성하기 위한 세션 팩토리 함수
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#데이터베이스 세션 반환 함수
def get_db():
    db = SessionLocal()
    
    return db

# 세션 생성 함수
@contextmanager #데이터베이스 세션을 안전하게 처리할 수 있도록 함
def get_db_session():
    db = SessionLocal()  # 세션 생성
    try:
        yield db  # 세션을 호출자에게 반환
    finally:
        db.close()  # 작업 완료 후 세션 종료
