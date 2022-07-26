import torch
import json
import numpy as np

import omni.graph.core as og
from omni.replicator.core import AnnotatorRegistry


class PytorchListener:
    def __init__(self):
        self.data = {}

    def write_data(self, data):
        self.data.update(data)

    def get_rgb_data(self):
        if "pytorch_rgb" in self.data:
            images = self.data["pytorch_rgb"]
            images = images[..., :3]
            images = images.permute(0, 3, 1, 2)
            return images
        else:
            return None
