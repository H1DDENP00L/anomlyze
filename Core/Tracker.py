import numpy as np
from .utilities.fast_tools import fast_distribute
class Tracker:
    def __init__(self, max_persons_count, frame_steps, track_limb, human_shape):
        self.__slots = np.zeros((max_persons_count, frame_steps) + human_shape, dtype=np.float32)        
        self.__track_limb = np.uint8(track_limb)

        # быстрее обращаться по ссылкам на срезы, чем брать срезы при помощи литералов на месте
        self.__no_last_frame = self.__slots[:, :frame_steps-1]
        
        if frame_steps > 1: # если кадров 2+, то можно взять часть без первого кадра
            self.__pre_last_frame_idx = np.uint16(frame_steps-2)
            self.__no_first_frame = self.__slots[:, 1:] # разделение
        else: # если кадр 1, то нельзя
            self.__pre_last_frame_idx = np.uint16(0)
            self.__no_first_frame = self.__no_last_frame
        
        self.__last_frame = self.__slots[:, -1]       
        self.__prev_max_persons_count = np.array([0]) # для возможности менять значение по ссылке
        
        self.__global_mtrx = np.full((max_persons_count, max_persons_count), fill_value=np.inf, dtype=np.float32)
        
    # значительно быстрее через numba.njit
    def distribute(self, new_humans): 
        fast_distribute(new_humans, self.__slots, self.__global_mtrx, 
                        self.__pre_last_frame_idx, self.__prev_max_persons_count, self.__track_limb)
        
    # через numpy быстрее, чем через numba.njit (особенно при увеличении размера) 
    def timeStep(self):
        # выполняем смещение кадров во времени
        # переносим 2 последних кадра на первые 2 позиции
        self.__no_last_frame[:self.__prev_max_persons_count[0]] = self.__no_first_frame[:self.__prev_max_persons_count[0]] 
        self.__last_frame[:self.__prev_max_persons_count[0]] = 0. # последний кадр затирем


    def resetState(self):
        self.__slots[:] = 0.
        self.__global_mtrx[:] = np.inf
        self.resetPrevPersonsCount()


    def resetPrevPersonsCount(self):
        self.__prev_max_persons_count[0] = 0 


    def getPersons(self):
        return self.__slots[:self.__prev_max_persons_count[0]]


    def getPersonsCount(self):
        return self.__prev_max_persons_count[0]


    def getSlotsCopy(self):
        return self.__slots.copy()