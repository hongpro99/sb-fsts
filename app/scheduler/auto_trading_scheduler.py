from datetime import datetime

from app.utils.database import get_db, get_db_session
from app.utils.crud_sql import SQLExecutor

# db = get_db()
sql_executor = SQLExecutor()


def scheduled_trading_task():
    print('매수가 완료되었습니다!')