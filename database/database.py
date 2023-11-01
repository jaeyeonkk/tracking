from sqlalchemy import create_engine
from app.config import Config
from sqlalchemy.orm import sessionmaker

# 전역 변수로 엔진 및 세션 팩토리 생성
db_url = Config.DB_URL
engine = create_engine(db_url, pool_size=10, max_overflow=20, pool_recycle=3600)
Session = sessionmaker(bind=engine)



def get_db_connection():
    # 세션 생성
    session = Session()

    # 연결 테스트
    # try:
    #     session.execute(text("SELECT 1"))
    #     print("MySQL database connected")
    # except OperationalError:
    #     print("MySQL database not connected")

    return session
