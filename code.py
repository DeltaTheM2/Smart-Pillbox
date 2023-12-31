# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
import time
import ssl
import wifi
import socketpool
import displayio
import digitalio
import board
import os
import terminalio
from adafruit_display_text import bitmap_label
from adafruit_bitmap_font import bitmap_font
import adafruit_requests
import adafruit_ili9341

# Get WiFi details secrets.py file
try:
    wifi.radio.connect(
        os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
    )
    print("Connected to %s!" % os.getenv("CIRCUITPY_WIFI_SSID"))
except Exception as e:  # pylint: disable=broad-except
    print(
        "Failed to connect to WiFi. Error:", e, "\nBoard will hard reset in 30 seconds."
    )
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

#Get the Time
DATA_SOURCE = "http://worldtimeapi.org/api/timezone/America/Los_Angeles"
device_name = "Warren's ESP"

# URL to fetch from
JSON_STARS_URL = "https://api.github.com/repos/adafruit/circuitpython"
FIREBASE_URL = "https://pillbox-3e02f-default-rtdb.firebaseio.com/"

firebase_path = FIREBASE_URL + "data.json"

# Set up background image and text
display = board.DISPLAY
bitmap = displayio.OnDiskBitmap("/images/HOMESCREEN.bmp")
default_tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

REMINDER_TIME = 28800

group = displayio.Group()
group.append(default_tile_grid)

#time label
font = bitmap_font.load_font("/fonts/Arial-Bold-36.bdf")
time_label = bitmap_label.Label(font, scale=1, color= 0x000000)
time_label.anchor_point = (0.2, 0.5)
time_label.anchored_position = (80, 67)

# main group to hold all of the display groups:
main_group = displayio.Group()
main_group.append(group)
main_group.append(time_label)

display.show(main_group)

current_background_image = "/images/HOMESCREEN.bmp"
#local Screens
HOMESCREEN = "/images/HOMESCREEN.bmp"
PILLCOUNTER = "/images/PILLCOUNTER.bmp"
SETTINGS = "/images/SETTINGS.bmp"
#PILLCOUNTER1 = "/images/     .bmp"



def set_background_image(filename):
    global current_background_image
    tile_bitmap = displayio.OnDiskBitmap(filename)
    new_tile_grid = displayio.TileGrid(tile_bitmap, pixel_shader=tile_bitmap.pixel_shader)
    group[0] = new_tile_grid
    current_background_image = filename


btnD0 = digitalio.DigitalInOut(board.BUTTON)
btnD0.direction = digitalio.Direction.INPUT
btnD0.pull = digitalio.Pull.UP


btnD1 = digitalio.DigitalInOut(board.D1)
btnD1.direction = digitalio.Direction.INPUT
btnD1.pull = digitalio.Pull.DOWN

btnD2 = digitalio.DigitalInOut(board.D2)
btnD2.direction = digitalio.Direction.INPUT
btnD2.pull = digitalio.Pull.DOWN
#extra button

#btn = digitalio.DigitalInOut(board.BUTTON)
#btn.direction = digitalio.Direction.INPUT
#btn.pull = digitalio.Pull.UP
#btn.switch_to_input(pull = digitalio.Pull.UP)

def display_counter(pill_name, count):
    main_group.pop()
    font = bitmap_font.load_font("/fonts/Arial-Bold-36.bdf")

    # Display Pill Name
    text_area_name = bitmap_label.Label(font, text=pill_name + "\n" + str(count), color=0x000000)
    text_area_name.x = 80
    text_area_name.y = 50
    main_group.append(text_area_name)



def parse_time(datetime_str):
    time_str = datetime_str.split("T")[1].split(".")[0]
    hour, minute, _ = map(int, time_str.split(":"))
    period = "AM"
    if hour >= 12:
        period = "PM"
        if hour > 12:
            hour -= 12
    elif hour == 0:
        hour = 12

    return hour, minute, period

def parse_reminder():
    global REMINDER_TIME
    hour = REMINDER_TIME // 3600
    minute = (REMINDER_TIME % 3600) // 60
    if minute >= 60:
        minute = 0
        hour += 1
    elif minute < 0:
        minute = 60 - minute
        hour -= 1

    time_str = "{:02d}:{:02d}".format(hour, minute)
    main_group.pop()
    font = bitmap_font.load_font("/fonts/Arial-Bold-36.bdf")
    text_area = bitmap_label.Label(font, text=time_str, color = 0x000000)
    text_area.x = 80
    text_area.y = 67
    main_group.append(text_area)
    display.show(main_group)

counter = 0
previous_time = None

my_dict = {'Pill1' : counter, 'Pill2' : counter, 'Pill3' : counter}

firebasedata = {
        'Device Name': device_name,
        #'Pills' : pills,
        'Last pill taken' : 0
        }
pill_index = 0
selected_pill = list(my_dict.keys())[pill_index]
while True:
    response = requests.get(DATA_SOURCE)
    data = response.json()
    current_hour, current_minute, current_period = parse_time(data["datetime"])
    if current_background_image == HOMESCREEN:
        time_label.text = " {:2}:{:02}{}".format(current_hour, current_minute, current_period)
    else:
        time_label.text = ""

    if not btnD0.value:
        if current_background_image != HOMESCREEN:
            main_group.pop()
            set_background_image(HOMESCREEN)
            requests.post(firebase_path, json = firebasedata)
            time_label.text = " {:2}:{:02}{}".format(current_hour, current_minute, current_period)
            main_group.append(time_label)


    if btnD1.value:
        if current_background_image == HOMESCREEN:
            set_background_image(SETTINGS)
            requests.post(firebase_path, json = firebasedata)
            parse_reminder()
        elif current_background_image == PILLCOUNTER:
            pill_index = (pill_index + 1) % len(my_dict)
            selected_pill = list(my_dict.keys())[pill_index]
            requests.post(firebase_path, json = firebasedata)
            display_counter(selected_pill, my_dict[selected_pill])
        elif current_background_image == SETTINGS:
            REMINDER_TIME += 1800
            requests.post(firebase_path, json = firebasedata)
            parse_reminder()


    if btnD2.value:
        if current_background_image == HOMESCREEN:
            set_background_image(PILLCOUNTER)
        elif current_background_image == PILLCOUNTER:
            my_dict[selected_pill] += 1
            requests.post(firebase_path, json = firebasedata)
            display_counter(selected_pill, my_dict[selected_pill])
        elif current_background_image == SETTINGS:
            REMINDER_TIME -= 1800
            requests.post(firebase_path, json = firebasedata)
            parse_reminder()
