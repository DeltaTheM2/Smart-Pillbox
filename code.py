# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
import time
from adafruit_datetime import datetime
import ssl
import wifi
import socketpool
import displayio
import digitalio
import board
import json
import os
import storage
import terminalio
from adafruit_display_text import bitmap_label
from adafruit_bitmap_font import bitmap_font
import adafruit_requests
import adafruit_ili9341
import binascii
import microcontroller
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
FIREBASE_URL = "https://console.firebase.google.com/u/0/project/pillbox-3e02f/firestore/data/~2Fpills"

server_url = "https://smart-pillbox-server.onrender.com"

def get_qrcode(device_id):
    response = requests.get(f"https://smart-pillbox-server.onrender.com/register_device/{device_id}")
    if response.status_code == 200:
        with open("qrcode.bmp", 'wb') as file:
            file.write(response.content)
        print("qr saved")
    else:
        print("failed to download the bmp from server")


def get_or_create_device_id(filename="device_id.txt"):
      # Check if the device_id.txt file exists
    if filename in os.listdir("/"):
        with open(filename, "r") as file:
            device_id = file.read().strip()
            print("Existing Device ID:", device_id)
            return device_id
    else:
        # Generate a new device ID. This example uses the CPU's unique ID.
        device_id = binascii.hexlify(microcontroller.cpu.uid).decode("utf-8")
        with open(filename, "w") as file:
            file.write(device_id)
        print("New Device ID:", device_id)
        #get_qrcode(device_id)
        return device_id

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
PILLCOUNTER = "/images/PILLSCREEN.bmp"
SETTINGS = "/images/SETTINGS.bmp"
QRCODE = "/images/qrcode.bmp"
WHITEBG = "/images/whitebg.bmp"

def set_background_image(filename):
    global current_background_image
    tile_bitmap = displayio.OnDiskBitmap(filename)
    new_tile_grid = displayio.TileGrid(tile_bitmap, pixel_shader=tile_bitmap.pixel_shader)
    group[0] = new_tile_grid
    current_background_image = filename

def send_data(firebasedata):
    response = requests.post(f"{server_url}/update_firestore",headers={'Content-type': 'application/json', 'Accept': 'application/json'}, data=firebasedata)
    print("Response from server:", response.text)



def get_data(route="get_firestore"):
    response = requests.get(f"{server_url}/{route}")
    data = json.dumps(response)
    print("Data from server:", response.json())
    return response.json()

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
        hour -= 1
        minute = 60 - minute

    time_str = "{:02d}:{:02d}".format(hour, minute)
    main_group.pop()
    font = bitmap_font.load_font("/fonts/Arial-Bold-36.bdf")
    text_area = bitmap_label.Label(font, text=time_str, color = 0x000000)
    text_area.x = 80
    text_area.y = 67
    main_group.append(text_area)
    display.show(main_group)

def show_QR():
    whitebg_bitmap = displayio.OnDiskBitmap("/images/whitebg.bmp")
    tile_grid = displayio.TileGrid(whitebg_bitmap, pixel_shader=whitebg_bitmap.pixel_shader)
    main_group.append(tile_grid)
    qrcode_bitmap = displayio.OnDiskBitmap("/images/qrcode.bmp")
    tile_grid1 = displayio.TileGrid(qrcode_bitmap, pixel_shader=qrcode_bitmap.pixel_shader)
    main_group.append(tile_grid1)
    tile_grid1.x = 52
    tile_grid1.y = -2
    display.show(main_group)
counter = 0
previous_time = None


my_dict = {'Pill 1' : counter, 'Pill 2' : counter, 'Pill 3' : counter}

firebasedata = {
        'med_count': 20,
        'med_history':
             [datetime.fromisoformat('2024-01-21 16:30:00'),
              datetime.fromisoformat('2024-01-21 16:30:00')
             ],
        'med_name': "something",
        'reminder' : 12
        }
firebasedata['med_history'] = [int(dt.timestamp()) for dt in firebasedata['med_history']]
pill_index = 0



isRegistered = False

def isDeviceRegistered(device_id):
    response = requests.get(f"{server_url}/isRegistered")
    if response is not None:
        isRegistered = True
    



selected_pill = list(my_dict.keys())[pill_index]
#send_data(json.dumps(firebasedata))
#get_data()
device_id = get_or_create_device_id()
#get_qrcode(device_id)
timeOutCounter = 0
timeOutStart = time.time()
i2c_power = digitalio.DigitalInOut(board.TFT_I2C_POWER)
time.sleep(0.1)
#turning off the screen after the device has been inactive
i2c_power.switch_to_output()
time.sleep(0.1)
i2c_power.value = False
time.sleep(1)
i2c_power.value = True
show_QR()
while not isRegistered:
    time.sleep(15)
    isDeviceRegistered(device_id)
    print(isRegistered)

if isRegistered:
    main_group.pop()
while True:
    
    response = requests.get(DATA_SOURCE)
    data = response.json()
    current_hour, current_minute, current_period = parse_time(data["datetime"])
    if current_background_image == HOMESCREEN:
        time_label.text = " {:2}:{:02}{}".format(current_hour, current_minute, current_period)
        if timeOutCounter >= 60:
            i2c_power.value = False
        if time.time() - timeOutStart > 1:
           # print(timeOutCounter)
            timeOutCounter += 1
            timeOutStart = time.time()
    else:
        time_label.text = ""

    if not btnD0.value:
        if current_background_image != HOMESCREEN:
            main_group.pop()
            set_background_image(HOMESCREEN)
            time_label.text = " {:2}:{:02}{}".format(current_hour, current_minute, current_period)
            main_group.append(time_label)
            timeOutStart = time.time()
            i2c_power.value = True
            timeOutCounter = 0


    if btnD1.value:
        if current_background_image == HOMESCREEN:
            set_background_image(SETTINGS)
            parse_reminder()
        elif current_background_image == PILLCOUNTER:
            pill_index = (pill_index + 1) % len(firebasedata)
            selected_pill = list(my_dict.keys())[pill_index]
            display_counter(selected_pill, my_dict[selected_pill])
            timeOutStart = time.time()
            i2c_power.value = True
            timeOutCounter = 0
        elif current_background_image == SETTINGS:
            REMINDER_TIME += 1800
            parse_reminder()
            timeOutStart = time.time()
            i2c_power.value = True
            timeOutCounter = 0


    if btnD2.value:
        if current_background_image == HOMESCREEN:
            set_background_image(PILLCOUNTER)
        elif current_background_image == PILLCOUNTER:
            my_dict[selected_pill] += 1
            display_counter(selected_pill, my_dict[selected_pill])
            timeOutStart = time.time()
            i2c_power.value = True
            timeOutCounter = 0
        elif current_background_image == SETTINGS:
            REMINDER_TIME -= 1800
            parse_reminder()
            timeOutStart = time.time()
            i2c_power.value = True
            timeOutCounter = 0
