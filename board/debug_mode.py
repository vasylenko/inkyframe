import inky_helper as ih
import os
import sdcard 
from machine import Pin, SPI
import inky_helper as ih
import time
import sys


print("debug mode")

device_name = "/sdcard"

sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
sd = sdcard.SDCard(sd_spi, Pin(22))




try:
    os.mount(sd, device_name, readonly=False)
except:
    os.umount(device_name)
    os.mount(sd, device_name, readonly=False)
    # print("failed to mount sd card")

print(os.listdir(device_name))

if not device_name in sys.path:
    print(device_name + " is not in sys.path")
    print(sys.path)
    sys.path.append(device_name)
    print(sys.path)


print(os.listdir())
