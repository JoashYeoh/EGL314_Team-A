from dataclasses import dataclass


ZONE_HIT_TOLERANCE = 0.0


@dataclass
class Zone:

    center: tuple[float, float]
    radius: float

    color: str
    label: str

    active: bool = True

    min_radius: float = 0.10
    shrink_rate: float = 0.0

    capture_progress: float = 0.0
    captured: bool = False

    def contains_point(
        self,
        point: tuple[float, float] | None
    ) -> bool:

        if point is None:
            return False

        px, py = point
        zx, zy = self.center

        r = self.radius + ZONE_HIT_TOLERANCE

        dx = px - zx
        dy = py - zy

        return (dx * dx + dy * dy) <= (r * r)

    def shrink(self):

        if self.radius > self.min_radius:

            self.radius -= self.shrink_rate

            if self.radius < self.min_radius:
                self.radius = self.min_radius

    def update_capture(
        self,
        occupied: bool
    ):

        if self.captured:
            return

        if occupied:

            self.capture_progress += 1

            if self.capture_progress >= 100:

                self.capture_progress = 100
                self.captured = True



# Factory Functions
def create_default_safe_zones():

    return [
        Zone(
            center=(0.25, 0.25),
            radius=0.25,
            min_radius=0.10,
            shrink_rate=0.002,
            color="#00e5ff",
            label="ZONE A",
        ),
        Zone(
            center=(0.25, 0.75),
            radius=0.25,
            min_radius=0.10,
            shrink_rate=0.010,
            color="#ff4081",
            label="ZONE B",
        ),
        Zone(
            center=(0.75, 0.75),
            radius=0.25,
            min_radius=0.10,
            shrink_rate=0.006,
            color="#66ff66",
            label="ZONE C",
        ),
        Zone(
            center=(0.75, 0.25),
            radius=0.25,
            min_radius=0.10,
            shrink_rate=0.006,
            color="#FFE600FF",
            label="ZONE D",
        ),
    ]