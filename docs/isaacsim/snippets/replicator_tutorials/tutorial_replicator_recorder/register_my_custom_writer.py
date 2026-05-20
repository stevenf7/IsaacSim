# SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# __doc_snippet_mycustomwriter_begin__
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import AnnotatorRegistry, BackendDispatch, Writer
from omni.replicator.core import functional as F
from omni.replicator.core.scripts.backends import BaseBackend


class MyCustomWriter(Writer):
    """Minimal disk writer for rgb / normals (compatible with ``DiskBackend`` from the Synthetic Data Recorder)."""

    def __init__(
        self,
        rgb: bool = True,
        normals: bool = False,
        output_dir: str | None = None,
        backend: BaseBackend | None = None,
        **kwargs,
    ):
        self.version = "0.0.1"
        self.data_structure = "renderProduct"

        if backend is not None and not isinstance(backend, BaseBackend):
            raise TypeError("`backend` must inherit from `omni.replicator.core.scripts.backends.BaseBackend`.")

        if backend is not None:
            self.backend = backend
        elif output_dir:
            self.backend = BackendDispatch(output_dir=output_dir)
        else:
            raise ValueError("Provide `backend` (for example from the recorder) or `output_dir`.")

        self.annotators = []
        if rgb:
            self.annotators.append(AnnotatorRegistry.get_annotator("rgb"))
        if normals:
            self.annotators.append(AnnotatorRegistry.get_annotator("normals"))
        self._frame_id = 0

    def write(self, data: dict):
        if "renderProducts" in data:
            for rp_name, annotators_data in data["renderProducts"].items():
                rp_prefix = f"{rp_name}/"
                if "rgb" in annotators_data:
                    rgb_entry = annotators_data["rgb"]
                    rgb_arr = rgb_entry["data"] if isinstance(rgb_entry, dict) and "data" in rgb_entry else rgb_entry
                    self.backend.schedule(F.write_image, path=f"{rp_prefix}rgb/rgb_{self._frame_id}.png", data=rgb_arr)
                if "normals" in annotators_data:
                    n_entry = annotators_data["normals"]
                    n_arr = n_entry["data"] if isinstance(n_entry, dict) and "data" in n_entry else n_entry
                    colored = ((n_arr * 0.5 + 0.5) * 255).astype(np.uint8)
                    self.backend.schedule(
                        F.write_image, path=f"{rp_prefix}normals/normals_{self._frame_id}.png", data=colored
                    )
            self._frame_id += 1
            return

        for annotator in list(data.keys()):
            annotator_split = annotator.split("-")
            render_product_path = ""
            multi_render_prod = 0
            if len(annotator_split) > 1:
                multi_render_prod = 1
                render_product_name = annotator_split[-1]
                render_product_path = f"{render_product_name}/"

            if annotator.startswith("rgb"):
                if multi_render_prod:
                    render_product_path += "rgb/"
                filename = f"{render_product_path}rgb_{self._frame_id}.png"
                print(f"[{self._frame_id}] Writing {filename} ..")
                self.backend.schedule(F.write_image, path=filename, data=data[annotator])

            if annotator.startswith("normals"):
                if multi_render_prod:
                    render_product_path += "normals/"
                filename = f"{render_product_path}normals_{self._frame_id}.png"
                print(f"[{self._frame_id}] Writing {filename} ..")
                colored_data = ((data[annotator] * 0.5 + 0.5) * 255).astype(np.uint8)
                self.backend.schedule(F.write_image, path=filename, data=colored_data)

        self._frame_id += 1

    def on_final_frame(self):
        self._frame_id = 0


rep.writers.register_writer(MyCustomWriter)
# __doc_snippet_mycustomwriter_end__

import asyncio
import os

import omni.usd
from isaacsim.replicator.synthetic_recorder.synthetic_recorder import SyntheticRecorder


async def _run_my_custom_writer_async():
    omni.usd.get_context().new_stage()
    rep.orchestrator.set_capture_on_play(False)

    rep.functional.create.xform(name="World")
    rep.functional.create.dome_light(intensity=500, parent="/World", name="DomeLight")
    cube = rep.functional.create.cube(parent="/World", name="Cube")
    rep.functional.modify.semantics(cube, {"class": "my_cube"}, mode="add")

    cam = rep.functional.create.camera(position=(5, 5, 5), look_at=(0, 0, 0), parent="/World", name="Camera")
    cam_path = str(cam.GetPath()) if hasattr(cam, "GetPath") else cam

    out_dir = os.path.join(os.getcwd(), "_out_my_custom_writer")
    print(f"Output directory: {out_dir}")

    recorder = SyntheticRecorder()
    recorder.writer_name = "MyCustomWriter"
    recorder.writer_params = {"rgb": True, "normals": True}
    recorder.backend_type = "DiskBackend"
    recorder.backend_params = {"output_dir": out_dir}
    recorder.rp_data = [(cam_path, 512, 512, "MyRenderProduct")]
    recorder.num_frames = 3
    recorder.verbose = True

    print(f"Starting recorder, output directory: {out_dir}")
    await recorder.start_stop_async()


asyncio.ensure_future(_run_my_custom_writer_async())
