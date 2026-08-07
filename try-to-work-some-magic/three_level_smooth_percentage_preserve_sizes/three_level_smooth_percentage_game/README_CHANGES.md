# Three-Level Survival Game

This package is based on the latest uploaded project structure.

## Game flow

- Level 1: protect Zones A and B for 10 seconds.
- Level 2: protect Zones A, B and C for 15 seconds.
- Level 3: protect Zones A, B, C and D for 20 seconds.
- Every required zone starts at maximum radius and shrinks immediately when unoccupied.
- A zone expands/refills while at least one tag is inside.
- If any required zone reaches minimum radius, the game enters the Game Over state.
- After Level 3, the win and finale OSC functions run immediately.
- The final screen remains until Return to Lobby is pressed.

## Tutorial flow

1. The full tutorial zones begin shrinking. Enter one to refill it.
2. Leave the zone and observe it shrinking.
3. Keep both tutorial zones above minimum for five seconds.
4. View the tutorial danger zone, then start the game.

## Testing

Mouse simulation:

```bash
python game.py --simulate --windowed --tags 2
```

Physical tags:

```bash
python game.py --tags 2 --port 5005
```

The receiver still expects:

```text
/distances <tag_id> <d0> <d1> ... <d7>
```

## OSC configuration

Review `osc_sender.py` before show use.

- Level 1 retains the existing Zone A/B Reaper custom actions.
- Level 2 and Level 3 Reaper action maps are intentionally empty because those IDs were not supplied.
- GrandMA level and zone sequence numbers are clearly grouped near the top of the level cue section.
