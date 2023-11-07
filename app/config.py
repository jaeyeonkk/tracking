import json

with open("secrets.json") as f:
    secrets = json.load(f)


class Config(object):
    DB_HOST = secrets["db_host"]
    DB_NAME = secrets["db_name"]
    DB_USER = secrets["db_user"]
    DB_PW = secrets["db_pw"]
    DB_PORT = secrets["db_port"]
    DB_DRIVER = secrets["db_driver"]
    DB_CHARSET = secrets["db_charset"]
    SECRET_KEY = secrets["secret_key"]
    DB_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"
