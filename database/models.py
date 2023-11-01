import datetime
import pytz
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

kst = pytz.timezone("Asia/Seoul")  # 한국 시간

def current_time():
    return datetime.datetime.now(kst)

class QList(Base):
    __tablename__ = "q_list"

    q_lang = Column(String, nullable=False)
    q_level = Column(String, nullable=False)
    q_id = Column(Integer, primary_key=True, nullable=False)
    q_name = Column(String, nullable=False)
    q_content = Column(Text, nullable=False)
    ex_print = Column(Text, nullable=False)
    c_answer_code = Column(Text, nullable=False)
    cpp_answer_code = Column(Text, nullable=False)
    p_answer_code = Column(Text, nullable=False)
    j_answer_code = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)


class Student(Base):
    __tablename__ = "student"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)