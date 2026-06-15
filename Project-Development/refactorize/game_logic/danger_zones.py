from dataclasses import dataclass


@dataclass
class DangerZone:

    center: tuple[float, float]
    radius: float

    color: str
    label: str

    velocity_x: float
    velocity_y: float

    active: bool = True

    def contains_point(
        self,
        point: tuple[float, float] | None
    ) -> bool:

        if point is None:
            return False

        px, py = point
        zx, zy = self.center

        dx = px - zx
        dy = py - zy

        return (
            dx * dx + dy * dy
        ) <= (
            self.radius * self.radius
        )

    def move(self):

        x, y = self.center

        next_x = x + self.velocity_x
        next_y = y + self.velocity_y

        if next_x - self.radius < 0.0 or next_x + self.radius > 1.0:
            self.velocity_x *= -1

        if next_y - self.radius < 0.0 or next_y + self.radius > 1.0:
            self.velocity_y *= -1

        self.center = (
            x + self.velocity_x,
            y + self.velocity_y
        )

    def increase_speed(
        self,
        multiplier=1.25
    ):

        self.velocity_x *= multiplier
        self.velocity_y *= multiplier



# Factory Functions
def create_default_danger_zones():

    return [

        DangerZone(
            center=(0.5, 0.5),
            radius=0.10,
            color="#ff0000",
            label="DANGER-V",
            velocity_x=0.0,
            velocity_y=0.015,
        ),

        DangerZone(
            center=(0.5, 0.5),
            radius=0.10,
            color="#ff0000",
            label="DANGER-H",
            velocity_x=0.015,
            velocity_y=0.0,
        ),
    ]