
from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from constants import *
from shared_sate import *
from trilateration import trilaterate_2d
from zones import *





# ---------------------------------------------------------------------------
# OSC handler — called from the OSC server thread for every distances message
# ---------------------------------------------------------------------------
def make_osc_handler(state: SharedState, anchor_ids, anchor_positions_list,
                    csv_writer=None):
    def handle_distances(address, *args):
        if not state.game_started:
            return

        if state.stop: return 

        if len(args) < 9:
            print(f"[osc] malformed message (got {len(args)} args)")
            return

        tag_id    = int(args[0])
        if state.simulate and tag_id == 0: #-- Ignore real update of tag 0 if simulation is active
            return
        distances = [float(v) for v in args[1:9]]

        if tag_id >= state.n_tags:
            return

        tag = state.tags[tag_id]
        dist_for_trilat = [distances[i] for i in anchor_ids]
        raw_pos = trilaterate_2d(anchor_positions_list, dist_for_trilat)

        with state.lock:
            tag.last_distances = distances
            tag.last_update = time.time()
            if raw_pos is not None:
                tag.kalman.predict()
                fx, fy = tag.kalman.update(raw_pos[0], raw_pos[1])
                tag.raw_position  = raw_pos
                tag.filt_position = (fx, fy)
                
                current_zones = set()
                for zi, zone in enumerate(ZONES):
                    if point_in_zone(tag.filt_position, zone):
                        current_zones.add(zi)

                entered = current_zones - tag.zones_inside
                exited  = tag.zones_inside - current_zones

                for zi in entered:
                    zone = ZONES[zi]
                    if zone.get("captured"): # checks if zone is already captured, so as to not re-trigger osc
                        continue
                    print(f"[ZONE] Tag {tag_id} ENTERED {ZONES[zi]['label']}")
                    send_zone_enter(tag_id, zi)

                for zi in exited:
                    print(f"[ZONE] Tag {tag_id} EXITED {ZONES[zi]['label']}")
                    send_zone_exit(tag_id, zi)

                tag.zones_inside = current_zones
            else:
                tag.kalman.predict()
            
            state.frame_count += 1

        if csv_writer is not None:
            row_data = [time.time(), tag_id, COLOR_NAMES[state.row_color_index[tag_id]]]
            row_data += [f"{distances[i]:.3f}" for i in anchor_ids]
            if raw_pos is not None:
                row_data += [f"{raw_pos[0]:.3f}", f"{raw_pos[1]:.3f}"]
            else:
                row_data += ["", ""]
            if tag.filt_position is not None:
                row_data += [f"{tag.filt_position[0]:.3f}", f"{tag.filt_position[1]:.3f}"]
            else:
                row_data += ["", ""]
            csv_writer.writerow(row_data)

    return handle_distances




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
