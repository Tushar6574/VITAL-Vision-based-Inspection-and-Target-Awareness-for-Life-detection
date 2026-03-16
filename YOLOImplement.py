import cv2
import numpy as np
import urllib.request

url = 'http://10.212.19.91/cam-hi.jpg'

whT = 320
confThreshold = 0.5
nmsThreshold = 0.3

# Load class names
with open('coco.names','rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Load YOLO
net = cv2.dnn.readNetFromDarknet('yolov3.cfg','yolov3.weights')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObject(outputs,img):
    hT,wT,cT = img.shape
    bbox=[]
    classIds=[]
    confs=[]

    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]

            if confidence > confThreshold:
                w,h = int(det[2]*wT), int(det[3]*hT)
                x,y = int(det[0]*wT - w/2), int(det[1]*hT - h/2)

                bbox.append([x,y,w,h])
                classIds.append(classId)
                confs.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(bbox,confs,confThreshold,nmsThreshold)

    for i in indices.flatten():
        x,y,w,h = bbox[i]

        label = classNames[classIds[i]]
        conf = confs[i]

        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,255),2)
        cv2.putText(img,f'{label.upper()} {int(conf*100)}%',
                    (x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,0,255),2)

while True:

    img_resp = urllib.request.urlopen(url)
    imgnp = np.array(bytearray(img_resp.read()),dtype=np.uint8)
    img = cv2.imdecode(imgnp,-1)

    blob = cv2.dnn.blobFromImage(img,1/255,(whT,whT),[0,0,0],1,crop=False)
    net.setInput(blob)

    layerNames = net.getLayerNames()
    outputNames = [layerNames[i-1] for i in net.getUnconnectedOutLayers().flatten()]

    outputs = net.forward(outputNames)

    findObject(outputs,img)

    cv2.imshow('UGV Vision System',img)

    if cv2.waitKey(1)==ord('q'):
        break

cv2.destroyAllWindows()
