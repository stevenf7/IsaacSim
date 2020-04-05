import carb
import carb.input
import omni.kit.editor
import omni.kit.ui
import omni.kit.commands
import omni.isaac
import random
import json
from enum import Enum
import sys
import math

from pxr import Usd, UsdGeom, Sdf, Gf, Tf
from ..bindings import _ros_bridge

EXTENSION_NAME = "Isaac Ros Bridge"


class RosEvent:
    def __init__(
        self,
        rosbridge_interface,
        parent_layout,
        node_handle,
        prim_list,
        topic,
        queue_size,
        MessageType,
        EventType,
        event_handle=-1,
    ):
        print("Python: Adding Ros Event")
        self._ros = rosbridge_interface
        self.node_handle = node_handle
        if event_handle == -1:
            self.event_handle = self._ros.add_ros_event(
                node_handle, prim_list, topic, queue_size, MessageType, EventType
            )
        else:
            self.event_handle = event_handle

        self.type = EventType
        self.paths = prim_list
        self.message = MessageType
        self.parent_layout = parent_layout

        self.layout = self.parent_layout.add_child(omni.kit.ui.RowColumnLayout(7, False))
        self.layout.add_child(omni.kit.ui.Label(""))
        self.layout.add_child(omni.kit.ui.Label(""))
        self.layout.add_child(omni.kit.ui.Label("\n".join(prim_list)))
        self.layout.add_child(omni.kit.ui.Label(topic))
        self.layout.add_child(omni.kit.ui.Label(str(MessageType)))
        self.layout.add_child(omni.kit.ui.Label(str(EventType)))
        self.delete_btn = self.layout.add_child(omni.kit.ui.Button("Delete"))
        self.delete_btn.set_clicked_fn(self._on_delete_event)

    def __del__(self):
        print("Python: deleteRosEvent")

    def _on_delete_event(self, widget):
        self._delete()

    def _delete(self):
        self._ros.delete_ros_event(self.node_handle, self.event_handle)
        self.layout.clear()
        self.parent_layout.remove_child(self.layout)


class RosNode:
    def __init__(self, rosbridge_interface, parent_layout, _usd_context, node_handle=-1):
        print("Python: Adding Ros Node")
        self._ros = rosbridge_interface
        if node_handle == -1:
            self.node_handle = self._ros.add_ros_node()
        else:
            self.node_handle = node_handle

        self.events = []
        self._usd_context = _usd_context
        self.parent_layout = parent_layout
        # Create node layout
        self.layout = parent_layout.add_child(omni.kit.ui.CollapsingFrame("Ros Node " + str(self.node_handle), True))
        self.del_node_btn = self.layout.add_child(omni.kit.ui.Button("Delete Node"))
        self.del_node_btn.width = -1
        self.del_node_btn.set_clicked_fn(self._on_delete_node)
        self.seperator = self.parent_layout.add_child(omni.kit.ui.Separator())
        self._create_event_menu()

    def _on_delete_node(self, widget):
        self._delete()

    def _delete(self):
        self._ros.delete_ros_node(self.node_handle)
        self.layout.clear()
        self.parent_layout.remove_child(self.layout)
        self.parent_layout.remove_child(self.seperator)

    def _create_event_menu(self):
        self.row_layout = self.layout.add_child(omni.kit.ui.RowColumnLayout(7, True))
        self.prim_btn = self.row_layout.add_child(omni.kit.ui.Button("Pick Selected"))
        self.prim_btn.set_clicked_fn(self._on_prim_select)

        self.prim_widget = self.row_layout.add_child(omni.kit.ui.ListBox("", True, -1))
        self.prim_widget.width = -1

        self.clear_btn = self.row_layout.add_child(omni.kit.ui.Button("X"))
        self.clear_btn.set_clicked_fn(self._on_pick_list_clear)

        self.topic_widget = self.row_layout.add_child(omni.kit.ui.TextBox("topic_name"))

        self.messageTypeBox = self.row_layout.add_child(omni.kit.ui.ComboBox(""))
        self.messageTypeBox.add_item("NONE")
        self.messageTypeBox.add_item("EMPTY")
        self.messageTypeBox.add_item("POSE")
        self.messageTypeBox.add_item("JOINT_STATE")
        self.messageTypeBox.add_item("TF")
        self.messageTypeBox.add_item("IMAGE")
        self.messageTypeBox.add_item("CAMERA_INFO")
        self.messageTypeBox.add_item("BOUNDING_BOX")
        self.messageTypeBox.add_item("RANGE_SCAN")
        self.messageTypeBox.selected_index = 0

        self.eventTypeBox = self.row_layout.add_child(omni.kit.ui.ComboBox(""))
        self.eventTypeBox.add_item("NONE")
        self.eventTypeBox.add_item("PUBLISH")
        self.eventTypeBox.add_item("SUBSCRIBE")
        self.eventTypeBox.add_item("SERVICE")
        self.eventTypeBox.add_item("PERIODIC")
        self.eventTypeBox.selected_index = 0
        self.add_btn = self.row_layout.add_child(omni.kit.ui.Button("Add Event"))
        self.add_btn.set_clicked_fn(self._on_add_event)

    def _on_add_event(self, widget):
        prim_list = [self.prim_widget.get_item_at(index) for index in range(self.prim_widget.get_item_count())]
        # TODO: in theory we need to remove events that are deleted
        self.events.append(
            RosEvent(
                self._ros,
                self.layout,
                self.node_handle,
                prim_list,
                self.topic_widget.value,
                100,
                _ros_bridge.MessageType(self.messageTypeBox.selected_index),
                _ros_bridge.EventType(self.eventTypeBox.selected_index),
            )
        )
        self.prim_widget.clear_items()

    def _on_prim_select(self, widget):
        prim_list = self._usd_context.get_selection().get_selected_prim_paths()
        for prim in prim_list:
            self.prim_widget.add_item(prim)

    def _on_pick_list_clear(self, widget):
        self.prim_widget.clear_items()

    def _add_json_events(self, json_events):
        for j in range(len(json_events)):
            json_event = json_events[j]
            prim_list = json_event["paths"]
            self.topic_widget.value = json_event["topic"]
            queue_size = json_event["queue_size"]
            self.events.append(
                RosEvent(
                    self._ros,
                    self.layout,
                    self.node_handle,
                    prim_list,
                    self.topic_widget.value,
                    queue_size,
                    _ros_bridge.message_from_string(json_event["message"]),
                    _ros_bridge.event_from_string(json_event["event"]),
                    j,
                )
            )


class RosBridgeMenu:
    def __init__(self, rosbridge_interface):
        self._usd_context = omni.usd.get_context()
        self._input = carb.input.acquire_input_interface()
        self._isaac = rosbridge_interface
        self._nodes = []
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 300)
        self.stage = self._usd_context.get_stage()
        header = self._window.layout.add_child(omni.kit.ui.RowColumnLayout(3, True))
        header.set_column_width(0, omni.kit.ui.Percent(60))
        header.set_column_width(1, omni.kit.ui.Percent(20))
        header.set_column_width(1, omni.kit.ui.Percent(20))

        create_btn = header.add_child(omni.kit.ui.Button("Create ROS Node"))
        create_btn.set_clicked_fn(self._on_create_node)
        create_btn.width = -1

        config_btn = header.add_child(omni.kit.ui.Button("JSON Config"))
        config_btn.set_clicked_fn(self._on_view_config)
        config_btn.width = -1

        self.publish_clock = header.add_child(omni.kit.ui.CheckBox("Publish clock"))
        self.publish_clock.value = True
        self.publish_clock.set_on_changed_fn(self._toggle_clock)

        self.node_column = self._window.layout.add_child(omni.kit.ui.ColumnLayout())

        self._stage_event_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event
        )

    def _on_stage_event(self, event):
        self.stage = self._usd_context.get_stage()
        # print("_on_stage_event", event.type)
        if event.type == int(omni.usd.StageEventType.OPENED):
            for node in self._nodes:
                node._delete()
            self._nodes = []
            # print("STAGE OPENED", event.type)
            if self.stage.GetRootLayer().customLayerData:
                print("Loading USD from JSON")
                if "IsaacRosBridgeJSON" in self.stage.GetRootLayer().customLayerData:
                    json_str = self.stage.GetRootLayer().customLayerData["IsaacRosBridgeJSON"]
                    self._isaac.parse_json_string(json_str)
                    self._create_ui_from_json(self._isaac.get_json_string())
            else:
                print("Default JSON not found in USD")

    def _toggle_clock(self, state):
        print("set_clock_state ", state)
        self._isaac.set_clock_state(state)

    def _on_update(self, dt):
        print("update")

    def _on_view_config(self, widget):
        self._popup = None
        self._popup = omni.kit.ui.Popup("JSON input/output", modal=True, width=500, height=500)
        jsonstr = self._isaac.get_json_string()
        sublayout = self._popup.layout.add_child(omni.kit.ui.ColumnLayout())
        sublayout.add_child(omni.kit.ui.Label("Current JSON: (right click to copy)"))
        sublayout.add_child(omni.kit.ui.Separator())
        scrolling_frame = sublayout.add_child(omni.kit.ui.ScrollingFrame("", 500, 500))
        json_out_widget = scrolling_frame.add_child(
            omni.kit.ui.Label(jsonstr, useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )
        json_out_widget.width = -1
        sublayout.add_child(omni.kit.ui.Separator())
        sublayout.add_child(omni.kit.ui.Label("Path To Json (local paths only, omni:/ not supported yet)"))
        json_in_widget = sublayout.add_child(omni.kit.ui.TextBox(""))
        json_in_widget.width = -1
        json_in_widget.readonly = False

        footer = sublayout.add_child(omni.kit.ui.RowColumnLayout(2, True))
        load_btn = footer.add_child(omni.kit.ui.Button("Load"))
        load_btn.width = -1
        close_btn = footer.add_child(omni.kit.ui.Button("Close"))
        close_btn.width = -1

        def _on_load_json(widget, self=self, json_out=json_out_widget, json_in=json_in_widget):
            with open(json_in.text, "r") as file:
                self._isaac.parse_json_string(file.read())
                json_out.text = self._isaac.get_json_string()
                self._create_ui_from_json(json_out.text)

        def _on_close_popup(widget, popup=self._popup):
            popup.hide()
            popup = None

        load_btn.set_clicked_fn(_on_load_json)
        close_btn.set_clicked_fn(_on_close_popup)

    def _create_ui_from_json(self, json_str):
        node_event_dict = json.loads(json_str)
        if "clock" in node_event_dict:
            self.publish_clock.value = node_event_dict["clock"]
        for i in range(len(node_event_dict["nodes"])):
            node = node_event_dict["nodes"][i]
            ros_node = RosNode(self._isaac, self.node_column, self._usd_context, i)
            self._nodes.append(ros_node)
            ros_node._add_json_events(node)

    def _on_create_node(self, widget):
        # TODO: in theory we need to remove nodes that are deleted
        self._nodes.append(RosNode(self._isaac, self.node_column, self._usd_context))

    def _on_menu_click(self, menu, value):
        stage = self._usd_context.get_stage()
        defaultPrimPath = str(stage.GetDefaultPrim().GetPath())
        defaultPrimPath = ""
        prims = self._usd_context.get_selection().get_selected_prim_paths()
        upAxis = UsdGeom.GetStageUpAxis(stage)

    def shutdown(self):
        self._window.set_update_fn(None)
        del self._window
        self.menus = []
