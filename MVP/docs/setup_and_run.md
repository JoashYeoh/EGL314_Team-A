# Setup & Run Guide
This guide explains how to prepare the software environment and launch the UWB game system after all UWB modules have been configured.

## System Overview

The system consists of three main components:

- **Sensor Raspberry Pi** – Receives UWB data from the tag and transmits distance measurements via OSC.
- **Game Laptop** – Runs the game application (`game.py`), processes player positions, renders the GUI, and controls game logic.
- **Media Laptops** – Runs REAPER, L-ISA, and GrandMA3 for audio playback, spatialisation, and lighting control.

The overall data flow is shown below.

```text
                UWB Anchors (A00–A05)
                        ↓
                 Wireless UWB ranging
                        ↓
                 UWB Tag (T00/T01)
                        ↓
                  UART Connection
                        ↓
              Sensor Raspberry Pi
                  └── uart.py
                        ↓
                 OSC (/distances)
                  Ethernet / Wi-Fi
                        ↓
                 Game Laptop
                  └── game.py
                        ↓
        ┌───────────────────────────────┐
   Game Logic & GUI              OSC Commands
         ↓                              ↓
  Game Display                    REAPER / GrandMA3
```

## Project Directory

The laptop running `game.py` should contain the following files.

```text
project/
│
├── game.py
├── constants.py
├── game_manager.py
├── level_config.py
├── osc_handler.py
├── osc_sender.py
├── shared_state.py
├── tutorial.py
├── viewer.py
├── zones.py
├── trilateration.py
├── kalman.py
│
└── (other supporting files)
```

The Sensor Raspberry Pi should run:

```text
uart.py
```

## Required Assets

The media laptop should contain the following software and assets.

### REAPER

Required audio assets include:

- Game background music
- Safe zone audio tracks
- Level completion audio
- Game over audio
- Final game sequence audio

For step-by-step configuration guide, click [here](software_setup.md#43-reaper).

### L-ISA

Ensure the following are prepared:

- L-ISA project
- Speaker configuration
- Audio routing configuration

For step-by-step configuration guide, click [here](software_setup.md#4-reaper-laptop-set-up).

### GrandMA3

Ensure all required lighting sequences and OSC commands are configured before running the game.

For step-by-step configuration guide, click [here](software_setup.md#5-grandma3-set-up).

## Script Dependencies

The game is launched from `game.py`, which coordinates the remaining modules.

```text
game.py
│
├── constants.py
│
├── shared_state.py
│   └── kalman.py
│
├── game_manager.py
│   ├── level_config.py
│   ├── constants.py
│   └── zones.py
│       ├── constants.py
│       └── osc_sender.py
│
├── viewer.py
│   ├── constants.py
│   └── shared_state.py
│
├── tutorial.py
│   ├── constants.py
│   └── osc_sender.py
│
├── osc_handler.py
│   ├── trilateration.py
│   ├── shared_state.py
│   └── osc_sender.py
│
└── osc_sender.py
    └── constants.py
```

### Module Responsibilities

| Module | Purpose |
|----------|---------|
| `game.py` | Main application entry point. |
| `constants.py` | Stores game configuration, anchor locations, zone parameters, and OSC settings. |
| `shared_state.py` | Maintains player tracking data shared across modules. |
| `kalman.py` | Smooths player movement using a 2D Kalman filter. |
| `osc_handler.py` | Receives OSC distance messages and computes player positions. |
| `trilateration.py` | Converts UWB distance measurements into 2D coordinates. |
| `viewer.py` | Displays the game arena, players, and overlays. |
| `tutorial.py` | Displays the tutorial before gameplay begins. |
| `game_manager.py` | Controls game progression, levels, tutorials, and game states. |
| `zones.py` | Updates safe zones, danger zones, and collision detection. |
| `osc_sender.py` | Sends OSC commands to REAPER and GrandMA3. |
| `level_config.py` | Defines level settings such as survival time and active zones. |


## Network Configuration

Before starting the system, ensure that:

- Both Raspberry Pis and the Game Laptop are connected to the same network.
- `uart.py` is configured to send OSC messages to the Game Laptop.
- The OSC port matches the listening port used by `game.py`.
- The IP addresses configured in `constants.py` are correct.

```python
OSC_REAPER_TARGET_IP
OSC_REAPER_TARGET_PORT

OSC_GMA3_TARGET_IP
OSC_GMA3_TARGET_PORT
```

## Running the System

Once all hardware and software have been configured, launch the system in the following order.

1. Power on all UWB anchors.
2. Power on the UWB tag(s).
3. On the Sensor Raspberry Pi, run:
```bash
python uart.py
```
4. On the Game Laptop, run:
```bash
python game.py
```

## Command-Line Options

`game.py` supports the following optional arguments.

| Command | Description |
|----------|-------------|
| `python game.py` | Launch with default settings. |
| `python game.py --tags 2` | Specify the number of tracked tags. |
| `python game.py --simulate` | Enable mouse simulation instead of live UWB tracking. |
| `python game.py --port 5005` | Specify the OSC listening port. |

## Execution Sequence

After `game.py` starts, the system executes the following sequence.

```text
Launch game.py
      │
Create Shared State
      │
Create Game Manager
      │
Start OSC Server
      │
Receive OSC data from uart.py
      │
Display Tutorial Window
      │
User presses Start Game
      │
Launch Game Viewer
      │
Tutorial Mode
      │
Press SPACE to continue
      │
Level 1
      │
Level 2
      │
Level 3
      │
Game End Sequence
```

## Pre-Run Checklist

Before each game session, verify the following.

- All UWB anchors are powered on.
- UWB tags are fully charged.
- UART connections are secure.
- `uart.py` is running on the Sensor Raspberry Pi.
- `game.py` is running on the Game Laptop.
- Both devices are connected to the same network.
- REAPER, L-ISA, and GrandMA3 are running.
- The OSC IP addresses and ports are configured correctly.
- Tutorial images are present in the `Assets` folder.
- The game arena is free from large obstacles that may interfere with UWB signals.