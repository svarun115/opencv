import cv2.cv as cv
from datetime import datetime
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
import unicodedata
import codecs
from collections import Counter
import threading

class MotionDetectorInstantaneous():
    
    def onChange(self, val):
        self.threshold = val
    
    def __init__(self,threshold=5):
    
        self.capture=cv.CaptureFromCAM(0)
        #self.capture = cv.CaptureFromFile(<filename>)
        self.frame = cv.QueryFrame(self.capture) #Take a frame to init recorder
        
        self.frame1gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t-1
        cv.CvtColor(self.frame, self.frame1gray, cv.CV_RGB2GRAY)
        
        self.res = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
        self.frame2gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t
        
        self.width = self.frame.width
        self.height = self.frame.height
        self.nb_pixels = self.width * self.height
        self.threshold = threshold

        
        cv.NamedWindow("Image")
        cv.CreateTrackbar("Detection treshold: ", "Image", self.threshold, 100, self.onChange)
        
   
    def run(self):
        started = time.time()

        while True:
            curframe = cv.QueryFrame(self.capture)
            self.processImage(curframe) #Process the image

            self.curr = datetime.now()
            self.somethingHasMoved()
            cv.ShowImage("Res", self.res)
            
            cv.Copy(self.frame2gray, self.frame1gray)
            c=cv.WaitKey(1) % 0x100
            #Break if user enters 'Esc'.
            if c==27 or c == 10: 
                break          
    
    def processImage(self, frame):
        cv.CvtColor(frame, self.frame2gray, cv.CV_RGB2GRAY)
        
        #Absdiff to get the difference between to the frames
        cv.AbsDiff(self.frame1gray, self.frame2gray, self.res)
        
        #Remove the noise and do the threshold
        cv.Smooth(self.res, self.res, cv.CV_BLUR, 5,5)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_OPEN)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_CLOSE)
        cv.Threshold(self.res, self.res, 10, 255, cv.CV_THRESH_BINARY_INV)

    def somethingHasMoved(self):
        nb=0 #Will hold the number of black pixels
        position = []
        for x in range(self.height): #Iterate over the whole image
            for y in range(self.width):
                if self.res[x,y] == 0.0: #If the pixel is black keep it
                    nb += 1
                    position.append((x,y))#Store the position of the black pixel
        try:
           thread = threading.Thread(target = self.frame_thread,args=(nb,position))
           thread.start()
        except:
           print "Error: unable to start thread" 


    def frame_thread(self,nb,position,):
        avg = (nb*100.0)/self.nb_pixels #Calculate the average of black pixel in the image
        left = 0
        right = 0
        top = 0
        bottom = 0
        sum_hori = 0
        sum_verti = 0
        avg_hori = 0
        avg_verti = 0

        for pixel in position:
            if pixel[1] > 320:
                left += 1
            else:
                right +=1 
            if pixel[0] > 240:
                bottom +=1
            else:
                top +=1
            sum_hori += pixel[1]
            sum_verti+= pixel[0] 

        if len(position)>0:
            avg_hori = sum_hori/len(position)
            avg_verti = sum_verti/len(position)

        if left > right:
            if top > bottom :
                area = 2
                print "Top Left"
            else:
                area = 3
                print "Bottom Left"
        else:
            if top > bottom :
                area = 1
                print "Top Right"
            else:
                area = 4
                print "Bottom Right"

         # Add elements to the XML tree
        frame = ET.SubElement(video, "frame")
        ET.SubElement(frame, "time").text = time.strftime("%H:%M:%S")
        ET.SubElement(frame, "value").text = "{}".format(avg)
        ET.SubElement(frame, "region").text = "{}".format(area)
        ET.SubElement(frame, "avg_hori").text = "{}".format(avg_hori)
        ET.SubElement(frame, "avg_verti").text = "{}".format(avg_verti)


        
def prettify(elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

if __name__=="__main__":
    tree = ET.parse('motion_output.xml')
    root = tree.getroot()
    video = ET.Element("video")
    doc = ET.SubElement(video, "date")
    doc.text = time.strftime("%d/%m/%Y")
    detect = MotionDetectorInstantaneous()
    threshold = ET.SubElement(video, "threshold")
    threshold.text = "{}".format(detect.threshold)
    detect.run()
    video = ET.fromstring(prettify(video).encode("ascii"))
    root.append(video)
    tree = ET.ElementTree(root)
    tree.write("motion_output.xml")
