
from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from constants import *




# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
osc_tx_reaper = udp_client.SimpleUDPClient(OSC_TARGET_IP, OSC_TARGET_PORT)


def send_start_game_bgm(): #-- start game track

    print("START BUTTON PRESSED")
    #start
    osc_tx_reaper.send_message("/action/40161", 1)   #jump marker 1
    osc_tx_reaper.send_message("/action/40804", 1)    #select track 1
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play


def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_reaper.send_message("/action/40807", 1)    #select track 4
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE B":
        osc_tx_reaper.send_message("/action/40808", 1)    #select track 5
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE C":
        osc_tx_reaper.send_message("/action/40809", 1)    #select track 6
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    if zone_name == "ZONE D":
        osc_tx_reaper.send_message("/action/40810", 1)    #select track 7
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_reaper.send_message("/action/40807", 1)    #select track 4
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE B":
        osc_tx_reaper.send_message("/action/40808", 1)    #select track 5
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE C":
        osc_tx_reaper.send_message("/action/40809", 1)    #select track 6
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute
    
    if zone_name == "ZONE D":
        osc_tx_reaper.send_message("/action/40810", 1)    #select track 7
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


"""
def send_zone_expanded(zone_index): #-- when respective zone fully expanded, trigger stinger
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_reaper.send_message("/cue/7/go", "")
        osc_tx_reaper.send_message("/cue/3/stop", "")

    if zone_name == "ZONE B":
        osc_tx_reaper.send_message("/cue/8/go", "")
        osc_tx_reaper.send_message("/cue/4/stop", "")

    if zone_name == "ZONE C":
        osc_tx_reaper.send_message("/cue/9/go", "")
        osc_tx_reaper.send_message("/cue/5/stop", "")
    
    if zone_name == "ZONE D":
        osc_tx_reaper.send_message("/cue/10/go", "")
        osc_tx_reaper.send_message("/cue/6/stop", "")

    print(f"[OSC] Zone {zone_index} Fully Expanded")
"""

def send_game_over():  #-- when tag hit danger zone triger multiplay
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40162", 1)   #jump marker 2
    osc_tx_reaper.send_message("/action/40805", 1)    #select track 2
    osc_tx_reaper .send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play

    print(
        f"[OSC] Sent Game Over "
    )


def send_game_win():
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40163", 1)   #jump marker 3
    osc_tx_reaper.send_message("/action/40806", 1)    #select track 3
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play
    
    print("[OSC] WIN")


def send_pause_reaper():
    osc_tx_reaper.send_message("/action/1008", 1) #pause


