# Setup & Run Guide

This guide explains how to prepare and run the UWB game system. It covers the required software, project files, network configuration, system startup sequence, and basic checks before starting a game.

## 1. System Overview

The UWB game system consists of three main components:

* **Sensor Raspberry Pi** – Receives UWB distance measurements through UART and sends them to the Game Laptop using OSC.
* **Game Laptop** – Runs `game.py`, receives OSC data, calculates player positions, manages game logic, and displays the game interface.
* **Media Laptops** – Runs REAPER, L-ISA, and GrandMA3 for audio, spatial audio, and lighting control.

### System Data Flow

```text
UWB Anchors
     ↓
  UWB Tag
     ↓
   UART
     ↓
Sensor Raspberry Pi
     ↓
  uart.py
     ↓
OSC /distances
     ↓
Game Laptop
     ↓
  game.py
     ↓
┌─────────────────────────────┐
│ Shared State & Game Manager │
└──────────────┬──────────────┘
               ↓
       Position Processing
               ↓
        Zone / Game Logic
               ↓
          Viewer GUI
               ↓
       Game Display Output

          OSC Commands
               ↓
      REAPER / GrandMA3
```

---

# 2. Software Requirements

The following software must be installed before running the system.

### Game Laptop

* Python 3
* Tkinter
* `python-osc`
* NumPy
* Matplotlib
* All project Python modules

### Sensor Raspberry Pi

* Python 3
* UART communication libraries
* `python-osc`
* `uart.py`

### Media Laptops

* REAPER
* L-ISA
* GrandMA3

Make sure all required software has been configured before starting the game.

---

# 3. Project Files

The Game Laptop should contain the main game files:

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
└── Assets/
```

The Sensor Raspberry Pi should contain:

```text
sensor/
│
└── uart.py
```

### Main Module Responsibilities

| Module             | Responsibility                                                          |
| ------------------ | ----------------------------------------------------------------------- |
| `game.py`          | Main program that starts and connects the different game components.    |
| `constants.py`     | Stores system settings, anchor positions, zones, and OSC configuration. |
| `shared_state.py`  | Stores player tracking and game data shared between modules.            |
| `kalman.py`        | Smooths the calculated player position.                                 |
| `trilateration.py` | Calculates player coordinates from UWB distance measurements.           |
| `osc_handler.py`   | Receives OSC distance data and processes player positions.              |
| `game_manager.py`  | Controls the game state, levels, and transitions.                       |
| `viewer.py`        | Displays the game arena, player positions, zones, and game information. |
| `tutorial.py`      | Displays the lobby/tutorial screen before the game starts.              |
| `zones.py`         | Controls zone movement, shrinking, and player-zone interactions.        |
| `osc_sender.py`    | Sends OSC commands to external media software.                          |
| `level_config.py`  | Stores settings for individual game levels.                             |

---

# 4. Network Configuration

The Sensor Raspberry Pi and Game Laptop must be connected to the same network.

Before running the system, check:

* Sensor Raspberry Pi is connected to the network.
* Game Laptop is connected to the same network.
* The IP address of the Game Laptop is correctly configured in `uart.py`.
* The OSC receiving port matches the port used by `game.py`.
* REAPER and GrandMA3 target IP addresses are correctly configured.

The OSC settings are configured in `constants.py`.

```python
OSC_REAPER_TARGET_IP
OSC_REAPER_TARGET_PORT

OSC_GMA3_TARGET_IP
OSC_GMA3_TARGET_PORT
```

The default OSC receiving port in `game.py` is:

```text
5005
```

---

# 5. UWB System Preparation

Before starting the software:

1. Power on all UWB anchors.
2. Check that the anchors are correctly positioned.
3. Power on the UWB tag(s).
4. Check that the UWB modules have been configured correctly.
5. Connect the Sensor Raspberry Pi to the UWB system through UART.
6. Make sure the tag is within the operating area.

The UWB system must be working correctly before starting the game application.

---

# 6. Starting the Sensor Raspberry Pi

Open a terminal on the Sensor Raspberry Pi and navigate to the folder containing `uart.py`.

Run:

```bash
python uart.py
```

The script reads UWB distance measurements through UART and sends them to the Game Laptop using OSC.

The data is sent using the OSC address:

```text
/distances
```

Keep this program running throughout the game.

---

# 7. Starting the Game Laptop

On the Game Laptop, navigate to the project folder containing `game.py`.

Run:

```bash
python game.py
```

The program will:

1. Create the shared game state.
2. Create the Game Manager.
3. Start the OSC server.
4. Begin listening for UWB distance data.
5. Display the tutorial/lobby screen.
6. Wait for the user to start the game.

The default OSC listening port is:

```text
5005
```

---

# 8. Game Startup Sequence

The main program follows this sequence:

```text
Start game.py
      ↓
Create Shared State
      ↓
Create Game Manager
      ↓
Start OSC Server
      ↓
Listen for /distances
      ↓
Display Tutorial / Lobby
      ↓
User Starts Game
      ↓
Display Game Viewer
      ↓
Process Player Positions
      ↓
Update Zones & Game Logic
      ↓
Game Ends
      ↓
Return to Lobby
```

This allows the system to continuously receive UWB data while the game interface and game logic are running.

---

# 9. Command-Line Options

The game supports several optional commands.

### Start normally

```bash
python game.py
```

Starts the game using the default settings.

### Set number of tags

```bash
python game.py --tags 2
```

Specifies the number of UWB tags being tracked.

### Simulation Mode

```bash
python game.py --simulate
```

Runs the game using simulated player movement instead of live UWB data. This is useful for testing the game without the UWB hardware.

### Change OSC Port

```bash
python game.py --port 5005
```

Changes the OSC listening port used by the game.

### Windowed Mode

```bash
python game.py --windowed
```

Runs the game in windowed mode instead of the normal display mode.

---

# 10. Media System Preparation

Before starting gameplay, ensure the media systems are running.

### REAPER

Check that:

* Required audio files are available.
* The REAPER project is open.
* Audio routing is configured.
* OSC communication is enabled.

### L-ISA

Check that:

* The correct L-ISA project is open.
* Speaker configuration is loaded.
* Audio routing is working correctly.

### GrandMA3

Check that:

* The correct show file is loaded.
* Required lighting sequences are available.
* OSC communication is configured.
* The correct network connection is being used.

---

# 11. Pre-Run Checklist

Before starting a game session, check the following:

* [ ] UWB anchors are powered on.
* [ ] UWB tags are powered on and charged.
* [ ] Anchors are positioned correctly.
* [ ] Sensor Raspberry Pi is connected to the UWB system.
* [ ] Sensor Raspberry Pi and Game Laptop are on the same network.
* [ ] `uart.py` is running.
* [ ] `game.py` is running.
* [ ] OSC port is configured correctly.
* [ ] IP addresses in the configuration are correct.
* [ ] REAPER is running.
* [ ] L-ISA is running.
* [ ] GrandMA3 is running.
* [ ] Required game assets are available.
* [ ] The game area is clear of major obstacles.
* [ ] Player tags are detected correctly.

---

# 12. Basic Troubleshooting

### Game does not receive player data

Check that:

* `uart.py` is running.
* Both devices are connected to the same network.
* The Game Laptop IP address is correct.
* The OSC port matches between `uart.py` and `game.py`.
* UWB anchors and tags are powered on.

### Game starts but player position does not move

Check:

* UWB tag connection.
* Anchor positions.
* Distance measurements received by `uart.py`.
* Trilateration configuration.
* Kalman filter settings.

### Media does not respond

Check:

* REAPER and GrandMA3 are running.
* Target IP addresses are correct.
* OSC ports are correct.
* Both systems are connected to the same network.
* OSC commands are correctly configured.

---

# 13. Shutdown Procedure

After completing the game session:

1. Exit the game application.
2. Stop `uart.py` on the Sensor Raspberry Pi.
3. Stop REAPER, L-ISA, and GrandMA3 if they are no longer required.
4. Power down the UWB tags.
5. Power down the UWB anchors.
6. Shut down the Raspberry Pi if necessary.

This prevents unnecessary power consumption and ensures the system is properly closed.

---

# 14. Quick Start

For a normal game session, the basic startup procedure is:

```text
1. Power UWB Anchors
          ↓
2. Power UWB Tags
          ↓
3. Start uart.py
          ↓
4. Start REAPER / L-ISA / GrandMA3
          ↓
5. Start game.py
          ↓
6. Check Tutorial / Lobby
          ↓
7. Start Game
          ↓
8. Play Game
          ↓
9. Game Ends
          ↓
10. Return to Lobby
```

This procedure provides a consistent method for preparing, launching, operating, and shutting down the UWB game system.
