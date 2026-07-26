# Software Set-up Documentation
In this document, you will find a guide on how to go about software set-up for the respective hardwares involved in the system. 

Documentation Guide:
* [1. Raspberry Pi Set-up](#1-Raspberry-Pi-Set-up)
* [2. `uart.py` Set-Up](#2-uartpy-Set-Up)
* [3. `game.py` Set-Up](#3-gamepy-Set-Up)
    * [3.1. OSC Target Configuration](#31-OSC-Target-Configuration)
    * [3.2. Tracking-Data Receiving Port](#32-Tracking-Data-Receiving-Port)
    * [3.3. Configuring the Number of Tags](#33-Configuring-the-Number-of-Tags)
    * [3.4. Tag Simulation Mode](#34-Tag-Simulation-Mode)
    * [3.5. Starting the Game](#35-Starting-the-Game)
    * [3.6. Module Responsibilities](#36-Module-Responsibilities)
* [4. REAPER Laptop Setup](#4-REAPER-Laptop-Set-Up)
    * [4.1. L-ISA Processor](#41-L-ISA-Processor)
    * [4.2. L-ISA Controller](#42-L-ISA-Controller)
    * [4.3. REAPER](#43-REAPER)
* [5. GrandMA3 Setup](#5-GrandMA3-Set-Up)
* [6. Appendix](#6-gamepy-Set-Up)
    * [6.1. Lasptop as Game Pi Set-up](#61-Laptop-as-Game-Pi-Set-up)
    * [6.2. About L-ISA Processor](#61-About-L-ISA-Processor-(Desktop))
    * [6.3. About L-ISA Controller](#61-About-L-ISA-Controller)
    * [6.4. About REAPER](#61-About-REAPER)
    * [6.5. About GrandMA3](#61-About-GrandMA3)


---

## 1. Raspberry Pi Set-up 
### Hardware
1. Single Board Computer: Raspberry Pi 4 Model B
2. Operating System: Raspbian Buster Full

### Initital Set-up of Raspberry Pi (first boot)
This is a **crucial step**, to set up the Raspberry Pi that will be used. *[Reference to a step by step guide here](https://github.com/huats-club/rpistarterkit#setting-up-the-raspberry-pi-first-initial-boot)*.
- Updating of Raspberry Pi
- Updating of date
- Enabling SSH
- Enabling VNC
- Enabling HDMI Hotplug
- Disabling Screen Blanking
- Configuring Static IP
- Python Virtual Environtment (venv) Creation

### Venv Set-up and Python Dependencies
This is the Venv that you will install all the required Python Dependencies in, and the Venv that you will be running either `uart.py` or `game.py` in.
#### Activating Venv 
1. Open your terminal and navigate to your project directory:
```bash
cd /path/to/your/project
```
2. Run the activation command based on your target folder name:
```bash
source <venv_name>/bin/activate
```
#### Installing Python Dependencies
```bash
sudo apt-get update
pip3 install python-osc==1.8.1
pip install pyserial matplotlib
sudo apt-get install -y libopenblas-dev python3-pil.imagetk
```
| **Package**         | **Used by**                            |
|---------------------|----------------------------------------|
| `pythonosc`           | `uart.py` & `game.py` — data transfer via UDP |
| `pyserial`            | uwb-config-files & `uart.py` — UART I/O       |
| `matplotlib`          | `game.py` — embedded plot                     |
| `python3-pil.imagetk` | Tkinter image rendering for matplotlib        |      
| `libopenblas-dev`     | NumPy / matplotlib acceleration               |

---

## 2. `uart.py` Set-Up
### Set up of default OSC Host IP and Port (receiver - Pi running `game.py`)
Before running `uart.py` on the **Sensor Pi**
At line 50 and 51 of `uart.py` change the default host IP, and the port that host is receiving osc message at accordingly.
```python
DEFAULT_HOST = "X.X.X.X"
DEFAULT_PORT = 5005
```

### Host IP and Port Override via CLI
When running `uart.py` you can overide the defalt Host IP and Port.
```python
python3 uart.py --host 192.168.1.XX --port 5005
```

### Configuring Number of Tags to Capture via CLI
```python
python3 uart.py --tags X
```
**Important note: the value of `X` has to be the same as that set at `game.py`.*


---


## 3. `game.py` Setup
The game application has been refactored into multiple Python modules. *Each module is responsible for a specific part of the system*, while `game.py` remains the **main entry point** used to launch the application.

Before starting the game, **configure the OSC network addresses**, **tracking-data port**, and **number of UWB tags**.


### 3.1 OSC Target Configuration
The **outgoing OSC network settings** are stored in `constants.py`. The application sends OSC messages to:
1. REAPER for audio playback and control.
2. grandMA3 for lighting playback and control.

Update the following values to match the devices on the production network:
```python
OSC_REAPER_TARGET_IP = "192.168.254.12"
OSC_REAPER_TARGET_PORT = 8000

OSC_GMA3_TARGET_IP = "192.168.254.252"
OSC_GMA3_TARGET_PORT = 8080
```

| Setting | Purpose |
| --- | --- |
| `OSC_REAPER_TARGET_IP` | IP address of the computer running REAPER |
| `OSC_REAPER_TARGET_PORT` | UDP port on which REAPER receives OSC messages |
| `OSC_GMA3_TARGET_IP` | IP address of the computer running grandMA3 onPC |
| `OSC_GMA3_TARGET_PORT` | UDP port on which grandMA3 receives OSC messages |

Ensure that all devices are connected to the same network. The configured UDP ports must also be allowed through the firewall on each receiving computer.

> The previous MultiPlay target configuration is no longer used. REAPER and
> grandMA3 now have separate OSC destination settings.


### 3.2 Tracking-Data Receiving Port
The game **receives UWB tracking data through OSC**. Its default receiving port is
defined in `constants.py`:

```python
DEFAULT_PORT = 5005
```

The UART Pi must send its tracking data to the same port. For example:

```bash
python3 uart.py --port 5005
```

> The `--port` option shown above configures the destination port used by
> `uart.py`. Its value must match `DEFAULT_PORT` in `constants.py`.


### 3.3 Configuring the Number of Tags
Use the `--tags` option when launching `game.py` to specify the **number of UWB tags** that the application should track:

```bash
python3 game.py --tags X
```

Replace `X` with the required number of tags. For example, to run the game with
two tags:

```bash
python3 game.py --tags 2
```

> The number of tags configured in `game.py` must match the number of tags
> being transmitted by `uart.py`.


### 3.4 Tag Simulation Mode
Simulation mode allows the game to be **tested without physical UWB tags**. The **mouse position inside the game window** is used to **simulate the movement of a tag**.

Start the application in simulation mode with:

```bash
python3 game.py --simulate
```

Simulation mode can be used to test:
1. Safe-zone entry and exit.
2. Zone expansion and shrinking.
3. Danger-zone collisions.
4. Level progression.
5. Game-won and game-over conditions.
6. OSC cues sent to REAPER and grandMA3.

*^ Note: The simulated tag simply acts as an actual tag.*


### 3.5 Starting the Game
For normal operation with two physical tags:

```bash
python3 game.py --tags 2
```

For development using mouse-based tag simulation:

```bash
python3 game.py --simulate
```

To display all command-line options supported by the current version of
`game.py`:

```bash
python3 game.py --help
```


### 3.6 Module Responsibilities
Although the application is launched through `game.py`, its functionality is distributed across the **following modules**:

| Module | Responsibility |
| --- | --- |
| `game.py` | Initializes and launches the game application |
| `constants.py` | Stores network addresses, ports, zone definitions, and shared constants |
| `game_manager.py` | Controls game states, level progression, and win or loss conditions |
| `level_config.py` | Stores the configuration and objectives for each game level |
| `shared_state.py` | Stores shared game and tag-tracking information |
| `osc_handler.py` | Receives and processes OSC tracking data |
| `osc_sender.py` | Sends OSC cues to REAPER and grandMA3 |
| `trilateration.py` | Calculates tag positions from UWB anchor distances |
| `kalman.py` | Smooths calculated tag positions using a Kalman filter |
| `zones.py` | Handles safe zones, danger zones, and zone interactions |
| `tutorial.py` | Controls the tutorial stage and transition into the game |
| `viewer.py` | Displays the game window, tracked tags, zones, and HUD |

*Note: More info on how each script is dependent on each other can be found [here]().*


---


## 4. REAPER Laptop Set-Up
### Hardware
1. Laptop running
    - REAPER
    - L-ISA Processor & Controller
    - Dante Virtual Soundcard (DVS)
    - LoopMIDI


---


### 4.1 L-ISA Processor
### L-ISA Processor Set-up & Configuration
1. Select Network interface as the interface that Dante Network is on (red box)
2. Select **ASIO** as the Audio Device Type (yellow box)
3. Select **Dante Virtual Soundcard** as the Output (green box)
![L-ISA Processor Config](assets/l-isa-processor-config.png)


---


### 4.2 L-ISA Controller
### L-ISA Controller Set-up & Configuration
#### Connecting L-ISA Prcessor to L-ISA Controller
1. Click **Processors** to go to Processor connection window (red box)
2. To connect `L-ISA Prcoessor` to `L-ISA Controller`, click **'connect'** (yellow box)  
*(note: it will toggle between connect and disconnec. If connected will see green arrow)*
![L-ISA Connect Processor](assets/l-isa-controller-connect.png)

#### Configuring Speaker Output Positions and Routing
1. Click **Settings** to go to Settings window (red box)
2. To go to speaker configuration, click **'Spekaers'** (yellow box)  
![L-ISA Speaker Config Window](assets/l-isa-controller-speaker-setting.png)
3. To route speaker, **select the desired speaker** in the visualiser on the right (red box)
4. Followed by **clicking the respective Output** coloumn to open up the routing page (yellow box)
![L-ISA Speaker Config selection](assets/l-isa-controller-speaker-select.png)
5. In the routing page, **select the desired routing** for your speaker (red box)
6. To confirm and save changes, click **'Save'** (yellow box)
![L-ISA Speaker Routing](assets/l-isa-controller-speaker-routing.png)

#### Setting up reciving MTC from REAPER
For a detailed step by step guide refer to a guide [here](../../LoopMIDI%20Integration/Reaper_midi_to_LISA.md).


---


### 4.3 REAPER
### REAPER Set-up & Configuration
#### OSC Configuration
1. Go to **Reaper Preference** using the shortcup `Ctrl + P`
2. Navigate to **Control/OSC/Web** (red box)
3. Cick on `Add` to configure new OSC Device (green box)
![Reaper Preferences Window](assets/reaper-preferences-osc.png)
4. Configure new **OSC Device** following these steps
    - Select **OSC (Open Sound Control)** (red box) 
    - Enter **desired name** (yellow box)
    - Select **Configure device IP+local port** (blue box)
    - Enter in respective port and IP details.
    ![OSC Configuration Window](assets/reaper-osc-device.png)
    *^ Important Note: the **Local listen port** must match the port number entered in python osc sender script.*

#### Track Routing Set-up
There are two ways to route your tracks.  
#### Per track routing set-up
1. Open the **Mixer panel** using the shortcut `Ctrl + M`
![Reaper Mixer](assets/reaper-mixer.png)
2. Select the **track routing button** on desired track (red box)
3. To route, click **Add new hardware output...** and select desired output (green box)
![Reaper Track Routing](assets/reaper-track-routing.png)

#### Routing matrix
1. Open the **Routing Matrix panel** using the shortcut `Alt + R`
![Reaper Routing Matrix](assets/reaper-matrix.png)
2. Click on the corresponding box to route the **desired track** to the **respective output**


#### MTC to L-ISA Controller Set-up
In an *overview*, to **send MIDI-Timeclock to L-ISA Controller from REAPER**
1. Create MIDI Port via LoopMIDI
2. Setup MIDI Time Clock generator on REAPER Track
3. Send MIDI Time Clock via the MIDI Port
4. Set to recieve MTC on L-ISA Controller

For a detailed step by step guide refer to a guide [here](../../LoopMIDI%20Integration/Reaper_midi_to_LISA.md).


----


## 5. GrandMA3 Set-Up
### Hardware
1. Laptop running
    - GrandMA3 onPC
2. GrandMA Node 
3. Lighting Fixtures

### GrandMA3 Set-up & Configuration
#### Setting up OSC Reciving Commands
1. To **enter OSC config window**, click the **gearbox icon** (top right red box)
2. Followed by **In & Out** (middle yellow box)
![GrandMA3 In & Out](assets/gma-in-out.png)
3. In the **In & Out settings** page, select **OSC** (red box)
4. To make a new OSC Data, click **'New OSC Data'** (yellow box)
5. Ensure **Network Interface** is **matching** with **Destination IP** (green box)  
*(Note: This is the network interface where GrandMA will recieve commands from)*
6. Ensure **Mode** is **'UDP'** (blue box)
7. Set **Port** to **'8080'** (orange box)
8. Set **Prefix** to **'gma3'** (pink box)
9. Ensure to **toggle 'Recieve' and 'Recieve Command'** to be **'Yes'** (purple box)
![GrandMA3 OSC Config](assets/gma-osc-config.png)


---


## 6. Appendix 
### 6.1 Laptop as Game Pi Set-up
#### Venv Creation
1. Install Miniconda3

Download zip file containing installer [here](assets/Miniconda3-latest-Windows-x86_64.zip).

2. Open the **Windows Start Menu**. Search for and open **Anaconda Prompt** or **Anaconda PowerShell Prompt**.

3. Run the creation command and specify your desired Python version: (in this case, 3.11)
```batch
conda create -n <venv_name> python=3.11
```
Press `y` when prompted to confirm the installation of base packages


#### Venv Activation
```batch
conda activate <venv_name>
```

#### Installing Python Dependencies
```bash
pip install python-osc==1.8.1
pip install pyserial matplotlib
conda install pillow
```
| **Package**         | **Used by**                            |
|---------------------|----------------------------------------|
| `pythonosc`         | `uart.py` & `game.py` — data transfer via UDP |
| `pyserial`          | uwb-config-files & `uart.py` — UART I/O       |
| `matplotlib`        | `game.py` — embedded plot                     |
| `pillow`            | Tkinter image rendering for matplotlib        |      


### 6.2 About L-ISA Processor (Desktop)
L-ISA Processor Desktop is a software-based spatial audio processor included in the L-ISA Studio software suite. It provides the processing capabilities of an L-ISA hardware processor directly on a Windows or macOS computer without requiring dedicated processing hardware.

In this project, audio from REAPER is routed through the L-ISA Audio Bridge into L-ISA Processor Desktop. The software then applies the sound positioning and spatial effects configured in L-ISA Controller before sending the processed audio to the selected audio output device.

Some relevant features include:
1. Software-based spatial audio processing
2. Processing of up to 96 individual audio objects
3. Support for up to 16 audio outputs
4. Control of sound position, width, distance, and elevation
5. Object-based room and spatial effects
6. Binaural monitoring through headphones
7. Multi-speaker immersive audio output
8. Integration with L-ISA Controller
9. Audio routing through L-ISA Audio Bridge
10. Output through headphones or a compatible audio interface

Below are some links that may be useful.
- For more information about **L-ISA Processor Desktop**, visit the [L-ISA Processor Desktop guide](https://www.l-acoustics.com/stories/create-spatial-audio-l-isa-studio-desktop-processor-setup/)
- For more information about the complete **L-ISA Studio** software suite, visit the [L-ISA Studio product page](https://www.l-acoustics.com/products/l-isa-studio/)
- To download **L-ISA Studio**, visit the [L-ISA Studio download page](https://www.l-acoustics.com/products/l-isa-studio/) 


### 6.3 About L-ISA Controller
L-ISA Controller is the software interface used to configure and control the L-ISA spatial audio system. It allows the operator to place and move individual sound sources within a virtual three-dimensional space.

The software sends control instructions to the L-ISA Processor, which performs the actual audio processing. In this project, L-ISA Controller is used to manage the spatial position and movement of the audio tracks played from REAPER.

Some relevant features include:
1. Control of sound position, width, distance, and elevation
2. Creation of sound movements and trajectories
3. Snapshot programming and recall
4. Spatial effects and room simulation
5. MIDI Time Code synchronization
6. OSC control and external system integration
7. Real-time monitoring of the spatial audio mix

Below are some links that may be useful.
- For more information about **L-ISA Controller**, visit the [L-ISA Controller product page](https://www.l-acoustics.com/products/l-isa-controller/)
- To download **L-ISA Controller**, visit the [L-ISA Controller download page](https://www.l-acoustics.com/products/l-isa-controller/)
- For manuals and technical information, visit the [L-Acoustics Documentation Centre](https://www.l-acoustics.com/result-documentation-center/?choice=L-ISA%20Controller#page-1)


### 6.4 About REAPER
REAPER is a digital audio workstation developed by Cockos for recording, editing, arranging, processing, and playing audio and MIDI.

In this project, REAPER acts as the main audio playback system. It plays the music and sound-effect tracks, sends audio to the L-ISA Processor, and communicates with other parts of the system using OSC and MIDI Time Code.

Some relevant features include:
1. Multi-track audio
2. Flexible audio routing
3. Audio editing and mixing
4. Cue and timeline-based playback
5. Volume, effect, and parameter automation
6. OSC control over a network
7. MIDI and MIDI Time Code output
8. Support for scripts, actions, and external controllers
9. Multi-channel and surround-audio routing

Below are some links that may be useful.
- For more information about **REAPER**, visit the [REAPER website](https://www.reaper.fm/)
- To download and install **REAPER**, visit the [REAPER download page](https://www.reaper.fm/download.php)
- For the **REAPER User Guide**, visit the [REAPER documentation page](https://www.reaper.fm/userguide.php)
- For information about OSC control in **REAPER**, visit the [REAPER OSC documentation](https://www.reaper.fm/sdk/osc/osc.php)


### 6.5 About GrandMA3
grandMA3 is a professional lighting-control platform developed by MA Lighting. It is used to configure lighting fixtures, create lighting looks, program cues, and control lighting during live productions.

In this project, grandMA3 onPC receives OSC commands from the Python game application. These commands trigger programmed lighting sequences that respond to game events. Lighting data is then sent through a grandMA3 node to the connected lighting fixtures.

Some relevant features include:
1. Lighting-fixture patching and configuration
2. Creation of presets and lighting looks
3. Cue and sequence programming
4. Executor-based playback control
5. Phaser and lighting-effect programming
6. OSC input and output
7. Network communication with grandMA3 nodes
8. DMX output to lighting fixtures
9. Show-file storage and backup
10. Pre-programming and lighting visualization

Below are some links that may be useful.
- For more information about **grandMA3**, visit the [grandMA3 product page](https://www.malighting.com/grandma3/)
- To download **grandMA3 onPC**, visit the [MA Lighting download page](https://www.malighting.com/downloads/products/grandma3/)
- For the **grandMA3 User Manual**, visit the [grandMA3 Help website](https://help.malighting.com/grandMA3/)
- For information about OSC configuration, visit the [grandMA3 OSC documentation](https://help.malighting.com/grandMA3/2.3/HTML/remote_inputs_osc.html)
