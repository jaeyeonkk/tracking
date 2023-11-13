
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from app import app


PER_PAGE = 10 


@app.route("/")
def not_logged_home():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("main.html")


@app.route('/iframe')
def iframe():
    return render_template('iframe.html')


@app.route('/iiframe')
def iiframe():
    return render_template('iiframe.html')


@app.route("/main")
@login_required
def home():
    return render_template("main2.html")



if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)