import asyncio
import base64
import io
import json
import os
import signal
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import carb
import numpy as np
import omni
import omni.ext
import omni.kit.commands
import omni.ui as ui
import pxr
from omni.isaac.onshape.client import OnshapeClient
from omni.isaac.onshape.scripts.style import UI_STYLES
from PIL import Image, ImageChops
from pxr import Gf, Kind, Sdf, Usd, UsdGeom, UsdLux, UsdShade, Vt
from pxr.Vt import DoubleArray, IntArray, Vec2fArray, Vec3fArray


class ConfigurationItem(ui.AbstractItem):
    def __init__(self, config, param_id, _id):
        super().__init__()
        self.config = config
        self.model = ui.SimpleStringModel(self.config["optionName"])
        self.param_id = param_id
        self.id = _id
        self.unit = None

    def get_value_as_string(self):
        return self.config["optionName"]

    def get_value(self):
        return self.config["option"]

    def get_item_value(self):
        return "{}={}".format(self.param_id, self.config["option"])


class ConfigurationListModel(ui.AbstractItemModel):
    def __init__(self, configs):
        super().__init__()
        self.unit = None
        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(lambda a: self.item_changed(None))
        self.model = ui.SimpleIntModel()
        self.parameter_id = configs["message"]["parameterId"]
        self.node_id = configs["message"]["nodeId"]
        self.name = configs["message"]["parameterName"]
        self.type = configs["typeName"]
        self.QuantityType = "INTEGER"
        if self.type == "BTMConfigurationParameterQuantity":
            self.unit = configs["message"]["rangeAndDefault"]["message"]["units"]
            min_value = configs["message"]["rangeAndDefault"]["message"]["minValue"]
            max_value = configs["message"]["rangeAndDefault"]["message"]["maxValue"]
            self.QuantityType = configs["message"]["quantityType"]
            if self.QuantityType == "INTEGER":
                self.model = ui.SimpleIntModel()
                self.model.set_min(int(min_value))
                self.model.set_max(int(max_value))
                self.model.set_value(int(configs["message"]["rangeAndDefault"]["message"]["defaultValue"]))
            elif self.QuantityType in ["REAL", "ANGLE", "LENGTH"]:
                self.model = ui.SimpleFloatModel()
                self.model.set_min(float(min_value))
                self.model.set_max(float(max_value))
                self.model.set_value(float(configs["message"]["rangeAndDefault"]["message"]["defaultValue"]))

        elif self.type == "BTMConfigurationParameterEnum":
            self._items = {}
            if "options" in configs["message"].keys():
                self._items = {
                    c["message"]["option"]: ConfigurationItem(c["message"], self.parameter_id, i)
                    for i, c in enumerate(configs["message"]["options"])
                }
                # print(self._items[configs["message"]["defaultValue"]].id)
                self.model.set_value(self._items[configs["message"]["defaultValue"]].id)
        elif self.type == "BTMConfigurationParameterString":
            self.model = ui.SimpleStringModel()
            self.model.set_value(configs["message"]["defaultValue"])
        elif self.type == "BTMConfigurationParameterBoolean":
            self.model = ui.SimpleBoolModel()
            self.model.set_value(configs["message"]["defaultValue"])
        self.model.add_value_changed_fn(lambda a: self.item_changed(a))

    def item_changed(self, item=None):
        self._item_changed(None)

    def set_value(self, value):
        if self.type == "BTMConfigurationParameterQuantity":
            if self.QuantityType == "INTEGER":
                self.model.set_value(int(value))
            else:
                self.model.set_value(float(value))
        elif self.type == "BTMConfigurationParameterBoolean":
            self.model.set_value(bool(value))
        elif self.type == "BTMConfigurationParameterString":
            self.model.set_value(value)
        elif self.type == "BTMConfigurationParameterEnum":
            self.model.set_value(value)

    def get_value(self):
        if self.type == "BTMConfigurationParameterQuantity":
            if self.QuantityType == "INTEGER":
                return self.model.get_value_as_int()
            else:
                return self.model.get_value_as_float()
        elif self.type == "BTMConfigurationParameterBoolean":
            return self.model.get_value_as_bool()
        elif self.type == "BTMConfigurationParameterString":
            return self.model.get_value_as_string()
        elif self.type == "BTMConfigurationParameterEnum":
            i = self._current_index.get_value_as_int()
            return self.get_item_children()[i].get_value()

    def get_value_as_string(self):
        if self.type == "BTMConfigurationParameterQuantity":
            if self.QuantityType == "INTEGER":
                return str(self.model.get_value_as_int())
            else:
                return f"{self.model.get_value_as_float():0.4f}"
        elif self.type == "BTMConfigurationParameterBoolean":
            return str(self.model.get_value_as_bool())
        elif self.type == "BTMConfigurationParameterString":
            return self.model.get_value_as_string()
        elif self.type == "BTMConfigurationParameterEnum":
            i = self._current_index.get_value_as_int()
            return self.get_item_children()[i].get_value_as_string()

    def build_widget(self):
        self.frame = ui.Frame(style={"spacing": 2})
        with self.frame:
            with ui.HStack():
                if self.unit:
                    ui.Label("{} ({})".format(self.name, self.unit))
                else:
                    ui.Label("{}".format(self.name))
                if self.type == "BTMConfigurationParameterEnum":
                    ui.ComboBox(self)
                elif self.type == "BTMConfigurationParameterQuantity":
                    if self.QuantityType == "INTEGER":
                        ui.IntSlider(self.model)
                    else:
                        ui.FloatDrag(self.model)
                elif self.type == "BTMConfigurationParameterBoolean":
                    ui.CheckBox(self.model)
                elif self.type == "BTMConfigurationParameterString":
                    ui.StringField(self.model)

    def get_item_value(self):
        extra = ""
        if self.type == "BTMConfigurationParameterQuantity":
            if self.unit:
                extra = "+{}".format(self.unit)
        return "{}={}{}".format(self.parameter_id, self.get_value(), extra)

    def get_item_children(self, parentItem=None):
        if parentItem is None:
            return list(self._items.values())
        return []

    def get_selected(self):
        return self.get_item_children(None)[self.model.get_value_as_int()]

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model
