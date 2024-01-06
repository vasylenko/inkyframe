import gc
import time
from machine import reset, Pin, SPI
import inky_helper as ih
import os
import sdcard 
import sys
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"


# A short delay to give USB chance to initialise
time.sleep(0.5)

# Setup for the display.
display = PicoGraphics(DISPLAY)
WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

# Setup for SD card
sdcard_mount_point = "/sdcard"
sd_spi, sd = None, None

def show_error(text):
    print(text)
    display.set_font("bitmap8")
    display.set_pen(1)
    display.clear()
    display.set_pen(0)
    display.text(text, 5, 16, WIDTH, 4)
    display.update()


def launcher():
    y_offset = 35

    # Draws the menu
    display.set_pen(1)
    display.clear()
    display.set_pen(0)

    # display.set_pen(display.create_pen(255, 100, 200))
    display.set_pen(2)
    display.rectangle(0, 0, WIDTH, 50)
    display.set_pen(1)
    title = "Launcher"
    title_len = display.measure_text(title, 4) // 2
    display.text(title, (WIDTH // 2 - title_len), 10, WIDTH, 4)

    display.set_pen(display.create_pen(5, 147, 162))
    display.rectangle(30, HEIGHT - (340 + y_offset), WIDTH - 60, 50)
    display.set_pen(1)
    display.text("A. CALENDAR", 35, HEIGHT - (325 + y_offset), 600, 3)

    display.set_pen(display.create_pen(255, 122, 72))
    display.rectangle(30, HEIGHT - (280 + y_offset), WIDTH - 60, 50)
    display.set_pen(1)
    display.text("B. ... to be updated", 35, HEIGHT - (265 + y_offset), 600, 3)

    display.set_pen(display.create_pen(16, 55, 120))
    display.rectangle(30, HEIGHT - (220 + y_offset), WIDTH - 60, 50)
    display.set_pen(1)
    display.text("C. ... to be updated", 35, HEIGHT - (205 + y_offset), 600, 3)

    display.set_pen(display.create_pen(227, 55, 30))
    display.rectangle(30, HEIGHT - (160 + y_offset), WIDTH - 60, 50)
    display.set_pen(1)
    display.text("D. ... to be updated", 35, HEIGHT - (145 + y_offset), 600, 3)

    display.set_pen(display.create_pen(21, 31, 48))
    display.rectangle(30, HEIGHT - (100 + y_offset), WIDTH - 60, 50)
    display.set_pen(1)
    display.text("E. ... to be updated", 35, HEIGHT - (85 + y_offset), 600, 3)

    display.set_pen(0)
    note = "Hold A + E, then press Reset, to return to the Launcher"
    note_len = display.measure_text(note, 2) // 2
    display.text(note, (WIDTH // 2 - note_len), HEIGHT - 30, 600, 2)

    ih.led_warn.on()
    display.update()
    ih.led_warn.off()

    # Now we've drawn the menu to the screen, we wait here for the user to select an app.
    # Then once an app is selected, we set that as the current app and reset the device and load into it.

    # You can replace any of the included examples with one of your own,
    # just replace the name of the app in the line "ih.update_last_app("nasa_apod")"

    while True:
        if ih.inky_frame.button_a.read():
            ih.inky_frame.button_a.led_on()
            ih.update_state("calendar")
            time.sleep(0.5)
            reset()
        # if ih.inky_frame.button_b.read():
        #     ih.inky_frame.button_b.led_on()
        #     ih.update_state("word_clock")
        #     time.sleep(0.5)
        #     reset()
        # if ih.inky_frame.button_c.read():
        #     ih.inky_frame.button_c.led_on()
        #     ih.update_state("daily_activity")
        #     time.sleep(0.5)
        #     reset()
        # if ih.inky_frame.button_d.read():
        #     ih.inky_frame.button_d.led_on()
        #     ih.update_state("news_headlines")
        #     time.sleep(0.5)
        #     reset()
        # if ih.inky_frame.button_e.read():
        #     ih.inky_frame.button_e.led_on()
        #     ih.update_state("calendar")
        #     time.sleep(0.5)
        #     reset()


# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_warn.off()
ih.network_led_pwm.duty_u16(0)

if ih.inky_frame.button_a.read() and ih.inky_frame.button_e.read():
    launcher()

if ih.file_exists("state.json"):
    # Loads the JSON config and prepares the device for the last app that was running.
    print("Loading state.json")
    ih.load_state()
    ih.launch_app(ih.state['run'])

else:
    print("No state.json file found, launching the launcher")
    launcher()

ih.clear_button_leds() 
try:
    print("Initializing SD card")
    sd_spi = SPI(0, sck=Pin(18, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(16, Pin.OUT))
    sd = sdcard.SDCard(sd_spi, Pin(22))
    time.sleep(0.5)
except:
    show_error("Insert the SD card")
    ih.stop_execution()

try:
    print("Mounting SD card")
    os.mount(sd, sdcard_mount_point, readonly=True)
except:
    print("Failed to mount SD card, perhaps it is already mounted?")
    print("Unmounting SD card")
    os.umount(sdcard_mount_point)
    print("Mounting SD card")
    os.mount(sd, sdcard_mount_point, readonly=True)
    print("SD card mounted")
else:
    print("SD card mounted")
    time.sleep(0.5)

if not sdcard_mount_point in sys.path:
    print("Adding SD card mount point to sys.path")
    sys.path.append(sdcard_mount_point)

# Sets secrets for the app
try:
    print("Getting secrets for the app")
    from secrets import API_AUTH_HEADER, API_AUTH_KEY, API_URL
    ih.app.API_AUTH_HEADER = API_AUTH_HEADER
    ih.app.API_AUTH_KEY = API_AUTH_KEY
    ih.app.API_URL = API_URL
    # ih.app.SMTH_ELSE = SMTH_ELSE
except ImportError:
    show_error("Pleaese specify API_AUTH_HEADER, API_AUTH_KEY in secrets.py on the SD card")
    ih.stop_execution()

# Enables wifi
try:
    print("Getting WiFi credentials")
    from secrets import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    show_error("Pleaese specify WIFI_SSID,WIFI_PASSWORD in secrets.py on the SD card")
    ih.stop_execution()
if not ih.network_connect(WIFI_SSID, WIFI_PASSWORD):
    show_error("No WiFi connection")
    ih.stop_execution()

# Syncs the time
if not ih.sync_time():
    show_error("Could not sync time")
    ih.stop_execution()

gc.collect()

# Gets the data to draw on the screen
if not ih.app.update():
    show_error("Exception in update")
    ih.stop_execution()

# Draws the data on the screen
ih.app.draw()

ih.deep_sleep(ih.app.UPDATE_INTERVAL)
