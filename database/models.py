import datetime
import pytz

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import generate_password_hash, check_password_hash
from database.database import get_db_connection


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


class FaceUser(Base):
    __tablename__ = "face_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    user_email = Column(String(100), unique=True)
    password = Column(String(200))
    _is_active = Column(Boolean, default=True)  # changed to _is_active
    _authenticated = Column(Boolean, default=False)  # changed to _authenticated

    def set_password(self, password):
        hashed_password = generate_password_hash(password)
        # print(f"Generated hash: {hashed_password}")
        self.password = hashed_password

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def get(user_id):
        db_session = get_db_connection()
        user = db_session.query(FaceUser).filter_by(id=user_id).first()
        db_session.close()
        return user

    # Flask-Login integration
    def is_authenticated(self):  # added parentheses
        return self._authenticated  # changed to _authenticated

    def is_active(self):  # added parentheses
        return self._is_active  # changed to _is_active

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class FaceSubmissions(Base):
    __tablename__ = 'face_submissions'

    sub_id = Column(Integer, primary_key=True, autoincrement=True)
    q_id = Column(Integer, ForeignKey("q_list.q_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("face_user.id"), nullable=False)
    code_content = Column(Text, nullable=False)
    start_time = Column(TIMESTAMP, default=current_time, nullable=False)
    submission_time = Column(TIMESTAMP, default=current_time, nullable=False)
    is_correct = Column(Boolean)
    compile_result = Column(Text)
    language = Column(String(255))
    face_many = Column(Integer)
    face_empty = Column(Integer)
    face_change = Column(Integer)
    head_rotation = Column(Integer)