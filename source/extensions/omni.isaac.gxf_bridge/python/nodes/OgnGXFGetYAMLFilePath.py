# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os

import carb


class OgnGXFGetYAMLFilePath:
    """
    Dynamically generates path to YAML file in app.gxf_bridge.yamlBaseFolder.
    """

    @staticmethod
    def compute(db) -> bool:

        # Test for empty input path
        if len(db.inputs.path) == 0:
            db.log_error("Input path cannot be empty.")
            return False

        # Get YAML base folder setting
        yaml_base_folder = carb.settings.get_settings().get("/exts/omni.isaac.gxf_bridge/yamlBaseFolder")
        yaml_base_folder = carb.tokens.get_tokens_interface().resolve(yaml_base_folder)
        yaml_base_folder = os.path.normpath(yaml_base_folder)
        if not os.path.exists(yaml_base_folder):
            db.log_error(f'exts."omni.isaac.gxf_bridge".yamlBaseFolder does not exist: {yaml_base_folder}')
            return False

        # Construct and test output path
        output_path = os.path.join(yaml_base_folder, db.inputs.path)
        if not os.path.exists(output_path):
            db.log_error(f"Could not find specified YAML file: {output_path}")
            return False

        db.outputs.path = output_path
        return True
