import os 



CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.abspath(os.path.join(CONFIG_DIR, '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(CORE_DIR, '..')) # Корень проекта Chii2

# --- Теперь используем PROJECT_ROOT для построения путей ---
WEIGHTS_DIR = os.path.join(PROJECT_ROOT, '__Weights')
INPUTS_DIR = os.path.join(PROJECT_ROOT, '__Inputs')

BODY_POINTS_NUM = 17
BODY_POINTS_DIM = 2
TRACK_LIMB = (11, 12)

CLASSIF_MODEL_FILENAME = 'NS0.03_1_AM15_0.75_Q60_N512_FullyEncodedGura_VL97.0_TR99.84.pt'
CLASSIF_MODEL = os.path.join(WEIGHTS_DIR, CLASSIF_MODEL_FILENAME)

SEQ_LENGTH = 60
MAX_PERSON_COUNT = 15
CLASSES = ['squat', 'walk', 'sit', 'stand', 'unknown']
CLASSIFIER_NEURONS = 512

# Путь для Chii.py (тоже лучше сделать абсолютным)
DEFAULT_INPUT_FILENAME = 'check.mp4'
INPUT_PATH = os.path.join(INPUTS_DIR, DEFAULT_INPUT_FILENAME) # Путь по умолчанию для Chii.py

# Путь к модели YOLO (тоже лучше сделать абсолютным или относительно корня)
YOLO_MODEL_FILENAME = 'yolo11n-pose.pt' # Убедись, что имя правильное! Может yolov8n-pose.pt?
YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, YOLO_MODEL_FILENAME) # Ищем модель в корне проекта


BODY25 = [
    'Nose_x', 'Nose_y',
           
    'Chest_x', 'Chest_y',
            
    'R_Sho_x', 'R_Sho_y',
    'R_Elb_x', 'R_Elb_y',
    'R_Wr_x', 'R_Wr_y',
            
    'L_Sho_x', 'L_Sho_y',
    'L_Elb_x', 'L_Elb_y',
    'L_Wr_x', 'L_Wr_y',
            
    'Groin_x', 'Groin_y',
            
    'R_Hip_x', 'R_Hip_y',
    'R_Kn_x', 'R_Kn_y',
    'R_An_x', 'R_An_y',
            
    'L_Hip_x', 'L_Hip_y',
    'L_Kn_x', 'L_Kn_y', 
    'L_An_x', 'L_An_y',
            
    'R_Eye_x', 'R_Eye_y',            
    'L_Eye_x', 'L_Eye_y',
    
    'R_Ear_x', 'R_Ear_y',
    'L_Ear_x', 'L_Ear_y', 
            
    'L_Sol_x', 'L_Sol_y',
    'L_Toe_x', 'L_Toe_y',
    'L_Heel_x', 'L_Heel_y',
    
    'R_Sol_x', 'R_Sol_y',
    'R_Toe_x', 'R_Toe_y',
    'R_Heel_x', 'R_Heel_y',
            
    'Class'
]

YOLO17 = [
    'Nose_x', 'Nose_y',
    
    'Left_Eye_x', 'Left_Eye_y',
    'Right_Eye_x', 'Right_Eye_y',
    
    'Left_Ear_x', 'Left_Ear_y',
    'Right_Ear_x', 'Right_Ear_y',
    
    'Left_Shoulder_x', 'Left_Shoulder_y',
    'Right_Shoulder_x', 'Right_Shoulder_y',
    
    'Left_Elbow_x', 'Left_Elbow_y',
    'Right_Elbow_x', 'Right_Elbow_y',
    
    'Left_Wrist_x', 'Left_Wrist_y',
    'Right_Wrist_x', 'Right_Wrist_y',
    
    'Left_Hip_x', 'Left_Hip_y',
    'Right_Hip_x', 'Right_Hip_y',
    
    'Left_Knee_x', 'Left_Knee_y',
    'Right_Knee_x', 'Right_Knee_y',
    
    'Left_Ankle_x', 'Left_Ankle_y',
    'Right_Ankle_x', 'Right_Ankle_y',
    
    'Class'
]