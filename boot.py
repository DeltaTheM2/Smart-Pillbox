import os
import wifi
import socketpool
import adafruit_requests
import storage
import microcontroller
import binascii
import ssl
storage.remount("/",readonly=False,disable_concurrent_write_protection=True)
def get_or_create_device_id(filename="device_id.txt"):
    if filename in os.listdir("/"):
        with open(filename, "r") as file:
            device_id = file.read().strip()
            print("Existing Device ID: ", device_id)
            return device_id
    else:
        device_id = binascii.hexify(microcontroller.cpu.uid).decode("uft-8")
        with open(filename, "w") as file:
            file.write(device_id)
        print("New Device ID:", device_id)
        return device_id

def get_qrcode(device_id=get_or_create_device_id()):
    response = requests.get(f"https://smart-pillbox-server.onrender.com/register_device/{device_id}")
    if response.status_code == 200:
        with open("qrcode.bmp", 'wb') as file:
            file.write(response.content)
        print("qr saved")
    else:
        print("failed to download the bmp from server")

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
print("getting qrcode")
get_qrcode()

