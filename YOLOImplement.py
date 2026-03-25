import cv2
import numpy as np
import urllib.request
import time
import requests  

ROVER_IP = '10.66.116.91' 
CAM_URL = f'http://{ROVER_IP}/cam-lo.jpg'
CONTROL_URL = f'http://{ROVER_IP}/victim'

whT = 320
confThreshold = 0.5
nmsThreshold = 0.3

# Load YOLO
with open('coco.names', 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

net = cv2.dnn.readNetFromDarknet('yolov3.cfg', 'yolov3.weights')
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObjects(outputs, img):
    hT, wT, cT = img.shape
    bbox, classIds, confs = [], [], []
    human_detected = False

    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]

            if confidence > confThreshold:
                w, h = int(det[2]*wT), int(det[3]*hT)
                x, y = int((det[0]*wT)-w/2), int((det[1]*hT)-h/2)
                bbox.append([x,y,w,h])
                classIds.append(classId)
                confs.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)

    if len(indices) > 0:
        for i in indices.flatten():
            label = classNames[classIds[i]]
            if label == 'person':
                human_detected = True
                x, y, w, h = bbox[i]
                cv2.rectangle(img, (x,y), (x+w,y+h), (0,0,255), 3) # Red box for humans
                cv2.putText(img, f'VICTIM {int(confs[i]*100)}%',
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
    
    return human_detected

last_alert_time = 0

while True:
    try:
        # 1. Get Frame
        img_resp = urllib.request.urlopen(CAM_URL, timeout=2)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgnp, -1)

        # 2. Run YOLO
        blob = cv2.dnn.blobFromImage(img, 1/255, (whT, whT), [0,0,0], 1, crop=False)
        net.setInput(blob)
        layerNames = net.getLayerNames()
        outputNames = [layerNames[i-1] for i in net.getUnconnectedOutLayers()]
        outputs = net.forward(outputNames)

        # 3. Detect Humans
        is_human = findObjects(outputs, img)

        if is_human:
            # 4. ALERT THE ROVER
            # We use a 2-second cooldown so we don't spam the ESP32 with 30 requests per second
            if time.time() - last_alert_time > 2:
                print("!!! HUMAN DETECTED - SENDING STOP SIGNAL !!!")
                try:
                    requests.get(CONTROL_URL, timeout=0.5)
                    last_alert_time = time.time()
                except Exception as e:
                    print("Failed to send alert to Rover:", e)

        cv2.imshow('UGV Disaster Management Feed', img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print("Error in Stream/Processing:", e)
        time.sleep(1)

cv2.destroyAllWindows()
