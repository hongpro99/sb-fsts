from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

DATABASE_URL = "postgresql://coupleof:coupleof123@coupleof-rds.cp9lsfxv5if3.ap-northeast-2.rds.amazonaws.com/auto_trading"

# 엔진 설정
engine = create_engine(DATABASE_URL)

# 세션 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    
    return db

# 세션 생성 함수
@contextmanager
def get_db_session():
    db = SessionLocal()  # 세션 생성
    try:
        yield db  # 세션을 호출자에게 반환
    finally:
        db.close()  # 작업 완료 후 세션 종료
