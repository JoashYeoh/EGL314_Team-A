from threading import Timer

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from MVP.game.constants import *




# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
osc_tx_reaper = udp_client.SimpleUDPClient(OSC_REAPER_TARGET_IP, OSC_REAPER_TARGET_PORT)
osc_tx_gma3 = udp_client.SimpleUDPClient(OSC_GMA3_TARGET_IP, OSC_GMA3_TARGET_PORT)


def send_bgm():
    osc_tx_reaper.send_message("/action/41763", 1)  #jump to region 3
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/1007", 1) #play


def send_start_sequence():
    osc_tx_gma3.send_message("/gma3/cmd", "off sequence *")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 78")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 79")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 80")
    send_tutorial_cue()


def send_start_game(): 
    print("[OSC Reaper] START BUTTON PRESSED")
    #gma
    osc_tx_gma3.send_message("/gma3/cmd", "off Sequence 78")
    osc_tx_gma3.send_message("/gma3/cmd", "off Sequence 80")
    #reaper
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

    command = f"Goto Sequence {sequence} Cue {cue}"
    osc_tx_gma3.send_message("/gma3/cmd", command)
    print(f"Goto Sequence {sequence} Cue {cue}")


def send_tutorial_cue():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Sequence 8")




# ---------------------------------------------------------------------------
# End-of-game sequence
# ---------------------------------------------------------------------------

def send_game_end_default_lighting():
    """
    Sent immediately after Level 3 is completed.

    This should restore GrandMA to the desired default or neutral
    lighting state before the final show sequence begins.
    """

    osc_tx_gma3.send_message("/gma3/cmd", "off sequence *")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 78")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 79")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 80")
    send_level_win()
    Timer(2.0, send_pause_reaper).start()

    print(
        f"[OSC GMA3] Game-end default lighting: "
    )


def send_game_end_finale():
    """
    Sent after the game-end delay.

    Triggers the final GrandMA lighting sequence and the
    final REAPER audio sequence.
    """

    # ---------------------------------------------
    # GrandMA finale
    # ---------------------------------------------
    osc_tx_gma3.send_message("/gma3/cmd", "off sequence *")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 10")
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 1 Sequence 11")

    print(
        f"[OSC GMA3] Game-end finale: "
        f"SIREN!!"
    )

    # ---------------------------------------------
    # REAPER finale
    # ---------------------------------------------

    osc_tx_reaper.send_message("/action/40341", 1)   #mute all tracks
    osc_tx_reaper.send_message("/action/1068", 1) #toggle repeat
    osc_tx_reaper.send_message("/action/41762", 1)  #jump to region 2
    osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
    osc_tx_reaper.send_message("/action/40957", 1)    #select track 19
    osc_tx_reaper.send_message("/action/40731", 1)  #selected track unmute
    osc_tx_reaper.send_message("/action/1007", 1)  #play

    print("[OSC REAPER] Game-end finale triggered")