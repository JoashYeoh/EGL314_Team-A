# game_logic/zone_manager.py

from game_logic.zones import Zone
from game_logic.danger_zones import DangerZone


class ZoneManager:

    def __init__(
        self,
        safe_zones: list[Zone],
        danger_zones: list[DangerZone]
    ):

        self.safe_zones = safe_zones
        self.danger_zones = danger_zones

        self.game_over = False


# Occupancy Check
    def zone_is_occupied(
        self,
        zone: Zone,
        tags
    ) -> bool:

        for tag in tags:

            if tag.filt_position is None:
                continue

            if zone.contains_point(
                tag.filt_position
            ):
                return True

        return False


# Find Safe Zones For A Point
    def point_in_safe_zones(
        self,
        point
    ) -> set[int]:

        zones = set()

        for idx, zone in enumerate(
            self.safe_zones
        ):

            if zone.contains_point(point):
                zones.add(idx)

        return zones


# Update Safe Zones
    def update_safe_zones(
        self,
        tags
    ):

        for zone in self.safe_zones:

            if zone.captured:
                continue

            occupied = self.zone_is_occupied(
                zone,
                tags
            )

            zone.update_capture(
                occupied
            )

            if occupied:
                print(
                    f"{zone.label} expanding "
                    f"{zone.radius:.3f}"
                )
                zone.expand()
            else:
                print(
                    f"{zone.label} shrinking "
                    f"{zone.radius:.3f}"
                )
                zone.shrink()


# update Danger Zone 
    def update_danger_zones(
        self,
        tags
    ):

        for zone in self.danger_zones:

            zone.move()

            for tag in tags:

                if tag.filt_position is None:
                    continue

                if zone.contains_point(
                    tag.filt_position
                ):

                    print(
                        f"[GAME OVER] "
                        f"{zone.label}"
                    )

                    self.game_over = True

                    return


# Check All Captured
    def all_zones_captured(
        self
    ) -> bool:

        return all(
            zone.captured
            for zone in self.safe_zones
        )


# Increase Danger Speed
    def increase_danger_speed(
        self,
        multiplier=1.5
    ):

        for zone in self.danger_zones:

            zone.increase_speed(
                multiplier
            )
    

# Reset Safe Zones
    def reset_safe_zones(
        self
    ):

        for zone in self.safe_zones:

            zone.capture_progress = 0

            zone.captured = False


# Update Zones
    def update(self, tags):

        if self.game_over:
            return "GAME_OVER"

        self.update_safe_zones(tags)

        self.update_danger_zones(tags)

        if self.game_over:
            return "GAME_OVER"

        if self.all_zones_captured():
            return "ROUND_COMPLETE"

        return None