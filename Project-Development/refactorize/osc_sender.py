from threading import Timer

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from constants import *




# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
osc_tx_reaper = udp_client.SimpleUDPClient(OSC_REAPER_TARGET_IP, OSC_REAPER_TARGET_PORT)
osc_tx_gma3 = udp_client.SimpleUDPClient(OSC_GMA3_TARGET_IP, OSC_GMA3_TARGET_PORT)



def send_start_game_bgm(): #-- start game track

    print("START BUTTON PRESSED")
    #start
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat
    osc_tx_reaper.send_message("/action/41761", 1)  #jump to region 1
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/40955", 1)  #select track 17
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play


def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 2")
        osc_tx_reaper.send_message("/action/40958", 1)    #select track 20
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE B":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 3")
        osc_tx_reaper.send_message("/action/40959", 1)    #select track 21
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE C":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 4")
        osc_tx_reaper.send_message("/action/40960", 1)    #select track 22
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    if zone_name == "ZONE D":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 5")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 23
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )

def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 2 Sequence 2")
        osc_tx_reaper.send_message("/action/40958", 1)    #select track 4
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE B":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 2 Sequence 3")
        osc_tx_reaper.send_message("/action/40959", 1)    #select track 5
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE C":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 2 Sequence 4")
        osc_tx_reaper.send_message("/action/40960", 1)    #select track 6
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute
    
    if zone_name == "ZONE D":
        #--osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 2 Sequence 5")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 7
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_game_over():  #-- when tag hit danger zone triger multiplay
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40162", 1)   #jump marker 2
    osc_tx_reaper.send_message("/action/40956", 1)    #select track 18
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat

    print(
        f"[OSC] Sent Game Over "
    )


def send_game_win():
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40163", 1)   #jump marker 3
    osc_tx_reaper.send_message("/action/40957", 1)    #select track 19
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1)  #play
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat
    
    print("[OSC] WIN")


def send_pause_reaper():
    osc_tx_reaper.send_message("/action/1008", 1) #pause




def send_zone_cue(zone, cue):
    zone_name = zone["label"]

    if zone_name == "ZONE A":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue {cue} Sequence 2")

    if zone_name == "ZONE B":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue {cue} Sequence 3")

    if zone_name == "ZONE C":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue {cue} Sequence 4")
    
    if zone_name == "ZONE D":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue {cue} Sequence 5")

    print(
        f"[OSC GMA3] Sent "
        f"Cue {cue} {zone_name}"
    )


def send_danger_movement():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Sequence 6")
    osc_tx_gma3.send_message("/gma3/cmd", "Go Sequence 7")

    print(
        f"[OSC GMA3] Sent "
        f"Go Sequence 6 & 7"
    )
