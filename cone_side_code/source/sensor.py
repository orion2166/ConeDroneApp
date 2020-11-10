import signal
import sys
#import RPi.GPIO as GPIO disabled for the moment because I'm on my windows machine
import schedule #using the schedule library, by Daniel Bader (Task scheduling)
from smbus2 import SMBus #using smbus2 by Karl-Petter Lindegaard (I2C messaging)
import time
import RPi.GPIO as GPIO
import schedule

SDA_PIN = 3 #I don't think these are strictly necessary but I'm leaving them anyway
SCL_PIN = 5
PIN6_PIN = 16 #pin 6 on the sensor, which is used to check when data is ready. AKA: when a reading is taken!

global dist
################################################################################################################
#configuring
#I can't actually connect to an RPi to test what I'm doing here, so take what currently exists here more as a guide than as word of god...

#this opens an smbus, and closes it at the end of this block.
with SMBus(1) as bus:
    #write_byte_data(address, register, data)
    bus.write_byte_data(0x10, 0x23, 0x00) #set sensor to continuous mode
    bus.write_byte_data(0x10, 0x25, 0x01) #enable lidar sensor. The documentation straight-up lies, it says setting this to *0x00* enables the sensor.
    bus.write_byte_data(0x10, 0x26, 0x04) #set read period to 20ms (I think!)
    bus.write_byte_data(0x10, 0x27, 0x00) #set read period to 20ms
    bus.write_byte_data(0x10, 0x28, 0x00) #disable low power mode
    #minimum amplitude, and minimum/maximum distances work just fine with the default values (100, and .2m and 8m respectively).
    #reads below the amplitude get set to the dummy value, which is 0. IE: uncertain things get sent to the Zero Distance box, which we already don't care about.

GPIO.setmode(GPIO.BCM) #use pin numbers instead of GPIO numbers. This'll probably be changed as this section of code is integrated with the rest.
GPIO.setup(PIN6_PIN, GPIO.IN) #gotta read from
################################################################################################################

#It looks like data is stored as two bytes, in two registers. Add high to low, and you should get the total? I... think? it's unclear.
#    dist = dataArray[ 0] + ( dataArray[ 1] << 8); (taken from a tfluna arduino repo). 8-shift right is 256x.  s
#The main function will need to schedule checkSensor in its main loop, along with periodically checking on it.
#Faster than every 20ms would be awesome, but honestly I'm not terribly picky.
def checkSensor(distance_arr):
    #If the sensor is still updating its registers, wait a sec
    dist = distance_arr[0]
    if not GPIO.input(PIN6_PIN):
        time.sleep(.001)
    
    #TFLuna stores data in 2 registers, one byte each. First is the low half of the result, second is the high half.
    with SMBus(1) as bus:
        dist = bus.read_byte_data(0x10, 0x00)#
        dist = dist + (bus.read_byte_data(0x10, 0x01) << 8)

    #package information to be sent out (gotta do it weird due to how schedule works)
    distance_arr[0] = interpretDistance(dist)
    distance_arr[1] = dist

def interpretDistance(distance):
    return (distance > 195 and distance < 1000) #sensor distance is in cm

################################################################################################################
#schedule setup
#warble = 0
#schedule.every(.008).seconds.do(checkSensor, dist=warble) #I tested, this does in fact work. yay.

################################################################################################################
#TODO figure out how to get this to activate frequently without blocking the main thread too much (run scheduler in its own thread?) (smth about run_continuously?)
#TODO put in indication and stuff
