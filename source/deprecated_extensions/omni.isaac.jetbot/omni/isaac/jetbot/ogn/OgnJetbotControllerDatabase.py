"""Support for simplified access to data on nodes of type omni.isaac.jetbot.JetbotController

Jetbot Controller
"""

import omni.graph.core as og
import traceback
import sys


class OgnJetbotControllerDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.isaac.jetbot.JetbotController

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.execIn
            inputs.forwardVelocity
            inputs.rotationVelocity
    """

    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}
    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata, Is_Required, DefaultValue
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface(
        [
            ("inputs:execIn", "execution", 0, None, "The input execution", {}, True, None),
            (
                "inputs:forwardVelocity",
                "double",
                0,
                "Forward Velocity",
                "velocity for moving back and forth",
                {og.MetadataKeys.DEFAULT: "0"},
                True,
                0,
            ),
            (
                "inputs:rotationVelocity",
                "double",
                0,
                "Rotation Velocity",
                "velocity for rotating",
                {og.MetadataKeys.DEFAULT: "0"},
                True,
                0,
            ),
        ]
    )

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.execIn = og.Database.ROLE_EXECUTION
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to input attributes"""

        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

        @property
        def execIn(self):
            data_view = og.AttributeValueHelper(self._attributes.execIn)
            return data_view.get()

        @execIn.setter
        def execIn(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.execIn)
            data_view = og.AttributeValueHelper(self._attributes.execIn)
            data_view.set(value)

        @property
        def forwardVelocity(self):
            data_view = og.AttributeValueHelper(self._attributes.forwardVelocity)
            return data_view.get()

        @forwardVelocity.setter
        def forwardVelocity(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.forwardVelocity)
            data_view = og.AttributeValueHelper(self._attributes.forwardVelocity)
            data_view.set(value)

        @property
        def rotationVelocity(self):
            data_view = og.AttributeValueHelper(self._attributes.rotationVelocity)
            return data_view.get()

        @rotationVelocity.setter
        def rotationVelocity(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.rotationVelocity)
            data_view = og.AttributeValueHelper(self._attributes.rotationVelocity)
            data_view.set(value)

    class ValuesForOutputs(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to output attributes"""

        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""

        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = OgnJetbotControllerDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = OgnJetbotControllerDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = OgnJetbotControllerDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "get_node_type", None)
            if callable(get_node_type_function):
                return get_node_type_function()
            return "omni.isaac.jetbot.JetbotController"

        @staticmethod
        def compute(context, node):
            db = OgnJetbotControllerDatabase(node)
            try:
                db.inputs._setting_locked = True
                compute_function = getattr(OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "compute", None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:
                    return compute_function(context, node)
                return OgnJetbotControllerDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f"Assertion raised in compute - {error}\n{stack_trace}", add_context=False)
            finally:
                db.inputs._setting_locked = False
            return False

        @staticmethod
        def initialize(context, node):
            OgnJetbotControllerDatabase._initialize_per_node_data(node)

            # Set any default values the attributes have specified
            db = OgnJetbotControllerDatabase(node)
            db.inputs.forwardVelocity = 0
            db.inputs.rotationVelocity = 0
            initialize_function = getattr(OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "initialize", None)
            if callable(initialize_function):
                initialize_function(context, node)

        @staticmethod
        def release(node):
            release_function = getattr(OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "release", None)
            if callable(release_function):
                release_function(node)
            OgnJetbotControllerDatabase._release_per_node_data(node)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(
                OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "update_node_version", None
            )
            if callable(update_node_version_function):
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "initialize_type", None)
            needs_initializing = True
            if callable(initialize_type_function):
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(og.MetadataKeys.EXTENSION, "omni.isaac.jetbot")
                node_type.set_metadata(og.MetadataKeys.UI_NAME, "Jetbot Controller")
                node_type.set_metadata(og.MetadataKeys.CATEGORIES, "isaacSim")
                node_type.set_metadata(
                    og.MetadataKeys.CATEGORY_DESCRIPTIONS, "isaacSim,robot controller inside Isaac Sim"
                )
                node_type.set_metadata(og.MetadataKeys.DESCRIPTION, "Jetbot Controller")
                node_type.set_metadata(og.MetadataKeys.LANGUAGE, "Python")
                OgnJetbotControllerDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(
                OgnJetbotControllerDatabase.NODE_TYPE_CLASS, "on_connection_type_resolve", None
            )
            if callable(on_connection_type_resolve_function):
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None
    GENERATOR_VERSION = (1, 3, 1)
    TARGET_VERSION = (2, 23, 4)

    @staticmethod
    def register(node_type_class):
        OgnJetbotControllerDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(OgnJetbotControllerDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.isaac.jetbot.JetbotController")
