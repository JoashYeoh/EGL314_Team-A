# Game Logic Documentation

Overview:
The UWB Interactive Game is a location-based game that uses Ultra-Wideband (UWB) tracking to monitor the player's position in real time.

The player's physical movement is translated into actions within the game. By moving around the play area, players interact with different zones that appear on the game screen.

The objective is to capture safe zones while avoiding danger zones and survive until the end of the game.

Gameplay Flow:

The game is divided into three main stages:

Tutorial
    ↓
Zone Capture Phase
    ↓
Survival Phase
    ↓
Victory / Game Over

Stage 1: Tutorial

When the game starts, players are presented with a tutorial screen.

The tutorial explains:

How player movement is tracked
The difference between Safe Zones and Danger Zones
How to capture zones
How to win or lose the game

Once all players understand the rules, the game begins.

Stage 2: Zone Capture Phase:

During this phase, several Safe Zones appear on the game field.

What is a Safe Zone?
A Safe Zone is an area that players must enter and remain inside to capture.

WHAT HAPPENS WHEN U GET INTO THE SAFE ZONE:
Player enters Safe Zone
          ↓
Zone begins expanding
          ↓
Player remains inside
          ↓
Zone reaches maximum size
          ↓
Zone is captured

Capturing a Zone

To successfully capture a zone:

1:Move into the Safe Zone.
2:Stay within the zone boundary.
3:Allow the zone to fully expand.
4:Once fully expanded, the zone is considered captured.

The process is repeated until all Safe Zones have been captured.

Danger Zones:

While players are capturing Safe Zones, Danger Zones are also present on the field.

What is a Danger Zone?

Danger Zones are hazardous areas that players must avoid.

If a player enters a Danger Zone:

Player enters Danger Zone
          ↓
      Game Over

Danger Zones move throughout the play area, forcing players to constantly reposition themselves.      

Stage 3: Survival Phase

After all Safe Zones have been captured, the game enters Survival Mode.

During this phase:

1:No new Safe Zones appear.
2:Existing Safe Zones gradually shrink.
3:Danger Zones become more aggressive.
4:Players must survive for a fixed duration.

All Safe Zones Captured
          ↓
Survival Mode Begins
          ↓
Avoid Danger Zones
          ↓
Survive Countdown Timer

The goal is to remain alive until the timer reaches zero.

Win Condition:

A player wins if they successfully survive until the end of the Survival Phase.

Capture All Safe Zones
          ↓
Enter Survival Phase
          ↓
Survive Entire Timer
          ↓
      Victory

When this happens:

1:Victory audio is played
2;Victory visuals are displayed
3:The game ends successfully

Lose Conditions

The game can end in failure under the following situations:

1. Entering a Danger Zone:

   Player touches Danger Zone
          ↓
     Game Over

2. Safe Zones Destroyed

If all Safe Zones disappear before the player successfully completes the objective:

No Remaining Safe Zones
          ↓
     Game Over

Real-Time Player Tracking:

The game uses AI Thinker UWB modules to continuously track player positions.

The tracking process works as follows:

Player Carries UWB Tag
          ↓
Anchors Measure Distances
          ↓
Sensor Pi Receives Data
          ↓
Game Pi Calculates Position
          ↓
Player Marker Updated On Screen

This allows the game to accurately determine whether a player is inside a Safe Zone or Danger Zone.

Audio and Visual Feedback:

The game provides immediate feedback to players through audio and visual effects.

Examples include:

| Event                 | Feedback                  |
| --------------------- | ------------------------- |
| Game Start            | Start music plays         |
| Zone Captured         | Capture sound effect      |
| Enter Danger Zone     | Warning / Game Over sound |
| Survival Phase Starts | New background music      |
| Victory               | Victory music and visuals |

This feedback helps players understand what is happening during gameplay without needing to look at technical information.
     
Summary

The objective of the game is simple:

1:Capture all Safe Zones.
2:Avoid all Danger Zones.
3:Survive the final Survival Phase.
4:Reach the end of the timer to win.
