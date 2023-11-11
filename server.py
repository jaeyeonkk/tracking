
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
import base64
from app import app


@app.route("/")
def not_logged_home():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main.html")


@app.route("/main")
@login_required
def home():
    return render_template("main2.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)