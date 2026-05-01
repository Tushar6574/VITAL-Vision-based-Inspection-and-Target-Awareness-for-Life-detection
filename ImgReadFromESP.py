import cv2
import urllib.request
import numpy as np
 
url = 'http://10.66.116.91/cam-lo.jpg'
cv2.namedWindow("live Cam Testing", cv2.WINDOW_AUTOSIZE)
 
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Failed to open the IP camera stream")
    exit()
 
while True:

    img_resp=urllib.request.urlopen(url)
    imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)

    im = cv2.imdecode(imgnp,-1)
 
    cv2.imshow('live Cam Testing',im)
    key=cv2.waitKey(5)
    if key==ord('q'):
        break
    
 
cap.release()
cv2.destroyAllWindows()
