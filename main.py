#!/usr/bin/env python
import time
import logging
import os
logging.basicConfig(level=logging.DEBUG, format= '%(asctime)s\t%(message)s')
import cv2

HORIZONTAL_RES=500 #actual frame can be between HORIZONTAL_RES/2 and HORIZONTAL_RES
CAPTURE_DEVICE= 0
CAPTURE_INTERVAL= 5 #seconds
RETRY_N = 2   #number of times to retry after changing state to make sure it is permanent
RETRY_CAPTURE_INTERVAL= 0.5
LOCK_COMMAND="/usr/bin/xscreensaver-command -lock"

classifier = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
assert not classifier.empty()
webcam = cv2.VideoCapture()

def get_frame():
    '''get the next frame. This function is designed for non-continuous grabbing'''
    webcam.open( CAPTURE_DEVICE )
    assert webcam.isOpened()
    rval, frame = webcam.read()
    webcam.release()
    assert rval
    return frame

def calculate_mini_frame_size():
    frame= get_frame()
    frame_size= frame.shape
    #print "frame_size:", frame_size
    downscale_factor= int( frame_size[1] / HORIZONTAL_RES) 
    #print "downscale_factor:",downscale_factor
    miniframe_size= (frame_size[1]/downscale_factor,frame_size[0]/downscale_factor)
    #print "miniframe_size:", miniframe_size
    return miniframe_size


def face_detected( frame_size ):
    frame= get_frame()
    miniframe = cv2.resize(frame, frame_size)
    faces = classifier.detectMultiScale(miniframe)
    detected= len(faces)>0
    #cv2.imshow("face", miniframe)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    print faces
    return detected

def new_face_detection_state( state ):
    logging.info( "new state: {0}".format(state) )
    if not state:
        os.system(LOCK_COMMAND)

fs= calculate_mini_frame_size()
last_hard_state= True          #last state we are sure of (after checking for flapping)
last_soft_state= True          #last state detected
last_soft_state_count= 0       #duration of last_soft_state

last_detected= True
logging.info( "started" )

while True:
    cycle_start_time= time.time()
    try:
        detected= face_detected( fs )
    except Exception as e:
        logging.warn("Failed to capture frame: "+str(e))
        time.sleep(CAPTURE_INTERVAL)
        continue
    if detected!=last_soft_state:
        logging.debug("soft state changed to {0}".format(detected))
        last_soft_state= detected
        last_soft_state_count=1
    else:
        last_soft_state_count+=1
        if last_soft_state != last_hard_state:
            if last_soft_state_count > RETRY_N:
                new_face_detection_state(detected)
                last_hard_state= last_soft_state
    cycle_end_time= time.time()
    cycle_duration= cycle_end_time - cycle_start_time
    if last_hard_state==last_soft_state: 
        time.sleep(max(0,CAPTURE_INTERVAL-cycle_duration))
    else:
        time.sleep(max(0,RETRY_CAPTURE_INTERVAL-cycle_duration))

