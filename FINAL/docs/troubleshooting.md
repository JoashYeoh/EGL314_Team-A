# Troubleshooting

This section lists common issues that may occur while setting up or running the UWB game system, along with their possible causes and recommended solutions.

---

## 1. No UWB Data Received

### Symptoms

* Player position does not appear on the game screen.
* No distance values are displayed.
* The player icon does not move.

### Possible Causes

* UART cable is not connected properly.
* UWB tag is powered off.
* Incorrect serial port selected.
* Sensor Raspberry Pi is not running `uart.py`.

### Solution

* Check that the UWB tag is powered on.
* Verify that all UART connections are secure.
* Confirm that the correct serial port is configured.
* Restart `uart.py` on the sensor Raspberry Pi.

---

## 2. OSC Communication Not Working

### Symptoms

* `uart.py` is receiving data, but `game.py` does not update.
* No player movement is shown on the game display.

### Possible Causes

* Incorrect IP address.
* Incorrect OSC port.
* Network connection between the Raspberry Pis has failed.

### Solution

* Ensure both Raspberry Pis are connected to the same network.
* Verify the destination IP address in `uart.py`.
* Confirm that both programs are using the same OSC port.
* Test connectivity using the `ping` command.

---

## 3. Incorrect Player Position

### Symptoms

* Player appears in the wrong location.
* Position jumps unexpectedly.
* Player moves even when standing still.

### Possible Causes

* Incorrect anchor coordinates.
* Poor UWB signal quality.
* Tag is blocked by large objects.
* Calibration has not been completed.

### Solution

* Verify all anchor positions in the configuration file.
* Ensure anchors are mounted securely.
* Remove large metal objects that may interfere with the signal.
* Recalibrate the system before starting the game.

---

## 4. Player Position is Jittery

### Symptoms

* Player marker constantly shakes.
* Movement appears unstable.

### Possible Causes

* Signal reflections.
* Temporary UWB interference.
* Kalman filter settings require adjustment.

### Solution

* Ensure the play area has minimal obstacles.
* Check that the Kalman filter is enabled.
* Reduce sources of wireless interference where possible.

---

## 5. Safe Zone Does Not Shrink

### Symptoms

* Safe zone remains the same size throughout the game.

### Possible Causes

* Game timer has not started.
* Zone update function is not running.
* Game has not entered the active state.

### Solution

* Verify that the game has started successfully.
* Confirm that the zone update function is being called.
* Restart the game if necessary.

---

## 6. Game Does Not End

### Symptoms

* Game continues running after players leave the safe zone.

### Possible Causes

* Safe zone has not fully shrunk.
* Game-ending condition has not been reached.

### Solution

* Allow the safe zone to shrink completely.
* Verify that the game-ending logic is enabled.
* Check that the final zone radius reaches its minimum value.

---

## 7. GUI Does Not Open

### Symptoms

* `game.py` starts but no window appears.

### Possible Causes

* Missing Python libraries.
* Display configuration issue.
* Tkinter installation problem.

### Solution

* Install all required Python packages.
* Verify that Tkinter is installed correctly.
* Restart the Raspberry Pi.

---

## 8. Python Module Not Found

### Symptoms

```
ModuleNotFoundError
```

### Possible Causes

* Required library is missing.
* Virtual environment is not activated.

### Solution

* Activate the correct Python environment.
* Install the missing package using:

```
pip install <package_name>
```

* Verify that all project dependencies are installed.

---

## 9. UWB Tag Not Detected

### Symptoms

* Tag never appears in the game.

### Possible Causes

* Battery is empty.
* Tag firmware is incorrect.
* Tag ID does not match the game configuration.

### Solution

* Recharge or replace the battery.
* Verify the firmware version.
* Check that the tag ID matches the configured player ID.

---

## 10. High CPU Usage or Slow Performance

### Symptoms

* Game becomes laggy.
* Display updates slowly.

### Possible Causes

* Too many background applications.
* High rendering load.
* Insufficient Raspberry Pi resources.

### Solution

* Close unnecessary applications.
* Restart the Raspberry Pi.
* Reduce debugging output if enabled.
* Ensure only the required programs are running.

---

## General Checks Before Running the Game

Before each game session, verify the following:

* All UWB anchors are powered on.
* UWB tags are fully charged.
* UART connections are secure.
* Both Raspberry Pis are connected to the same network.
* `uart.py` is running on the sensor Raspberry Pi.
* `game.py` is running on the game Raspberry Pi.
* OSC IP address and port are correct.
* The game arena is free from large obstacles that may interfere with UWB signals.
