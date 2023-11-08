from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    make_response,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from flask_wtf.csrf import generate_csrf

from app.csrf_protection import csrf
from app.forms import LoginForm, SignupForm
from database.database import get_db_connection
from database.models import User, FaceUser

auth = Blueprint("auth", __name__)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@login_manager.unauthorized_handler
def unauthorized_callback():
    return render_template("unauthorized.html")


def init_login_manager(app):
    login_manager.init_app(app)


@auth.route("/login", methods=["GET", "POST"])
def login():
    # 로그인 상태를 확인하여 이미 로그인한 경우 홈으로 리다이렉트
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()  # 폼 객체 생성
    error_message = None

    # POST 요청 시 폼 유효성 검사
    if request.method == "POST" and form.validate_on_submit():
        db_session = get_db_connection()

        # 사용자가 입력한 이메일과 비밀번호를 가져옴
        email = form.useremail.data
        password = form.password.data

        # 해당 이메일을 가진 사용자를 데이터베이스에서 찾음
        user = db_session.query(User).filter_by(user_email=email).first()

        # 사용자가 존재하고 비밀번호가 맞는 경우
        if user is not None:
            password_check = user.check_password(password)
            if password_check:
                user._authenticated = True
                db_session.add(user)
                db_session.commit()
                login_user(user)  # 사용자가 로그인
                return redirect(url_for("home"))

            else:
                error_message = "이메일 또는 비밀번호를 잘못 입력했습니다. 입력하신 내용을 다시 확인해주세요."

        db_session.close()
    return render_template("login.html", form=form, error_message=error_message)


@auth.route("/logout")
@login_required
def logout():
    current_user._authenticated = False  # 사용자가 로그아웃 하였으므로 _authenticated를 False로 설정
    logout_user()  # 로그아웃
    # flash("Logged out successfully.")
    return redirect(url_for("not_logged_home"))


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = SignupForm()
    db_session = get_db_connection()

    # 폼 유효성 검사를 통과한 경우
    if form.validate_on_submit():
        # 사용자가 입력한 이름, 이메일, 비밀번호를 가져옴
        name = form.name.data
        email = form.useremail.data
        password = form.password.data

        # 새로운 user 생성
        new_user = FaceUser(username=name, user_email=email)
        new_user.set_password(password)

        # db에 유저 저장
        db_session.add(new_user)
        db_session.commit()

        db_session.close()
        return redirect(url_for("auth.login"))
    else:
        csrf_token = generate_csrf()
        response = make_response(render_template("signup.html", csrf_token=csrf_token))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        db_session.close()
    return response


@auth.route("/check_duplicate", methods=["POST"])
@csrf.exempt
def check_duplicate():
    db_session = get_db_connection()
    email = request.form.get("useremail")

    user = db_session.query(FaceUser).filter_by(user_email=email).first()

    if user:
        db_session.close()
        return jsonify({"success": False, "message": "사용할 수 없는 이메일입니다."})
    else:
        db_session.close()
        return jsonify({"success": True, "message": "사용 가능한 이메일입니다."})
