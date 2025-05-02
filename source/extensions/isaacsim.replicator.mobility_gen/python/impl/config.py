import json
from dataclasses import asdict, dataclass
from typing import Literal, Optional, Tuple


@dataclass
class Config:
    scenario_type: str
    robot_type: str
    scene_usd: str

    def to_json(self):
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(data: str):
        data = json.loads(data)
        return Config(scenario_type=data["scenario_type"], robot_type=data["robot_type"], scene_usd=data["scene_usd"])
