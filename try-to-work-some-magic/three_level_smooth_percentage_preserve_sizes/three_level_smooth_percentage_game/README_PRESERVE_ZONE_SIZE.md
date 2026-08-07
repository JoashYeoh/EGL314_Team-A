# Preserve zone sizes between levels

This build preserves the current radius of zones that carry into the next level.

- Level 1 -> Level 2: Zones A and B keep their current size; Zone C starts at 100%.
- Level 2 -> Level 3: Zones A, B and C keep their current size; Zone D starts at 100%.
- Starting a new game or retrying still resets all zones before Level 1.
- Existing percentage OSC tracking is preserved across the level transition, so GrandMA does not receive a false 100% cue for an existing partially depleted zone.
