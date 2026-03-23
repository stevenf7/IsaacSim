import numpy as np


class RobotScenario:
    """Encapsulates a Jetbot + Franka + Cube scenario with randomization."""

    def __init__(self, name: str, offset: np.ndarray = np.array([0.0, 0.0, 0.0]), randomize: bool = False):
        self.name = name
        self.offset = offset
        self.randomize = randomize
        self.state = 0
        self.step_counter = 0
        self.pick_phase = 0

        # Randomize cube goal position if enabled
        if randomize:
            random_x = np.random.uniform(1.1, 1.4)
            self.cube_goal = np.array([random_x, 0.0, 0.0]) + offset
        else:
            self.cube_goal = np.array([1.2, 0.0, 0.0]) + offset

        # ... rest of the class remains the same
