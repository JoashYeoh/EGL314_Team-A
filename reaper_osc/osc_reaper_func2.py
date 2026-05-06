# This python script demonstrate OSC control on Raspberry Pi to Reaper
from pythonosc import udp_client
import time


# ───────── CONFIGURE THIS ─────────
receiver_ip = "192.168.254.62"		# client IP (e.g. laptop with Reaper) 
receiver_port = 8000                # client listening port number (e.g. Reaper listening port number)	
# ──────────────────────────────────


# Create an OSC client to send messages
client = udp_client.SimpleUDPClient(receiver_ip, receiver_port)

def send_message(address, message):
	try:
		# Send an OSC message to the receiver
		client.send_message(address, message)

		print("Message sent successfully.")
	except:
		print("Message not sent")



msg = float(1)

def cue1():
    send_message("/action/_cc5f46ed829e9648bf3fb5f8e27b8491", msg)

def cue2():
    send_message("/action/_1a852e88880d4942ab7bacfc7d85e591", msg)

def pause():
    send_message("/action/1008", msg)
    

def handle_input(source, command):
    if command == "cue1":
        cue1()
    elif command == "cue2":
        cue2()
    elif command == "pause":
        pause()
        

handle_input("test", "cue1")
time.sleep(1)

handle_input("test", "pause")
time.sleep(1)

handle_input("test", "cue2")
time.sleep(1)