from flask import Flask, jsonify, render_template, Response
import cv2
import dlib
from datetime import datetime, timedelta


app = Flask(__name__)

predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
detector = dlib.get_frontal_face_detector()

# 전역 변수를 선언하고 초기화합니다
face_count = 0
last_face_seen_time = None

def eye_tracking():
    global face_count, last_face_seen_time
    cap = cv2.VideoCapture(0)
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

            # 눈의 위치를 찾아서 원으로 표시합니다
            for n in range(36, 48):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)
        
        # JPEG 형식으로 인코딩하여 웹페이지에 전송
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route('/face_count')
def face_count_route():
    global face_count
    return jsonify(face_count=face_count)

@app.route('/face_info')
def face_info_route():
    global face_count, last_face_seen_time
    no_face_for = (datetime.now() - last_face_seen_time).seconds if last_face_seen_time else 0
    return jsonify(face_count=face_count, no_face_for=no_face_for)


@app.route('/video_feed')
def video_feed():
    return Response(eye_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)
