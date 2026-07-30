from threading import Timer

from pythonosc import udp_client

from constants import *



osc_tx_reaper = udp_client.SimpleUDPClient(OSC_REAPER_TARGET_IP, OSC_REAPER_TARGET_PORT)
osc_tx_gma3 = udp_client.SimpleUDPClient(OSC_GMA3_TARGET_IP, OSC_GMA3_TARGET_PORT)


# ---------------------------------------------------------------------------
# Game Starting Sequences
# ---------------------------------------------------------------------------
def send_off_all():
    osc_tx_gma3.send_message("/gma3/cmd", "Off Seq *")

def send_start_lobby():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 99 cue 1")
    return

def send_start_tutorial():
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 109 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 1")
    return

def send_start_game(): 
    print("[OSC Reaper] START BUTTON PRESSED")
    #gma
    osc_tx_gma3.send_message("/gma3/cmd", "off Sequence 99")
    osc_tx_gma3.send_message("/gma3/cmd", "off Sequence 100 fade 5")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 106 cue 2")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 110 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 111 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 112 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 113 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 114 cue 1")
    #reaper
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat
    osc_tx_reaper.send_message("/action/41761", 1)  #jump to region 1
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/40955", 1)  #select track 17
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play



# ---------------------------------------------------------------------------
# Tutorial Zone Logic Sequences
# ---------------------------------------------------------------------------
def send_tutorial_zone_enter(tag_id, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 2")

    if zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 2")

    print(
            f"[OSC] Sent Tutorial ENTER "
            f"Tag={tag_id} Zone={zone_name}"
        )

def send_tutorial_zone_exit(tag_id, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 1")

    if zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 1")

    print(
            f"[OSC] Sent Tutorial EXIT "
            f"Tag={tag_id} Zone={zone_name}"
        )

def send_tutorial_zone_max(zone_index, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        #osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 2")
        return

    if zone_name == "TUTORIAL ZONE 2":
        #osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 2")
        return

    print(
            f"[OSC] Sent Tutorial CAPTURE "
            f"Tag={zone_index} Zone={zone_name}"
        )

def send_tutorial_danger_zone():
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 106 cue 1")


# ---------------------------------------------------------------------------
# Zone Logic Sequences
# ---------------------------------------------------------------------------
def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 110 cue 2")
        osc_tx_reaper.send_message("/action/40958", 1)    #select track 20
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE B":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 111 cue 2")
        osc_tx_reaper.send_message("/action/40959", 1)    #select track 21
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE C":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 112 cue 2")
        osc_tx_reaper.send_message("/action/40960", 1)    #select track 22
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    if zone_name == "ZONE D":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 113 cue 2")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 23
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE E":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 114 cue 2")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 23
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 110 cue 1")
        osc_tx_reaper.send_message("/action/40958", 1)    #select track 20
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE B":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 111 cue 1")
        osc_tx_reaper.send_message("/action/40959", 1)    #select track 21
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE C":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 112 cue 1")
        osc_tx_reaper.send_message("/action/40960", 1)    #select track 22
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute
    
    if zone_name == "ZONE D":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 113 cue 1")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 23
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    if zone_name == "ZONE E":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 114 cue 1")
        osc_tx_reaper.send_message("/action/40961", 1)    #select track 23
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track mute

    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


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


def send_danger_movement(axis, cue):
    if axis == "horizontal":
        sequence = 6
    elif axis == "vertical":
        sequence = 7
    else:
        print(f"Unknown danger axis: {axis}")
        return

    command = f"Goto Cue {cue} Sequence {sequence}"
    osc_tx_gma3.send_message("/gma3/cmd", command)
    print(f"Goto Cue {cue} Sequence {sequence}")


def send_game_over():  #-- when tag hit danger zone
    osc_tx_gma3.send_message("/gma3/cmd", "off Sequence *")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 115 cue 1")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 78 cue 1")
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40162", 1)   #jump marker 2
    osc_tx_reaper.send_message("/action/40956", 1)    #select track 18
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat

    print(
        f"[OSC] Sent Game Over "
    )


def send_level_win():
    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/40163", 1)   #jump marker 3
    osc_tx_reaper.send_message("/action/40957", 1)    #select track 19
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1)  #play
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat
    
    print("[OSC] WIN")


def send_pause_reaper():
    osc_tx_reaper.send_message("/action/1008", 1) #pause



# ---------------------------------------------------------------------------
# End-of-game sequence
# ---------------------------------------------------------------------------

def send_game_win():
    """
    Sent when game win.

    Triggers the final GrandMA lighting sequence and the
    final REAPER audio sequence.
    """
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 2")

    print(
        f"[OSC GMA3] Game-end default lighting: "
    )

    osc_tx_reaper.send_message("/action/41266", 1)   #jump to game win marker
    


def send_game_end_finale():
    """
    Sent after the game-end delay.

    Triggers the final GrandMA lighting sequence and the
    final REAPER audio sequence.
    """
    osc_tx_reaper.send_message("/action/40163", 1)   # Jump to Ending AI Voice Marker

    print("[OSC REAPER] Game-end finale triggered: AI Voice Playing...")


# ---------------------------------------------------------------------------
# New game flow: called once when a zone reaches maximum size
# ---------------------------------------------------------------------------
def send_zone_complete(zone_index):
    zone_name = ZONES[zone_index]["label"]
    sequence_map = {
        "ZONE A": 110,
        "ZONE B": 111,
        "ZONE C": 112,
        "ZONE D": 113,
        "ZONE E": 114,  # Change this to the actual GrandMA sequence for Zone E.
    }
    sequence = sequence_map.get(zone_name)
    if sequence is not None:
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue 4 Sequence {sequence}")
    print(f"[OSC] Zone completed: {zone_name}")
