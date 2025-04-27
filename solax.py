"""
================================================================================
 Solax Solar Monitor on Pico Display
--------------------------------------------------------------------------------
 This script connects to Wi-Fi and fetches real-time solar data from the
 Solax Cloud API. It then displays current power and today's energy yield
 using the Pimoroni Pico Display.

 Hardware:
   - Raspberry Pi Pico W
   - Pimoroni Pico Display Pack
   - Pimoroni RGBLED and Button inputs (A, B, X, Y)

 Features:
   - Wi-Fi connection status feedback via RGB LED
   - Live display of solar generation data
   - Manual data refresh via button press
   - Auto-refresh every 60 seconds

 Author: James Flores
 Date: 2025-04-24
 License: MIT
================================================================================
"""
import network
import requests
import json
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB565
from pimoroni import Button, RGBLED

# Initialize the display and buttons
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB565, rotate=0)
WIDTH, HEIGHT = display.get_bounds()

# Initialize buttons
button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Create pens for different colors
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
BLUE = display.create_pen(0, 0, 255)

# Wi-Fi credentials
SSID = "..."
PASSWORD = "..."

# Solax API settings
API_URL = "https://global.solaxcloud.com/api/v2/dataAccess/realtimeInfo/get"
TOKEN_ID = "..."
WIFI_SN = "..."

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)
    
    return wlan.status() == 3

def fetch_solar_data():
    try:
        headers = {
            'tokenId': TOKEN_ID,
            'Content-Type': 'application/json'
        }
        payload = {
            'wifiSn': WIFI_SN
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return {
                    'current_power': data['result']['acpower'] / 1000,  # Convert W to kW
                    'yield_today': data['result']['yieldtoday']
                }
        print(f"Error: HTTP status code {response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching solar data: {e}")
        return None

def display_solar_data(solar_data):
    if solar_data is None:
        display_message("Failed to fetch solar data", RED)
        return

    display.set_pen(BLACK)
    display.clear()

    # Display current power (largest and most prominent)
    display.set_pen(GREEN)
    display.text("Current Power", 10, 10, scale=2)
    display.set_pen(WHITE)
    display.text(f"{solar_data['current_power']:.2f}kW", 10, 30, scale=4)

    # Display today's yield
    display.set_pen(BLUE)
    display.text("Today's Yield", 10, 70, scale=2)
    display.set_pen(WHITE)
    display.text(f"{solar_data['yield_today']:.2f}kWh", 10, 90, scale=3)

    display.update()

def display_message(message, color):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(color)
    lines = message.split('\n')
    y = HEIGHT // 2 - (len(lines) * 20 // 2)
    for line in lines:
        display.text(line, 10, y, scale=2, wordwrap=WIDTH-20)
        y += 25
    display.update()

# Main program
led = RGBLED(6, 7, 8)
led.set_rgb(0, 0, 0)
display_message("Solar Display\nStarting...", WHITE)
time.sleep(2)

if not connect_wifi():
    display_message("WiFi Connection\nFailed!", RED)
    while True:
        led.set_rgb(32, 0, 0)
        time.sleep(1)
        led.set_rgb(0, 0, 0)
        time.sleep(1)

# Main loop
last_update = 0
update_interval = 60  # Update every minute

while True:
    current_time = time.time()
    
    # Check if any button is pressed
    if button_a.read() or button_b.read() or button_x.read() or button_y.read():
        led.set_rgb(0, 0, 32)  # Blue LED while refreshing
        if network.WLAN(network.STA_IF).isconnected():
            solar_data = fetch_solar_data()
            if solar_data:
                led.set_rgb(0, 32, 0)  # Green LED indicates successful data fetch
                display_solar_data(solar_data)
                last_update = current_time
            else:
                led.set_rgb(32, 0, 0)  # Red LED indicates error
                display_message("Failed to get\nsolar data", RED)
        time.sleep(0.5)  # Debounce delay
        
    # Regular timed update
    elif current_time - last_update >= update_interval:
        if not network.WLAN(network.STA_IF).isconnected():
            connect_wifi()
            time.sleep(10)

        solar_data = fetch_solar_data()
        if solar_data:
            led.set_rgb(0, 32, 0)  # Green LED indicates successful data fetch
            display_solar_data(solar_data)
        else:
            led.set_rgb(32, 0, 0)  # Red LED indicates error
            display_message("Failed to get\nsolar data", RED)
        last_update = current_time
    
    time.sleep(0.1)  # Small delay to prevent busy-waiting

