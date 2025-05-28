import cv2
import numpy as np
import random
import sys
import torch

class Scaler:
    def __init__(self, scale_factor):
        self.scale_f = scale_factor
    
    def __call__(self, img):
        if img is not None:
            return cv2.resize(img, (int(img.shape[1]*self.scale_f), 
                                    int(img.shape[0]*self.scale_f)))       
        return img

class Cropper:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    
    def __call__(self, img):
        if img is not None:
            return img[self.y1:self.y2, self.x1:self.x2]      
        return img


class RandomAmputation2:
    def __init__(self, amp_bnd, prob=0.25):
        self.amp_bnd = amp_bnd
        self.prob = prob
    
    def __call__(self, X):
        if random.random() < self.prob:
            X = X.copy()
            seq_len = X.shape[0]
            what_to_delete = np.ones([X.shape[1]]) #массив единиц
            indices = np.random.choice(what_to_delete.size,
                                       replace=False,
                                       size=random.randint(1, self.amp_bnd))#выбираем точки для зануления
            what_to_delete[indices] = 0 #зануляем конечности
            #размножаем на длину последовательности и второе измерение
            what_to_delete = np.ones([seq_len, *X.shape[1:3]])*what_to_delete.reshape([X.shape[1], 1])
            X *= what_to_delete #занулям конечности
        return X


class RandomNoise:
    def __init__(self, up_bnd=0.02, prob=0.25):
        self.up_bnd = up_bnd
        self.prob = prob
    
    def __call__(self, X):
        if random.random() < self.prob:
            X = X.copy()
            dezitegrator = X > 0
            noise = np.random.uniform(low=-self.up_bnd,
                                      high=self.up_bnd,
                                      size=X.shape[0]*X.shape[1]*X.shape[2])
            X += noise.reshape(X.shape[0], X.shape[1], 2)
            X *= dezitegrator
            X = np.clip(X, 0, 1) #защищиаемся от выходов за пределы единичного квадрата
        return X


class PersonNegativeNormalizer:
    def __init__(self):
        pass

    def __call__(self, X):
        return X.clone() + 1

class ToMotion0:
    def __init__(self, scale=1):
        self.scale = scale
        
    def __call__(self, X):
        if self.scale > 1:
            return (X[1:] - X[:-1]) * self.scale   
        return X[1:] - X[:-1]  

class ToMotion:
    def __init__(self, scale=1):
        self.scale = scale
        
    def __call__(self, X):
        ka = X[1:] > 0
        put = X[:-1] > 0
        kaput = ka*put
        if self.scale > 1:
            return (X[1:] - X[:-1]) * self.scale * kaput
        return (X[1:] - X[:-1]) * kaput

        
class ToImageFASTER:
    def __init__(self, res=72, blur_ksize=None, sigma=None, line_thickness=1):
        self.res = res
        self.pairs = [(0, 1), (0, 16), (0, 15),
                      (1, 2), (1, 5), (1, 8),
                      (2, 3), #(2, 17),
                      (3, 4),
                      (5, 6), #(5, 18),
                      (6, 7),
                      (8, 9), (8, 12),
                      (9, 10),
                      (10, 11),
                      (11, 24), (11, 22),
                      (12, 13),
                      (13, 14),
                      (14, 21), (14, 19),
                      (15, 17),
                      (16, 18),
                      (19, 20),
                      (22, 23)]
        if blur_ksize:
            self.blur_ksize = blur_ksize
        else:
            ksize = self.res // 12 # а скока надо?
            if ksize % 2 == 0:
                ksize -= 1
            self.blur_ksize = (ksize, ksize)
        if sigma:
            self.sigma = sigma
        else:
            self.sigma = round(self.res / 72)
        self.line_thickness = line_thickness #self.res // 72 + 1
    
    def __call__(self, X):
        seq_len = X.shape[0]
        img = np.zeros((seq_len, self.res, self.res), dtype=np.uint8)
        pts = (X*(self.res - 1)).astype(np.int16) # а нужен ли -1? Надо проверить, походу cv2.line похер на это
        for i in range(seq_len):
            for pair in self.pairs:
                pt1 = pts[i][pair[0]]
                pt2 = pts[i][pair[1]]
                if (pt1 * pt2).sum(): # МЫ ПРОФИССИАНАЛЫ!!1
                    cv2.line(img[i], pt1, pt2, 64, thickness=self.line_thickness*4)
                    cv2.line(img[i], pt1, pt2, 128, thickness=self.line_thickness*2)
                    cv2.line(img[i], pt1, pt2, 255, thickness=self.line_thickness)
            img[i] = cv2.GaussianBlur(img[i], ksize=self.blur_ksize, sigmaX=self.sigma, sigmaY=self.sigma)
        return img