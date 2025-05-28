import os
import cv2
import numpy as np
import pandas as pd
from time import time
from threading import Thread
from .ActivityClassifier import *
from .Tracker import *
from .PoseEstimator import *
from .utilities.tools import *
from .utilities.fast_tools import fast_personwise_normalize_all
import Core.utilities.config as cfg


class Main(Thread):
    def __init__(self, 
                 names_of_classes, 
                 max_persons_count, 
                 pose_estimator_params=None, 
                 human_shape=(cfg.BODY_POINTS_NUM, cfg.BODY_POINTS_DIM), 
                 frame_steps=3, 
                 track_limb=cfg.TRACK_LIMB,
                 classifier_neurons=512, 
                 classifier_threshold=0.5,
                 classifier_transform=None,
                 classifier_weights_path=cfg.CLASSIF_MODEL):
        Thread.__init__(self)      
        self.pe = PoseEstimator()
        
        self.tr = Tracker(max_persons_count=max_persons_count, 
                          frame_steps=frame_steps,
                          human_shape=human_shape, 
                          track_limb=track_limb)
        
        self.ac = ActivityClassifier(len(names_of_classes),
                                     input_size=human_shape[0]*human_shape[1],
                                     seq_length=frame_steps,
                                     hidden_layer_size=classifier_neurons,
                                     weights_path=classifier_weights_path)
        self.human_shape = human_shape
        self.names_of_classes = names_of_classes
        self.rect_colors = (len(names_of_classes)-1)*[(255, 255, 255)] + [(0, 0, 255)]
        
        # Для многопоточности
        self.__is_alive = False
        self.__current_frame = None
        self.__classifier_threshold = classifier_threshold
        self.tr.resetState()
        self.__classifier_transform = classifier_transform
        self.__dummy_slots = self.tr.getSlotsCopy() # сюда будут помещаться нормализованные скелеты людей
        self.__output = {'frame': None, 
                         'classes': None,
                         'bboxes': None}
    
    # ----------------- Тест многопоточности -----------------
    
    def setFrame(self, img):
        self.__current_frame = img

    def getOutput(self):
        return self.__output

    def stop(self):
        self.__is_alive = False # после этого цикл будет завершен

    def run(self):
        self.__is_alive = True
        while self.__is_alive:
            if self.__current_frame is None:
                continue
            #start = time() 
            img, persons, rects = self.pe.processFrame(self.__current_frame)
            if persons.shape[1] != 0: # НЕ ТРОГАЙТЕ, ТАК НАДО
                self.tr.distribute(persons[:, :self.human_shape[0], :2]) # отпиливыем вероятности срезом
                rects_, Xs = fast_personwise_normalize_all(self.tr.getPersons(),
                                                      self.__dummy_slots[:self.tr.getPersonsCount()])                
                results = self.ac.predictAction(Xs, 
                                                self.__classifier_threshold, 
                                                self.__classifier_transform)
                classes = results.argmax(dim=1) # выбираем классы для всех людей
                rects = rects_ # ПОДМЕНА НА НАШИ РАМКИ
                for i in range(len(rects)):
                    class_id = classes[i]
                    conf = results[i][class_id]
                    if conf > self.__classifier_threshold:
                        img = drawRectangle(img, 
                                            *rects[i], 
                                            rect_color=self.rect_colors[class_id],
                                            title=f'ID:{i} | {self.names_of_classes[class_id]}: {conf:.2f}')
                    else:
                        img = drawRectangle(img, *rects[i], rect_color=self.rect_colors[-1],
                                            title=f'ID:{i} | {self.names_of_classes[-1]}: {conf:.2f}')
                self.__output['frame'] = img
                self.__output['classes'] = classes
                self.__output['bboxes'] = rects
            else:
                self.__output['frame'] = img
                self.__output['classes'] = None
                self.__output['bboxes'] = None
                self.tr.resetPrevPersonsCount() # если в кадре нет людей, то обнуляем число отслеживаемых людей
            self.tr.timeStep()
            #print('FPS', 1/(time()-start)) 