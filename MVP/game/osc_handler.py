import time

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

from MVP.game.constants import *

from MVP.game.trilateration import trilaterate_2d

from MVP.game.shared_state import SharedState

"""from zones import point_in_zone"""

from MVP.game.osc_sender import *


# ---------------------------------------------------------------------------
# OSC handler — called from the OSC server thread for every distances message
# ---------------------------------------------------------------------------
def make_osc_handler(state: SharedState, anchor_ids, anchor_positions_list,
                    csv_writer=None):
    def handle_distances(address, *args):
        if not state.game_started:
            return

        if state.stop:
            return 

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
                
                """current_zones = set()
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

                tag.zones_inside = current_zones"""
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