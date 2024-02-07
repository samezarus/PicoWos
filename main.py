import network
import socket
import time

import ujson as json

from machine import Pin, I2C

import ubinascii


def val_from_str(key_val: str) -> str:
    l = key_val.split(': ')
    return l[1] if len(l) == 2 else ''


def url_params(raw_url: str) -> {}:
    result = {
        "url": "",
        "params": {}
    }

    if "?" not in raw_url:
        result["url"] = raw_url
    else:
        l = raw_url.split("?")
        result["url"] = l[0]

        ll = l[1].split("&")
        if len(ll) > 0:
            for item in ll:
                if "=" in item:
                    lll = item.split("=")
                    result["params"][lll[0]] = lll[1]

    return result


class Request():
    def __init__(self, byte_request) -> None:
        r = byte_request.decode("utf-8").split('\r\n')

        rr = r[0].split(' ')

        self.method: str = rr[0]
        self.url: dict = url_params(rr[1])
        self.ver: str = rr[2]

        self.host: str = val_from_str(r[1])
        self.connection: str = val_from_str(r[2])
        self.upgrade_insecure_requests: str = val_from_str(r[3])
        self.user_agent: str = val_from_str(r[4])
        self.accept: str = val_from_str(r[5])
        self.referer: str = val_from_str(r[6])
        self.accept_encoding: str = val_from_str(r[7])
        self.accept_language: str = val_from_str(r[8])


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

def_led = Pin('LED', Pin.OUT)
def_led_state = "OFF"

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
        
        # raw_request = request.decode("utf-8").split('\r\n')
        # print(raw_request)
        
        r = Request(request)
        # print(r.url)
        # print(url_params(r.url))
        print(r.url)

        
        request = str(request)

        try:
            request = request.split()
            
            request = request[1]
            # print('Request:', request)
        except IndexError as e:
            print(f'IndexError: {e}')
        
        # Process the request and update variables
        if request == '/lighton?':
            print("LED on")
            def_led.value(1)
            def_led_state = "ON"
        elif request == '/lightoff?':
            print("LED off")
            def_led.value(0)
            def_led_state = 'OFF'

        # Generate HTML response
        response = webpage(def_led_state)  

        # Send the HTTP response and close the connection
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except OSError as e:
        conn.close()
        print('Connection closed')