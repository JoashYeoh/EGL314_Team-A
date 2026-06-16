# EGL314 - POC - UWB Interactive Zone Capture Game

## Table of Contents
* [1. Project Overview](#1-project-overview)
* [2. System Architecture](#2-system-architecture-poc)
* [3. Repository Structure](#3-repository-structure-poc)
    * [3.1. assets/ ](#31-assets)
    * [3.2. docs/ ](#32-docs)
    * [3.3. module_config-files/ ](#33-module_config-files)
    * [3.4. game.py ](#34-gamepy)
    * [3.5. uart.py ](#35-uartpy)



## 1. Project Overview

An interactive multiplayer game that uses **Ai-Thinker BU03-Kit UWB modules (DW3000 + STM32F103)** for real-time player tracking.

The system consists of:
- 6 Anchors (BU03-Kit UWB modules)
- 2 Tags (BU03-Kit UWB modules)
- Sensor Pi (UWB data acquisition)
- Game Pi (game engine & visualisation)
- Multiplay (audio playback)

In the game, players must capture safe zones while avoiding moving danger zones. Visualised through `game.py` running on the Game Pi.



## 2. System Architecture (POC)
```mermaid
flowchart 
    A[AI Thinker UWB Kit] -->|UART| B[Sensor Pi -> uart.py]
    B -->|OSC| c[Game Pi -> game.py]
    c -->|OSC| D[Multiplay]
```



## 3. Repository Structure (POC/)

### 3.1. assets/
Contains:
- Tutorial images
- Gameplay images
- Audio assets
- UI resources


### 3.2. docs/
| **Documentation**    | **Purpose**                           |
|----------------------|---------------------------------------|
| `architecture.md`      | Explain Software pipeline             |
| `hardware_setup.md`    | Hardware setup utilised               |
| `uwb_configuration.md` | Configuration workflow                |
| `calibration.md`       | Anchor layout and calibration         |
| `software_setup.md`    | Software configuration                |
| `game_logic.md`        | Explain game itself                   |
| `osc_reference.md`     | All OSC traffic                       |
| `troubleshooting.md`   | Some possible troubles and what to do |


### 3.3. module_config-files/
These are the scripts used during deployment and setup of anchors and tags.

| **Script**           | **Purpose**                             |
|----------------------|-----------------------------------------|
| `bu03_detect.py`       | Detect connected module                 |
| `bu03_inspect.py`      | Read module information                 |
| `bu03_multi_config.py` | Configure connected module              |
| `check_uart.sh`        | Verify UART communication               |
| `viewer_calibrate.py`  | Calibration and coordinate verification |


### 3.4 game.py
This is the script that runs on the **Game Pi**.

Responsibilities of this script: 
- Receives OSC distance data
- Performs trilateration
- Applies Kalman filtering
- Handles zone detection
- Runs game state machine
- Sends OSC commands to Multiplay
- Displays GUI


### 3.5 uart.py
This is the script that runs on the **Sensor Pi**.

Responsibilities of this script:
- Reads UART data from BU03 UWB anchor that is connected to the **Sensor Pi**
- Parses distance frames
- Applies calibration offsets
- Assigns tag IDs
- Sends distance data to **Game Pi** via OSC
