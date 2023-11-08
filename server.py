import os
from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.auth import auth, init_login_manager
from app.coding_test import coding_test
from app.config import Config
from app.csrf_protection import init_csrf
from app.dashboard import dashboard

app = Flask(__name__, static_folder="app/static")
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "templates")
app.secret_key = Config.SECRET_KEY  # session 연결을 위한 키

app.register_blueprint(auth)
app.register_blueprint(coding_test)
app.register_blueprint(dashboard)

init_login_manager(app)
init_csrf(app)


@app.route("/")
def not_logged_home():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main.html")


@app.route("/main")
@login_required
def home():
    return render_template("main2.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)
