from pimoroni_i2c import PimoroniI2C
from pcf85063a import PCF85063A
import math
from machine import Pin, PWM, Timer
import time
import inky_frame # https://github.com/pimoroni/pimoroni-pico/blob/main/micropython/modules_py/inky_frame.py
import json
import network
import os
# import socket
import sys
import requests

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

state = {"run": None}
app = None


# turn off the network led and disable any pulsing animation that's running
def stop_network_led():
    led_wifi.off()

def battery_sleep(minutes):
    time.sleep(1)
    network_disconnect()
    stop_network_led()
    led_busy.off()
    print("Going to deep sleep for {} minutes".format(minutes))
    inky_frame.sleep_for(minutes)

def usb_sleep(minutes):
    print("Going to sleep for {} minutes".format(minutes))
    rtc.clear_timer_flag()
    rtc.set_timer(minutes, ttp=rtc.TIMER_TICK_1_OVER_60HZ)
    rtc.enable_timer_interrupt(True)
    stop_network_led()
    time.sleep(minutes*60)

# Turns off the button LEDs
def clear_button_leds():
    inky_frame.button_a.led_off()
    inky_frame.button_b.led_off()
    inky_frame.button_c.led_off()
    inky_frame.button_d.led_off()
    inky_frame.button_e.led_off()

def network_connect(SSID, PSK):
    print("Attempting to connect the WiFi network", SSID)
    # Turn on the WiFi LED
    led_wifi.on()
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)    
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs

    # Wait for the WiFi to connect
    wlan.connect(SSID, PSK)
    max_wait_wifi = 15
    while max_wait_wifi > 0:
        time.sleep(2)
        if wlan.isconnected():
            print("Connected to the WiFi network", SSID)
            time.sleep(5) # sometimes, well... sometimes it just helps to wait a little longer
            max_wait_internet = 3
            while max_wait_internet > 0:
                if validate_wifi_connection():
                    print("Internet connection validated")
                    led_wifi.off()
                    return True
                max_wait_internet -= 1
                print("Waiting for the internet connection...")
                time.sleep(4)
            if max_wait_internet == 0:
                max_wait_wifi -= 1
                print('Wait a little...')                    
    print("Failed to connect to the WiFi network", SSID, wlan.status())
    led_wifi.off()
    return False     
    # 0   STAT_IDLE -- no connection and no activity,
    # 1   STAT_CONNECTING -- connecting in progress,
    # -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
    # -2  STAT_NO_AP_FOUND -- failed because no access point replied,
    # -1  STAT_CONNECT_FAIL -- failed due to other problems,
    # 3   STAT_GOT_IP -- connection successful.

# function that validates the wifi connection by making a request to ifconfig.me/ip and printing the received IP address
def validate_wifi_connection():
    try:
        print("Validating the WiFi connection")
        ip = requests.get("https://ifconfig.me/ip").text
        print("IP address:", ip)
        return True
    except Exception as e:
        print("Failed to validate the WiFi connection", e)
        return False


def network_disconnect():
    print("Attempting to disconnect from the WiFi network")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
    stop_network_led()
    print("Disconnected from the WiFi network")


def stop_execution():
    print("Stopping execution")
    network_disconnect()
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
        print("Failed to synchronize the time", e)
        return False
    
def file_exists(filename):
    try:
        return (os.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False


def clear_state():
    if file_exists("state.json"):
        os.remove("state.json")


def save_state(data):
    with open("/state.json", "w") as f:
        f.write(json.dumps(data))
        f.flush()


def load_state():
    global state
    data = json.loads(open("/state.json", "r").read())
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