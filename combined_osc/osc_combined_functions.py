import time
from pythonosc import udp_client

# ───────── CONFIGURE THIS ─────────
Server_IP = "192.168.254.149"   # Use "127.0.0.1" if GrandMA3 is on the same PC
Server_PORT = 2000 # Must match OSC Input port in GrandMA3 (ST default often 8000)
# ──────────────────────────────────

# Function for Sending OSC Messages
def send_message(address: str, message: str):
    try:
        client = udp_client.SimpleUDPClient(Server_IP, Server_PORT)
        client.send_message(address, message)
        print(f"Sent: {message}")
    except Exception as e:
        print(f"Message not sent: {e}")


# GrandMA Functions
addr = "/gma3/cmd"

# Math Function to convert Values to Command line Values to GMA3 Values e.g. pan; -315 = 0 = -315, pan; 315 = 65535 = 315
def GMA3_Value_Converter(y, y_min, y_max, x_min=0, x_max=65535):
    y = max(min(y, y_max), y_min)  # clamp y
    return int(round((y - y_min) * (x_max - x_min) / (y_max - y_min) + x_min))

def gma_pan(fixture: str, value: float, y_min: float, y_max: float):
    # Convert to GMA3 absolute value
    gma_pan_value = GMA3_Value_Converter(value, y_min, y_max)
    send_message(addr, fixture)
    send_message(addr, f"Attribute pan At Absolute Decimal16 {gma_pan_value}")

def gma_tilt(fixture: str, value: float, y_min: float, y_max: float):
    # Convert to GMA3 absolute value
    gma_tilt_value = GMA3_Value_Converter(value, y_min, y_max)
    send_message(addr, fixture)
    send_message(addr, f"Attribute tilt At Absolute Decimal16 {gma_tilt_value}")
 
def gma_preset(fixture: str, value: int):
    send_message(addr, f"{fixture} At Preset {value}")

def gma_go(value: int):
    send_message(addr, f"Go Sequence {value}")

def gma_cue(value: int, value2: int):
    send_message(addr, f"Goto Cue {value} Sequence {value2}")

def gma_dimmer(fixture: str, value: int):
    send_message(addr, f"{fixture} At {value}")




# Reaper Functions
msg = float(1) # Trigger TRUE Value

def reaper_play():
    send_message("/action/1007", msg)

def reaper_pause():
    send_message("/action/1008", msg)

def reaper_play_pause():
    send_message("/action/40073", msg)

def reaper_stop():
    send_message("/action/1016", msg)

def reaper_play_stop():
    send_message("/action/40044", msg)

def reaper_marker(marker_no: int):
    #addr = "/action/40161" # Jump to Marker One
    if marker_no <= 10:
        send_message(f"/action/4016{str(marker_no)}", msg)
    elif marker_no > 10:
        return print("reaper marker error. Please input a marker ID between 1 to 10")
    

def handle_input(source, command):
    if command == "cue1":
        reaper_marker(1)
    elif command == "cue2":
        reaper_marker(2)
    elif command == "pause":
        reaper_pause()
    elif command == "play":
        reaper_play()



# L-ISA Functions
def lisa_pan(degrees):
    # math to convert pan degree value to corresponding pan float value
    degrees = max(-180.0, min(180.0, float(degrees)))
    pan = (degrees + 180.0) / 360.0

    addr = "/ext/src/1/p"
    send_message(addr, pan)

def lisa_distance(percent): 
    # math to convert distance value to corresponding distance float value
    percent = max(0.0, min(100.0, float(percent)))
    distance = percent / 100.0

    addr = "/ext/src/1/d"
    send_message(addr, distance)

def lisa_fx(fx):
    addr = "/ext/src/1/send/1"
    send_message(addr, fx)


# ────────────────── BACKLOG 1 SPRINT 1 ──────────────────
# ───────── CALLING OF FUNTIONS ─────────
"""
lisa_pan(180)  #lisa_pan(float(1)) # 0 -> -180deg, 0.5 -> 0deg,  1 -> 180deg
lisa_distance(60)  # 0 -> 0%, 1 -> 100%
lisa_fx(float(0))  # 0 -> off, 0.5 -> -6dB,  1 -> 0dB


gma_dimmer("Fixture 1", 20)  # Fixture number, dimmer value
gma_tilt("Fixture 1", 90, -125, 125)  # Fixture number, angle in degrees, min value on MA, max value on MA
gma_pan("Fixture 1", -45, -315, 315)
gma_preset("Fixture 1", 21.1)  # Fixture number, preset number
gma_go(1)  # go+ on sequence __
gma_cue(2, 1)  # goto cue __ on sequence __


reaper_marker(2)  # jump to maker __
reaper_play() 
"""

# ────────────────── BACKLOG 1 SPRINT 2 ──────────────────
# ───────── CALLING OF FUNTIONS ─────────

# From 00:00:00:00
handle_input("test", "play") # Reaper Start tracks
gma_cue(1,1) # Trigger cue 1 of sequence 1
time.sleep(7)

handle_input("test", "pause") # Reaper Pause
time.sleep(3)

## Makrer 1
handle_input("test", "cue1") # Reaper Jump to marker 1
handle_input("test", "play") # Reaper continue lay tracks
gma_cue(2,1) # Trigger cue 2 of sequence 1
time.sleep(10)

handle_input("test", "pause") # Reaper Pause
time.sleep(3)

## Makrer 2
handle_input("test", "cue2") # Repaer Jump to marker 2
handle_input("test", "play") # Reaper continue lay tracks
gma_cue(3,1) # Trigger cue 3 of sequence 1
time.sleep(10)

handle_input("test", "pause") # Reaper pause (end of show)
