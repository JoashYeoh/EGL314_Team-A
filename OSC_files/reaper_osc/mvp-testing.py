# This python script demonstrate OSC control on Raspberry Pi to Reaper
from pythonosc import udp_client
import time

# ───────── CONFIGURE THIS ─────────
receiver_ip = "192.168.1.108"		# client IP (e.g. laptop with Reaper) 
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

"""print("START BUTTON PRESSED")
#start
send_message("/action/40161", 1)   #jump marker 1
send_message("/action/40804", 1)    #select track 1
send_message("/action/40731", 1)  #selected track unmute
send_message("/action/1007", 1) #play

#lost
send_message("/action/40341", 1)   #mute all tracks
send_message("/action/40162", 1)   #jump marker 2
send_message("/action/40805", 1)    #select track 2
send_message("/action/40731", 1)  #selected track unmute
send_message("/action/1007", 1) #play
time.sleep(2)
send_message("/action/1008", 1) #pause

#won
send_message("/action/40341", 1)   #mute all tracks
send_message("/action/40163", 1)   #jump marker 3
send_message("/action/40806", 1)    #select track 3
send_message("/action/40731", 1)  #selected track unmute
send_message("/action/1007", 1) #play
time.sleep(2)
send_message("/action/1008", 1) #pause

#zone1occu
send_message("/action/40807", 1)    #select track 4
send_message("/action/40731", 1)  #selected track toggle unmute

#zone2occu
send_message("/action/40808", 1)    #select track 5
send_message("/action/40731", 1)  #selected track toggle unmute

#zone3occu
send_message("/action/40809", 1)    #select track 6
send_message("/action/40731", 1)  #selected track toggle unmute

#zone4occu
send_message("/action/40810", 1)    #select track 7
send_message("/action/40731", 1)  #selected track toggle mute/unmute

#zone1un
send_message("/action/40807", 1)    #select track 4
send_message("/action/40730", 1)  #selected track mute

#zone2un
send_message("/action/40808", 1)    #select track 5
send_message("/action/40730", 1)  #selected track mute

#zone3un
send_message("/action/40809", 1)    #select track 6
send_message("/action/40730", 1)  #selected track mute

#zone4un
send_message("/action/40810", 1)    #select track 7
send_message("/action/40730", 1)  #selected track mute"""


send_message("/action/1068", 1) #toggle repeat
send_message("/action/41761", 1) #jump to region
send_message("/action/43102", 1) #set loop points to region
send_message("/action/1007", 1) #play
