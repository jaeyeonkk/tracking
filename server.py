import os
from flask import Flask, render_template

from app.auth import auth, init_login_manager
from app.coding_test import coding_test
from app.config import Config

app = Flask(__name__, static_folder="app/static")
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates")
app.secret_key = Config.SECRET_KEY  # session 연결을 위한 키

app.register_blueprint(auth)
app.register_blueprint(coding_test)

init_login_manager(app)


@app.route("/")
def home():
    return render_template("main.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)
