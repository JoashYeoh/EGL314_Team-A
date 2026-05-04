# This python script demonstrate OSC control on Raspberry Pi to Reaper
from pythonosc import udp_client


# ───────── CONFIGURE THIS ─────────
receiver_ip = "0.0.0.0"		# client IP (e.g. laptop with Reaper) 
receiver_port = 8000          # client listening port number (e.g. Reaper listening port number)	
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


# ───────── CALLING OF FUNTIONS ─────────

msg = float(1) # Trigger TRUE Value

# Play  Function in Reaper
send_message("/action/1007", msg)

# Pause Function in Reaper
send_message("/action/1008", msg)

# Stop Function in Reaper
send_message("/action/1016", msg)

# Play/Pause Function in Reaper
send_message("/action/40073", msg)

# Play/Stop Function in Reaper
send_message("/action/40044", msg)

# Jump to marker Function in Reaper
send_message(f"/reaper/action/40161", msg)	# this function can take markers from 1 - 10, after marker 10 it is a differnt function