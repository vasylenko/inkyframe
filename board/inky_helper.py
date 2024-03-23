from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
from machine import Pin, SPI, lightsleep
import time
import inky_frame # https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules_py/inky_frame.py
import ujson
from network import WLAN, STA_IF
import os
import sdcard
# import socket
import sys
# import requests

# Pin setup for VSYS_HOLD needed to sleep and wake.
HOLD_VSYS_EN_PIN = 2
hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT)

# intialise the pcf85063a real time clock chip
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
rtc = PCF85063A(i2c)


led_busy = inky_frame.led_busy
led_wifi = inky_frame.led_wifi
button_a = inky_frame.button_a
button_b = inky_frame.button_b
button_c = inky_frame.button_c
button_d = inky_frame.button_d
button_e = inky_frame.button_e

state = {"run": None}
app = None

class InkyHelperError(Exception):
    """Exception raised when there is an error with an inkyhelper function."""
    pass

### SD CARD ###
def init_sd_card():
    try:
        sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
        sd_card = sdcard.SDCard(sd_spi, Pin(22))
        time.sleep(1)
        return sd_card
    except Exception as e:
        raise InkyHelperError(e)

def mount_sd_card(sd_card, sd_card_mount_point):
    try:
        print("Mounting SD card")
        os.mount(sd_card, sd_card_mount_point, readonly=False)
    except:
        print("Failed to mount SD card, perhaps it is already mounted?")
        print("Unmounting SD card")
        os.umount(sd_card_mount_point)
        print("Mounting SD card")
        os.mount(sd_card, sd_card_mount_point, readonly=False)
        print("SD card mounted")
    else:
        print("SD card mounted")

###############
        
#### LEDS #####
# Turns off the button LEDs
def clear_button_leds():
    button_a.led_off()
    button_b.led_off()
    button_c.led_off()
    button_d.led_off()
    button_e.led_off()

def clear_all_leds():
    led_wifi.off()
    led_busy.off()
    clear_button_leds()

def progress_bar_fill(led_letter):
    if led_letter == "a":
        button_a.led_on()
    elif led_letter == "b":
        button_b.led_on()
    elif led_letter == "c":
        button_c.led_on()
    elif led_letter == "d":
        button_d.led_on()
    elif led_letter == "e":
        button_e.led_on()

def progress_bar_clear(led_letter=None):
    if led_letter == "a":
        button_a.led_off()
    elif led_letter == "b":
        button_b.led_off()
    elif led_letter == "c":
        button_c.led_off()
    elif led_letter == "d":
        button_d.led_off()
    elif led_letter == "e":
        button_e.led_off()
    elif led_letter == None:
        clear_button_leds()

def illuminate_button_leds(times=3):
    clear_button_leds()

    leds = [button_a, button_b, button_c, button_d, button_e]

    n = 0
    while n < times:
        for led in leds:
            led.led_on()
            time.sleep(0.1)
            led.led_off()
            time.sleep(0.1)
        n += 1
    clear_button_leds()        

###############

#### SLEEPs ###
def usb_sleep(milliseconds):
    illuminate_button_leds()
    time.sleep(1)
    lightsleep(milliseconds)   

def sleep(minutes):
    inky_frame.sleep_for(minutes)

def battery_sleep(minutes):
    time.sleep(1)
    network_disconnect()
    led_wifi.off()
    led_busy.off()
    print("Going to deep sleep for {} minutes".format(minutes))
    inky_frame.sleep_for(minutes)

###############

### NETWORK ###
def network_connect(SSID, PSK):
    print("Attempting to connect the WiFi network", SSID)
    # Turn on the WiFi LED
    led_wifi.on()
    
    wlan = WLAN(STA_IF)
    wlan.active(True)    
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs

    # Wait for the WiFi to connect
    wlan.connect(SSID, PSK)
    max_wait_wifi = 15
    while max_wait_wifi > 0:
        if wlan.isconnected():
            print("Connected to the WiFi network", SSID)
            time.sleep(5) # sometimes, well... sometimes it just helps to wait a little longer
            return  
        max_wait_wifi -= 1
        time.sleep(5)                 
    led_wifi.off()
    raise InkyHelperError("Failed to connect to the WiFi network", SSID)
    # 0   STAT_IDLE -- no connection and no activity,
    # 1   STAT_CONNECTING -- connecting in progress,
    # -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
    # -2  STAT_NO_AP_FOUND -- failed because no access point replied,
    # -1  STAT_CONNECT_FAIL -- failed due to other problems,
    # 3   STAT_GOT_IP -- connection successful.


def network_disconnect():
    print("Attempting to disconnect from the WiFi network")
    wlan = WLAN(STA_IF)
    wlan.disconnect()
    wlan.active(False)
    led_wifi.off()
    print("Disconnected from the WiFi network")

###############

### APP and STATE ###

def clear_state():
    if file_exists("state.ujson"):
        os.remove("state.ujson")


def save_state(data):
    with open("/state.ujson", "w") as f:
        f.write(ujson.dumps(data))
        f.flush()


def load_state():
    global state
    data = ujson.loads(open("/state.json", "r").read())
    if type(data) is dict:
        state = data


def update_state(running):
    global state
    state['run'] = running
    save_state(state)


def launch_app(app_name):
    global app
    app = __import__(app_name)
    print(app)
    update_state(app_name)

######################## 

def write_debug_msg(filename, message):
    year, month, day, hour, mins, secs, weekday, yearday = time.localtime() 
    with open (filename, "a") as f:
        print("{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}: ".format(year, month, day, hour, mins, secs) + message, file=f)

def show_error(display, text):
    WIDTH, HEIGHT = display.get_bounds()
    print(text)
    display.set_font("bitmap8")
    display.set_pen(1)
    display.clear()
    display.set_pen(0)
    display.text(text, 5, 16, WIDTH, 4)
    display.update()

def stop_execution():
    print("Stopping execution")
    network_disconnect()
    clear_all_leds()
    time.sleep(0.1)
    inky_frame.turn_off()
    sys.exit() # for usb power

def sync_time():
    try:
        print("Synchronizing the time")
        inky_frame.set_time()
        inky_frame.pcf_to_pico_rtc()
        year, month, day, hour, mins, secs, weekday, yearday = time.localtime()   
        print("Time set to: " + "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, mins, secs) + "UTC")  
        return True
    except Exception as e:
        raise InkyHelperError(e)
    
def file_exists(filename):
    try:
        return (os.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False    