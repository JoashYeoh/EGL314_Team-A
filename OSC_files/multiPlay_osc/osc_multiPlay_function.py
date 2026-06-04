# Huats 2023 oscstarterkit
# This python script can be used to control Multiplay 3 software
# For more infomation, please refer to 
# http://da-share.com/help/multiplay3/OSC-Control-Cue-Actions.html
from pythonosc import udp_client

def send_message(receiver_ip, receiver_port, address, message):
  try:
    # Create an OSC client to send messages
    client = udp_client.SimpleUDPClient(receiver_ip, receiver_port)

    # Send an OSC message to the receiver
    client.send_message(address, message)

    print("Message sent successfully.")
  except:
    print("Message not sent")

# FOR INFO: IP address and port of the receiving Raspberry Pi
PI_A_ADDR = "192.168.254.189"    # wlan ip
PORT = 8888 

send_message(PI_A_ADDR, PORT, "/cue/1/go", "")
