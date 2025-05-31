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
from datetime import datetime, timezone
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Core import Main as CoreMain
from Core.utilities import config as cfg
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError, ClientError
import numpy as np

from flask_cors import CORS 

# запуск flask --app WebApp.app run --host=0.0.0.0 --port=5000     
UPLOAD_FOLDER = 'uploads' 
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'} 



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


app.config['S3_ENDPOINT_URL'] = os.environ.get('S3_ENDPOINT_URL', 'http://localhost:9000')
app.config['S3_ACCESS_KEY'] = os.environ.get('S3_ACCESS_KEY', 'chii2accesskey') 
app.config['S3_SECRET_KEY'] = os.environ.get('S3_SECRET_KEY', 'chii2secretkeyVERYSTRONG') 
app.config['S3_DEFAULT_BUCKET_ANOMALIES'] = os.environ.get('S3_DEFAULT_BUCKET_ANOMALIES', 'user-anomalies') 


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Макс. размер файла 100 MB 
app.secret_key = 'super secret key' 


app.config['SECRET_KEY'] = 'pf9WkLp3s6vPYb289aKDR4hVTf2eXm7E' 
app.config['JWT_SECRET_KEY'] = 'anotherLongerAndEvenMoreSecureRandomStringForJWT!7N3kXp9s' 

password = urllib.parse.quote_plus("zxc")  
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{password}@localhost:5432/chii_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"] 
app.config["JWT_QUERY_STRING_NAME"] = "token" 


db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
from .models import User, Anomaly



try:
    s3_client = boto3.client(
        's3',
        endpoint_url=app.config['S3_ENDPOINT_URL'],
        aws_access_key_id=app.config['S3_ACCESS_KEY'],
        aws_secret_access_key=app.config['S3_SECRET_KEY'],
        config=Config(signature_version='s3v4'), # Важно для MinIO
        region_name='us-east-1' 
    )
    
    try:
        s3_client.head_bucket(Bucket=app.config['S3_DEFAULT_BUCKET_ANOMALIES'])
        print(f"Successfully connected to MinIO and bucket '{app.config['S3_DEFAULT_BUCKET_ANOMALIES']}' exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Warning: Bucket '{app.config['S3_DEFAULT_BUCKET_ANOMALIES']}' not found in MinIO. Please create it.")
            try:
                s3_client.create_bucket(Bucket=app.config['S3_DEFAULT_BUCKET_ANOMALIES'])
                print(f"Bucket '{app.config['S3_DEFAULT_BUCKET_ANOMALIES']}' created successfully.")
            except Exception as e_create:
                print(f"Failed to create bucket: {e_create}")
        else:
            print(f"Error checking MinIO bucket: {e}")

except Exception as e_s3_init:
    s3_client = None 
    print(f"Error initializing S3 client: {e_s3_init}. Anomaly saving will be disabled.")



processing_state = {
    "model_thread": None,
    "model_instance": None,
    "input_path": None, 
    "is_running": False,
    "error": None,
    "last_frame": None, 
    "source_type": None, 
    "user_id_who_started_processing": None 

}
frame_lock = threading.Lock() 


def upload_file_to_s3(file_path, bucket_name, object_name=None):
    if s3_client is None:
        print("S3 client not initialized. Cannot upload file.")
        return None

    if object_name is None:
        object_name = os.path.basename(file_path)
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        # URL для доступа к файлу (может зависеть от настроек MinIO и прокси)
        file_url = f"{app.config['S3_ENDPOINT_URL']}/{bucket_name}/{object_name}"
        print(f"File {file_path} uploaded to {bucket_name}/{object_name}. URL: {file_url}")
        return file_url
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found for S3 upload.")
        return None
    except NoCredentialsError:
        print("Error: Credentials not available for S3 upload.")
        return None
    except ClientError as e:
        print(f"S3 ClientError during upload: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during S3 upload: {e}")
        return None


def save_anomaly_segment(frames_buffer, fps, user_id_who_started, source_identifier, source_type, anomaly_start_time, detected_class_name):
    if not frames_buffer:
        print("Frame buffer is empty, cannot save anomaly.")
        return

    if s3_client is None: 
        print("S3 client not available. Skipping anomaly saving.")
        return

    timestamp_str = anomaly_start_time.strftime("%Y%m%d_%H%M%S%f")[:-3] 
    
    
    if source_type == 'file':
        safe_source_name = os.path.basename(source_identifier).split('.')[0]
    elif source_type == 'rtsp':
        
        safe_source_name = source_identifier.split('/')[-1].replace(':', '-').replace('.', '_') 
        if not safe_source_name: safe_source_name = "rtsp_stream"
    else:
        safe_source_name = "unknown_source"
    
    
    bucket_name = app.config['S3_DEFAULT_BUCKET_ANOMALIES']

    video_filename_base = f"{safe_source_name}_user{user_id_who_started}_{timestamp_str}_{detected_class_name}"
    temp_video_path = f"temp_anomaly_{video_filename_base}.mp4"

    print(f"Attempting to save anomaly segment: {temp_video_path} for user {user_id_who_started}")

    try:
        height, width, _ = frames_buffer[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        video_writer = cv2.VideoWriter(temp_video_path, fourcc, float(fps), (width, height))
        for frame_to_write in frames_buffer:
            video_writer.write(frame_to_write)
        video_writer.release()
        print(f"Temporary anomaly video saved locally to {temp_video_path}")

        # Загружаем в MinIO
        s3_video_url = upload_file_to_s3(temp_video_path, bucket_name, f"{video_filename_base}.mp4")

        if s3_video_url:
            print(f"Anomaly video uploaded to S3: {s3_video_url}")
            # --- Сохранение метаданных в PostgreSQL ---
            try:
                
                print("TODO: Save anomaly metadata to PostgreSQL:")
                print(f"  user_id: {user_id_who_started}")
                print(f"  timestamp_detected: {anomaly_start_time}")
                print(f"  source_type: {source_type}")
                print(f"  source_identifier: {source_identifier}")
                print(f"  video_segment_url: {s3_video_url}")
                print(f"  duration_seconds: {int(len(frames_buffer)/fps if fps > 0 else 0)}")
                print(f"  detected_class: {detected_class_name}")

                # with app.app_context():
                #     new_anomaly = Anomaly(user_id=user_id, timestamp_detected=anomaly_start_time,
                #                           source_type=source_type, source_identifier=source_identifier,
                #                           video_segment_url=s3_video_url,
                #                           duration_seconds=int(len(frames_buffer)/fps if fps > 0 else 0),
                #                           detected_class=detected_class_name)
                #     db.session.add(new_anomaly)
                #     db.session.commit()
                #     print("Anomaly metadata saved to PostgreSQL.")

            except Exception as e_db:
                print(f"Error saving anomaly metadata to PostgreSQL: {e_db}")
        else:
            print("Failed to upload anomaly video to S3. Metadata not saved.")

    except Exception as e_video_write:
        print(f"Error writing temporary anomaly video: {e_video_write}")
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path) # Удаляем временный файл




def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_model_thread(source_path_or_url, source_type, user_id_who_started):
    global processing_state 

    cap = None 
    model = None 
    try:
        print(f"Starting model processing for {source_type}: {source_path_or_url}")
        processing_state["source_type"] = source_type 
        

        
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
        last_anomaly_save_time = None 
        ANOMALY_SAVE_COOLDOWN_SECONDS = 10 # Сохранять кадр аномалии не чаще чем раз в 10 секунд
        print(f"Source FPS: {fps if fps > 0 else 'N/A (likely stream)'}")

        while processing_state["is_running"] and cap.isOpened():
            ret, original_frame = cap.read() 
            if not ret: 
                print(f"Stream ended or cannot read frame (ret is False).")
                if source_type == 'file': break
                else: # RTSP
                    print("Waiting for RTSP stream to recover...")
                    time.sleep(1)
                    if not processing_state["is_running"]: break
                    continue
            
            if original_frame is None: 
                print(f"Original frame is None after cap.read(), though ret was True. Skipping.")
                time.sleep(0.05) 
                continue

            frame_for_model = original_frame.copy() 
            model.setFrame(frame_for_model)
            result = model.getOutput() 

            anomaly_detected_on_this_frame = False
            detected_anomaly_class_name = None

            if result and result.get('classes') is not None:
                try:
                    class_indices_tensor = result['classes'] 
                    class_indices = class_indices_tensor.cpu().numpy() if hasattr(class_indices_tensor, 'cpu') else np.array(class_indices_tensor)
                    for class_idx_float in class_indices:
                        class_idx = int(class_idx_float)
                        action_class_name = cfg.CLASSES[class_idx] if 0 <= class_idx < len(cfg.CLASSES) else "error_idx"
                        if action_class_name == 'unknown': 
                            anomaly_detected_on_this_frame = True
                            detected_anomaly_class_name = 'unknown'
                            break 
                except Exception as e_class_proc:
                    print(f"Error processing classes from Core model: {e_class_proc}")

            if anomaly_detected_on_this_frame:
                current_time = datetime.now(timezone.utc)
                ready_to_save = False
                if last_anomaly_save_time is None:
                    ready_to_save = True
                else:
                    time_since_last_save = (current_time - last_anomaly_save_time).total_seconds()
                    if time_since_last_save >= ANOMALY_SAVE_COOLDOWN_SECONDS:
                        ready_to_save = True
                
                if ready_to_save:
                    print(f"ANOMALY FRAME DETECTED ({detected_anomaly_class_name}) at {current_time}. Saving ORIGINAL frame.")
                    last_anomaly_save_time = current_time

                    
                    if source_type == 'file':
                        safe_source_name_for_temp = os.path.basename(source_path_or_url)
                        safe_source_name_for_temp = os.path.splitext(safe_source_name_for_temp)[0]
                    elif source_type == 'rtsp':
                        safe_source_name_for_temp = source_path_or_url.replace("rtsp://", "").replace("/", "_").replace(":", "-").replace(".", "_")
                        if not safe_source_name_for_temp: safe_source_name_for_temp = "rtsp_stream"
                    else:
                        safe_source_name_for_temp = "unknown_source"
                    temp_frame_filename_base = f"{safe_source_name_for_temp}_user{user_id_who_started}_{current_time.strftime('%Y%m%d_%H%M%S%f')[:-3]}_{detected_anomaly_class_name}"
                    temp_frame_path = f"temp_anomaly_frame_{temp_frame_filename_base}.jpg"
                    
                    
                    if original_frame is not None:
                        save_success = cv2.imwrite(temp_frame_path, original_frame) 
                    else:
                        print("CRITICAL ERROR: original_frame is None before imwrite! Cannot save.")
                        save_success = False


                    if save_success:
                        print(f"Temporary anomaly frame saved to {temp_frame_path}")
                        # --- Загрузка в MinIO ---
                        bucket_name_for_anomalies = app.config['S3_DEFAULT_BUCKET_ANOMALIES']
                        s3_object_name = f"{temp_frame_filename_base}.jpg"
                        s3_frame_url = upload_file_to_s3(temp_frame_path, bucket_name_for_anomalies, s3_object_name)

                        if s3_frame_url:
                            print(f"Anomaly frame uploaded to S3: {s3_frame_url}")
                            
                            try:
                                with app.app_context():
                                    from .models import Anomaly 
                                    
                                    new_anomaly = Anomaly(
                                        user_id=user_id_who_started, 
                                        timestamp_detected=current_time,
                                        source_type=source_type, 
                                        source_identifier=source_path_or_url,
                                        image_url=s3_frame_url, 
                                        
                                        detected_class=detected_anomaly_class_name,
                                        is_reviewed=False
                                    )
                                    db.session.add(new_anomaly)
                                    db.session.commit()
                                    print(f"Anomaly frame metadata (ID: {new_anomaly.id}) saved to PostgreSQL.")
                            except Exception as e_db_frame:
                                print(f"Error saving anomaly frame metadata to PostgreSQL: {e_db_frame}")
                        else:
                            print(f"Failed to upload anomaly frame to S3. Metadata not saved.")
                        
                        if os.path.exists(temp_frame_path):
                            os.remove(temp_frame_path) 
                    else:
                        print(f"Failed to save temporary anomaly frame: {temp_frame_path}")

            if result and result.get('frame') is not None:
                with frame_lock:
                    processing_state["last_frame"] = result['frame'].copy()
            
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
        if source_type == 'file' and 'source_path_or_url' in locals() and os.path.exists(source_path_or_url):
             try:
                 
                 print(f"File processing finished for: {source_path_or_url}")
             except OSError as e:
                 print(f"Error removing file {source_path_or_url}: {e}")
        print("Model thread cleanup complete.")




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
        print(f"Error during registration: {e}")
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




@app.route('/api/anomalies', methods=['GET'])
@jwt_required()
def get_anomalies():
    print("==== GET /api/anomalies CALLED ====") 
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = Anomaly.query.order_by(Anomaly.timestamp_detected.desc()).paginate(page=page, per_page=per_page, error_out=False)
    anomalies_list = pagination.items 
    
    anomalies_data = []
    for anomaly_item in anomalies_list: 
        anomalies_data.append({
            "id": anomaly_item.id,
            "user_id": anomaly_item.user_id,
            "timestamp_detected": anomaly_item.timestamp_detected.isoformat(),
            "source_type": anomaly_item.source_type,
            "source_identifier": anomaly_item.source_identifier,
            "image_url": anomaly_item.image_url,
            "detected_class": anomaly_item.detected_class,
            "description": anomaly_item.description,
            "is_reviewed": anomaly_item.is_reviewed
        })

    return jsonify({
        "anomalies": anomalies_data,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200

@app.route('/', methods=['GET'])
def index():
    
    return jsonify({"message": "Welcome to Chii2 API!"}) 


@app.route('/auth/me', methods=['GET'])
@jwt_required() # эндпоинт требует валидный токен
def get_current_user_data():
    current_user_id = get_jwt_identity() 
    user = User.query.get(int(current_user_id)) 

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
    current_user_id = get_jwt_identity() 
    processing_state["user_id_who_started_processing"] = int(current_user_id)

    if processing_state["is_running"]:
        return jsonify({"error": "Processing is already running."}), 400

    # 1. проверяет есть ли файл в запросе
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    # 2. получает объект файла
    file = request.files['file'] 

    # 3. проверяет выбрал ли пользователь файл
    if file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    
    if file and allowed_file(file.filename):
        # --- Все проверки пройдены, можно сохранять и запускать ---
        filename = secure_filename(file.filename) 
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
            thread = threading.Thread(target=run_model_thread, args=(filepath,'file', int(current_user_id)), daemon=True) 
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
        
        return jsonify({"error": f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"}), 400





@app.route('/start_rtsp', methods=['POST'])
@jwt_required()
def start_rtsp():

    current_user_id = get_jwt_identity() 
    processing_state["user_id_who_started_processing"] = int(current_user_id) 

    print(f"User {current_user_id} accessing /start_rtsp")
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
        processing_state["input_path"] = rtsp_url # Сохранить URL
        processing_state["is_running"] = True

        # запуск поток
        thread = threading.Thread(target=run_model_thread, args=(rtsp_url,'rtsp', current_user_id), daemon=True) 
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

            ret, buffer = cv2.imencode('.jpg', frame_to_send)
            if not ret:
                # print("Failed to encode frame")
                continue # пропускает кадр если не удалось закодировать

            frame_bytes = buffer.tobytes()
            # отправка кадра в формате MJPEG
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
    current_user_id = get_jwt_identity()
    print(f"User {current_user_id} accessing /stop")
    if not processing_state["is_running"]:
        return jsonify({"message": "No processing is currently running."}), 400

    processing_state["is_running"] = False 


    return jsonify({"message": "Stop signal sent. Processing will stop soon."})


@app.route('/api/anomalies/<int:anomaly_id>/review', methods=['PUT']) 
@jwt_required()
def mark_anomaly_as_reviewed(anomaly_id):
    current_user_id = get_jwt_identity() 
    anomaly = Anomaly.query.get_or_404(anomaly_id)
    

    anomaly.is_reviewed = True
    db.session.commit()
    return jsonify({"message": f"Anomaly {anomaly_id} marked as reviewed."}), 200


if __name__ == '__main__':
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
    # use_reloader=False ВАЖНО, чтобы не запускать модель дважды в debug режиме!