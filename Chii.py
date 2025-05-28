import torch
import cv2 as cv
from Core import Main, Nets
import Core.utilities.config as cfg

messages = []
commands = []

m = Main(max_persons_count=cfg.MAX_PERSON_COUNT,
         names_of_classes=cfg.CLASSES,
         frame_steps=cfg.SEQ_LENGTH,
         classifier_neurons=cfg.CLASSIFIER_NEURONS)

#m.start() # ОСТОРОЖНО, МОЖНО ПОВИСНУТЬ ПОСЛЕ ИМПОРТА, ЕСЛИ В ГЛАВНОМ ФАЙЛЕ ЧТО-ТО ПОЙДЕТ НЕ ТАК

def checkFrame():
    result = m.getOutput()
    #print(result['classes'], result['bboxes'])
    if result['bboxes']:
        print(messages[0])
        print("Command to send: ", commands[0])
    else:
        print(messages[1])
        print("Command to send: ", commands[1])
    return result

def mainloop():
    cap = cv.VideoCapture(cfg.INPUT_PATH)   
    # Find frame size of a webcam
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    print('width, height:', width, height)
    previewVideo = True

    try:
        m.start() # запускаем отдельный поток
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                m.setFrame(frame)
                img = m.getOutput()['frame']
                if previewVideo == True:
                    img = m.getOutput()['frame']
                    if img is not None:
                        cv.imshow("RTSP Preview", img)#frame)
                    if cv.waitKey(1) == 27: # ESC
                        raise KeyboardInterrupt # соблюдаем интерфейсы

            else:
                print("Unable to open camera, or stream end!")
                break
    except KeyboardInterrupt:
        print("Keyboard exception caught!\nExiting...") 
    finally:
        m.stop()
        m.join()
        cap.release()
        cv.destroyAllWindows()

if __name__ == '__main__': # ДЛЯ ТЕСТА
    mainloop()