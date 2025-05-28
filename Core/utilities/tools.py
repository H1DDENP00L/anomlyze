import cv2


def drawRectangle(image, left, top, right, bottom, title=None,
                  rect_color=(255, 255, 255), text_color=(0, 0, 0)):
        
        if right == 0 or bottom == 0:
            return image
        
        dx = (right - left) * 0.05
        dy = (bottom - top) * 0.05
        right += dx
        left -= dx
        top -= dy
        bottom += dy
        
        cv2.rectangle(img=image, pt1=(int(left), int(top)), pt2=(int(right), int(bottom)),
                      color=rect_color, thickness=2)
        
        if title:     
            cv2.rectangle(img=image, pt1=(int(left), int(top-30)), pt2=(int(left+len(title)*9), int(top)),
                          color=rect_color, thickness=-1)
            cv2.putText(img=image, text=title, org=(int(left+5), int(top-10)),
                        fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5,
                        color=text_color, thickness=1)
        return image