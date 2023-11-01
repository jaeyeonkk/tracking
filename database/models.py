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

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    submission_id = Column(Integer, primary_key=True, autoincrement=True)
    q_id = Column(Integer, ForeignKey("q_list.q_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code_content = Column(Text, nullable=False)
    submission_time = Column(TIMESTAMP, default=current_time, nullable=False)
    is_correct = Column(Boolean)
    compile_result = Column(Text)
    language = Column(String(20), nullable=False)