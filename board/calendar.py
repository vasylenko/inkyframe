import gc
import utime
import requests
# from urllib import urequest
from picographics import PicoGraphics, DISPLAY_INKY_FRAME_7 as DISPLAY  # 7.3"

API_AUTH_HEADER = None
API_AUTH_KEY = None
API_URL = None
UPDATE_INTERVAL = 7200 # in minutes, e.g., update every 12 hours
CALENDAR_API_PATH = "/calendars"
CALENDAR_NAME = "Personal"
NUM_CAL_EVENTS = 5


display = PicoGraphics(DISPLAY)

BLACK = 0
WHITE = 1
GREEN = 2
BLUE = 3
RED = 4
YELLOW = 5
ORANGE = 6
TAUPE = 7


title_font_scale = 1.4
title_font_thickness = 4
title_rectangle_heigh = 75
title_font_color = WHITE
title_background_color = GREEN

date_background_color = RED
date_background_width = 2.5 * title_rectangle_heigh

events_font_scale = 1.2
events_font_baseline = 10 * events_font_scale
events_font_descenders = 20 * events_font_scale
events_base_spacing = 70
events_font_thickness = 3
event_highlight_color_today = RED
event_highlight_color_tomorrow = YELLOW
event_font_colot_default = BLACK
event_font_colot_today = WHITE


gc.collect()

logfile = None # should be set from main.py

def update():
    print("Updating calendar...")
    global calendar_events
    request_address = None
    if not API_AUTH_HEADER or not API_AUTH_KEY:
        print("API_AUTH_HEADER or API_AUTH_KEY not set")
        return False
    if API_URL:
        request_address = API_URL + CALENDAR_API_PATH + "/" + CALENDAR_NAME + "?num-events=" + str(NUM_CAL_EVENTS)
    else:
        print("API_URL not set")
        return False
    headers = {API_AUTH_HEADER: API_AUTH_KEY, "Content-Type": "application/json"}
    response = None
    try:
        response = requests.get(request_address, headers=headers)
        if response.status_code != 200:
            response.raise_for_status()
    except Exception as e:
        print("Failed to update calendar", e)
        return False
    try:
        calendar_events = response.json()
        response.close()
    except:
        return False

    gc.collect()  
    return True

def draw():
    print("Drawing calendar...")
    gc.collect()    
    display.set_pen(WHITE)
    display.clear()
    display.set_font("sans")
    WIDTH, HEIGHT = display.get_bounds()

    current_time = utime.time()
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    display.set_pen(title_background_color)
    display.rectangle(0, 0, WIDTH, title_rectangle_heigh)
    display.set_pen(title_font_color)
    display.set_thickness(title_font_thickness)
    title_text = "Upcoming Events"
    # text_len = display.measure_text(title_text, title_font_scale) // 2
    # display.text(title_text, (WIDTH // 2 - text_len), title_rectangle_heigh // 2, WIDTH, title_font_scale)
    display.text(title_text, 0, int(title_rectangle_heigh / 2), WIDTH, title_font_scale)
    
    today = "{:02d} {}".format(utime.localtime(current_time)[2], month_names[utime.localtime(current_time)[1]])  # format today's date as 'dd MMM
    text_len = display.measure_text(today, title_font_scale)
    display.set_pen(date_background_color)
    display.rectangle(int(WIDTH - date_background_width), 0, int(date_background_width), title_rectangle_heigh)
    display.set_pen(title_font_color)
    display.text(today, int(WIDTH - date_background_width + (date_background_width - text_len) / 2), int(title_rectangle_heigh / 2), WIDTH, title_font_scale)

    display.set_pen(title_font_color)
    display.rectangle(0, title_rectangle_heigh, WIDTH, HEIGHT)    
    

    today = "{:02d}.{}".format(utime.localtime(current_time)[2], month_names[utime.localtime(current_time)[1]])  # format today's date as 'dd MMM'
    line_num = 1
    display.set_thickness(events_font_thickness)
    for i in calendar_events:
        event_date = i['dateTime'].split(".")[0]+"."+i['dateTime'].split(".")[1]  # get the date part of 'dateTime'
        if event_date == today:
            display.set_pen(event_highlight_color_today)
            display.rectangle(0, int(events_base_spacing * line_num + title_rectangle_heigh - 2*events_font_baseline), WIDTH, int(2*events_font_descenders) )
            display.set_pen(event_font_colot_today)
            display.text(i['dateTime']+" "+i['summary'], 0, int(events_base_spacing * line_num + title_rectangle_heigh), WIDTH, events_font_scale)
            line_num += 1
        else:
            display.set_pen(event_font_colot_default)
            display.text(i['dateTime']+" "+i['summary'], 0, int(events_base_spacing * line_num + title_rectangle_heigh), WIDTH, events_font_scale)
            line_num += 1

    gc.collect()
    display.update()
