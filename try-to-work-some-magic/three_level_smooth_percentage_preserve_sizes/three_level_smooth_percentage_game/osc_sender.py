from pythonosc import udp_client

from constants import *


osc_tx_reaper = udp_client.SimpleUDPClient(
    OSC_REAPER_TARGET_IP,
    OSC_REAPER_TARGET_PORT,
)
osc_tx_gma3 = udp_client.SimpleUDPClient(
    OSC_GMA3_TARGET_IP,
    OSC_GMA3_TARGET_PORT,
)


# ---------------------------------------------------------------------------
# General flow cues
# ---------------------------------------------------------------------------
def send_off_all():
    osc_tx_gma3.send_message("/gma3/cmd", "Off Seq *")


def send_start_lobby():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 1")


def send_start_tutorial():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 2")


def send_start_game():
    print("[OSC] GAME START")
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 3")


# ---------------------------------------------------------------------------
# Tutorial cues
# ---------------------------------------------------------------------------
def send_tutorial_zone_enter(tag_id, zone_index):
    zone_name = TUTORIAL_ZONES[zone_index]["label"]
    sequence_zone1 = 107
    sequence_zone2 = 108
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Sequence {sequence_zone1} cue 2")
    elif zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Sequence {sequence_zone2} cue 2")
    
    print(f"[OSC] Tutorial ENTER Tag={tag_id} Zone={zone_name}")


def send_tutorial_zone_exit(tag_id, zone_index):
    zone_name = TUTORIAL_ZONES[zone_index]["label"]
    sequence_zone1 = 107
    sequence_zone2 = 108
    if zone_name == "TUTORIAL ZONE 1":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Sequence {sequence_zone1} cue 1")
    elif zone_name == "TUTORIAL ZONE 2":
        osc_tx_gma3.send_message("/gma3/cmd", f"Goto Sequence {sequence_zone2} cue 1")
    
    print(f"[OSC] Tutorial ENTER Tag={tag_id} Zone={zone_name}")


def send_tutorial_zone_max(zone_index, zone_label=None):
    zone_name = TUTORIAL_ZONES[zone_index]["label"]
    print(f"[OSC] Tutorial zone reached maximum: {zone_name}")


def send_tutorial_survival_start():
    # Replace this command with the cue used for the tutorial survival example.
    print("[OSC] Tutorial survival example started")


def send_tutorial_danger_zone():
    osc_tx_gma3.send_message("/gma3/cmd", "Goto Sequence 106 cue 1")


# ---------------------------------------------------------------------------
# Level cues
# Update these mappings to match your actual GrandMA and REAPER show files.
# ---------------------------------------------------------------------------
LEVEL_START_GMA = {
    LEVEL_1: "Goto Sequence 140 thru 141 Cue 1",
    LEVEL_2: "Goto Sequence 142 Cue 1",
    LEVEL_3: "Goto Sequence 143 Cue 1",
}

LEVEL_COMPLETE_GMA = {
    LEVEL_1: "Goto Sequence 103 Cue 2",
    LEVEL_2: "Goto Sequence 103 Cue 2",
    LEVEL_3: "Goto Sequence 103 Cue 3",
}


def send_level_start(level_number):
    command = LEVEL_START_GMA.get(level_number)
    if command:
        osc_tx_gma3.send_message("/gma3/cmd", command)
    print(f"[OSC] Level {level_number} start")


def send_level_complete(level_number):
    command = LEVEL_COMPLETE_GMA.get(level_number)
    if command:
        osc_tx_gma3.send_message("/gma3/cmd", command)
    print(f"[OSC] Level {level_number} complete")


# The same GrandMA sequence is used for each zone in every level.
ZONE_SEQUENCES = {
    "ZONE A": 110,
    "ZONE B": 111,
    "ZONE C": 112,
    "ZONE D": 113,
}

# Separate sequences represent each zone's percentage/size.
ZONE_PERCENTAGE_SEQUENCES = {
    "ZONE A": 140,
    "ZONE B": 141,
    "ZONE C": 142,
    "ZONE D": 143,
}

# 100% uses Cue 1, 90% Cue 2, down to 0% Cue 11.
ZONE_PERCENTAGE_CUES = {
    percentage: ((100 - percentage) // 10) + 1
    for percentage in range(100, -1, -10)
}


def send_zone_percentage(zone_index, percentage_step, direction="initial"):
    zone_name = ZONES[zone_index]["label"]
    sequence = ZONE_PERCENTAGE_SEQUENCES.get(zone_name)
    cue = ZONE_PERCENTAGE_CUES.get(percentage_step)

    if sequence is None or cue is None:
        return

    # Approximate time Python takes to travel through one 10% interval.
    # expand_rate = 0.00935 -> about 0.56 s per 10%
    # shrink_rate = 0.00450 -> about 1.17 s per 10%
    if direction == "shrinking":
        fade_time = 1.17
    elif direction == "expanding":
        fade_time = 0.56
    else:
        fade_time = 0.0

    osc_tx_gma3.send_message(
        "/gma3/cmd",
        f"Goto Sequence {sequence} Cue {cue} Fade {fade_time}",
    )

    print(
        f"[OSC] {zone_name} {direction} -> {percentage_step}% "
        f"Sequence {sequence} Cue {cue} Fade {fade_time}"
    )


# Level 1 keeps your existing REAPER actions. Fill Level 2/3 where required.
ZONE_ENTER_REAPER_BY_LEVEL = {
    LEVEL_1: {
        "ZONE A": "_RSde8c27471113c433ab8f75b7bb736ddb74db96c4",
        "ZONE B": "_RS0e63e8c1c3d8c7701d535fb9c883459fe10d58a9",
    },
    LEVEL_2: {},
    LEVEL_3: {},
}

ZONE_EXIT_REAPER_BY_LEVEL = {
    LEVEL_1: {
        "ZONE A": "_RS96f4032a72f7526436170776848754bc047bc4b0",
        "ZONE B": "_RS8a0090cf315a283032f73526614a2b9b270db77d",
    },
    LEVEL_2: {},
    LEVEL_3: {},
}


def send_zone_enter(tag_id, zone_index, level_number=None):
    zone_name = ZONES[zone_index]["label"]
    level_number = level_number or LEVEL_1

    sequence = ZONE_SEQUENCES.get(zone_name)
    if sequence is not None:
        # OSC Reaper on enter
        return

    action = ZONE_ENTER_REAPER_BY_LEVEL.get(level_number, {}).get(zone_name)
    if action:
        osc_tx_reaper.send_message(f"/action/{action}", 1)

    print(
        f"[OSC] Level={level_number} ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index, level_number=None):
    zone_name = ZONES[zone_index]["label"]
    level_number = level_number or LEVEL_1

    sequence = ZONE_SEQUENCES.get(zone_name)
    if sequence is not None:
        # OSC Reaper on enter
        return

    action = ZONE_EXIT_REAPER_BY_LEVEL.get(level_number, {}).get(zone_name)
    if action:
        osc_tx_reaper.send_message(f"/action/{action}", 1)

    print(
        f"[OSC] Level={level_number} EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


# Retained for compatibility; survival mode does not permanently capture zones.
def send_zone_complete(zone_index):
    print(f"[OSC] Zone complete: {ZONES[zone_index]['label']}")


# ---------------------------------------------------------------------------
# Game over and win
# ---------------------------------------------------------------------------
def send_game_over():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Sequence 115")

    print("[OSC] Game over")


def send_game_win():
    osc_tx_gma3.send_message("/gma3/cmd", "Go Macro 5")
    print("[OSC] Game win")


def send_game_end_finale():
    osc_tx_reaper.send_message("/action/40166", 1)   #jump marker 6
    print("[OSC] Final sequence triggered")


# Compatibility stubs for removed manual Zone E flow.
def send_zone_e_manual_start():
    print("[OSC] Manual Zone E is disabled in the three-level survival version")


def send_danger_movement(axis, cue):
    print(f"[OSC] Danger movement axis={axis} cue={cue}")
