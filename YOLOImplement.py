import cv2
import numpy as np
import urllib.request
import time

CAM_URL = 'http://10.66.116.91/cam-lo.jpg'

whT = 320
confThreshold = 0.5
nmsThreshold = 0.3

# Load classes
with open('coco.names', 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Load YOLO
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

            if confidence > 0.5:
                w, h = int(det[2]*wT), int(det[3]*hT)
                x, y = int((det[0]*wT)-w/2), int((det[1]*hT)-h/2)

                bbox.append([x,y,w,h])
                classIds.append(classId)
                confs.append(float(confidence))

    indices = cv2.dnn.NMSBoxes(bbox, confs, 0.5, 0.3)

    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = bbox[i]
            label = classNames[classIds[i]]

            if label == 'person':
                human_detected = True

            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,255), 2)
            cv2.putText(img, f'{label.upper()} {int(confs[i]*100)}%',
                        (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,255), 2)

    return human_detected

# Main loop
while True:
    try:
        img_resp = urllib.request.urlopen(CAM_URL, timeout=2)
        imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
        img = cv2.imdecode(imgnp, -1)

        blob = cv2.dnn.blobFromImage(img, 1/255, (whT, whT), [0,0,0], 1, crop=False)
        net.setInput(blob)

        layerNames = net.getLayerNames()
        outputNames = [layerNames[i-1] for i in net.getUnconnectedOutLayers()]

        outputs = net.forward(outputNames)

        human_detected = findObjects(outputs, img)

        if human_detected:
            cv2.putText(img, "HUMAN DETECTED", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

        cv2.imshow('UGV Live Feed', img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)

cv2.destroyAllWindows()
