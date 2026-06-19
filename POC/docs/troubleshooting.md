# Troubleshooting Documentation

## 1. No Player Position Appears on Screen

Symptoms:

1:Game launches successfully.

2:No player marker is visible.

3:Player movement is not detected.

Possible Cause:
The Game Pi is not receiving UWB data from the Sensor Pi.

Solution:

1:Verify uart.py is running on the Sensor Pi.

2:Check that both Raspberry Pis are connected to the same network.

3:Verify the Game Pi IP address configured in uart.py.

4:Ensure OSC messages are being transmitted correctly.

## 2. Player Position Is Inaccurate

Symptoms:

1:Marker appears in the wrong location.

2:Position jumps around unexpectedly.

3:Physical position does not match screen position.

Possible Cause:
The UWB system has not been calibrated correctly.

Solution:
1:Run viewer_calibrate.py.
2:Verify anchor coordinates are correct.
3:Ensure anchors have not been moved after calibration.
4:Remove large metal objects that may interfere with UWB signals.

## 3. No UWB Data Received

Symptoms:

1:No distance readings are displayed.

2:Player tracking does not start.

Possible Cause
UART communication between the UWB receiver and Sensor Pi has failed.

Solution
Run:
./check_uart.sh

1:Check UART wiring.

2:Verify the correct serial port is being used.

3:Restart the UWB receiver module.

## 4. Audio or Media Effects Do Not Trigger

Symptoms:

1:Gameplay works normally.

2:Music and sound effects do not play.

Possible Cause:
OSC communication between the Game Pi and media server is not working.

Solution:

1: Verify the media server / Multiplay is running.

2: Confirm both devices are connected to the same network.

3: Check that Sensor Pi is running uart.py

4: Confirm correct IP addresses (Sensor Pi → Game Pi → Multiplay).

5: Ensure OSC port numbers match on all devices.

6: Check OSC IP settings are correct.

7: Confirm Multiplay is listening on the correct port.

8: Allow UDP traffic / check firewall settings if needed.

## 5. Game Starts but Immediately Ends

Symptoms:

1:Game launches.

2:Game Over appears almost instantly.

Possible Cause:
The player's detected position is inside a danger zone due to incorrect calibration.

Solution:

1:Re-run calibration using viewer_calibrate.py.

2:Verify the player's starting position.

3:Confirm danger zones are displayed in the correct locations.

**Quick Checklist Before Running the Game:**

✓ UWB modules powered on

✓ UART connection verified

✓ Sensor Pi running uart.py

✓ Game Pi running game.py

✓ Both Pis connected to same network

✓ Calibration completed

✓ Player position visible on screen

✓ OSC communication working
