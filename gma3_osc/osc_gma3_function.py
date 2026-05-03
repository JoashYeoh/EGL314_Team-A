# This python script demonstrate OSC control on Raspberry Pi to GrandMA3
from pythonosc import udp_client, osc_message_builder
import time


# ───────── CONFIGURE THIS ─────────
receiver_ip = "0.0.0.0"		# client IP (e.g. laptop with grandMA3) 
receiver_port = 8080                # client listening port number (e.g. grandMA3 listening port number)
addr = "/gma3/cmd"		# /<Must match the Prefix in GrandMA3 In & Out Configuration>/cmd
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


# Math Function to convert Values to Command line Values to GMA3 Values e.g. pan; -315 = 0 = -315, pan; 315 = 65535 = 315
def GMA3_Value_Converter(y, y_min, y_max, x_min=0, x_max=65535):
    y = max(min(y, y_max), y_min)  # clamp y
    return int(round((y - y_min) * (x_max - x_min) / (y_max - y_min) + x_min))


def set_attribute(fixture: str, attribute: str, value: float, y_min: float, y_max: float):
    # Convert to GMA3 absolute value
    gma_value = GMA3_Value_Converter(value, y_min, y_max)
    # Send Messages
    send_message(addr, fixture)
    send_message(addr, f"Attribute '{attribute}' At Absolute Decimal16 {gma_value}")



# ───────── CALLING OF FUNTIONS ─────────

set_attribute("Fixture 1", "tilt", 90, -125, 125)	# tilt / pan 

send_message(addr, "Fixture 1 At Preset 21.1")	# triggering preset 21.1 on Fixture 1

send_message(addr, "Go Sequence 1")	# Go+ on Sequence 1

send_message(addr, "Goto Cue 3 Sequence 1")	# Jump to Cue 3 on Sequence 1

send_message(addr, "Fixture 1 At 50") # Set Fixture 1 brightness to 50%