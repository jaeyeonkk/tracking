
from flask import render_template, redirect, url_for, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime
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


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route('/tracking')
def index():
    return render_template('index.html')


# @app.route('/face_info')
# def face_info_route():
#     global face_count, last_face_seen_time, face_changed, head_rotation_alert
#     no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
#     return jsonify(face_count=face_count, no_face_for=no_face_for, face_changed=face_changed, head_rotation_alert=head_rotation_alert)


# @app.route('/video_feed')
# def video_feed():
#     return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run("0.0.0.0", port="5000", debug=True)
