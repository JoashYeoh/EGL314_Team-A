# ---------------------------------------------------------------------------
# Kalman filter (position + velocity, 2-D)
# ---------------------------------------------------------------------------
class Kalman2D:
    def __init__(self, dt=0.10, q=0.12, r=1.1):
        self.dt = dt
        self.q  = q
        self.r  = r
        self.state = [0.0, 0.0, 0.0, 0.0]
        self.P = [[1.0, 0, 0, 0], [0, 1.0, 0, 0],
                [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
        self.initialized = False

    def predict(self):
        if not self.initialized:
            return
        self.state[0] += self.state[2] * self.dt
        self.state[1] += self.state[3] * self.dt
        for i in range(4):
            self.P[i][i] += self.q

    def update(self, mx, my):
        if not self.initialized:
            self.state = [mx, my, 0.0, 0.0]
            self.initialized = True
            return mx, my
        Kx = self.P[0][0] / (self.P[0][0] + self.r)
        Ky = self.P[1][1] / (self.P[1][1] + self.r)
        old_x, old_y = self.state[0], self.state[1]
        self.state[0] += Kx * (mx - self.state[0])
        self.state[1] += Ky * (my - self.state[1])
        self.state[2] = (self.state[0] - old_x) / self.dt
        self.state[3] = (self.state[1] - old_y) / self.dt
        self.P[0][0] *= (1 - Kx)
        self.P[1][1] *= (1 - Ky)
        return self.state[0], self.state[1]