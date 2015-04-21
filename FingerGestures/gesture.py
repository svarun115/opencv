import cv2
import numpy as np
import math
import xml.etree.ElementTree as ET
import time
from xml.dom import minidom
import unicodedata
import codecs

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def gesture_recog():
    while(cap.isOpened()):
        ret, img = cap.read()
        cv2.rectangle(img,(300,300),(0,0),(0,255,0),0)
        crop_img = img[0:300, 0:300]
        grey = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        value = (35, 35)
        blurred = cv2.GaussianBlur(grey, value, 0)
        _, thresh1 = cv2.threshold(blurred, 127, 255,
                                   cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        cv2.imshow('Thresholded', thresh1)
        contours, hierarchy = cv2.findContours(thresh1.copy(),cv2.RETR_TREE, \
                cv2.CHAIN_APPROX_NONE)
        max_area = -1
        for i in range(len(contours)):
            cnt=contours[i]
            area = cv2.contourArea(cnt)
            if(area>max_area):
                max_area=area
                ci=i
        cnt=contours[ci]
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.rectangle(crop_img,(x,y),(x+w,y+h),(0,0,255),0)
        hull = cv2.convexHull(cnt)
        drawing = np.zeros(crop_img.shape,np.uint8)
        cv2.drawContours(drawing,[cnt],0,(0,255,0),0)
        cv2.drawContours(drawing,[hull],0,(0,0,255),0)
        hull = cv2.convexHull(cnt,returnPoints = False)
        defects = cv2.convexityDefects(cnt,hull)
        count_defects = 0
        cv2.drawContours(thresh1, contours, -1, (0,255,0), 3)
        for i in range(defects.shape[0]):
            s,e,f,d = defects[i,0]
            start = tuple(cnt[s][0])
            end = tuple(cnt[e][0])
            far = tuple(cnt[f][0])
            a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
            c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
            angle = math.acos((b**2 + c**2 - a**2)/(2*b*c)) * 57
            if angle <= 90:
                count_defects += 1
                cv2.circle(crop_img,far,1,[0,0,255],-1)
            cv2.line(crop_img,start,end,[0,255,0],2)
        
        frame = ET.SubElement(video, "frame")
        ET.SubElement(frame, "time").text = time.strftime("%H:%M:%S")
        ET.SubElement(frame, "fingers").text = "{}".format((count_defects+1))
        cv2.imshow('Gesture', img)
        all_img = np.hstack((drawing, crop_img))
        cv2.imshow('Contours', all_img)
        k = cv2.waitKey(10)
        if k == 27:
            break



if __name__=="__main__":
    tree = ET.parse('finger_output.xml')
    root = tree.getroot()
    video = ET.Element("video")
    doc = ET.SubElement(video, "date")
    doc.text = time.strftime("%d/%m/%Y")
    #calling function
    cap = cv2.VideoCapture(0)
    gesture_recog()
    video = ET.fromstring(prettify(video).encode("ascii"))
    root.append(video)
    tree = ET.ElementTree(root)
    tree.write("finger_output.xml")
