import network
import requests
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB565
from pimoroni import Button, RGBLED

# Initialize the display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB565, rotate=0)
WIDTH, HEIGHT = display.get_bounds()

# Create pens for different colors
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
RED = display.create_pen(255, 0, 0)
BLUE = display.create_pen(0, 0, 255)

# Wi-Fi credentials
SSID = "..."
PASSWORD = "..."

# Weather API settings
CITY = "Albury"
API_URL = f"https://wttr.in/{CITY}?format=%C,%t"

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

def fetch_weather():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.text.split(',')
            return {
                'description': data[0],
                'temperature': data[1]
            }
        else:
            print(f"Error: HTTP status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def display_weather(weather_data):
    if weather_data is None:
        display_message("Failed to fetch weather data", RED)
        return

    display.set_pen(BLACK)
    display.clear()

    # Display city name
    display.set_pen(GREEN)
    display.text(CITY, 10, 10, scale=3, wordwrap=WIDTH-20)

    # Display temperature (largest and most prominent)
    display.set_pen(WHITE)
    temp = weather_data['temperature'].replace('+','').strip()
    display.text(temp, 10, 40, scale=7)

    # Display weather description
    display.set_pen(WHITE)
    display.text(weather_data['description'], 10, 110, scale=2, wordwrap=WIDTH-20)

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
display_message("Weather Display\nStarting...", WHITE)
time.sleep(2)
connect_wifi()
time.sleep(10)
weather_data = fetch_weather()

while True:
    if not network.WLAN(network.STA_IF).isconnected():
        connect_wifi()
        time.sleep(10)

    new_weather_data = fetch_weather()
    if new_weather_data:
        led.set_rgb(0, 0, 0)
        display_weather(new_weather_data)
    else:
        print("Failed to get weather")
        led.set_rgb(32, 0, 0)
        display_weather(weather_data)

    time.sleep(900)  # Update every 15 minutes