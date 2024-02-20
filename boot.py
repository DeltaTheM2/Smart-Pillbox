import os
import wifi
import socketpool
import adafruit_requests
import storage
import microcontroller
import binascii

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
        return device_id

# Attempt to connect to Wi-Fi
try:
    print("Connecting to Wi-Fi...")
    wifi.radio.connect(ssid="YOUR_SSID", password="YOUR_PASSWORD")
    print("Connected to Wi-Fi")
except Exception as e:
    print("Failed to connect to Wi-Fi:", e)
    # Consider handling reconnection or alerting the user here.

# Initialize the requests library for future HTTP requests
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, None)

# Generate or read the existing device ID
device_id = get_or_create_device_id()

# Note: Further logic to check device registration could go here or in code.py,
# depending on when you want to perform the check and how it impacts your application flow.
