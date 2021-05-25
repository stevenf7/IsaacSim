import omni
import textwrap


def create_graphviz_tree(self, tree_item, robot, graph):
    if not tree_item:
        return
    if isinstance(tree_item, list):
        for item in tree_item:
            joint = robot.joints[item["A_joint"]]
            color = "red"
            if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_REVOLUTE:
                color = "green"
            if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_PRISMATIC:
                color = "blue"
            if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_CONTINUOUS:
                color = "orange"
            graph.node(item["B_link"], textwrap.fill(item["B_link"], 20), style="filled", shape="rect")
            graph.edge(
                item["A_link"], item["B_link"], xlabel=textwrap.fill(item["A_joint"], 20), color=color, penwidth=str(5)
            )
            create_graphviz_tree(item["B_node"], robot, graph)
    else:
        graph.node("Root", style="filled", shape="doublecircle")
        graph.node(tree_item["B_link"], style="filled", shape="rect")
        graph.edge("Root", tree_item["B_link"], tree_item["A_joint"], color="red", penwidth=str(5))
        create_graphviz_tree(tree_item["B_node"], robot, graph)


def generate_robot_image(self, robot, vertical=True):
    from graphviz import Graph

    im = None
    robot_tree = urdf_interface.get_kinematic_chain(robot)

    robot_graph = Graph("robot_graph", strict=True, engine="dot")
    robot_graph.attr(splines="ortho")
    if vertical:
        robot_graph.attr(rankdir="TB")
    else:
        robot_graph.attr(rankdir="LR")

    robot_graph.attr(packMode="node")
    with robot_graph.subgraph(name="cluster_legend") as legend_graph:

        legend_graph.attr(label="Legend")
        legend_graph.node("legend_fixed", "Fixed", color="red", shape="rect", margin=".05", height="0", penwidth=str(3))
        legend_graph.node(
            "legend_revolute", "Revolute", color="green", shape="rect", margin="0.05", height="0", penwidth=str(3)
        )
        legend_graph.node("legend_empty", "", style="invis", margin="0", width="0", height="0")
        legend_graph.node(
            "legend_prismatic", "Prismatic", color="blue", shape="rect", margin="0.05", height="0", penwidth=str(3)
        )
        legend_graph.node(
            "legend_continuous", "Continuous", color="orange", shape="rect", margin="0.05", height="0", penwidth=str(3)
        )

    try:
        from PIL import Image
        import io

        create_graphviz_tree(robot_tree, robot, robot_graph)
        robot_graph.edge("legend_empty", "Root", ltail="cluster_legend", style="invis")
        buffer = io.BytesIO(robot_graph.pipe(format="png"))
        buffer.seek(0)
        im = Image.open(buffer)
        im.thumbnail([min(im.size[0], 3000), min(im.size[1], 3000)], Image.ANTIALIAS)
        # im.show()
        im = im.convert("RGBA")  # needed sometimes as image can change to RGB without this
    except Exception as e:
        im = None
        print("Error: ", e, ", graph generation disabled")
    return im


def modal_graph():
    rgb_byte_provider = None
    rgb_image_provider = None
    robot_graph_im = None
    # if robot_graph_im is not None:
    #     with ui.VStack():
    #         with ui.ScrollingFrame():
    #             rgb_byte_provider = omni.ui.ByteImageProvider()
    #             rgb_image_provider = omni.ui.ImageWithProvider(
    #                 rgb_byte_provider,
    #                 width=robot_graph_im.size[0],
    #                 height=robot_graph_im.size[1],
    #                 fill_policy=ui.IwpFillPolicy.IWP_PRESERVE_ASPECT_FIT,
    #             )

    #             rgb_byte_provider.set_bytes_data(
    #                 list(robot_graph_im.tobytes("raw", "RGBA")),
    #                 [int(robot_graph_im.size[0]), int(robot_graph_im.size[1])],
    #             )

    # def scale_image(scale):
    #     rgb_image_provider.width = ui.Length(scale[0])
    #     rgb_image_provider.height = ui.Length(scale[1])

    # def update_image(vertical=True):
    #     robot_graph_im = generate_robot_image(robot, vertical=vertical)
    #     # if im is not None:
    #     rgb_byte_provider.set_bytes_data(
    #         list(robot_graph_im.tobytes("raw", "RGBA")),
    #         [int(robot_graph_im.size[0]), int(robot_graph_im.size[1])],
    #     )
    #     scale_image([int(robot_graph_im.size[0]), int(robot_graph_im.size[1])])

    # with ui.HStack(height=0):
    #     ui.Label("Scale: ", width=0)
    #     model = ui.FloatDrag(min=0.1, height=0).model
    #     model.set_value(1.0)
    #     model.add_value_changed_fn(
    #         lambda m: (
    #             scale_image(
    #                 (
    #                     int(robot_graph_im.size[0] * m.get_value_as_float()),
    #                     int(robot_graph_im.size[1] * m.get_value_as_float()),
    #                 )
    #             )
    #         )
    #     )
    # with ui.HStack(height=0):
    #     ui.Label("Layout Orientation: ", width=0)
    #     model = ui.ComboBox(1, "Horizontal", "Vertical").model
    #     model.add_item_changed_fn(lambda m, i: (update_image(m.get_item_value_model().as_int)))
