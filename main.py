# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-web-server-micropython/

import network
import socket
import time

#import json
import ujson as json

from machine import Pin, I2C

import ubinascii

# HTU21D /// https://github.com/flrrth/pico-htu21d
from htu21d import HTU21D


# HTML template for the webpage
def webpage(state):
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pico Web Server</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Raspberry Pi Pico Web Server</h1>
            <h2>Led Control</h2>
            <form action="./lighton">
                <input type="submit" value="Light on" />
            </form>
            <br>
            <form action="./lightoff">
                <input type="submit" value="Light off" />
            </form>
            <p>LED state: {state}</p>
        </body>
        </html>
        """
    return str(html)


def load_conf() -> dict:
    try:
        with open('conf.json', 'r') as f:
            return json.load(f)
    except:
        print('conf.json not found')
        return dict()


def save_conf() -> bool:
    result = True


conf = load_conf()

urls = {
    '/b-led-on': None,
    '/b-led-off': None
}

# Initialize variables
state = "OFF"

# Create an LED object on pin 'LED'
led = Pin('LED', Pin.OUT)

# Wi-Fi credentials
wlan_ssid = conf['wifi']['ssid']
wlan_password = conf['wifi']['password']

# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wlan_ssid, wlan_password)

# Wait for Wi-Fi connection
connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() >= 3:
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    time.sleep(1)

# Check if connection is successful
if wlan.status() != 3:
    raise RuntimeError('Failed to establish a network connection')
else:
    network_info = wlan.ifconfig()
    
    print(f'Pico connect to: {wlan_ssid}')

    print('Pico IP:', network_info[0])

    mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
    print(f'Pico MAC: {mac}')
    
# Set up socket and start listening
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen()

print('Listening on', addr)

# Main loop to listen for connections
while True:
    try:
        conn, addr = s.accept()
        
        # Receive and parse the request
        request = conn.recv(1024)
        request = str(request)

        try:
            request = request.split()[1]
            print('Request:', request)
        except IndexError as e:
            print(f'IndexError: {e}')
        
        # Process the request and update variables
        if request == '/lighton?':
            print("LED on")
            led.value(1)
            state = "ON"
        elif request == '/lightoff?':
            led.value(0)
            state = 'OFF'

        # Generate HTML response
        response = webpage(state)  

        # Send the HTTP response and close the connection
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except OSError as e:
        conn.close()
        print('Connection closed')