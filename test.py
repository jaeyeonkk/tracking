from flask import Flask, jsonify, render_template, Response
import cv2
import dlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
detector = dlib.get_frontal_face_detector()
face_rec_model = dlib.face_recognition_model_v1(
    "dlib_face_recognition_resnet_model_v1.dat"
)


# 전역 변수를 선언하고 초기화합니다
face_count = 0
last_face_seen_time = None
last_face_descriptor = None
face_changed = False
eye_deviation_count = 0

executor = ThreadPoolExecutor(max_workers=4)  # 스레드 풀을 생성합니다


def compute_face_descriptor(frame, landmarks):
    global last_face_descriptor, face_changed
    current_face_descriptor = face_rec_model.compute_face_descriptor(frame, landmarks)

    if last_face_descriptor and current_face_descriptor:
        diff = sum(
            [
                (a - b) ** 2
                for a, b in zip(last_face_descriptor, current_face_descriptor)
            ]
        )
        if diff > 0.2:  # 이 값을 조정하여 감지 감도를 변경할 수 있습니다
            face_changed = True
        else:
            face_changed = False  # 얼굴 특성이 일치할 때 face_changed를 False로 설정
        last_face_descriptor = current_face_descriptor
    elif current_face_descriptor:
        last_face_descriptor = current_face_descriptor
        face_changed = False


def eye_tracking():
    global face_count, last_face_seen_time
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 15)  # FPS를 15로 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 너비를 640으로 설정
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 높이를 480으로 설정
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        face_count = len(faces)
        if face_count > 0:
            last_face_seen_time = datetime.now()

        for face in faces:
            x1, y1, x2, y2 = (face.left(), face.top(), face.right(), face.bottom())
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 얼굴 랜드마크를 탐지합니다
            landmarks = predictor(gray, face)
            check_eye_deviation(landmarks)

            # 눈의 위치를 찾아서 원으로 표시합니다
            for n in range(36, 48):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)

            # 30 프레임마다 얼굴 특성 계산을 수행합니다
            if frame_count % 10 == 0:
                executor.submit(compute_face_descriptor, frame, landmarks)

        frame_count += 1  # 프레임 카운터를 증가시킵니다

        # JPEG 형식으로 인코딩하여 웹페이지에 전송
        _, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


def calculate_eye_deviation(landmarks):
    left_eye_points = landmarks.parts()[36:42]
    right_eye_points = landmarks.parts()[42:48]

    left_eye_center_x = sum([pt.x for pt in left_eye_points]) // 6
    left_eye_center_y = sum([pt.y for pt in left_eye_points]) // 6
    right_eye_center_x = sum([pt.x for pt in right_eye_points]) // 6
    right_eye_center_y = sum([pt.y for pt in right_eye_points]) // 6

    left_eye_width = left_eye_points[3].x - left_eye_points[0].x
    right_eye_width = right_eye_points[3].x - right_eye_points[0].x

    left_white_ratio = (left_eye_center_x - left_eye_points[0].x) / left_eye_width
    right_white_ratio = (right_eye_center_x - right_eye_points[0].x) / right_eye_width

    return left_white_ratio, right_white_ratio


def check_eye_deviation(landmarks):
    global eye_deviation_count
    left_white_ratio, right_white_ratio = calculate_eye_deviation(landmarks)

    deviation_threshold = 0.001  # 임계값 수정
    if (
        abs(left_white_ratio - 0.5) > deviation_threshold
        or abs(right_white_ratio - 0.5) > deviation_threshold
    ):
        eye_deviation_count += 1
        if eye_deviation_count >= 5:
            alert_eye_deviation()
            eye_deviation_count = 0
    else:
        eye_deviation_count = 0


def alert_eye_deviation():
    print("경고: 눈동자가 치우쳐졌습니다!")


def check_eye_deviation(landmarks):
    global eye_deviation_count
    left_white_ratio, right_white_ratio = calculate_eye_deviation(landmarks)

    print(
        f"Left White Ratio: {left_white_ratio}, Right White Ratio: {right_white_ratio}"
    )  # 이 부분을 추가


@app.route("/face_info")
def face_info_route():
    global face_count, last_face_seen_time, face_changed, eye_deviation_count
    no_face_for = (
        (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
    )
    return jsonify(
        face_count=face_count,
        no_face_for=no_face_for,
        face_changed=face_changed,
        eye_deviation_count=eye_deviation_count,
    )


@app.route("/video_feed")
def video_feed():
    return Response(
        eye_tracking(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=True)
