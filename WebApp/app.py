import os 
import threading
import time
import io 
import cv2
import urllib.parse
from flask import Flask, request, Response, jsonify, render_template, url_for, redirect
from werkzeug.utils import secure_filename
import sys 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core import Main as CoreMain
from Core.utilities import config as cfg

from flask_cors import CORS 


UPLOAD_FOLDER = 'uploads' 
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'} # Разрешенные расширения видео



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Макс. размер файла 100 MB 
app.secret_key = 'super secret key' 


app.config['SECRET_KEY'] = 'pf9WkLp3s6vPYb289aKDR4hVTf2eXm7E' # Сгенерированный ранее
app.config['JWT_SECRET_KEY'] = 'anotherLongerAndEvenMoreSecureRandomStringForJWT!7N3kXp9s' # Сгенерированный ранее

password = urllib.parse.quote_plus("zxc")  
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{password}@localhost:5432/chii'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"] 
app.config["JWT_QUERY_STRING_NAME"] = "token" 


db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
from .models import User # Импортируем нашу модель





processing_state = {
    "model_thread": None,
    "model_instance": None,
    "input_path": None, 
    "is_running": False,
    "error": None,
    "last_frame": None, # Храним последний обработанный кадр для MJPEG
    "source_type": None # тип источника (file/rtsp)

}
frame_lock = threading.Lock() # Блокировка для безопасного доступа к last_frame

# --- Вспомогательные функции ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_model_thread(source_path_or_url, source_type):
    """Функция, которая будет выполняться в отдельном потоке"""
    global processing_state
    cap = None # Инициализируем cap
    model = None # Инициализируем model
    try:
        print(f"Starting model processing for {source_type}: {source_path_or_url}")
        processing_state["source_type"] = source_type 
        

        # ---Адаптируем логику из Chii.py сюда (ПРОЩЕ для старта) ---
        model = CoreMain(
            max_persons_count=cfg.MAX_PERSON_COUNT,
            names_of_classes=cfg.CLASSES,
            frame_steps=cfg.SEQ_LENGTH, 
            classifier_neurons=cfg.CLASSIFIER_NEURONS
        )
        processing_state["model_instance"] = model
        model.start()

        
        print(f"Attempting to open source: {source_path_or_url}")
        cap = cv2.VideoCapture(source_path_or_url)
        
        if source_type == 'rtsp':
            
            time.sleep(2) 

        if not cap.isOpened():
            # Очень важно логировать реальный путь/url
            raise ValueError(f"Cannot open video source: {source_path_or_url}")
        print(f"Successfully opened source: {source_path_or_url}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Source FPS: {fps if fps > 0 else 'N/A (likely stream)'}")

        while processing_state["is_running"] and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Stream ended or cannot read frame.")
                
                if source_type == 'file':
                     break
                else:
                     
                     print("Waiting for RTSP stream to recover...")
                     time.sleep(1) 
                     
                     if not processing_state["is_running"]: break
                     continue

            model.setFrame(frame)

            result = model.getOutput()

            if result and result.get('frame') is not None:
                with frame_lock:
                    processing_state["last_frame"] = result['frame'].copy()

            # Адаптивная пауза для контроля FPS стрима (если нужно)
            time.sleep(0.03) 

        print("Exited processing loop.")

    except Exception as e:
        print(f"Error in model thread: {e}")
        processing_state["error"] = str(e)
    finally:
        print("Cleaning up model thread...")
        if cap is not None and cap.isOpened():
            cap.release()
            print("Video capture released.")
        if model and hasattr(model, 'stop'):
             model.stop()
             if hasattr(model, 'join'):
                
                 model_thread_instance = processing_state.get("model_instance")
                 if model_thread_instance and isinstance(model_thread_instance, threading.Thread):
                     model_thread_instance.join(timeout=2.0) 
                 print("Model stop called.")
        
        with frame_lock:
            processing_state["last_frame"] = None
        processing_state["is_running"] = False
        processing_state["model_thread"] = None
        processing_state["model_instance"] = None
        processing_state["input_path"] = None
        processing_state["source_type"] = None
        # Удаляем файл, только если это был файл
        if source_type == 'file' and 'source_path_or_url' in locals() and os.path.exists(source_path_or_url):
             try:
                 
                 print(f"File processing finished for: {source_path_or_url}")
             except OSError as e:
                 print(f"Error removing file {source_path_or_url}: {e}")
        print("Model thread cleanup complete.")



# === API Эндпоинты Аутентификации ===

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing username, email, or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if User.query.filter_by(email=email.lower()).first():
        return jsonify({"error": "Email already exists"}), 400

    try:
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        access_token = create_access_token(identity=str(new_user.id))  
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
             "user_id": new_user.id #
             }), 201 # Created
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {e}") # Временный вывод
        return jsonify({"error": "Registration failed"}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401 # Unauthorized





@app.route('/', methods=['GET'])
def index():
    
    return jsonify({"message": "Welcome to Chii2 API!"}) 



# WebApp/app.py

@app.route('/auth/me', methods=['GET'])
@jwt_required() # Этот эндпоинт требует валидный токен
def get_current_user_data():
    current_user_id = get_jwt_identity() # Получаем ID пользователя из токена
    user = User.query.get(int(current_user_id)) # Ищем пользователя по ID, преобразовав его в int

    if not user:
        return jsonify({"error": "User not found"}), 404

    
    
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() 
    }
    return jsonify(user_data), 200


@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_video():
    global processing_state
    if processing_state["is_running"]:
        return jsonify({"error": "Processing is already running."}), 400

    # 1. Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    # 2. Получаем объект файла
    file = request.files['file'] # Теперь 'file' точно определена здесь

    # 3. Проверяем, выбрал ли пользователь файл
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    
    if file and allowed_file(file.filename):
        # --- Все проверки пройдены, можно сохранять и запускать ---
        filename = secure_filename(file.filename) # Безопасное имя файла
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            print(f"File saved to: {filepath}")

            # Сбрасываем состояние перед запуском
            with frame_lock: processing_state["last_frame"] = None
            processing_state["error"] = None
            processing_state["input_path"] = filepath 
            processing_state["is_running"] = True

            # Запускаем поток
            thread = threading.Thread(target=run_model_thread, args=(filepath,'file'), daemon=True) 
            processing_state["model_thread"] = thread
            thread.start()

            # Возвращаем JSON
            return jsonify({"message": "File uploaded and processing started.", "source": filepath})

        except Exception as e:
            print(f"Error during file save or thread start: {e}")
            
            processing_state["is_running"] = False
            processing_state["input_path"] = None
            return jsonify({"error": f"Failed to save or start processing: {str(e)}"}), 500
    else:
        # Если тип файла не разрешен
        return jsonify({"error": f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"}), 400


@app.route('/start_rtsp', methods=['POST'])
@jwt_required()
def start_rtsp():

    current_user_id = get_jwt_identity() 
    print(f"User {current_user_id} accessing /start_rtsp")
    global processing_state
    if processing_state["is_running"]:
        return jsonify({"error": "Processing is already running."}), 400

    data = request.get_json()
    rtsp_url = data.get('rtsp_url')

    if not rtsp_url:
        return jsonify({"error": "RTSP URL is required."}), 400

    
    if not rtsp_url.lower().startswith('rtsp://'):
         return jsonify({"error": "Invalid RTSP URL format."}), 400

    try:
        # Сбрасываем состояние
        with frame_lock: processing_state["last_frame"] = None
        processing_state["error"] = None
        processing_state["input_path"] = rtsp_url # Сохраняем URL
        processing_state["is_running"] = True

        # Запускаем поток
        thread = threading.Thread(target=run_model_thread, args=(rtsp_url,'rtsp'), daemon=True) # Передаем тип 'rtsp'
        processing_state["model_thread"] = thread
        thread.start()

        return jsonify({"message": "RTSP stream processing started.", "source": rtsp_url})

    except Exception as e:
        processing_state["is_running"] = False
        processing_state["input_path"] = None
        return jsonify({"error": f"Failed to start RTSP processing: {str(e)}"}), 500
    



@app.route('/video_feed')
@jwt_required()
def video_feed():
    """Эндпоинт для MJPEG стрима."""
    current_user_id = get_jwt_identity()
    print(f"User {current_user_id} accessing /video_feed")
    def generate_frames():
        print("Starting MJPEG stream...")
        while True:
            frame_to_send = None
            with frame_lock: # Получаем кадр под блокировкой
                if processing_state["last_frame"] is not None:
                    frame_to_send = processing_state["last_frame"].copy()

            if frame_to_send is None:
                
                time.sleep(0.1) 
                
                if not processing_state["is_running"] and processing_state["input_path"] is None:
                     print("Processing stopped or finished, closing stream.")
                     break 
                continue 

            # Кодируем кадр в JPEG
            ret, buffer = cv2.imencode('.jpg', frame_to_send)
            if not ret:
                # print("Failed to encode frame")
                continue # Пропускаем кадр, если не удалось закодировать

            frame_bytes = buffer.tobytes()
            # Отправляем кадр в формате MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.01) 

    
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    
    current_user_id = get_jwt_identity()
    print(f"User {current_user_id} accessing /status")
    
    status = {
        "is_running": processing_state["is_running"],
        "input_path": processing_state["input_path"], 
        "source_type": processing_state["source_type"],
        "error": processing_state["error"],
        # "model_active": processing_state["model_thread"] is not None and processing_state["model_thread"].is_alive()
    }
    return jsonify(status)

@app.route('/stop', methods=['POST'])
@jwt_required()
def stop_processing():
    global processing_state
    current_user_id = get_jwt_identity()
    print(f"User {current_user_id} accessing /stop")
    if not processing_state["is_running"]:
        return jsonify({"message": "No processing is currently running."}), 400

    processing_state["is_running"] = False # Поток run_model_thread увидит это и выйдет из цикла


    return jsonify({"message": "Stop signal sent. Processing will stop soon."})




if __name__ == '__main__':
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # threaded=True позволяет обрабатывать несколько запросов одновременно
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
    # use_reloader=False ВАЖНО, чтобы не запускать модель дважды в debug режиме!