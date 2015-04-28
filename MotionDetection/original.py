import cv2.cv as cv
from datetime import datetime
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
import unicodedata
import codecs

class MotionDetectorInstantaneous():
    
    def onChange(self, val): #callback when the user change the detection threshold
        self.threshold = val
    
    def __init__(self,threshold=5, doRecord=True, showWindows=True):
        self.writer = None
        self.font = None
        self.doRecord=doRecord #Either or not record the moving object
        self.show = showWindows #Either or not show the 2 windows
        self.frame = None
    
        self.capture=cv.CaptureFromCAM(0)
        #self.capture = cv.CaptureFromFile(<filename>)
        self.frame = cv.QueryFrame(self.capture) #Take a frame to init recorder
        if doRecord:
            self.initRecorder()
        
        self.frame1gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t-1
        cv.CvtColor(self.frame, self.frame1gray, cv.CV_RGB2GRAY)
        
        #Will hold the thresholded result
        self.res = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)
        
        self.frame2gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U) #Gray frame at t
        
        self.width = self.frame.width
        self.height = self.frame.height
        self.nb_pixels = self.width * self.height
        self.threshold = threshold
        self.isRecording = False
        self.trigger_time = 0 #Hold timestamp of the last detection
        
        if showWindows:
            cv.NamedWindow("Image")
            cv.CreateTrackbar("Detection treshold: ", "Image", self.threshold, 100, self.onChange)
        
    def initRecorder(self): #Create the recorder
        codec = cv.CV_FOURCC('M', 'J', 'P', 'G') #('W', 'M', 'V', '2')
        self.writer=cv.CreateVideoWriter(datetime.now().strftime("%b-%d_%H_%M_%S")+".mp4", codec, 5, cv.GetSize(self.frame), 1)
        self.font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 2, 8) #Creates a font

    def run(self):
        started = time.time()
        while True:
            
            curframe = cv.QueryFrame(self.capture)
            #cv.Resize(src, dst, interpolation=CV_INTER_LINEAR)

            instant = time.time() #Get timestamp o the frame
            self.processImage(curframe) #Process the image
            cv.WriteFrame(self.writer, curframe) 
            if not self.isRecording:
                if self.somethingHasMoved():
                    self.trigger_time = instant #Update the trigger_time
                    if instant > started +5:#Wait 5 second after the webcam start for luminosity adjusting etc..
                      #  print datetime.now().strftime("%b %d, %H:%M:%S"), "Something is moving !"
                        if self.doRecord: #set isRecording=True only if we record a video
                            self.isRecording = True
            else:
                if instant >= self.trigger_time +10: #Record during 10 seconds
                  #  print datetime.now().strftime("%b %d, %H:%M:%S"), "Stop recording"
                    self.isRecording = False
                else:
                    cv.PutText(curframe,datetime.now().strftime("%b %d, %H:%M:%S"), (25,30),self.font, 0) #Put date on the frame
                    cv.WriteFrame(self.writer, curframe) #Write the frame
            
            if self.show:
                cv.ShowImage("Image", curframe)
                cv.ShowImage("Res", self.res)
            
            cv.Copy(self.frame2gray, self.frame1gray)
            c=cv.WaitKey(1) % 0x100
            if c==27 or c == 10: #Break if user enters 'Esc'.
                break         

        self.writer = None   
    
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

        for x in range(self.height): #Iterate the hole image
            for y in range(self.width):
                if self.res[x,y] == 0.0: #If the pixel is black keep it
                    nb += 1
        avg = (nb*100.0)/self.nb_pixels #Calculate the average of black pixel in the image

#       Add elements to the XML tree
        frame = ET.SubElement(video, "frame")
        ET.SubElement(frame, "time").text = time.strftime("%H:%M:%S")
        ET.SubElement(frame, "value").text = "{}".format(avg)

        if avg > self.threshold:#If over the ceiling trigger the alarm
            return True
        else:
            return False
        
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
    detect = MotionDetectorInstantaneous(doRecord=True)
    threshold = ET.SubElement(video, "threshold")
    threshold.text = "{}".format(detect.threshold)
    detect.run()
    video = ET.fromstring(prettify(video).encode("ascii"))
    root.append(video)
    tree = ET.ElementTree(root)
    tree.write("motion_output.xml")
