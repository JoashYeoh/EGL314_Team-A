# OSC Reference

This document describes the OSC functions defined in `osc_sender.py`,
their game triggers, the commands sent to grandMA3 and REAPER, and their
expected results.

## 1. Game Starting Sequences

### `send_off_all()`

#### Python function

``` python
send_off_all()
```

#### Game trigger

Called when the game needs to **stop all currently running grandMA3
sequences**, typically as part of resetting or preparing the lighting
system.

#### grandMA3 commands

    Order Command       Purpose
  ------- ------------- -----------------------------------------------
        1 `Off Seq *`   Stops all currently active grandMA3 sequences

#### Expected result

All active grandMA3 sequences are switched off, allowing the lighting
system to start from a known state.

------------------------------------------------------------------------

### `send_start_lobby()`

#### Python function

``` python
send_start_lobby()
```

#### Game trigger

Called when the application enters the **Lobby**. This prepares the
room's lobby lighting and starts the corresponding ambient audio
playback.

#### grandMA3 commands

  ------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------
                             1 `Go Macro 1`          Executes the grandMA3
                                                     macro used to
                                                     initialise the lobby
                                                     lighting state

  ------------------------------------------------------------------------

#### REAPER commands

  --------------------------------------------------------------------------------------------------
                         Order Action                                          Purpose
  ---------------------------- ----------------------------------------------- ---------------------
                             1 Custom action                                   Sets REAPER repeat
                               `_RS4cb981b7c961f3b84673b9007ab7caa7bb13a182`   mode

                             2 `41764`                                         Jumps playback to
                                                                               Region 4

                             3 `43102`                                         Sets the loop points
                                                                               to the selected
                                                                               region

                             4 `1007`                                          Starts playback

                             5 Custom action                                   Mutes Tracks 11--14
                               `_RS0a8bd5995464dc985213e2e1071132a46345050e`   
  --------------------------------------------------------------------------------------------------

#### Expected result

The room enters its **Lobby state**, with the lobby lighting active and
Region 4 playing continuously while Tracks 11--14 remain muted.

------------------------------------------------------------------------

### `send_start_tutorial()`

#### Python function

``` python
send_start_tutorial()
```

#### Game trigger

Called when the player selects **PLAY TUTORIAL** from the Lobby.

#### grandMA3 commands

  ------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------
                             1 `Go Macro 2`          Executes the grandMA3
                                                     macro used to
                                                     initialise the
                                                     tutorial lighting

  ------------------------------------------------------------------------

#### REAPER commands

  ------------------------------------------------------------------------------------------
                         Order Action                                  Purpose
  ---------------------------- --------------------------------------- ---------------------
                             1 `40168`                                 Jumps playback to
                                                                       Marker 8

                             2 `40944`                                 Selects Track 8

                             3 `40731`                                 Unmutes the selected
                                                                       track

                             4 `1007`                                  Starts playback

                             5 `Timer(20, send_start_tutorial_play)`   Calls the tutorial
                                                                       play sequence after
                                                                       20 seconds
  ------------------------------------------------------------------------------------------

#### Expected result

The tutorial introduction begins, including the associated lighting
state and tutorial audio. After **20 seconds**, the system automatically
transitions into the tutorial gameplay audio state.

------------------------------------------------------------------------

### `send_start_tutorial_play()`

#### Python function

``` python
send_start_tutorial_play()
```

#### Game trigger

Called automatically **20 seconds after `send_start_tutorial()`**.

#### REAPER commands

    Order Action    Purpose
  ------- --------- ---------------------------------------------
        1 `41763`   Jumps playback to Region 3
        2 `43102`   Sets the loop points to the selected region
        3 `1007`    Starts playback

#### Expected result

REAPER transitions from the tutorial introduction audio into the
**looping tutorial gameplay audio**.

------------------------------------------------------------------------

### `send_start_game()`

#### Python function

``` python
send_start_game()
```

#### Game trigger

Called when the main game begins, either after completing the tutorial
or by selecting **INSTANT PLAY** from the Lobby.

#### grandMA3 commands

  ------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------
                             1 `Go Macro 3`          Executes the grandMA3
                                                     macro used to
                                                     initialise the main
                                                     game lighting

  ------------------------------------------------------------------------

#### REAPER commands

  --------------------------------------------------------------------------------------------------
                         Order Action                                          Purpose
  ---------------------------- ----------------------------------------------- ---------------------
                             1 `41761`                                         Jumps playback to
                                                                               Region 1

                             2 `43102`                                         Sets loop points to
                                                                               Region 1

                             3 `1007`                                          Starts playback

                             4 Custom action                                   Mutes Tracks 11--14
                               `_RS0a8bd5995464dc985213e2e1071132a46345050e`   
  --------------------------------------------------------------------------------------------------

#### Expected result

The system enters the **main gameplay state**, with the game lighting
loaded and Region 1 playing as the looping game audio.

------------------------------------------------------------------------

## 2. Tutorial Zone Logic Sequences

### `send_tutorial_zone_enter(tag_id, zone_label)`

#### Python function

``` python
send_tutorial_zone_enter(tag_id, zone_label)
```

#### Game trigger

Called when a tracked player/tag **enters one of the tutorial safe
zones**.

#### grandMA3 commands

  ---------------------------------------------------------------------------
  Tutorial Zone           Command                     Purpose
  ----------------------- --------------------------- -----------------------
  Tutorial Zone 1         `Goto Sequence 107 cue 2`   Changes Tutorial Zone 1
                                                      lighting to its
                                                      occupied/expanding
                                                      state

  Tutorial Zone 2         `Goto Sequence 108 cue 2`   Changes Tutorial Zone 2
                                                      lighting to its
                                                      occupied/expanding
                                                      state
  ---------------------------------------------------------------------------

#### REAPER commands

  Tutorial Zone          Track Action
  ----------------- ---------- -------------------
  Tutorial Zone 1     Track 11 Select and unmute
  Tutorial Zone 2     Track 12 Select and unmute

#### Expected result

Entering a tutorial zone activates its corresponding **zone expansion
lighting and audio feedback**.

------------------------------------------------------------------------

### `send_tutorial_zone_exit(tag_id, zone_label)`

#### Python function

``` python
send_tutorial_zone_exit(tag_id, zone_label)
```

#### Game trigger

Called when a tracked player/tag **leaves a tutorial safe zone**.

#### grandMA3 commands

  ---------------------------------------------------------------------------
  Tutorial Zone           Command                     Purpose
  ----------------------- --------------------------- -----------------------
  Tutorial Zone 1         `Goto Sequence 107 cue 1`   Returns Tutorial Zone 1
                                                      to its
                                                      inactive/shrinking
                                                      state

  Tutorial Zone 2         `Goto Sequence 108 cue 1`   Returns Tutorial Zone 2
                                                      to its
                                                      inactive/shrinking
                                                      state
  ---------------------------------------------------------------------------

#### REAPER commands

  Tutorial Zone          Track Action
  ----------------- ---------- -----------------
  Tutorial Zone 1     Track 11 Select and mute
  Tutorial Zone 2     Track 12 Select and mute

#### Expected result

Leaving a tutorial zone returns its lighting to the **shrinking/inactive
state** and stops its associated zone audio.

------------------------------------------------------------------------

### `send_tutorial_zone_max(zone_index, zone_label)`

#### Python function

``` python
send_tutorial_zone_max(zone_index, zone_label)
```

#### Game trigger

Called when a tutorial zone reaches its **maximum size** during the
expansion tutorial.

#### REAPER commands

  Tutorial Zone          Track Action
  ----------------- ---------- -----------------
  Tutorial Zone 1     Track 11 Select and mute
  Tutorial Zone 2     Track 12 Select and mute

#### Expected result

Once the tutorial zone reaches maximum expansion, its associated
expansion audio is muted.

> **Note:** The current implementation does not send a grandMA3 command
> when a tutorial zone reaches maximum size.

------------------------------------------------------------------------

### `send_tutorial_danger_zone()`

#### Python function

``` python
send_tutorial_danger_zone()
```

#### Game trigger

Called when the tutorial reaches the **Danger Zone Tutorial** stage.

#### grandMA3 commands

  ------------------------------------------------------------------------------
                         Order Command                     Purpose
  ---------------------------- --------------------------- ---------------------
                             1 `Goto Sequence 106 cue 1`   Activates the
                                                           danger-zone tutorial
                                                           lighting

  ------------------------------------------------------------------------------

#### Expected result

The danger-zone visual state is activated to introduce players to the
danger-zone mechanic before the main game starts.

------------------------------------------------------------------------

## 3. Main Game Zone Logic

### `send_zone_enter(tag_id, zone_index)`

#### Python function

``` python
send_zone_enter(tag_id, zone_index)
```

#### Game trigger

Called when a tracked player/tag **enters one of the main game safe
zones**.

#### grandMA3 commands

  ---------------------------------------------------------------------------
  Zone                    Command                     Purpose
  ----------------------- --------------------------- -----------------------
  Zone A                  `Goto Sequence 110 cue 2`   Activates Zone A
                                                      occupied/expansion
                                                      state

  Zone B                  `Goto Sequence 111 cue 2`   Activates Zone B
                                                      occupied/expansion
                                                      state

  Zone C                  `Goto Sequence 112 cue 2`   Activates Zone C
                                                      occupied/expansion
                                                      state

  Zone D                  `Goto Sequence 113 cue 2`   Activates Zone D
                                                      occupied/expansion
                                                      state

  Zone E                  `Goto Sequence 114 cue 2`   Activates Zone E
                                                      occupied/expansion
                                                      state
  ---------------------------------------------------------------------------

#### REAPER commands

  Zone          Track Action
  -------- ---------- -------------------
  Zone A     Track 11 Select and unmute
  Zone B     Track 12 Select and unmute
  Zone C     Track 13 Select and unmute
  Zone D     Track 14 Select and unmute
  Zone E     Track 15 Select and unmute

#### Expected result

When a player occupies a safe zone, the corresponding lighting sequence
moves into its **active/expansion state**, while that zone's REAPER
audio track is unmuted.

------------------------------------------------------------------------

### `send_zone_exit(tag_id, zone_index)`

#### Python function

``` python
send_zone_exit(tag_id, zone_index)
```

#### Game trigger

Called when a tracked player/tag **leaves one of the main game safe
zones**.

#### grandMA3 commands

  --------------------------------------------------------------------------
  Zone                    Command                    Purpose
  ----------------------- -------------------------- -----------------------
  Zone A                  `Go- Sequence 110 cue 1`   Returns Zone A towards
                                                     its inactive state

  Zone B                  `Go- Sequence 111 cue 1`   Returns Zone B towards
                                                     its inactive state

  Zone C                  `Go- Sequence 112 cue 1`   Returns Zone C towards
                                                     its inactive state

  Zone D                  `Go- Sequence 113 cue 1`   Returns Zone D towards
                                                     its inactive state

  Zone E                  `Go- Sequence 114 cue 1`   Returns Zone E towards
                                                     its inactive state
  --------------------------------------------------------------------------

#### REAPER commands

  Zone          Track Action
  -------- ---------- -----------------
  Zone A     Track 11 Select and mute
  Zone B     Track 12 Select and mute
  Zone C     Track 13 Select and mute
  Zone D     Track 14 Select and mute
  Zone E     Track 15 Select and mute

#### Expected result

When a zone becomes unoccupied, its lighting begins returning towards
its **inactive/shrinking state**, while the corresponding REAPER zone
track is muted.

------------------------------------------------------------------------

### `send_zone_complete(zone_index)`

#### Python function

``` python
send_zone_complete(zone_index)
```

#### Game trigger

Called once when a main-game safe zone reaches its **maximum size and is
considered captured**.

#### grandMA3 commands

  Zone       Sequence Command
  -------- ---------- ---------------------------
  Zone A          110 `Goto Cue 4 Sequence 110`
  Zone B          111 `Goto Cue 4 Sequence 111`
  Zone C          112 `Goto Cue 4 Sequence 112`
  Zone D          113 `Goto Cue 4 Sequence 113`
  Zone E          114 `Goto Cue 4 Sequence 114`

#### Expected result

The zone's grandMA3 sequence moves to **Cue 4**, representing the zone's
completed/captured lighting state.

------------------------------------------------------------------------

## 4. Game Progression Sequences

### `send_phase_one_complete()`

#### Python function

``` python
send_phase_one_complete()
```

#### Game trigger

Called once when **Zones A--D have all been captured**, marking the
completion of Phase 1 and beginning the transition into Phase 2.

#### grandMA3 commands

  ------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------
                             1 `Go Macro 5`          Executes the lighting
                                                     transition for Phase
                                                     1 completion / Phase
                                                     2 introduction

  ------------------------------------------------------------------------

#### REAPER commands

    Order Action    Purpose
  ------- --------- ----------------------------
        1 `40169`   Jumps playback to Marker 9
        2 `40944`   Selects Track 8
        3 `40731`   Unmutes Track 8
        4 `1007`    Starts playback

#### Expected result

After Zones A--D are captured, the system transitions into the **Phase 2
introduction**, changing the lighting and playing the corresponding AI
voice/audio cue before Zone E gameplay.

------------------------------------------------------------------------

### `send_zone_e_manual_start()`

#### Python function

``` python
send_zone_e_manual_start()
```

#### Game trigger

Called when the **Game Master manually starts the Zone E expansion
stage** during Phase 2.

#### grandMA3 commands

  ------------------------------------------------------------------------------
                         Order Command                     Purpose
  ---------------------------- --------------------------- ---------------------
                             1 `Goto Cue 2 Sequence 114`   Moves Zone E's
                                                           lighting sequence
                                                           into its
                                                           active/expanding
                                                           state

  ------------------------------------------------------------------------------

#### REAPER commands

    Order Action    Purpose
  ------- --------- ------------------------------------
        1 `41762`   Jumps playback to Region 2
        2 `43102`   Sets the loop points to the region
        3 `40952`   Selects Track 14
        4 `40731`   Unmutes the selected track
        5 `1007`    Starts playback

#### Expected result

Phase 2's Zone E gameplay begins, with Sequence 114 moving to Cue 2 and
Region 2 beginning playback.

> **Check:** `send_zone_enter()` associates Zone E with Track 15, while
> `send_zone_e_manual_start()` currently selects Track 14. Confirm
> whether this is intentional.

------------------------------------------------------------------------

### `send_pause_reaper()`

#### Python function

``` python
send_pause_reaper()
```

#### Game trigger

Called whenever the game logic needs to **pause REAPER playback**.

#### REAPER commands

    Order Action   Purpose
  ------- -------- ------------------------
        1 `1008`   Pauses REAPER playback

#### Expected result

Current REAPER playback is paused without affecting the grandMA3
lighting state.

------------------------------------------------------------------------

## 5. Game Failure Sequence

### `send_game_over()`

#### Python function

``` python
send_game_over()
```

#### Game trigger

Called when the game enters its **GAME OVER / failure state**.

#### grandMA3 commands

  ------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------
                             1 `Go Sequence 115`     Starts the grandMA3
                                                     game-over lighting
                                                     sequence

  ------------------------------------------------------------------------

#### REAPER commands

    Order Action    Purpose
  ------- --------- ----------------------------
        1 `40163`   Jumps playback to Marker 3
        2 `1007`    Starts playback

#### Expected result

The lighting system enters the **game-over state**, while REAPER plays
the associated failure/game-over audio.

------------------------------------------------------------------------

## 6. Game Win and Finale Sequences

### `send_game_win()`

#### Python function

``` python
send_game_win()
```

#### Game trigger

Called when the game's **win condition has been achieved**, after the
required safe zones have been captured.

#### grandMA3 commands

  ------------------------------------------------------------------------------
                         Order Command               Purpose
  ---------------------------- --------------------- ---------------------------
                             1 `Go Macro 6`          Executes the grandMA3
                                                     game-win/default-lighting
                                                     macro

  ------------------------------------------------------------------------------

#### Expected result

grandMA3 transitions the room into its **game-win / game-end lighting
state**.

------------------------------------------------------------------------

### `send_game_end_finale()`

#### Python function

``` python
send_game_end_finale()
```

#### Game trigger

Called during the **finale sequence after the game has been won**.

#### REAPER commands

    Order Action    Purpose
  ------- --------- ----------------------------
        1 `40166`   Jumps playback to Marker 6

#### Expected result

REAPER moves to the audio marker used to **initialise the next station /
play the finale AI voice cue**.

> **Check:** The current function jumps to Marker 6 but does not send
> REAPER's `Play` action (`1007`). Confirm whether playback is expected
> to already be running.
