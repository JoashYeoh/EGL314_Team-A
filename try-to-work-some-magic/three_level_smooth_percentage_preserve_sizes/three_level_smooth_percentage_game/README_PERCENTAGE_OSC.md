# Percentage-based zone OSC update

Replace these files in the three-level survival project:

- `constants.py`
- `zones.py`
- `osc_sender.py`

## GrandMA mapping

- Zone A: Sequence 140
- Zone B: Sequence 141
- Zone C: Sequence 142
- Zone D: Sequence 143

Cue mapping:

- 100%: Cue 1
- 90%: Cue 2
- 80%: Cue 3
- 70%: Cue 4
- 60%: Cue 5
- 50%: Cue 6
- 40%: Cue 7
- 30%: Cue 8
- 20%: Cue 9
- 10%: Cue 10
- 0%: Cue 11

The cue is sent only when a threshold is crossed. It works while shrinking and while expanding. Each active zone sends its initial 100% cue at the start of every level.

Edit `ZONE_PERCENTAGE_SEQUENCES` in `osc_sender.py` if your GrandMA sequence numbers differ.
