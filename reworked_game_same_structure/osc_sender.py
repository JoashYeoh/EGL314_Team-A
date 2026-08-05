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
    osc_tx_reaper.send_message("/action/40165", 1)   #jump marker 5
    osc_tx_reaper.send_message("/action/1007", 1) #play


def send_start_tutorial(): #--game_manager.py
    #gma (can be made into a macro on gma)
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 2")
    #reaper
    osc_tx_reaper.send_message("/action/_RSd6b802469d33dd40ead7bba016f569c8736f3782", 1)

def send_start_game(): #--game_manager.py
    print("[OSC Reaper] START BUTTON PRESSED")
    #gma (can be made to a macro on gma)
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 3")
    #reaper (can use a custom command)
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

    """#----------------Reaper Commands-----------------
    command_map = {
        "ZONE A": "_RS9398b62661e7c0931372878419d3f8f484112f74",
        "ZONE B": "_RS7515f5bc23cee9d17ce0fe0b3e7198e8a9eefa32",
        "ZONE C": "_RSf2009195414f90a4f40e7ee126f1193ff8921f6c",
        "ZONE D": "__RSb05e823170847907534ab5c8a4863a26507367bf",
        "ZONE E": "_RS7816dbdbd6cf50427fcabbb09b4329025e9534a8",  # Change this to the actual reaper command ID
    }
    command = command_map.get(zone_name)
    if command is not None:
        osc_tx_reaper.send_message(f"/action/{command}", 1)
    print(f"[OSC REAPER] Zone Exit: {zone_name} track fading out")
    print(f"[OSC REAPER] /action/{command}")"""


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

    """#----------------Reaper Commands-----------------
    command_map = {
        "ZONE A": "_RSa21f7316b8de7e468ed00684a916e1c28555ff2c",
        "ZONE B": "_RSa708927ed64312a4bf7fa340d14215a24b6229f4",
        "ZONE C": "_RS36767b1431746ce2ac75501409672132e52f48f4",
        "ZONE D": "_RS279ab297469ef56c2494673aa30f44aa012517cb",
        "ZONE E": "_RSae550719a358baee9bcf2274f393cd11ea8e4d21",  # Change this to the actual reaper command ID
    }
    command = command_map.get(zone_name)
    if command is not None:
        osc_tx_reaper.send_message(f"/action/{command}", 1)
    print(f"[OSC REAPER] Zone Exit: {zone_name} track fading out")
    print(f"[OSC REAPER] /action/{command}")"""


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
    osc_tx_reaper.send_message("/action/40953", 1)  #select track 15 
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

    # GrandMA example:
    osc_tx_gma3.send_message("/gma3/cmd", "Off Sequence 106")


def send_game_win():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 5")

    print(
        f"[OSC GMA3] Game-end default lighting: "
    )


def send_game_end_finale():
    osc_tx_reaper.send_message("/action/_RSe45b27b7d1b182ebf3023fcbef4960fc36e87626", 1)   # Jump to Ending AI Voice Marke

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

    """#----------------Reaper Commands-----------------
    command_map = {
        "ZONE A": "_RS96f4032a72f7526436170776848754bc047bc4b0",
        "ZONE B": "_RS8a0090cf315a283032f73526614a2b9b270db77d",
        "ZONE C": "_RS8e7e21b5dac0c5b2603073e94fdacb248b6212a8",
        "ZONE D": "_RS4ad29f7140dd40094aff3a9424c3d09b277525b2",
        "ZONE E": "_RS55d0260ebe69ccc552a007c201f6c1fadc475179",  # Change this to the actual reaper command ID
    }
    command = command_map.get(zone_name)
    if command is not None:
        osc_tx_reaper.send_message(f"/action/{command}", 1)
    print(f"[OSC REAPER] Zone completed: {zone_name} track fading out")
    print(f"[OSC REAPER] /action/{command}")"""


    
