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
        "center": (3.5,5.15),  #top left
        "radius": 0.10,
        "max_radius": 1.15,
        "min_radius": 0.10,
        "expand_rate": 0.010,
        "shrink_rate": 0.004,
        "color": "#00e5ff",
        "label": "ZONE A",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (6.00, 5.15),  #top right
        "radius": 0.10,
        "max_radius": 1.15,
        "min_radius": 0.10,
        "expand_rate": 0.010,
        "shrink_rate": 0.004,
        "color": "#ff40c3",
        "label": "ZONE B",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (6.00, 2.65),  #bottom right
        "radius": 0.10,
        "max_radius": 1.15,
        "min_radius": 0.10,
        "expand_rate": 0.010,
        "shrink_rate": 0.004,
        "color": "#66ff66",
        "label": "ZONE C",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (3.5, 2.65),  #bottom left
        "radius": 0.10,
        "max_radius": 1.15,
        "min_radius": 0.10,
        "expand_rate": 0.010,
        "shrink_rate": 0.004,
        "color": "#c266ff",
        "label": "ZONE D",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },


    # --- DANGER ZONE 1: Vertical (Up/Down) within Anchors ---
    {
        "start_center": (4.75, 3.9),
        "center": [4.9, 1.26],
        "radius": 0.30,          #show big my danger zone is
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": True,
        "is_danger": True,          # Unique flag to identify this as an enemy zone
        "start_velocity": [0.0, 0.03],
        "velocity": [0.0, 0.03],    # [X-speed, Y-speed] -> Moves ONLY up/down
    },
    # --- DANGER ZONE 2: Horizontal (Left/Right) within Anchors ---
    {
        "start_center": (4.9, 3.9),
        "center": [4.9, 1.26],
        "radius": 0.30,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": True,
        "is_danger": True,
        "start_velocity": [0.05, 0.0],
        "velocity": [0.05, 0.0],  # [X-speed, Y-speed] -> Moves ONLY left/right
    },
]


# Anchor Boundaries
L_X_MIN, L_X_MAX = 0.0, 9.858   # Set the left and right outer boundary walls
L_Y_MIN, L_Y_MAX = 0.0, 4.929   # Set the bottom and top outer boundary walls


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


# ---------------------------------------------------------------------------
# OSC to Reaper -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_TARGET_IP = "192.168.1.108"    # IP of laptop running Multi-play
OSC_TARGET_PORT = 8000
