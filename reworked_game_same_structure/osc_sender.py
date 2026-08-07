from threading import Timer

from pythonosc import udp_client

from constants import *



osc_tx_reaper = udp_client.SimpleUDPClient(OSC_REAPER_TARGET_IP, OSC_REAPER_TARGET_PORT)
osc_tx_gma3 = udp_client.SimpleUDPClient(OSC_GMA3_TARGET_IP, OSC_GMA3_TARGET_PORT)


# ---------------------------------------------------------------------------
# Game Starting Sequences
# ---------------------------------------------------------------------------
def send_off_all(): #--game_manager.py
    osc_tx_gma3.send_message("/gma3/cmd", "Off Seq *")


def send_start_lobby(): #--game_manager.py
    #gma
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 1")
    #reaper
    osc_tx_reaper.send_message("/action/_RS4cb981b7c961f3b84673b9007ab7caa7bb13a182", 1) #set repeat
    osc_tx_reaper.send_message("/action/41764", 1)  #jump to region 4
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    #osc_tx_reaper.send_message("/action/40165", 1)   #jump marker 5
    osc_tx_reaper.send_message("/action/1007", 1) #play
    osc_tx_reaper.send_message("/action/_RS0a8bd5995464dc985213e2e1071132a46345050e", 1) #mute track 11-14


def send_start_tutorial(): #--game_manager.py
    #gma (can be made into a macro on gma)
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 2")
    #reaper
    osc_tx_reaper.send_message("/action/40168", 1)   #jump marker 8
    osc_tx_reaper.send_message("/action/40944", 1)    #select track 8
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play  
    Timer(20, send_start_tutorial_play).start()


def send_start_tutorial_play():
    #reaper
    osc_tx_reaper.send_message("/action/41763", 1)  #jump to region 3
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/1007", 1) #play


def send_start_game(): #--game_manager.py
    print("[OSC Reaper] START BUTTON PRESSED")
    #gma (can be made to a macro on gma)
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 3")
    #reaper (can use a custom command)
    osc_tx_reaper.send_message("/action/41761", 1)  #jump to region 1
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/1007", 1) #play
    osc_tx_reaper.send_message("/action/_RS0a8bd5995464dc985213e2e1071132a46345050e", 1) #mute track 11-14




# ---------------------------------------------------------------------------
# Tutorial Zone Logic Sequences
# ---------------------------------------------------------------------------
def send_tutorial_zone_enter(tag_id, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 2")
        osc_tx_reaper.send_message("/action/40949", 1)    #select track 11
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 2")
        osc_tx_reaper.send_message("/action/40950", 1)    #select track 12
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    print(
            f"[OSC] Sent Tutorial ENTER "
            f"Tag={tag_id} Zone={zone_name}"
        )


def send_tutorial_zone_exit(tag_id, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 1")
        osc_tx_reaper.send_message("/action/40949", 1)    #select track 11
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute

    if zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 1")
        osc_tx_reaper.send_message("/action/40950", 1)    #select track 12
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute

    print(
            f"[OSC] Sent Tutorial EXIT "
            f"Tag={tag_id} Zone={zone_name}"
        )


def send_tutorial_zone_max(zone_index, zone_label):
    zone_name = TUTORIAL_ZONES[zone_label]["label"]
    if zone_name == "TUTORIAL ZONE 1":
        #osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 107 cue 2")
        osc_tx_reaper.send_message("/action/40949", 1)    #select track 11
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute
        return

    if zone_name == "TUTORIAL ZONE 2":
        #osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 108 cue 2")
        osc_tx_reaper.send_message("/action/40950", 1)    #select track 12
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute
        return

    print(
            f"[OSC] Sent Tutorial CAPTURE "
            f"Tag={zone_index} Zone={zone_name}"
        )


def send_tutorial_danger_zone(): #--game_manager.py
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 106 cue 1")


# ---------------------------------------------------------------------------
# Zone Logic Sequences
# ---------------------------------------------------------------------------
def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 110 cue 2")
        osc_tx_reaper.send_message("/action/40949", 1)    #select track 11
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE B":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 111 cue 2")
        osc_tx_reaper.send_message("/action/40950", 1)    #select track 12
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE C":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 112 cue 2")
        osc_tx_reaper.send_message("/action/40951", 1)    #select track 13
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    if zone_name == "ZONE D":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 113 cue 2")
        osc_tx_reaper.send_message("/action/40952", 1)    #select track 14
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute

    if zone_name == "ZONE E":
        osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 114 cue 2")
        osc_tx_reaper.send_message("/action/40953", 1)    #select track 15
        osc_tx_reaper.send_message("/action/40731", 1)  #selected track toggle unmute
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 110 cue 1")
        osc_tx_reaper.send_message("/action/40949", 1)    #select track 11
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute
        
    if zone_name == "ZONE B":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 111 cue 1")
        osc_tx_reaper.send_message("/action/40950", 1)    #select track 12
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute

    if zone_name == "ZONE C":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 112 cue 1")
        osc_tx_reaper.send_message("/action/40951", 1)    #select track 13
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute
        
    if zone_name == "ZONE D":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 113 cue 1")
        osc_tx_reaper.send_message("/action/40952", 1)    #select track 14
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute

    if zone_name == "ZONE E":
        osc_tx_gma3.send_message("/gma3/cmd", "Go- Sequence 114 cue 1")
        osc_tx_reaper.send_message("/action/40953", 1)    #select track 15
        osc_tx_reaper.send_message("/action/40730", 1)  #selected track toggle mute
        
    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_game_over():  #--game_manager
    #gma
    osc_tx_gma3.send_message("/gma3/cmd", "Go Sequence 115")
    #reaper
    osc_tx_reaper.send_message("/action/40163", 1)   #jump marker 3
    osc_tx_reaper.send_message("/action/1007", 1) #play

    print(
        f"[OSC] Sent Game Over "
    )


def send_zone_e_manual_start(): #--game manager
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 2 Sequence 114")
    osc_tx_reaper.send_message("/action/41762", 1)  #jump to region 2
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/40952", 1)  #select track 14 
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play
    print("[OSC] Starting Zone E manual expansion")


def send_pause_reaper():
    osc_tx_reaper.send_message("/action/1008", 1) #pause



# ---------------------------------------------------------------------------
# End-of-game sequence
# ---------------------------------------------------------------------------
def send_phase_one_complete():
    """
    Triggered once after Zones A-D are captured.
    """

    print("[OSC] Zones A-D captured — starting Phase 2")

    # GrandMA:
    osc_tx_gma3.send_message("/gma3/cmd", "Off Sequence 106")
    # Reaper
    # Jump to Ending AI Voice Marker (station 1 complete)
    osc_tx_reaper.send_message("/action/40169", 1)   #jump marker 9
    osc_tx_reaper.send_message("/action/40944", 1)    #select track 8
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1) #play   


def send_game_win():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 5")

    print(
        f"[OSC GMA3] Game-end default lighting: "
    )


def send_game_end_finale():
    #reaper 
    # send initatise station 2
    osc_tx_reaper.send_message("/action/40166", 1)   #jump marker 6

    print("[OSC REAPER] Game-end finale triggered: AI Voice Playing...")


# ---------------------------------------------------------------------------
# New game flow: called once when a zone reaches maximum size
# ---------------------------------------------------------------------------
def send_zone_complete(zone_index):
    zone_name = ZONES[zone_index]["label"]

    #----------------GrandMA3 Commands-----------------
    sequence_map = {
        "ZONE A": 110,
        "ZONE B": 111,
        "ZONE C": 112,
        "ZONE D": 113,
        "ZONE E": 114,  # Change this to the actual GrandMA sequence
    }
    sequence = sequence_map.get(zone_name)
    if sequence is not None:
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Cue 4 Sequence {sequence}")
    print(f"[OSC MA3] Zone completed: {zone_name} cue go")


    
