import omni.graph.core as og

keys = og.Controller.Keys
graph_handle, list_of_nodes, _, _ = og.Controller.edit(
    {"graph_path": "/action_graph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [("tick", "omni.graph.action.OnTick"), ("print", "omni.graph.ui_nodes.PrintText")],
        keys.SET_VALUES: [
            ("print.inputs:text", "Hello World"),
            (
                "print.inputs:logLevel",
                "Warning",
            ),  # setting the log level to warning so we can see the printout in terminal
        ],
        keys.CONNECT: [("tick.outputs:tick", "print.inputs:execIn")],
    },
)
