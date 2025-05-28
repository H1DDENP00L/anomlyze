import random
import numpy as np
from numba import njit
from .config import BODY_POINTS_NUM


@njit(fastmath=True)
def fast_personwise_normalize(person):
    person_len = person.shape[0]
    left, top = np.inf, np.inf
    right, bottom = 0, 0
    
    for i in range(person_len):      
        if person[i, 0] > 0:
            if person[i, 0] < left:
                left = person[i, 0]
            if person[i, 0] > right:
                right = person[i, 0]
                    
        if person[i, 1] > 0:
            if person[i, 1] < top:
                top = person[i, 1]
            if person[i, 1] > bottom:
                bottom = person[i, 1]       

    if right == 0 or bottom == 0:
        return (0, 0, 0, 0), person
    
    dx, dy = right-left, bottom-top

    if dx == dy == 0: # ЗЕРОБОЙ ДЕТЕКТЕД
        return (0, 0, 0, 0), person*0
   
    for i in range(person_len):        
        person[i, 0] = person[i, 0]-left
        if person[i, 0] < 0:
            person[i, 0] = 0
        else:
            person[i, 0] = person[i, 0]/dx
    
        person[i, 1] = person[i, 1]-top
        if person[i, 1] < 0:
            person[i, 1] = 0
        else:
            person[i, 1] = person[i, 1]/dy           
        
    return (left, top, right, bottom), person    


@njit(fastmath=True)
def fast_personwise_normalize_all(slots, output):
    person_len = slots.shape[2]
    rects = []
    for k in range(slots.shape[0]):        
        for j in range(slots.shape[1]):
            person = slots[k, j]
            out_person = output[k, j]
            left, top = np.inf, np.inf
            right, bottom = 0, 0
            
            for i in range(person_len):      
                if person[i, 0] > 0: # нужно для отрисовки прямоугольника для человека, у которого есть хотя бы 1 нулевая конечность
                    if person[i, 0] < left:
                        left = person[i, 0]
                    if person[i, 0] > right:
                        right = person[i, 0]
                            
                if person[i, 1] > 0:
                    if person[i, 1] < top:
                        top = person[i, 1]
                    if person[i, 1] > bottom:
                        bottom = person[i, 1]       
        
            if (right == 0 or bottom == 0) or (right == left or bottom == top):
                # ЛОВИМ ЗЕРОБОЕВ
                continue

            dx, dy = right-left, bottom-top
                            
            for i in range(person_len):        
                out_person[i, 0] = person[i, 0]-left
                if out_person[i, 0] < 0:
                    out_person[i, 0] = 0
                else:
                    out_person[i, 0] = out_person[i, 0]/dx
                
                out_person[i, 1] = person[i, 1]-top
                if out_person[i, 1] < 0:
                    out_person[i, 1] = 0
                else:
                    out_person[i, 1] = out_person[i, 1]/dy  
                    
        rects.append((left, top, right, bottom))
            
    return rects, output     


@njit(fastmath=True)
def fast_distribute(new_humans, slots, matrix, frame_steps, prev_persons_count, track_limb):    
    cur_count = max(prev_persons_count[0], new_humans.shape[0]) # если текущих кандидатов больше, то берем их, 
                                                                # иначе берем максимальное число раннее отслеживаемых людей
    
    # формируем матрицу оценок     
    est_mtrx = matrix[:min((slots.shape[0], cur_count)), # убеждаемся, что число отслеживаемых людей не превысит число слотов
                      :min(slots.shape[0], new_humans.shape[0])] # аналогично для кандидатов
    
    prev_persons_count[0] = cur_count # запоминаем новое максимальное число отслеживаемых людей
    
    # заполняем матрицу оценок
    for i in range(est_mtrx.shape[0]): # перебираем людей в слотах
        for j in range(est_mtrx.shape[1]): # перебираем кандидатов
            # slots[i, frame_steps]) - i-й человек с предпоследнего кадра              
            abs_diff = (np.abs(new_humans[j, track_limb[0]] - slots[i, frame_steps, track_limb[0]]) +
                        np.abs(new_humans[j, track_limb[1]] - slots[i, frame_steps, track_limb[1]]))
            est_mtrx[i, j] = abs_diff[0] + abs_diff[1]
      
    # выполняем распределение кандидатов на основе их оценок
    for i in range(min(est_mtrx.shape)): # кол-во слотов или кол-во кандидатов, в зависимости от того, что меньше
        idx = np.argmin(est_mtrx) # положение глобального минимума в матрице est_mtrx
        row, col = (idx // est_mtrx.shape[1]), (idx % est_mtrx.shape[1]) # строка и столбец глобального минимума
        #print(row, col)
        slots[row, -1] = new_humans[col] # помещаем человека col на последний кадр в слот row
        est_mtrx[row, :] = np.inf # затираем строку row
        est_mtrx[:, col] = np.inf # затираем столбец col 


# прогрев
fast_distribute(new_humans=np.zeros((1, BODY_POINTS_NUM, 3), dtype=np.float32)[:, :, :2], 
                slots=np.zeros((1, 1, BODY_POINTS_NUM, 2), dtype=np.float32, order='C'), 
                matrix=np.zeros((1, 1), dtype=np.float32, order='C'),
                frame_steps=np.uint16(1), 
                prev_persons_count=np.array([1]), 
                track_limb=np.uint8((1, 8)))

fast_personwise_normalize(person=np.zeros((BODY_POINTS_NUM, 2), dtype=np.float32, order='C'))

fast_personwise_normalize_all(slots=np.zeros((1, 1, BODY_POINTS_NUM, 2), dtype=np.float32, order='C'),
                              output=np.zeros((1, 1, BODY_POINTS_NUM, 2), dtype=np.float32, order='C'))