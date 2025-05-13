from abc import ABC, abstractmethod

import omni.usd
import usd.schema.isaac.robot_schema as rs

from ..utils.utils import Singleton


#######################
# Information saved in the templates and registry are meant for continuity for the wizard UI only.
# Robot definition and API/setting implementation are saved to the usd files at each step of the wizard.
#######################
@Singleton
class RobotRegistry:
    """
    A singleton class that keeps track of a single robot instance.
    """

    _instance = None
    _robot = None

    @classmethod
    def register(cls, name, instance):
        if cls._robot is not None:
            raise ValueError("A robot is already registered. Only one robot instance is allowed.")
        cls._robot = instance
        cls._robot_name = name

    @classmethod
    def get(cls):
        return cls._robot

    @classmethod
    def update(cls, instance):
        cls._robot = instance

    @classmethod
    def get_name(cls):
        return cls._robot_name if cls._robot is not None else None

    @classmethod
    def reset(cls):
        cls._robot = None
        cls._robot_name = None
        cls._instance = None


class RobotTemplate(ABC):
    @staticmethod
    def add_property(cls, name, default):
        """
        Dynamically adds a property `name` to `cls`.
        Stores `default` as the initial value, getter returns it, and setter rebinds it on the instance.
        Only supports simple data types like string, list, or dict.
        """
        private = f"_{name}"

        # Store the default value on the class
        setattr(cls, private, default)

        def getter(self):
            return getattr(self, private)

        def setter(self, value):
            setattr(self, private, value)

        doc = f"Dynamically added simple property '{name}' for storing basic data types"

        # Create and install the property
        prop = property(getter, setter, doc=doc)
        setattr(cls, name, prop)

    def __init__(self, name):
        # the properties default to any robot template
        self.add_property(self.__class__, "name", name)
        self.add_property(self.__class__, "parent_prim_path", None)
        self.add_property(self.__class__, "original_robot_path", None)
        self.add_property(self.__class__, "robot_root_folder", None)
        self.add_property(self.__class__, "base_file_path", None)
        self.add_property(self.__class__, "physics_file_path", None)
        self.add_property(self.__class__, "robot_file_path", None)
        self.add_property(self.__class__, "original_stage_path", None)

        # register the robot
        RobotRegistry().register(name, self)


class CustomRobot(RobotTemplate):
    def __init__(self, name):
        super().__init__(name)

        self.add_property(self.__class__, "robot_type", "Custom")
        self.add_property(self.__class__, "links", ["link1", "link2"])
        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"CustomRobot: {self.__dict__}"


class WheeledRobot(RobotTemplate):
    def __init__(self, name):

        super().__init__(name)

        # manipulator specific defaults
        self.add_property(self.__class__, "links", ["chassis", "wheel_left", "wheel_right"])
        self.add_property(self.__class__, "robot_type", "Wheeled Robot")
        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"WheeledRobot: {self.__dict__}"


class Manipulator(RobotTemplate):
    def __init__(self, name):
        super().__init__(name)
        self.add_property(self.__class__, "links", ["link1", "link2", "link3", "tooltip"])
        self.add_property(self.__class__, "robot_type", "Manipulator")
        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"Manipulator: {self.__dict__}"


class Gripper(RobotTemplate):
    def __init__(self, name):
        super().__init__(name)
        self.add_property(self.__class__, "links", ["base_link", "right_finger", "left_finger"])
        self.add_property(self.__class__, "robot_type", "Gripper")

        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"Gripper: {self.__dict__}"


class Humanoid(RobotTemplate):
    def __init__(self, name):
        super().__init__(name)
        self.add_property(self.__class__, "links", ["base_link", "right_leg", "left_leg", "right_arm", "left_arm"])
        self.add_property(self.__class__, "robot_type", "Humanoid")

        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"Humanoid: {self.__dict__}"


class Quadruped(RobotTemplate):
    def __init__(self, name):
        super().__init__(name)
        self.add_property(self.__class__, "links", ["base_link", "right_leg", "left_leg", "right_leg", "left_leg"])
        self.add_property(self.__class__, "robot_type", "Quadruped")

        # register the robot
        RobotRegistry().update(self)

    def __repr__(self):
        return f"Quadruped: {self.__dict__}"
