Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> import cv2
... import urllib.request
... import numpy as np
...  
... # Replace the URL with the IP camera's stream URL
... url = 'http://10.212.19.91/cam-hi.jpg'
... cv2.namedWindow("live Cam Testing", cv2.WINDOW_AUTOSIZE)
...  
...  
... # Create a VideoCapture object
... cap = cv2.VideoCapture(url)
...  
... # Check if the IP camera stream is opened successfully
... if not cap.isOpened():
...     print("Failed to open the IP camera stream")
...     exit()
...  
... # Read and display video frames
... while True:
...     # Read a frame from the video stream
...     img_resp=urllib.request.urlopen(url)
...     imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
...     #ret, frame = cap.read()
...     im = cv2.imdecode(imgnp,-1)
...  
...     cv2.imshow('live Cam Testing',im)
...     key=cv2.waitKey(5)
...     if key==ord('q'):
...         break
...     
...  
... cap.release()
