# tracking/kalman.py

class Kalman2D:
    """
    Simple 2D position + velocity Kalman-style filter.

    State vector:
        x
        y
        vx
        vy
    """

    def __init__(
        self,
        dt: float = 0.10,
        process_noise: float = 0.12,
        measurement_noise: float = 1.1,
    ):
        self.dt = dt

        self.q = process_noise
        self.r = measurement_noise

        # State:
        # [x, y, vx, vy]
        self.state = [0.0, 0.0, 0.0, 0.0]

        self.P = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

        self.initialized = False

    def predict(self) -> None:
        """
        Predict next state using velocity.
        """

        if not self.initialized:
            return

        self.state[0] += self.state[2] * self.dt
        self.state[1] += self.state[3] * self.dt

        for i in range(4):
            self.P[i][i] += self.q

    def update(
        self,
        measured_x: float,
        measured_y: float,
    ) -> tuple[float, float]:

        if not self.initialized:

            self.state = [
                measured_x,
                measured_y,
                0.0,
                0.0,
            ]

            self.initialized = True

            return (
                measured_x,
                measured_y,
            )

        kx = self.P[0][0] / (
            self.P[0][0] + self.r
        )

        ky = self.P[1][1] / (
            self.P[1][1] + self.r
        )

        old_x = self.state[0]
        old_y = self.state[1]

        self.state[0] += kx * (
            measured_x - self.state[0]
        )

        self.state[1] += ky * (
            measured_y - self.state[1]
        )

        self.state[2] = (
            self.state[0] - old_x
        ) / self.dt

        self.state[3] = (
            self.state[1] - old_y
        ) / self.dt

        self.P[0][0] *= (1 - kx)
        self.P[1][1] *= (1 - ky)

        return (
            self.state[0],
            self.state[1],
        )

    @property
    def position(self) -> tuple[float, float]:
        return (
            self.state[0],
            self.state[1],
        )

    @property
    def velocity(self) -> tuple[float, float]:
        return (
            self.state[2],
            self.state[3],
        )