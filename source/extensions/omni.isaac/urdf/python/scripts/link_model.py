import omni.ui as ui
import omni


# class RobotModel(ui.AbstractValueModel):
#     def __init__(self, robot=None):
#         self.robot = robot
#         self.models = [robot.name]
#         print("Robot Mode", robot)
#         # self.models[1].get_item_value_model(self.models[1].get_item_children()[0]).add_value_changed_fn(
#         #     lambda m, color_model=self.models[1], p=self.props: set_color(color_model, p)
#         # )

#     def get_value(self):
#         return self.props

#     def get_value_model(self, column_id):
#         if column_id < len(self.models):
#             return self.models[column_id]
joint_types = ["Revolute", "Continuous", "prismatic", "fixed", "floating", "planar"]


def colored_block(color, label):
    with ui.ZStack(width=ui.Percent(20)):
        ui.Rectangle(style={"background_color": color})
        model = ui.HStack()
        with model:
            ui.Spacer(width=2)
            ui.Label(label, alignment=ui.Alignment.CENTER, style={"color": 0xFF000000})
            ui.Spacer(width=2)


def create_xyz(labels, values):
    with ui.HStack():
        all_axis = ["X", "Y", "Z"]
        labels = {"X": labels[0], "Y": labels[1], "Z": labels[2]}
        values = {"X": values[0], "Y": values[1], "Z": values[2]}
        colors = {"X": 0xFF5555AA, "Y": 0xFF76A371, "Z": 0xFFA07D4F}
        for axis in all_axis:
            with ui.HStack():
                colored_block(colors[axis], labels[axis])
                ui.FloatField(name="transform", min=-1000000, max=1000000, step=0.01).model.set_value(values[axis])


def create_origin(origin):
    with ui.VStack():
        with ui.Frame(style={"border_color": 0xFF000000, "border_width": 1, "margin": 1}, height=ui.Percent(100)):
            with ui.ZStack(style={}):
                ui.Rectangle(style={"background_color": 0x00FFFFFF})
                with ui.VStack():
                    ui.Label("Origin [m] [rad]")
                    create_xyz([" X ", " Y ", " Z "], [origin.x, origin.y, origin.z])
                    create_xyz([" R ", " P ", " Y "], [origin.roll, origin.pitch, origin.yaw])
                    ui.Spacer(height=10)


def create_geometry(geometry):
    if geometry.type == omni.isaac.urdf._urdf.UrdfGeometryType.GEOMETRY_MESH:
        with ui.VStack():
            ui.Label("Geometry Type: Mesh")
            ui.Label(str(geometry.mesh_file_path))
            ui.Spacer(height=10)
            with ui.HStack():
                create_xyz(["Scale X", "Scale Y ", "Scale Z "], [geometry.scale_x, geometry.scale_y, geometry.scale_z])
    elif geometry.type == omni.isaac.urdf._urdf.UrdfGeometryType.GEOMETRY_BOX:
        with ui.VStack():
            ui.Label("Geometry Type: Box")
            ui.Spacer(height=5)
            with ui.HStack():
                create_xyz(
                    ["Size X [m]", "Size Y [m]", "Size Z [m]"], [geometry.size_x, geometry.size_y, geometry.size_z]
                )
    elif geometry.type == omni.isaac.urdf._urdf.UrdfGeometryType.GEOMETRY_CYLINDER:
        with ui.VStack():
            ui.Label("Geometry Type: Cylinder")
            ui.Spacer(height=5)
            with ui.HStack():
                colored_block(0xFF5555AA, "Radius")
                ui.FloatField().model.set_value(geometry.radius)
                colored_block(0xFFA07D4F, "Length")
                ui.FloatField().model.set_value(geometry.length)
    elif geometry.type == omni.isaac.urdf._urdf.UrdfGeometryType.GEOMETRY_SPHERE:
        with ui.VStack():
            ui.Label("Geometry Type: Sphere")
            ui.Spacer(height=5)
            with ui.HStack():
                colored_block(0xFFA07D4F, "Radius")
                ui.FloatField().model.set_value(geometry.radius)


def create_inertial(inertial):
    with ui.CollapsableFrame("Inertial Properties"):
        with ui.VStack():
            create_origin(inertial.origin)
            with ui.Frame(style={"border_color": 0xFF000000, "border_width": 1, "margin": 1}, height=ui.Percent(100)):
                with ui.ZStack():
                    ui.Rectangle(style={"background_color": 0x00FFFFFF})
                    with ui.VStack():
                        ui.Label("Mass Properties")
                        with ui.HStack():
                            colored_block(0xFFA07D4F, "Mass [kg]")
                            ui.FloatField().model.set_value(inertial.mass)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            create_xyz(
                                ["ixx", "iyy", "izz"],
                                [inertial.inertia.ixx, inertial.inertia.iyy, inertial.inertia.izz],
                            )
                        with ui.HStack():
                            ui.Label("Has Origin")
                            ui.CheckBox(enabled=False).model.set_value(inertial.has_origin)
                        with ui.HStack():
                            ui.Label("Has Mass")
                            ui.CheckBox(enabled=False).model.set_value(inertial.has_mass)
                        with ui.HStack():
                            ui.Label("Has Inertia")
                            ui.CheckBox(enabled=False).model.set_value(inertial.has_inertia)
                        ui.Spacer(height=10)


def create_visual(visual):
    with ui.CollapsableFrame("Visual Mesh Properties"):
        with ui.VStack():
            create_origin(visual.origin)
            create_geometry(visual.geometry)


def create_collision(collision):
    with ui.CollapsableFrame("Collision Mesh Properties"):
        with ui.VStack():
            create_origin(collision.origin)
            create_geometry(collision.geometry)


def create_joint(joint):
    with ui.VStack():
        ui.ComboBox(int(joint.type), *joint_types)
        ui.Spacer(height=10)
        create_origin(joint.origin)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Parent")
            ui.Button(str(joint.parent_link_name), enabled=False)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Child")
            ui.Button(str(joint.child_link_name), enabled=False)
        ui.Spacer(height=10)
        with ui.HStack():
            with ui.VStack():
                create_xyz(["Axis X", "Axis Y", "Axis Z"], [joint.axis.x, joint.axis.y, joint.axis.z])
        ui.Line(height=10)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Limits")
            ui.MultiFloatField(joint.limit.lower, joint.limit.upper)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Max Effort")
            ui.FloatField().model.set_value(joint.limit.effort)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Max Velocity")
            ui.FloatField().model.set_value(joint.limit.velocity)
        ui.Line(height=10)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Drive Type")
            ui.ComboBox(int(joint.drive.target_type), "None", "Position", "Velocity")
        with ui.HStack():
            colored_block(0xFFA07D4F, "Drive Target")
            ui.FloatField(min=-1e12, max=1e12).model.set_value(joint.drive.target)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Damping")
            ui.FloatField(min=0, max=1e12).model.set_value(joint.dynamics.damping)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Stiffness")
            ui.FloatField(min=0, max=1e12).model.set_value(joint.dynamics.stiffness)
        with ui.HStack():
            colored_block(0xFFA07D4F, "Friction")
            ui.FloatField(min=0, max=1e12).model.set_value(joint.dynamics.friction)


def create_material(material):
    with ui.HStack():
        ui.Label(material.name)
        ui.ColorWidget(material.color.r, material.color.g, material.color.b)


class RobotDelegate(ui.AbstractItemDelegate):
    def __init__(self):
        super().__init__()
        self._highlighting_enabled = True
        self._highlighting_text = None
        self.column_names = ["Link Name", "Inertial", "Visual", "Collision"]
        self.num_columns = len(self.column_names)
        self.listView = None

    def build_branch(self, model, item, column_id, level, expanded):
        with ui.HStack(width=16 * (level + 2), height=15):
            ui.Spacer(width=level * 5)
            with ui.ZStack(width=30):
                ui.Spacer()
                if model.can_item_have_children(item):
                    ui.Circle(style={"background_color": 0x00000000, "border_color": 0xFF000000, "border_width": 1})
                    with ui.HStack():
                        ui.Spacer()
                        align = ui.Alignment.V_CENTER
                        ui.Line(name="title", width=6, alignment=align)
                        ui.Spacer()
                    if not expanded:
                        with ui.VStack():
                            ui.Spacer()
                            align = ui.Alignment.H_CENTER
                            ui.Line(name="title", height=6, alignment=align)
                            ui.Spacer()
        # if column_id == 0:
        #     with ui.HStack(width=16 * (level + 2), height=0):
        #         ui.Spacer()
        #         if model.can_item_have_children(item):
        #             # Draw the +/- icon
        #             image_name = "-" if expanded else "+"
        #             ui.Label(image_name)
        #             ui.Spacer(width=4)

    def add_List_view(self, listView):
        self.listView = listView

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per item"""
        with ui.VStack():
            if isinstance(item, RobotSection):
                ui.Label(item.name, height=20)
            elif isinstance(item, RobotLinkItem):
                ui.Label(item.link.name, height=20)
            elif isinstance(item, RobotVisualItem):
                create_visual(item.visual)
            elif isinstance(item, RobotCollisionItem):
                create_collision(item.collision)
            elif isinstance(item, RobotInertialItem):
                create_inertial(item.inertial)
            elif isinstance(item, RobotJointItem):
                ui.Label(item.joint.name, height=20)
            elif isinstance(item, RobotJointDetailsItem):
                create_joint(item.joint)
            elif isinstance(item, RobotMaterialItem):
                create_material(item.material)
            else:
                ui.Label("Other Item")
            ui.Line()

    def build_header(self, column_id):
        ui.Label((self.column_names[column_id]))

    def on_mouse_pressed(self, button, item, expanded, arg):
        """Called when the user press the mouse button on the item"""
        pass


class RobotMaterialItem(ui.AbstractItem):
    def __init__(self, material=None):
        super().__init__()
        self.material = material

    def has_children(self):
        return False


class RobotInertialItem(ui.AbstractItem):
    def __init__(self, inertial=None):
        super().__init__()
        self.inertial = inertial

    def has_children(self):
        return False


class RobotVisualItem(ui.AbstractItem):
    def __init__(self, visual=None):
        super().__init__()
        self.visual = visual

    def has_children(self):
        return False


class RobotCollisionItem(ui.AbstractItem):
    def __init__(self, collision=None):
        super().__init__()
        self.collision = collision
        self.children = None

    def has_children(self):
        return False


class RobotLinkItem(ui.AbstractItem):
    def __init__(self, link=None):
        super().__init__()
        self.link = link
        self.children = (
            [RobotInertialItem(link.inertial)]
            + [RobotVisualItem(visual) for visual in link.visuals]
            + [RobotCollisionItem(collision) for collision in link.collisions]
        )

    def has_children(self):
        return len(self.children)


class RobotJointDetailsItem(ui.AbstractItem):
    def __init__(self, joint=None):
        super().__init__()
        self.joint = joint
        self.children = []

    def has_children(self):
        return False


class RobotJointItem(ui.AbstractItem):
    def __init__(self, joint=None):
        super().__init__()
        self.joint = joint
        self.children = [RobotJointDetailsItem(joint)]

    def has_children(self):
        return len(self.children)


class RobotSection(ui.AbstractItem):
    def __init__(self, name, children=[]):
        super().__init__()
        self.name = name
        self.children = children

    def has_children(self):
        return len(self.children)


class RobotListModel(ui.AbstractItemModel):
    def __init__(self, robot):
        super().__init__()
        self.children = [
            RobotSection("Materials", [RobotMaterialItem(material) for name, material in robot.materials.items()]),
            RobotSection("Links", [RobotLinkItem(link) for name, link in robot.links.items()]),
            RobotSection("Joints", [RobotJointItem(joint) for name, joint in robot.joints.items()]),
        ]

    def get_props(self):
        return [item.get_value() for item in self._children]

    def can_item_have_children(self, item):
        """TOO: NOT FINAL. Just a proof that is doesn't crash"""
        return item.has_children()

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is None:
            return self.children
        else:
            return item.children

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        """
        if item:
            return item.model
