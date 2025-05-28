import sys
import os
import cv2 as cv
import time
from datetime import datetime
import argparse
import Chii

g_rtspProtocolPrefix = 'rtsp://'
g_httpProtocolPrefix = 'http://'
g_defaultIPAddrString = '10.2.4.129'
g_defaultRtspPortNumber = 10554
g_defaultHttpPortNumber = 80
g_defaultCameraNumber = 31
g_defaultMonitorNumber = 9

g_imageFilenameSuffix = '.jpg'
g_defaultAccountInfo = 'Face:Face24'

g_ClassLabel_1 = "There are people in the frame."
g_ClassLabel_2 = "ALARM: There are no people in the frame."

# Добавить камеру на монитор
# 'http://10.2.4.129/intellect_core/React?command="MONITOR|9|ADD_SHOW|cam<31>,stream_id<31.1>"'

# Убрать камеру с монитора
# 'http://10.2.4.129/intellect_core/React?command="MONITOR|9|REMOVE|cam<31>,stream_id<31.1>"'

# Set program version
g_ClientVersion = "0.2"

def MergeRTSP_Server_URI(addr, port, camNumber):
    return g_rtspProtocolPrefix + g_defaultAccountInfo + '@' + addr + ':' + str(port) + '/' + str(camNumber)

def MergeHttp_Server_URI(addr, monNumber, camNumber, command):
    return g_httpProtocolPrefix + g_defaultAccountInfo + '@' + addr + ':' + str(g_defaultHttpPortNumber) + '/' + 'intellect_core/React?command=' + \
        '"MONITOR|' + str(monNumber) + '|' + command + '|cam<' + str(camNumber) + '>,stream_id<' + str(camNumber) + '.1>"'

def WriteFrameToFile(cv, imagesFolder, frame):
    filename = imagesFolder + "/image_" + str(datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%f"))  + g_imageFilenameSuffix
    cv.imwrite(filename, frame)    


def main():
    # defaultImagesFolderName = "./Images"
    # defaultOutputVideoPath = "./VideoFromCamera.avi"


    parser = argparse.ArgumentParser(prog = 'Rtsp Client')
    parser.add_argument("-a", "--addr", help = "IPv4 address string to connect to RSTP server (" + g_defaultIPAddrString + " by default)")
    parser.add_argument("-r", "--port", help = "Port number to connect to RSTP server (" + str(g_defaultRtspPortNumber) + " by default)")
    parser.add_argument("-c", "--camera", help = "Camera number to connect to RSTP server (" + str(g_defaultCameraNumber) + " by default)")
    parser.add_argument("-m", "--monitor", help = "Monitor number (" + str(g_defaultMonitorNumber) + " by default)")

    parser.add_argument("-p", "--video", help = "Path name to save a video, MJPEG only (AVI container). No video saved by default")
    parser.add_argument("-i", "--images", help = "Folder name to save JPEG images. No images saved by default")

    parser.add_argument("-v", "--version", action = 'version', version = "%(prog)s " + g_ClientVersion)
    parser.add_argument("-w", "--preview", action = "store_true", help ='preview video (Switched off by default)')


    args = parser.parse_args()

    previewVideo = True
    if not args.preview:
        previewVideo = False

    saveImages = True
    if not args.images:
        saveImages = False
    else:
        imagesFolder = args.images

        if not os.path.exists(imagesFolder):
            os.mkdir(imagesFolder)

    saveVideo = True
    if not args.video:
        saveVideo = False
    else:
        outputVideoFilename = args.video


    if saveVideo == True:
        print(f'Save video to {outputVideoFilename}')
    
    if saveImages == True:
        print(f'Save JPEG-s to {imagesFolder}.')


    if previewVideo != False:
        print(f'Video preview is enabled.\n')
    else:
        print(f'Video preview is disabled.\n')


    monNum = g_defaultMonitorNumber
    if args.monitor is not None:
        monNum = args.monitor

    if not args.addr:
        ipaddr = g_defaultIPAddrString
    else:
        ipaddr = args.addr

    if not args.port:
        portNum = g_defaultRtspPortNumber
    else:
        portNum = args.port

    if not args.camera:
        camNum = g_defaultCameraNumber
    else:
        camNum = args.camera

    rtspServerUri = MergeRTSP_Server_URI(ipaddr, portNum, camNum)
    print(f'Will be connect to {rtspServerUri}.')

    commandClass1 = MergeHttp_Server_URI(ipaddr, monNum, camNum, "REMOVE")
    commandClass2 = MergeHttp_Server_URI(ipaddr, monNum, camNum, "ADD_SHOW")
    

    # Find OpenCV version
    (major_ver, minor_ver, subminor_ver) = (cv.__version__).split('.')
    print(f'There is OpenCV version {major_ver} : {minor_ver} : {subminor_ver} on your localhost.')
    
    #cap = cv.VideoCapture('__Inputs/fall_down_1.mp4') # заглушка для теста
    cap = cv.VideoCapture(rtspServerUri) # вернуть при работе с потоком с камеры!

    # Find frame rate of a webcam
    if int(major_ver) < 3 :
        fps = cap.get(cv.cv.CV_CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
    else :
        fps = cap.get(cv.CAP_PROP_FPS)
        print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    # Find frame size of a webcam
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    print('width, height:', width, height)

    if saveVideo == True:
        out_video = cv.VideoWriter(outputVideoFilename, cv.VideoWriter_fourcc(*'MJPG'), fps, (width, height))

    Chii.messages.append(g_ClassLabel_1)
    Chii.messages.append(g_ClassLabel_2)
    Chii.commands.append(commandClass1)
    Chii.commands.append(commandClass2)
    
    try:
        Chii.m.start() # запускаем отдельный поток
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                if saveImages == True:
                    WriteFrameToFile(cv, imagesFolder, frame)
			
                if saveVideo == True:
                    out_video.write(frame)

                Chii.m.setFrame(frame) # задаем кадр
                #output = Chii.m.getOutput()
                result = Chii.checkFrame()
                if previewVideo == True:
                    img = result['frame'] # получаем обработанный кадр
                    if img is not None: # проверяем, что кадр существует в данным момент
                        cv.imshow("RTSP Preview", img) 
                    cv.waitKey(1)
            else:
                print("Unable to open camera, or stream end!")
                break

    except KeyboardInterrupt:
        print("Keyboard exception caught!\nExiting...") 
    finally:
        cap.release()
        if saveVideo == True:
            out_video.release()
        cv.destroyAllWindows()
        Chii.m.stop() # останавливаем поток
        Chii.m.join() # убеждаемся, что поток завершится до уничтожения главного потока

    print("Disconnected.\nExited.")


if __name__ == "__main__":
    main()