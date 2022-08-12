__copyright__ = "Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved."
__license__ = """
NVIDIA CORPORATION and its licensors retain all intellectual property
and proprietary rights in and to this software, related documentation
and any modifications thereto. Any use, reproduction, disclosure or
distribution of this software and related documentation without an express
license agreement from NVIDIA CORPORATION is strictly prohibited.
"""

import io
import json
from typing import Dict, List

import boto3
import numpy as np
from omni.replicator.core import AnnotatorRegistry, BackendDispatch, Writer, WriterRegistry
from omni.syntheticdata import SyntheticData
from PIL import Image

from ..utils import NumpyEncoder

NodeTemplate, NodeConnectionTemplate = SyntheticData.NodeTemplate, SyntheticData.NodeConnectionTemplate

__version__ = "0.0.1"


class DOPEWriter(Writer):
    """Basic writer capable of writing built-in annotator groundtruth.

    Attributes:
        output_dir:
            Output directory string that indicates the directory to save the results. If use_s3 == True, this will be the bucket name.
        semantic_types:
            List of semantic types to consider when filtering annotator data. Default: ["class"]
        image_output_format:
            String that indicates the format of saved RGB images. Default: "png"
        use_s3:
            Boolean value that indicates whether output will be written to s3 bucket. Default: False

    Example:
        >>> import omni.replicator.core as rep
        >>> camera = rep.create.camera()
        >>> render_product = rep.create.render_product(camera, (512, 512))
        >>> writer = rep.WriterRegistry.get("DOPEWriter")
        >>> import carb
        >>> tmp_dir = carb.tokens.get_tokens_interface().resolve("${temp}/rgb")
        >>> writer.initialize(output_dir=tmp_dir, class_name_to_index_map=class_name_to_index_map)
        >>> writer.attach([render_product])
        >>> rep.orchestrator.run()
    """

    def __init__(
        self,
        output_dir: str,
        class_name_to_index_map: Dict,
        semantic_types: List[str] = None,
        image_output_format: str = "png",
        use_s3: bool = False,
        bucket_name: str = "",
        endpoint_url: str = "",
    ):
        self._output_dir = output_dir
        self.backend = BackendDispatch({"paths": {"out_dir": output_dir}})
        self._backend = self.backend  # Kept for backwards compatibility
        self._output_dir = self.backend.output_dir
        self._frame_id = 0
        self._image_output_format = image_output_format
        self.annotators = []
        self.class_to_index = class_name_to_index_map
        self.index_to_class = {i: c for c, i in class_name_to_index_map.items()}

        self.use_s3 = use_s3

        if self.use_s3:
            if len(bucket_name) < 3 or len(bucket_name) > 63:
                raise Exception(
                    "Name of s3 bucket must be between 3 and 63 characters long. Please pass in a new bucket name to --output_folder."
                )
            self.session = boto3.Session()
            self.s3 = self.session.resource("s3", endpoint_url=endpoint_url)
            try:
                self.bucket = self.s3.create_bucket(Bucket=bucket_name)
            except:
                self.bucket = self.s3.Bucket(bucket_name)

        # Specify the semantic types that will be included in output
        if semantic_types is None:
            semantic_types = ["class"]

        # RGB
        self.annotators.append(AnnotatorRegistry.get_annotator("rgb"))

        # Pose Data
        self.annotators.append(AnnotatorRegistry.get_annotator("dope", init_params={"semanticTypes": semantic_types}))

    def write(self, data: dict):
        """Write function called from the OgnWriter node on every frame to process annotator output.

        Args:
            data: A dictionary containing the annotator data for the current frame.
        """
        for annotator in data.keys():
            annotator_split = annotator.split("-")
            render_product_path = ""
            multi_render_prod = 0
            # multiple render_products
            if len(annotator_split) > 1:
                multi_render_prod = 1
                render_product_name = annotator_split[-1]
                render_product_path = f"{render_product_name}/"

            if annotator.startswith("rgb"):
                if multi_render_prod:
                    render_product_path += "rgb/"
                self._write_rgb(data, render_product_path, annotator)

            if annotator.startswith("dope"):
                self._write_dope(data, render_product_path, annotator)

        self._frame_id += 1

    def _write_rgb(self, data: dict, render_product_path: str, annotator: str):
        image_id = "{:06d}".format(self._frame_id)

        if self.use_s3:
            rgb_img = Image.fromarray(data[annotator], "RGBA")
            mem_img = io.BytesIO()
            rgb_img.save(mem_img, format="PNG")

            self.bucket.put_object(Body=mem_img.getvalue(), Key=f"{image_id}.png")

        else:
            file_path = f"{render_product_path}{image_id}.{self._image_output_format}"
            self._backend.write_image(file_path, data[annotator])

    def _write_dope(self, data: dict, render_product_path: str, annotator: str):
        image_id = "{:06d}".format(self._frame_id)

        dope_data = data[annotator]["data"]
        id_to_labels = data[annotator]["info"]["idToLabels"]

        objects = []

        for object in dope_data:
            semanticId = object["semanticId"]

            class_name = id_to_labels[str(semanticId)]["class"]
            class_name = f"0{class_name.lstrip('_')}" if class_name[0] == "_" else class_name

            groundtruth = {
                "class": class_name,
                "visibility": object["visibility"].astype(np.float),
                "location": object["location"].astype(np.float),
                "quaternion_xyzw": object["rotation"].astype(np.float),
                "projected_cuboid": object["projected_cuboid"].astype(np.float),
            }

            objects.append(groundtruth)

        output = {"camera_data": {}, "objects": objects}  # TO-DO: Add camera_data. This is not used for training script

        if self.use_s3:
            self.bucket.put_object(Body=json.dumps(output, indent=2, cls=NumpyEncoder), Key=f"{image_id}.json")
        else:
            file_path = f"{render_product_path}{image_id}.json"
            buf = io.BytesIO()
            buf.write(json.dumps(output, indent=2, cls=NumpyEncoder).encode())
            self._backend.write_blob(file_path, buf.getvalue())


WriterRegistry.register(DOPEWriter)
