#!/usr/bin/env python3
########################################################################
# Filename    : UltrasonicRanging.py
# Description : Get distance via UltrasonicRanging sensor
# Author      : www.freenove.com
# modification: 2019/12/28
########################################################################
import RPi.GPIO as GPIO
import time
import requests
from pubnub.pubnub import PubNub, SubscribeListener, SubscribeCallback, PNStatusCategory 
from pubnub.pnconfiguration import PNConfiguration 
from pubnub.exceptions import PubNubException
import pubnub 
import numpy as np

trigPin = 16
echoPin = 18
MAX_DISTANCE = 220          # define the maximum measuring distance, unit: cm
timeOut = MAX_DISTANCE*60   # calculate timeout according to the maximum measuring distance

motorPins = (7, 11, 13, 15)    # define pins connected to four phase ABCD of stepper motor
CCWStep = (0x01,0x02,0x04,0x08) # define power supply order for rotating anticlockwise 
CWStep = (0x08,0x04,0x02,0x01)  # define power supply order for rotating clockwise

def Whoishere(name,count):
    pnconf = PNConfiguration()                                          
    pnconf.publish_key = 'pub-c-09e8cb71-5f5f-4f9d-9826-8ac234ced3b5'    
    pnconf.subscribe_key = 'sub-c-0f975440-22ff-11ec-880d-a65b09ab59bc'  
    pnconf.uuid='CPS14'
    pubnub = PubNub(pnconf)  
    
    channel='CPS14'
    data = {
        'message':  '{} is here. Opening the door. Total number of People inside are {} '.format(name,count) 
    }
    my_listener = SubscribeListener()                          
    pubnub.add_listener(my_listener)                           
    pubnub.subscribe().channels(channel).execute()             
    my_listener.wait_for_connect()                              
    print('connected')                                          
    pubnub.publish().channel(channel).message(data).sync()                                                   
    result = my_listener.wait_for_message_on(channel)       
    print(result.message)
    moveSteps(1,3,512)  # rotating 360 deg clockwise, a total of 2048 steps in a circle, 512 cycles
    time.sleep(5)
    moveSteps(0,3,512)  # rotating 360 deg anticlockwise

def pulseIn(pin,level,timeOut): # obtain pulse time of a pin under timeOut
    t0 = time.time()
    while(GPIO.input(pin) != level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    t0 = time.time()
    while(GPIO.input(pin) == level):
        if((time.time() - t0) > timeOut*0.000001):
            return 0;
    pulseTime = (time.time() - t0)*1000000
    return pulseTime
    
def getSonar():     # get the measurement results of ultrasonic module,with unit: cm
    GPIO.output(trigPin,GPIO.HIGH)      # make trigPin output 10us HIGH level 
    time.sleep(0.00001)     # 10us
    GPIO.output(trigPin,GPIO.LOW) # make trigPin output LOW level 
    pingTime = pulseIn(echoPin,GPIO.HIGH,timeOut)   # read plus time of echoPin
    distance = pingTime * 340.0 / 2.0 / 10000.0     # calculate distance with sound speed 340m/s 
    return distance
    
def setup():
    GPIO.setmode(GPIO.BOARD)      # use PHYSICAL GPIO Numbering
    GPIO.setup(trigPin, GPIO.OUT)   # set trigPin to OUTPUT mode
    GPIO.setup(echoPin, GPIO.IN)    # set echoPin to INPUT mode
    GPIO.setmode(GPIO.BOARD)       # use PHYSICAL GPIO Numbering
    for pin in motorPins:
        GPIO.setup(pin,GPIO.OUT)

def moveOnePeriod(direction,ms):    
    for j in range(0,4,1):      # cycle for power supply order
        for i in range(0,4,1):  # assign to each pin
            if (direction == 1):# power supply order clockwise
                GPIO.output(motorPins[i],((CCWStep[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
            else :              # power supply order anticlockwise
                GPIO.output(motorPins[i],((CWStep[j] == 1<<i) and GPIO.HIGH or GPIO.LOW))
        if(ms<3):       # the delay can not be less than 3ms, otherwise it will exceed speed limit of the motor
            ms = 3
        time.sleep(ms*0.001)
 
# continuous rotation function, the parameter steps specifies the rotation cycles, every four steps is a cycle
def moveSteps(direction, ms, steps):
    for i in range(steps):
        moveOnePeriod(direction, ms)
        
# function used to stop motor
def motorStop():
    for i in range(0,4,1):
        GPIO.output(motorPins[i],GPIO.LOW)
        

def loop():
    count=0
    name=[]
    while(True):
        distance = getSonar() # get distance
        #print ("The distance is : %.2f cm"%(distance))
        if distance >1.5 and distance <= 5:
            URL="http://127.0.0.1:5050/url"
            r=requests.get(url=URL)
            data=r.json()
            if 'result' in data:
                print(data)
                if data['result']=='nothing found':
                    continue
            else:
                if data['preds'] in name:
                    name.remove(data['preds'])
                    count=count-1
                    Whoishere(data['preds'],count)  
                else:
                    name.append(data['preds'])
                    count=count+1
                    Whoishere(data['preds'],count)
                      
 
            print(data)
            print(count)
            
            
        
        
if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    setup()
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        GPIO.cleanup()         # release GPIO resource


