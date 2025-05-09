# Display simplified PV (Alpha-style) summary on Pimoroni Pico Display from Shelly EM `/status`

import network
import urequests as requests
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY, PEN_RGB565
from pimoroni import Button, RGBLED

# === Config ===
SHELLY_URL = "http://x.x.x.x/status"
SSID = "..."
PASSWORD = "..."
UPDATE_INTERVAL = 60

# Init display & buttons
led = RGBLED(6, 7, 8)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, pen_type=PEN_RGB565, rotate=0)
WIDTH, HEIGHT = display.get_bounds()

button_a = Button(12)
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Colors
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
GREEN = display.create_pen(0, 255, 0)
YELLOW = display.create_pen(255, 255, 0)
BLUE = display.create_pen(0, 0, 255)
RED = display.create_pen(255, 0, 0)
ORANGE = display.create_pen(255, 128, 0)
CYAN = display.create_pen(0, 255, 255)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    for _ in range(15):
        if wlan.status() == 3:
            return True
        time.sleep(1)
    return False

def fetch_shelly_data():
    try:
        r = requests.get(SHELLY_URL)
        data = r.json()
        r.close()
        grid = data['emeters'][0]['power'] / 1000  # kW
        solar = data['emeters'][1]['power'] / 1000  # kW
        home = grid + solar
        shelly_time = data.get("time", "--:--")
        return {"grid": grid, "solar": solar, "home": home, "time": shelly_time}
    except Exception as e:
        print("Error fetching data:", e)
        reconnect_wifi()
        return None

def display_data(values):
    display.set_pen(BLACK)
    display.clear()

    display.set_pen(YELLOW)
    display.text(f"HOME: {values['home']:.2f} kW", 10, 10, scale=3)

    display.set_pen(GREEN)
    if values['solar'] * 1000 < 5:
        display.text("SOLAR: - kW", 10, 40, scale=3)
    else:
        display.text(f"SOLAR: {values['solar']:.2f} kW", 10, 40, scale=3)

    display.set_pen(CYAN if values['grid'] < 0 else ORANGE)
    display.text(f"FLOW: {values['grid']:.2f} kW", 10, 70, scale=3)

    display.set_pen(WHITE)
    display.text(f"Update time: {values['time']}", 10, HEIGHT - 20, scale=2)

    display.update()

def display_message(msg, color):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(color)
    y = HEIGHT // 2 - 20
    for line in msg.split("\n"):
        display.text(line, 10, y, scale=2)
        y += 25
    display.update()
    
def update_led(flow, tick_time):
    brightness = 16  # Half brightness (max is 32)

    if flow < 0:
        # Slow pulsing green every 2s
        if int(tick_time) % 2 == 0:
            led.set_rgb(0, brightness, 0)
        else:
            led.set_rgb(0, 0, 0)
    elif 0 <= flow <= 3:
        # Solid blue for normal usage
        led.set_rgb(0, 0, brightness)
    elif 3 < flow <= 5:
        # Solid orange for moderate usage
        led.set_rgb(brightness, brightness // 2, 0)
    else:
        # >5kW fast blinking red
        if int(tick_time * 5) % 2 == 0:
            led.set_rgb(brightness, 0, 0)
        else:
            led.set_rgb(0, 0, 0)
            
def reconnect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("Reconnecting WiFi...")
        wlan.disconnect()
        wlan.active(True)
        wlan.connect(SSID, PASSWORD)
        for _ in range(15):
            if wlan.status() == 3:
                print("WiFi reconnected successfully.")
                return True
            time.sleep(1)
        print("WiFi reconnection failed.")
    return False

# Start
led.set_rgb(0, 0, 0)
display_message("Shelly Display\nStarting...", WHITE)
time.sleep(2)

if not connect_wifi():
    display_message("WiFi Connection\nFailed!", RED)
    while True:
        led.set_rgb(32, 0, 0)
        time.sleep(1)
        led.set_rgb(0, 0, 0)
        time.sleep(1)

last_update = 0
values = None

while True:
    now = time.time()
    tick_time = time.ticks_ms() / 1000
    button_pressed = button_a.read() or button_b.read() or button_x.read() or button_y.read()

    if button_pressed:
        display_message("Refreshing...", WHITE)
        values = fetch_shelly_data()
        if values:
            display_data(values)
        else:
            display_message("Failed to\nget data", RED)
        last_update = now

    elif now - last_update > UPDATE_INTERVAL:
        values = fetch_shelly_data()
        if values:
            display_data(values)
        else:
            display_message("Failed to\nget data", RED)
        last_update = now

    # Update LED status based on latest flow reading
    if values:
        flow = values['grid']
        update_led(flow, tick_time)

    time.sleep(0.1)
