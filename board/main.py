import gc
import time
from machine import reset
import inky_helper as ih
import sys
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"


# A short delay to give USB chance to initialise
time.sleep(1)

# Setup for the display.
display = PicoGraphics(DISPLAY)
WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

running_app = None

# Setup for SD card
sd_card = None
sd_card_mount_point = "/sdcard"
logfile = "/sdcard/execution-log.log"


def launcher():
    ih.led_busy.on()

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

    display.update()

    ih.led_busy.off()

    while True:
        if ih.inky_frame.button_a.read():
            ih.inky_frame.button_a.led_on()
            ih.update_state("calendar_usb_power")
            time.sleep(0.5)
            reset()
        # if ih.inky_frame.button_b.read():
        #     ih.inky_frame.button_b.led_on()
        #     ih.update_state("air_meter")
        #     time.sleep(0.5)
        #     reset()

# Turn any LEDs off that may still be on from last run.
ih.clear_button_leds()
ih.led_busy.off()
ih.led_wifi.off()

if ih.button_a.read() and ih.button_e.read():
    launcher()

if ih.file_exists("state.json"):
    # Loads the JSON config and prepares the device for the last app that was running.
    print("Loading state.json")
    ih.load_state()
    # ih.launch_app(ih.state['run'])
    app = __import__(ih.state['run'])
    running_app = getattr(app, 'InkyApp')() 
else:
    print("No state.json file found, launching the launcher")
    launcher()

try:
    sd_card = ih.init_sd_card()
    ih.mount_sd_card(sd_card, sd_card_mount_point)
except Exception as e:
    ih.show_error(display,"Could not mount the SD card: " + str(e)) 
    reset()

if not sd_card_mount_point in sys.path:
    print("Adding SD card mount point to sys.path")
    sys.path.append(sd_card_mount_point)
    print("SD card mount point added to sys.path, sys.path is now:", sys.path)

try:
    print("Getting secrets for the app")
    from secrets import API_AUTH_HEADER, API_AUTH_KEY, API_URL
    running_app.set_api_info(API_AUTH_HEADER, API_AUTH_KEY, API_URL)
except ImportError as e:
    ih.show_error(display,"Could not get api info from "+sd_card_mount_point+"/"+"secrets.py: "+str(e))
    reset()
try:
    ih.progress_bar_fill("a")
    print("Getting WiFi credentials")
    from secrets import WIFI_SSID, WIFI_PASSWORD
    print(WIFI_SSID)
except ImportError as e:
    ih.progress_bar_clear()
    ih.show_error(display,"Could not get wifi info from "+sd_card_mount_point+"/"+"secrets.py: "+str(e))
    reset()

gc.collect()

try: 
    ih.progress_bar_fill("b")
    ih.network_connect(WIFI_SSID, WIFI_PASSWORD)
except Exception as e:
    ih.progress_bar_clear()
    reset()


# Syncs the time
try:
    ih.progress_bar_fill("c")
    ih.sync_time()
except Exception as e:
    ih.progress_bar_clear()
    reset()
gc.collect()


# Gets the data to draw on the screen
try:
    ih.progress_bar_fill("d")
    running_app.update()
except Exception as e:
    ih.progress_bar_clear()
    reset()
gc.collect()


# Draws the data on the screen
try:
    ih.progress_bar_fill("e")
    running_app.draw(display)
except Exception as e:
    ih.progress_bar_clear
    reset()
else:
    ih.illuminate_button_leds(10)


gc.collect()
ih.clear_all_leds()
time.sleep(1)    
ih.inky_frame.sleep_for(30)
reset()