# ---------------------------------------------------------------------------
# Anchor layout and view config  (must match uart.py)
# ---------------------------------------------------------------------------
ANCHORS = {
    0: (0.0, 0.0),
    1: (0.0, 0.50),
    2: (0.0, 1.0),
    3: (1.0, 1.0),
    4: (1.0, 0.50),
    5: (1.0, 0.0),
}

VIEW_BOUNDS = (-0.50, 1.50, -0.50, 1.50)

# ---------------------------------------------------------------------------
# Zone configs
# ---------------------------------------------------------------------------
ZONE_HIT_TOLERANCE = 0.0

ZONES = [
    {
        "center": (0.25, 0.25),  #top left
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0012,
        "color": "#00e5ff",
        "label": "ZONE A",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.25, 0.75),  #top right
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0005,
        "color": "#ff40c3",
        "label": "ZONE B",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.75, 0.75),  #bottom left
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.002,
        "color": "#66ff66",
        "label": "ZONE C",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.75, 0.25),  #bottom right
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0011,
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
        "center": [0.5, 0.5],
        "radius": 0.10,          #show big my danger zone is
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": True,
        "is_danger": True,          # Unique flag to identify this as an enemy zone
        "velocity": [0.0, 0.015],    # [X-speed, Y-speed] -> Moves ONLY up/down
    },
    # --- DANGER ZONE 2: Horizontal (Left/Right) within Anchors ---
    {
        "center": [0.5, 0.5],
        "radius": 0.10,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": True,
        "is_danger": True,
        "velocity": [0.015, 0.0],  # [X-speed, Y-speed] -> Moves ONLY left/right
    },
]


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


# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_TARGET_IP = "127.0.0.1"    # IP of laptop running Multi-play
OSC_TARGET_PORT = 8888
