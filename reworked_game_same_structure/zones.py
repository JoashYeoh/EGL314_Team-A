import random
from constants import TUTORIAL_ZONES,ZONES,ALL_ZONES,DANGER_BOUNDS,ZONE_HIT_TOLERANCE
from osc_sender import send_zone_enter,send_zone_exit,send_zone_complete,send_danger_movement,send_tutorial_zone_enter,send_tutorial_zone_exit,send_tutorial_zone_max


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


def get_zone_by_label(zone_label):
    for zone in ALL_ZONES:
        if zone["label"] == zone_label:
            return zone

    return None


def zone_occupied_by_other_tag(zone, tags, current_tag):
    """
    Returns True when at least one tag other than current_tag
    is currently inside the zone.
    """
    for other_tag in tags:
        if other_tag is current_tag:
            continue

        if other_tag.filt_position is None:
            continue

        if point_in_zone(other_tag.filt_position, zone):
            return True

    return False


def process_zone_transitions(state, tag_id, tag):
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

    # ------------------------------------------------------
    # Zone entered by this tag
    # ------------------------------------------------------
    for zone_label in entered:
        zone = zone_lookup.get(zone_label)

        if zone is None:
            continue

        print(
            f"[ZONE] Tag {tag_id} ENTERED "
            f"{zone_label}"
        )

        occupied_by_other_tag = zone_occupied_by_other_tag(zone, state.tags, tag,)

        # Only send the enter/expand cue when this tag is
        # the first tag entering the zone.
        if occupied_by_other_tag:
            print(
                f"[ZONE] {zone_label} was already occupied; "
                "enter OSC suppressed"
            )
            continue

        print(
            f"[ZONE] {zone_label} became occupied"
        )

        if zone.get("tutorial", False):
            tutorial_zone_index = TUTORIAL_ZONES.index(zone)
            send_tutorial_zone_enter(tag_id, tutorial_zone_index,) # OSC

        else:
            zone_index = ZONES.index(zone)
            send_zone_enter(tag_id, zone_index,) # OSC

    # ------------------------------------------------------
    # Zone exited by this tag
    # ------------------------------------------------------
    for zone_label in exited:
        zone = get_zone_by_label(zone_label)

        if zone is None:
            continue

        print(
            f"[ZONE] Tag {tag_id} EXITED "
            f"{zone_label}"
        )

        occupied_by_other_tag = zone_occupied_by_other_tag(zone, state.tags, tag,)

        # Only send the exit/shrink cue when this was the
        # final tag leaving the zone.
        if occupied_by_other_tag:
            print(
                f"[ZONE] {zone_label} is still occupied; "
                "exit OSC suppressed"
            )
            continue

        print(
            f"[ZONE] {zone_label} became empty"
        )

        if zone.get("tutorial", False):
            tutorial_zone_index = TUTORIAL_ZONES.index(zone)

            send_tutorial_zone_exit(tag_id, tutorial_zone_index,) # OSC

        else:
            zone_index = ZONES.index(zone)

            send_zone_exit(tag_id, zone_index,) # OSC

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

        # Captured game zones remain at maximum size.
        if zone.get("captured") and not is_tutorial:
            zone["radius"] = zone["max_radius"]
            continue

        occupied = zone_is_occupied(
            zone,
            state.tags,
        )

        if occupied:
            zone["radius"] = min(
                zone["max_radius"],
                zone["radius"] + zone["expand_rate"],
            )

            # Game-zone capture.
            if (
                zone["radius"] >= zone["max_radius"]
                and not is_tutorial
            ):
                zone["captured"] = True

                # Send only once.
                if not zone["expanded_sent"]:
                    zone["expanded_sent"] = True

                    zone_index = ZONES.index(zone)

                    send_zone_complete(
                        zone_index
                    )

                    print(
                        f"[ZONE CAPTURED] "
                        f"{zone['label']}"
                    )

        else:
            zone["radius"] = max(
                zone["min_radius"],
                zone["radius"] - zone["shrink_rate"],
            )


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
