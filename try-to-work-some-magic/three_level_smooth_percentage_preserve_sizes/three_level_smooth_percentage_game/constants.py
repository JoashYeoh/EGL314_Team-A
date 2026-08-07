# ---------------------------------------------------------------------------
# Anchor layout and view configuration
# ---------------------------------------------------------------------------
ANCHORS = {
    0: (0.0, 0.0),
    1: (0.0, 3.9),
    2: (0.0, 8.16),
    3: (9.5, 8.14),
    4: (9.5, 3.8),
    5: (9.5, 0.0),
}

VIEW_BOUNDS = (-1.50, 11.50, -1.50, 10.50)
ZONE_HIT_TOLERANCE = 0.0
DEFAULT_PORT = 5005

# ---------------------------------------------------------------------------
# Safe-zone construction
# ---------------------------------------------------------------------------
def safe(label, center, colour):
    return {
        "center": center,
        "radius": 0.30,
        "max_radius": 1.10,
        "min_radius": 0.30,
        "expand_rate": 0.00935,
        "shrink_rate": 0.00450,
        "color": colour,
        "label": label,
        "active": False,
        "safe": True,
        "tutorial": False,
        "captured": False,
        "expanded_sent": False,

        # Percentage OSC synchronization state.
        # last_percentage_step is the Python size step already reached.
        # osc_target_step is the next GrandMA destination currently fading toward.
        "last_percentage_step": None,
        "osc_target_step": None,
    }


ZONES = [
    safe("ZONE A", (3.50, 5.15), "#00e5ff"),
    safe("ZONE B", (6.00, 5.15), "#ff40c3"),
    safe("ZONE C", (6.00, 2.65), "#66ff66"),
    safe("ZONE D", (3.50, 2.65), "#c266ff"),
    safe("ZONE E", (4.75, 3.90), "#bdbdbd"),

    {
        "start_center": (4.75, 3.90),
        "center": [4.75, 3.90],
        "radius": 0.30,
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": False,
        "is_danger": True,
        "velocity": [0.0, 0.08],
        "axis": "vertical",
    },
    {
        "start_center": (4.75, 3.90),
        "center": [4.75, 3.90],
        "radius": 0.30,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": False,
        "is_danger": True,
        "velocity": [0.08, 0.0],
        "axis": "horizontal",
    },
]

DANGER_BOUNDS = (2.25, 7.25, 1.40, 6.40)

# ---------------------------------------------------------------------------
# Tutorial-only zones
# ---------------------------------------------------------------------------
def tutorial_safe(label, center, colour):
    return {
        "center": center,
        "radius": 1.10,
        "max_radius": 1.10,
        "min_radius": 0.30,
        "expand_rate": 0.00935,
        "shrink_rate": 0.00450,
        "color": colour,
        "label": label,
        "active": False,
        "safe": True,
        "tutorial": True,
        "captured": False,
        "expanded_sent": False,
        "tutorial_max_sent": False,
    }


TUTORIAL_ZONES = [
    tutorial_safe("TUTORIAL ZONE 1", (3.50, 3.90), "#00e5ff"),
    tutorial_safe("TUTORIAL ZONE 2", (6.00, 3.90), "#ffb300"),
]

TUTORIAL_DANGER_ZONE = {
    "center": (4.75, 3.90),
    "radius": 1.00,
    "min_radius": 1.00,
    "max_radius": 1.00,
    "expand_rate": 0.0,
    "shrink_rate": 0.0,
    "color": "#ff1744",
    "label": "TUTORIAL DANGER",
    "active": False,
    "safe": False,
    "tutorial": True,
    "is_danger": True,
    "velocity": (0.0, 0.0),
}

ALL_ZONES = ZONES + TUTORIAL_ZONES + [TUTORIAL_DANGER_ZONE]

# ---------------------------------------------------------------------------
# Three-level survival configuration
# ---------------------------------------------------------------------------
LEVEL_1 = 1
LEVEL_2 = 2
LEVEL_3 = 3

LEVEL_CONFIGS = {
    LEVEL_1: {
        "zone_labels": ["ZONE A", "ZONE B"],
        "survival_time": 10.0,
    },
    LEVEL_2: {
        "zone_labels": ["ZONE A", "ZONE B", "ZONE C"],
        "survival_time": 15.0,
    },
    LEVEL_3: {
        "zone_labels": ["ZONE A", "ZONE B", "ZONE C", "ZONE D"],
        "survival_time": 20.0,
    },
}

TUTORIAL_SURVIVAL_TIME = 5.0

# ---------------------------------------------------------------------------
# Application states
# ---------------------------------------------------------------------------
STATE_LOBBY = "lobby"
STATE_TUTORIAL = "tutorial"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_GAME_WON = "game_won"

TUTORIAL_EXPAND = "tutorial_expand"
TUTORIAL_SHRINK = "tutorial_shrink"
TUTORIAL_SURVIVE = "tutorial_survive"
TUTORIAL_DANGER = "tutorial_danger"

# Retained for compatibility with older imports.
ROUND_EXPAND = 0
ROUND_SURVIVE = 1

# ---------------------------------------------------------------------------
# Viewer colours
# ---------------------------------------------------------------------------
TAG_COLORS = [
    "#ff5252", "#42a5f5", "#66bb6a", "#ffb74d",
    "#ab47bc", "#26a69a", "#ec407a", "#bdbdbd",
]

COLOR_NAMES = [
    "red", "blue", "green", "orange",
    "purple", "teal", "pink", "gray",
]

# ---------------------------------------------------------------------------
# OSC targets
# ---------------------------------------------------------------------------
OSC_REAPER_TARGET_IP = "192.168.1.108"
OSC_REAPER_TARGET_PORT = 8000

OSC_GMA3_TARGET_IP = "192.168.254.252"
OSC_GMA3_TARGET_PORT = 8080
