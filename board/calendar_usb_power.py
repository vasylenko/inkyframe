import utime
import requests

class AppUpdateError(Exception):
    """Exception raised when there is an error updating the calendar."""
    pass

class DrawingSettings:
    # Drawing constants
    # BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE, TAUPE = 0, 1, 2, 3, 4, 5, 6, 7
    TITLE_FONT_SCALE = 14/10
    TITLE_FONT_THICKNESS = 4
    TITLE_RECTANGLE_HEIGHT = 75
    TITLE_FONT_COLOR = 1
    TITLE_BACKGROUND_COLOR = 2

    TITLE_DATE_BACKGROUND_COLOR = 4
    TITLE_DATE_BACKGROUND_WIDTH = 25/10 * TITLE_RECTANGLE_HEIGHT

    DATE_BACKGROUND_COLOR = 4
    DATE_BACKGROUND_WIDTH = 2.5 * TITLE_RECTANGLE_HEIGHT

    EVENTS_FONT_SCALE = 12/10
    EVENTS_FONT_BASELINE = 10 * EVENTS_FONT_SCALE
    EVENTS_FONT_DESCENDERS = 20 * EVENTS_FONT_SCALE
    EVENTS_BASE_SPACING = 70
    EVENTS_FONT_THICKNESS = 3

    EVENT_HIGHLIGHT_COLOR_TODAY = 4
    EVENT_FONT_COLOR_DEFAULT = 0
    EVENT_FONT_COLOR_TODAY = 1
    

class InkyApp:
    def __init__(self):
        self.api_auth_header = ""
        self.api_auth_key = ""
        self.api_url = ""
        self.update_interval = 300 # in minutes
        self.calendar_api_path = "/calendars"
        self.calendar_name = "Personal"
        self.num_cal_events = 5
        self.calendar_events = []
        self.last_update = 0

    def set_api_info(self, api_auth_header, api_auth_key, api_url):
        print("Setting API info...")
        self.api_auth_header = api_auth_header
        self.api_auth_key = api_auth_key
        self.api_url = api_url

    def update(self):
        print("Updating calendar...")
        request_address = None

        request_address = self.api_url + self.calendar_api_path + "/" + self.calendar_name + "?num-events=" + str(self.num_cal_events)

        headers = {self.api_auth_header: self.api_auth_key, "Content-Type": "application/json"}
        response = None
        response = requests.get(request_address, headers=headers)
        if response.status_code != 200:
            print("Failed to update calendar", response.status_code)
            response.raise_for_status()
        try:
            self.calendar_events = response.json()
        except IOError as e:
            raise AppUpdateError("Failed to update calendar", e)
        finally:
            response.close() 

    def draw(self, display):
        print("Drawing calendar...")
        # check if self.calendar_events is not empty; otherwise raise exception
        if not self.calendar_events:
            raise AppUpdateError("Calendar events list is empty")
        display.set_pen(1)
        display.clear()
        display.set_font("sans")
        WIDTH, HEIGHT = display.get_bounds()

        current_time = utime.time()
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        display.set_pen(DrawingSettings.TITLE_BACKGROUND_COLOR)
        display.rectangle(0, 0, WIDTH, DrawingSettings.TITLE_RECTANGLE_HEIGHT)
        display.set_pen(DrawingSettings.TITLE_FONT_COLOR)
        display.set_thickness(DrawingSettings.TITLE_FONT_THICKNESS)
        title_text = "Upcoming Events"

        display.text(title_text, 0, int(DrawingSettings.TITLE_RECTANGLE_HEIGHT / 2), WIDTH, DrawingSettings.TITLE_FONT_SCALE)
        
        today = "{:02d} {}".format(utime.localtime(current_time)[2], month_names[utime.localtime(current_time)[1]])  # format today's date as 'dd MMM
        text_len = display.measure_text(today, DrawingSettings.TITLE_FONT_SCALE)
        display.set_pen(DrawingSettings.DATE_BACKGROUND_COLOR)
        display.rectangle(int(WIDTH - DrawingSettings.DATE_BACKGROUND_WIDTH), 0, int(DrawingSettings.DATE_BACKGROUND_WIDTH), DrawingSettings.TITLE_RECTANGLE_HEIGHT)
        display.set_pen(DrawingSettings.TITLE_FONT_COLOR)
        display.text(today, int(WIDTH - DrawingSettings.DATE_BACKGROUND_WIDTH + (DrawingSettings.DATE_BACKGROUND_WIDTH - text_len) / 2), int(DrawingSettings.TITLE_RECTANGLE_HEIGHT / 2), WIDTH, DrawingSettings.TITLE_FONT_SCALE)

        display.set_pen(DrawingSettings.TITLE_FONT_COLOR)
        display.rectangle(0, DrawingSettings.TITLE_RECTANGLE_HEIGHT, WIDTH, HEIGHT)    
        

        today = "{:02d}.{}".format(utime.localtime(current_time)[2], month_names[utime.localtime(current_time)[1]])  # format today's date as 'dd MMM'
        line_num = 1
        display.set_thickness(DrawingSettings.EVENTS_FONT_THICKNESS)
        for i in self.calendar_events:
            event_date = i['dateTime'].split(".")[0]+"."+i['dateTime'].split(".")[1]  # get the date part of 'dateTime'
            if event_date == today:
                display.set_pen(DrawingSettings.EVENT_HIGHLIGHT_COLOR_TODAY)
                display.rectangle(0, int(DrawingSettings.EVENTS_BASE_SPACING * line_num + DrawingSettings.TITLE_RECTANGLE_HEIGHT - 2*DrawingSettings.EVENTS_FONT_BASELINE), WIDTH, int(2*DrawingSettings.EVENTS_FONT_DESCENDERS) )
                display.set_pen(DrawingSettings.EVENT_FONT_COLOR_TODAY)
                display.text(i['dateTime']+" "+i['summary'], 0, int(DrawingSettings.EVENTS_BASE_SPACING * line_num + DrawingSettings.TITLE_RECTANGLE_HEIGHT), WIDTH, DrawingSettings.EVENTS_FONT_SCALE)
                line_num += 1
            else:
                display.set_pen(DrawingSettings.EVENT_FONT_COLOR_DEFAULT)
                display.text(i['dateTime']+" "+i['summary'], 0, int(DrawingSettings.EVENTS_BASE_SPACING * line_num + DrawingSettings.TITLE_RECTANGLE_HEIGHT), WIDTH, DrawingSettings.EVENTS_FONT_SCALE)
                line_num += 1
        
        display.set_font("bitmap8")
        display.set_pen(DrawingSettings.EVENT_FONT_COLOR_DEFAULT)
        last_updated = "Last updated: "+"{:02d} {}, {:02d}:{:02d}".format(utime.localtime(current_time)[2], month_names[utime.localtime(current_time)[1]], utime.localtime(current_time)[3], utime.localtime(current_time)[4])
        last_updated_len = display.measure_text(text=last_updated, scale=2)
        display.text(last_updated, WIDTH-last_updated_len, HEIGHT - 16, scale=2)
        
        display.update()


