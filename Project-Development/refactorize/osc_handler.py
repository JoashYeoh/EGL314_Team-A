from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from constants import (ZONES)

# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_TARGET_IP = "127.0.0.1"    # IP of laptop running Multi-play
OSC_TARGET_PORT = 8888

osc_tx_multiPlay = udp_client.SimpleUDPClient(OSC_TARGET_IP, OSC_TARGET_PORT)


def start_game_bgm(state): #-- start game track

    print("START BUTTON PRESSED")
    osc_tx_multiPlay.send_message("/cue/1/go", "")

    state.game_music_started = True


def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/3/go", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/4/go", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/5/go", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/6/go", "")
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/3/stop", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/4/stop", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/5/stop", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/6/stop", "")

    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_expanded(zone_index): #-- when respective zone fully expanded, trigger stinger
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/7/go", "")
        osc_tx_multiPlay.send_message("/cue/3/stop", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/8/go", "")
        osc_tx_multiPlay.send_message("/cue/4/stop", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/9/go", "")
        osc_tx_multiPlay.send_message("/cue/5/stop", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/10/go", "")
        osc_tx_multiPlay.send_message("/cue/6/stop", "")

    print(f"[OSC] Zone {zone_index} Fully Expanded")


def send_game_over(tag_id, zone_label):  #-- when tag hit danger zone triger multiplay
    osc_tx_multiPlay.send_message("/stopall", "")
    osc_tx_multiPlay.send_message("/cue/2/go", "")

    print(
        f"[OSC] Sent Game Over "
        f"Tag={tag_id} Zone={zone_label}"
    )


def send_game_win():
    osc_tx_multiPlay.send_message("/stopall", "")
    osc_tx_multiPlay.send_message("/cue/11/go", "") # you win stinger
    print("WIN")