from ultralytics import YOLO
import torch
from Core.utilities import config as cfg # Импортируем конфиг



class PoseEstimator():
    def __init__(self, net =cfg.YOLO_MODEL_PATH):        
        self.net = YOLO(net)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"PoseEstimator using device: {self.device}") # Добавим лог
        
        try:
             self.net.to(self.device)
             print(f"YOLO model '{net}' loaded successfully on {self.device}")
        except Exception as e:
             print(f"Error moving YOLO model to {self.device}: {e}")
             raise # Перевыбрасываем ошибку, чтобы увидеть ее выше
        

    def to(self, device):
        self.net.to(device)

    
    def processFrame(self, frame):
        result = self.net([frame], verbose = False)
        return (result[0].plot(boxes=False, probs=False, labels=False), 
                result[0].keypoints.data.cpu().numpy(), 
                result[0].boxes.data.cpu().numpy()[:,:4])
