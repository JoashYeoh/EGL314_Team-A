# ---------------------------------------------------------------------------
# Anchor layout and view config  (must match uart.py)
# ---------------------------------------------------------------------------
ANCHORS = {
    0: (0.0, 0.0),
    1: (0.0, 3.9),
    2: (0.0, 8.16),
    3: (9.5, 8.14),
    4: (9.5, 3.8),
    5: (9.5, 0.0),
}

VIEW_BOUNDS = (-1.50, 11.50, -1.50, 10.50) #(xmin, xmax, ymin, ymax)

# ---------------------------------------------------------------------------
# Zone configs
# ---------------------------------------------------------------------------
ZONE_HIT_TOLERANCE = 0.0

ZONES = [
    {
        "center": (3.5, 5.15),  #top left
        "radius": 0.10,
        "max_radius": 1.25,
        "min_radius": 0.30,
        "expand_rate": 0.0060,
        "shrink_rate": 0.0045,
        "color": "#00e5ff",
        "label": "ZONE A",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
        "current_cue": 10,
        "last_direction": None,
        "hysteresis_active": False,
    },
    {
        "center": (6.00, 5.15),  #top right
        "radius": 0.10,
        "max_radius": 1.25,
        "min_radius": 0.30,
        "expand_rate": 0.0060,
        "shrink_rate": 0.0045,
        "color": "#ff40c3",
        "label": "ZONE B",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
        "current_cue": 10,
        "last_direction": None,
        "hysteresis_active": False,
    },
    {
        "center": (6.00, 2.65),  #bottom right
        "radius": 0.10,
        "max_radius": 1.25,
        "min_radius": 0.30,
        "expand_rate": 0.0060,
        "shrink_rate": 0.0045,
        "color": "#66ff66",
        "label": "ZONE C",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
        "current_cue": 10,
        "last_direction": None,
        "hysteresis_active": False,
    },
    {
        "center": (3.5, 2.65),  #bottom left
        "radius": 0.10,
        "max_radius": 1.25,
        "min_radius": 0.30,
        "expand_rate": 0.0060,
        "shrink_rate": 0.0045,
        "color": "#c266ff",
        "label": "ZONE D",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
        "current_cue": 10,
        "last_direction": None,
        "hysteresis_active": False,
    },


    # --- DANGER ZONE 1: Vertical (Up/Down) within Anchors ---
    {
        "start_center": (4.75, 3.9),
        "center": [4.75, 3.9],
        "radius": 0.30,          #show big my danger zone is
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": True,
        "is_danger": True,          # Unique flag to identify this as an enemy zone
        #"start_velocity": [0.0, 0.03],
        "velocity": [0.0, 0.08],    # [X-speed, Y-speed] -> Moves ONLY up/down
        "axis": "vertical",
        "movement_target": "max",
        "current_osc_cue": None,
    },
    # --- DANGER ZONE 2: Horizontal (Left/Right) within Anchors ---
    {
        "start_center": (4.75, 3.9),
        "center": [4.75, 3.9],
        "radius": 0.30,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": True,
        "is_danger": True,
        #"start_velocity": [0.05, 0.0],
        "velocity": [0.08, 0.0],  # [X-speed, Y-speed] -> Moves ONLY left/right
        "axis": "horizontal",
        "movement_target": "max",
        "current_osc_cue": None,
    },
]


# Danger Zone Boundaries
DANGER_BOUNDS = (2.25, 7.25, 1.4, 6.4) #(xmin, xmax, ymin, ymax)


TAG_COLORS = [
    "#ff5252", "#42a5f5", "#66bb6a", "#ffb74d",
    "#ab47bc", "#26a69a", "#ec407a", "#bdbdbd",
]

COLOR_NAMES = [
    "red", "blue", "green", "orange",
    "purple", "teal", "pink", "gray",
]

DEFAULT_PORT = 5005  # UDP port to listen on



# ---------------------------------------------------------------------------
# Game Phases - round progression
# ---------------------------------------------------------------------------
ROUND_EXPAND = 0
ROUND_SURVIVE = 1


STATE_PLAYING = "playing"
STATE_LEVEL_COMPLETE = "level_complete"
STATE_GAME_OVER = "game_over"
STATE_GAME_WON = "game_won"

GAME_OVER_DELAY = 0.05


GAME_END_SEQUENCE_DELAY = 10.0


# ---------------------------------------------------------------------------
# OSC -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_REAPER_TARGET_IP = "192.168.254.12"    # IP of laptop running REAPER
OSC_REAPER_TARGET_PORT = 8000

OSC_GMA3_TARGET_IP = "192.168.254.252"    # IP of laptop running GMA3
OSC_GMA3_TARGET_PORT = 8080
