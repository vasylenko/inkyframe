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

# Pin setup for VSYS_HOLD needed to sleep and wake.
HOLD_VSYS_EN_PIN = 2
hold_vsys_en_pin = Pin(HOLD_VSYS_EN_PIN, Pin.OUT)

# intialise the pcf85063a real time clock chip
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
rtc = PCF85063A(i2c)

led_warn = Pin(6, Pin.OUT)

# set up for the network LED
network_led_pwm = PWM(Pin(7))
network_led_pwm.freq(1000)
network_led_pwm.duty_u16(0)
wlan = network.WLAN(network.STA_IF)


state = {"run": None}
app = None

# set the brightness of the network led
def network_led(brightness):
    brightness = max(0, min(100, brightness))  # clamp to range
    # gamma correct the brightness (gamma 2.8)
    value = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
    network_led_pwm.duty_u16(value)


network_led_timer = Timer(-1)
network_led_pulse_speed_hz = 1


def network_led_callback(t):
    # updates the network led brightness based on a sinusoid seeded by the current time
    brightness = (math.sin(time.ticks_ms() * math.pi * 2 / (1000 / network_led_pulse_speed_hz)) * 40) + 60
    value = int(pow(brightness / 100.0, 2.8) * 65535.0 + 0.5)
    network_led_pwm.duty_u16(value)


# set the network led into pulsing mode
def pulse_network_led(speed_hz=1):
    global network_led_timer, network_led_pulse_speed_hz
    network_led_pulse_speed_hz = speed_hz
    network_led_timer.deinit()
    network_led_timer.init(period=50, mode=Timer.PERIODIC, callback=network_led_callback)


# turn off the network led and disable any pulsing animation that's running
def stop_network_led():
    global network_led_timer
    network_led_timer.deinit()
    network_led_pwm.duty_u16(0)


def sleep(t):
    # Time to have a little nap until the next update
    rtc.clear_timer_flag()
    rtc.set_timer(t, ttp=rtc.TIMER_TICK_1_OVER_60HZ)
    rtc.enable_timer_interrupt(True)

    # Set the HOLD VSYS pin to an input
    # this allows the device to go into sleep mode when on battery power.
    hold_vsys_en_pin.init(Pin.IN)

    # Regular time.sleep for those powering from USB
    time.sleep(60 * t)

def deep_sleep(t):
    time.sleep(1)
    network_disconnect()
    network_led_pwm.duty_u16(0)
    led_warn.off()
    print("Going to deep sleep for {} minutes".format(t))
    inky_frame.sleep_for(t)

# Turns off the button LEDs
def clear_button_leds():
    inky_frame.button_a.led_off()
    inky_frame.button_b.led_off()
    inky_frame.button_c.led_off()
    inky_frame.button_d.led_off()
    inky_frame.button_e.led_off()

def network_connect(SSID, PSK):
    print("Attempting to connect the WiFi network", SSID)
    # Enable the Wireless
    wlan.active(True)
    # Sets the Wireless LED pulsing and attempts to connect to your local network.
    pulse_network_led()
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs
    
    wlan.connect(SSID, PSK)
    # Number of attempts to make before timeout
    max_wait_wifi = 15
    while max_wait_wifi > 0:
        if wlan.isconnected():
            print("Connected to the WiFi network", SSID)
            return True
        max_wait_wifi -= 1
        print('Wait a little...')
        time.sleep(4)            

    stop_network_led()
    # network_led_pwm.duty_u16(30000)
    # led_warn.on()
    print("Failed to connect to the WiFi network", SSID, wlan.status())
    return False     
    # 0   STAT_IDLE -- no connection and no activity,
    # 1   STAT_CONNECTING -- connecting in progress,
    # -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
    # -2  STAT_NO_AP_FOUND -- failed because no access point replied,
    # -1  STAT_CONNECT_FAIL -- failed due to other problems,
    # 3   STAT_GOT_IP -- connection successful.
        

def network_disconnect():
    print("Attempting to disconnect from the WiFi network")
    wlan = network.WLAN(network.STA_IF)
    wlan.disconnect()
    wlan.active(False)
    stop_network_led()
    print("Disconnected from the WiFi network")

# def check_internet_connection():
#     max_wait_internet = 10
#     while max_wait_internet > 0:            
#         s = socket.socket()
#         try: 
#             s.connect(socket.getaddrinfo('8.8.8.8', 53)[0][-1])
#             print("connected to the internet")
#             s.close() 
#             return True             
#         except OSError as e:
#             print("failed to connect to the internet, let's wait a little...", e)
#             time.sleep(3)
#         s.close()    
#         max_wait_internet -= 1    
#     print("giving up, internet is not available")
#     return False

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