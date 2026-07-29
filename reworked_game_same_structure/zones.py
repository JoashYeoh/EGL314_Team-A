import random
from constants import TUTORIAL_ZONES,ZONES,ALL_ZONES,DANGER_BOUNDS,ZONE_HIT_TOLERANCE
from osc_sender import send_zone_enter,send_zone_exit,send_zone_complete,send_danger_movement


# ---------------------------------------------------------------------------
# Zone detection
# ---------------------------------------------------------------------------
def point_in_zone(point,zone):
    if point is None:
        return False
    
    px,py=point
    zx,zy=zone['center']
    r=zone['radius']+ZONE_HIT_TOLERANCE
    
    return (px-zx)**2+(py-zy)**2<=r*r   # a^2 + b^2 = c^2


def zone_is_occupied(zone,tags):
    for tag in tags:
            if tag.filt_position is None:
                continue
            if point_in_zone(tag.filt_position, zone):
                return True
    return False


def safe_zones(zone_list=None): 
    if zone_list is None:
        zone_list = ZONES
    return [z for z in ZONES if z.get('safe')]


def reset_zone_list(zone_list):
    for zone in zone_list:
        if not zone.get("safe"):
            continue

        zone["radius"] = zone["min_radius"]
        zone["captured"] = False
        zone["expanded_sent"] = False
        zone["active"] = False


def reset_zones(state):
    # Reset game zones.
    reset_zone_list(ZONES)
    # Reset tutorial zones.
    reset_zone_list(TUTORIAL_ZONES)
    # Clear which zones each tag thinks it is inside.
    for tag in state.tags:
        tag.zones_inside.clear()


def process_zone_transitions(tag_id, tag):
    current = set()
    zone_lookup = {}

    for zone in ALL_ZONES:
        if not zone.get("safe"):
            continue
        if not zone.get("active", True):
            continue

        zone_label = zone["label"]
        zone_lookup[zone_label] = zone

        if point_in_zone(tag.filt_position, zone):
            current.add(zone_label)

    entered = current - tag.zones_inside
    exited = tag.zones_inside - current

    for zone_label in entered:
        zone = zone_lookup[zone_label]

        print(
            f"[ZONE] Tag {tag_id} ENTERED "
            f"{zone_label}"
        )

        # Tutorial zones should not trigger normal game-zone OSC.
        if not zone.get("tutorial"):
            zone_index = ZONES.index(zone)
            send_zone_enter(tag_id, zone_index) # OSC

    for zone_label in exited:
        zone = next(
            (item for item in ALL_ZONES
                if item["label"] == zone_label
            ),
            None,
        )

        print(
            f"[ZONE] Tag {tag_id} EXITED "
            f"{zone_label}"
        )

        if zone is not None and not zone.get("tutorial"):
            zone_index = ZONES.index(zone)
            send_zone_exit(tag_id, zone_index) # OSC

    tag.zones_inside = current

    return entered, exited



# ---------------------------------------------------------------------------
#  Zone Grow Logic 
# ---------------------------------------------------------------------------
def update_zones(state):
    for zone in ALL_ZONES:
        if not zone.get("safe"):
            continue

        if not zone.get("active", True):
            continue

        is_tutorial = zone.get("tutorial", False)

        # Captured zones remain at maximum size if not in tutorial mode
        if zone.get("captured") and not is_tutorial:
            zone["radius"] = zone["max_radius"]
            continue

        # Zone expands when tag enters
        if zone_is_occupied(zone, state.tags):
            zone["radius"] = min(
                zone["max_radius"],
                zone["radius"] + zone["expand_rate"],
            )
            # When zone reaches maximum, set state as 'captured'
            if zone["radius"] >= zone["max_radius"]:
                if not zone.get("tutorial", False):
                    zone["captured"] = True

                    if not zone["expanded_sent"]:
                        zone["expanded_sent"] = True
                        zone_index = ZONES.index(zone)
                        send_zone_complete(zone_index) # OSC

                # Only game zones send the complete-zone OSC cue.
                if (not zone.get("tutorial") and not zone["expanded_sent"]):
                    zone["expanded_sent"] = True
                    zone_index = ZONES.index(zone)
                    send_zone_complete(zone_index) # OSC
        # Zone shrinks if tag not in zone
        else:
            zone["radius"] = max(zone["min_radius"],zone["radius"] - zone["shrink_rate"],)


def all_safe_zones_captured():
    return all(z.get('captured',False) for z in safe_zones())


# ---------------------------------------------------------------------------
#  Danger Zone Movement Logic 
# ---------------------------------------------------------------------------
def initialise_danger_zones():
    for z in ZONES:
        if not z.get('is_danger'):
            continue

        z['active']=True
        z['center']=z['start_center']

        direction=random.choice([-1,1])
        if z['axis']=='horizontal': z['velocity']=[abs(z['velocity'][0])*direction,0.0]
        else: z['velocity']=[0.0,abs(z['velocity'][1])*direction]


def update_danger_zones(state):
    xmin,xmax,ymin,ymax=DANGER_BOUNDS
    for z in ZONES:
        if not z.get('is_danger') or not z.get('active',True):
            continue

        x,y=z['center']
        vx,vy=z['velocity']
        r=z['radius']
        x+=vx; y+=vy

        if x-r<xmin or x+r>xmax:
            vx=-vx
            x=max(xmin+r,min(xmax-r,x))

        if y-r<ymin or y+r>ymax:
            vy=-vy
            y=max(ymin+r,min(ymax-r,y))

        z['center']=(x,y)
        z['velocity']=[vx,vy]
