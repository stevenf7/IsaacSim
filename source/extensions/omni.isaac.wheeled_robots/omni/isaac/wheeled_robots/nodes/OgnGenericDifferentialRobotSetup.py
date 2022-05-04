# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import numpy as np
import omni.graph.core as og


class OgnGenericDifferentialRobotSetup:
    """
        nodes for bundling robot parameters for any robot to be used by differential and articulation controller
    """

    @staticmethod
    def compute(db) -> bool:
        try:

            wheel_radius = db.inputs.wheelRadius
            wheel_distance = db.inputs.wheelDistance
            left_wheel_name = db.inputs.leftWheelName
            right_wheel_name = db.inputs.rightWheelName
            max_linear_speed = db.inputs.maxLinearSpeed
            max_angular_speed = db.inputs.maxAngularSpeed
            max_wheel_speed = db.inputs.maxWheelSpeed

            ## check input parameters
            if wheel_radius <= 0 or wheel_distance <= 0:
                db.log_warning("invalid wheel radius or distance")
                return False

            # parameters for articulation controller
            art_param_bundle = db.outputs.articulationControllerParams
            art_param_bundle.clear()

            wheel_names_attr = art_param_bundle.insert((og.Type(og.BaseDataType.TOKEN, array_depth=2), "joint_names"))
            wheel_names_attr.value = [left_wheel_name, right_wheel_name]

            # parameters for the differential controller
            diff_param_bundle = db.outputs.differentialControllerParams
            diff_param_bundle.clear()

            wheel_radius_attr = diff_param_bundle.insert(
                (og.Type(og.BaseDataType.DOUBLE, array_depth=1), "wheel_radius")
            )
            wheel_radius_attr.value = wheel_radius

            wheel_distance_attr = diff_param_bundle.insert(
                (og.Type(og.BaseDataType.DOUBLE, array_depth=1), "wheel_distance")
            )
            wheel_distance_attr.value = wheel_distance

            # if there are any limits set for the vehicle or joints
            limits_bundle = db.outputs.vehicleLimits
            limits_bundle.clear()

            if max_linear_speed:
                if max_linear_speed > 0:
                    max_linear_attr = limits_bundle.insert(
                        (og.Type(og.BaseDataType.DOUBLE, array_depth=1), "max_linear_speed")
                    )
                    max_linear_attr.value = max_linear_speed
                else:
                    db.log_warning("invalid max linear speed, no max linear speed used")

            if max_angular_speed:
                if max_angular_speed > 0:
                    max_angular_attr = limits_bundle.insert(
                        (og.Type(og.BaseDataType.DOUBLE, array_depth=1), "max_angular_speed")
                    )
                    max_angular_attr.value = max_angular_speed
                else:
                    db.log_warning("invalid max angular speed, no max angular speed used")

            if max_wheel_speed:
                if max_wheel_speed > 0:
                    max_wheel_attr = limits_bundle.insert(
                        (og.Type(og.BaseDataType.DOUBLE, array_depth=1), "max_wheel_speed")
                    )
                    max_wheel_attr.value = max_wheel_speed
                else:
                    db.log_warning("invalid max wheel speed, no max wheel speed used")

        except Exception as error:
            db.log_error(str(error))
            return False

        return True
