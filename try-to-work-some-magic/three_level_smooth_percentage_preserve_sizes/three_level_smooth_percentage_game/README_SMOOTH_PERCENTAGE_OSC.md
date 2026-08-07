# Smooth percentage OSC update

Updated files:

- `constants.py`
- `zones.py`
- `osc_sender.py`

## Behaviour

Each active game zone starts at 100% and sends its initial percentage cue.
When shrinking begins, GrandMA is immediately sent the *next* 10% destination
with a 1.17 s fade. When expanding begins, it is sent the next higher 10%
destination with a 0.56 s fade.

This keeps the GrandMA fade moving during the same interval as the Python zone,
rather than starting the fade after Python already crosses the threshold.

Percentage sequences remain:

- Zone A: Sequence 140
- Zone B: Sequence 141
- Zone C: Sequence 142
- Zone D: Sequence 143

Cue mapping: 100%=1, 90%=2, ..., 0%=11.
