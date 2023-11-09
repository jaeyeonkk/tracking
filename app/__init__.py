from flask import Flask
from app.config import Config

app = Flask(__name__, static_folder="static")

app.template_folder = "templates"
app.secret_key = Config.SECRET_KEY

from app.auth import auth, init_login_manager
from app.coding_test import coding_test
from app.config import Config
from app.csrf_protection import init_csrf
from app.dashboard import dashboard

# 블루 프린트 등록
app.register_blueprint(auth)
app.register_blueprint(coding_test)
app.register_blueprint(dashboard)


init_login_manager(app)
init_csrf(app)