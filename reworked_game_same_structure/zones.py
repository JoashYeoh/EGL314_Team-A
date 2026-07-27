import random
from constants import ZONES,DANGER_BOUNDS,ZONE_HIT_TOLERANCE
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


def safe_zones(): 
    return [z for z in ZONES if z.get('safe')]


def reset_zones(state):
    for z in safe_zones():
        z['radius']=z['min_radius']
        z['captured']=False
        z['expanded_sent']=False
        z['active']=True

    for t in state.tags:
        t.zones_inside.clear()


def process_zone_transitions(tag_id,tag):
    current=set()
    for i,z in enumerate(ZONES):
        if z.get('safe') and z.get('active',True) and point_in_zone(tag.filt_position,z):
            current.add(i)

    entered=current-tag.zones_inside
    exited=tag.zones_inside-current

    for i in entered:
        print(f"[ZONE] Tag {tag_id} ENTERED {ZONES[i]['label']}")
        send_zone_enter(tag_id,i)   # OSC

    for i in exited:
        print(f"[ZONE] Tag {tag_id} EXITED {ZONES[i]['label']}")
        send_zone_exit(tag_id,i)    # OSC

    tag.zones_inside=current
    return entered,exited


# ---------------------------------------------------------------------------
#  Zone Grow Logic 
# ---------------------------------------------------------------------------
def update_zones(state):
    for i,z in enumerate(ZONES):
        if not z.get('safe') or not z.get('active',True):
            continue

        # if Zone is captured, nothing happens
        if z.get('captured'):
            z['radius']=z['max_radius']
            continue

        # Zone expands while occupied
        if zone_is_occupied(z,state.tags):
            z['radius']=min(z['max_radius'],z['radius']+z['expand_rate'])
            if z['radius']>=z['max_radius']:
                z['captured']=True
                if not z['expanded_sent']:
                    z['expanded_sent']=True
                    send_zone_complete(i)

        # else Zone shrinks (while not occupied)
        else:
            z['radius']=max(z['min_radius'],z['radius']-z['shrink_rate'])


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
