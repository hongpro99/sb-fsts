from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
from fastapi import HTTPException

#CRUD(Create, Read, Update, Delete)
class SQLExecutor: #SQL 퀴리의 실행을 담당하는 클래스
    def __init__(self):
        pass 

    # SELECT 쿼리 실행
    def execute_select(self, db: Session, query: str, params: dict = None):
        """
        주어진 SELECT 쿼리를 실행하고 삽입된 레코드를 반환하는 메서드입니다.
        db: 데이터베이스 세션 객체
        query: 실행할 SQL 쿼리 문자열
        params: 쿼리의 파라미터로 사용될 딕셔너리 (선택 사항)
        """
        try:
            result = db.execute(text(query), params).mappings() #SQL 쿼리 실행
            return result.all()
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    # INSERT 쿼리 실행
    def execute_insert(self, db: Session, query: str, params: dict = None):

        try:
            result = db.execute(text(query), params).mappings()
            inserted_record = None
            inserted_record = result.all()
            db.commit() # commit하여 트랜잭션을 확정
            if inserted_record:
                print("Insert succeeded:", inserted_record)
            return inserted_record
        except IntegrityError as e: # 중복 키 에러
            db.rollback()
            raise HTTPException(status_code=500, detail="Duplicate Key error. already exists.")
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    # UPDATE 쿼리 실행
    def execute_update(self, db: Session, query: str, params: dict = None):
        try:
            result = db.execute(text(query), params).mappings()
            updated_record = None
            updated_record = result.all()
            db.commit()
            if updated_record:
                print("Update succeeded:", updated_record)
            return updated_record
        except SQLAlchemyError as e:
            db.rollback()
            raise e
    
    # UPSERT 쿼리 실행(INSERT 또는 UPDATE)
    def execute_upsert(self, db: Session, query: str, params: dict = None):
        try:
            result = db.execute(text(query), params).mappings()
            upserted_record = None
            upserted_record = result.all()
            db.commit()
            if upserted_record:
                print("Upsert succeeded:", upserted_record)
            return upserted_record
        except SQLAlchemyError as e:
            db.rollback()
            raise e

    # DELETE 쿼리 실행
    def execute_delete(self, db: Session, query: str, params: dict = None):
        try:
            result = db.execute(text(query), params).mappings()
            deleted_record = None
            deleted_record = result.all()
            db.commit()
            if deleted_record:
                print("Delete succeeded:", deleted_record)
                return deleted_record
            else:
                # 삭제할 데이터가 존재하지 않을 때
                raise HTTPException(status_code=404, detail="No data to delete")
        except SQLAlchemyError as e:
            db.rollback()
            raise e
