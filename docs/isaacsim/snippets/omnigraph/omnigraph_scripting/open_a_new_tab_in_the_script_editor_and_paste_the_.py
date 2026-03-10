import omni.graph.core as og

keys = og.Controller.Keys
(demand_graph_handle, _, _, _) = og.Controller.edit(
    {
        "graph_path": "/ondemand_graph",
        "evaluator_name": "execution",
        "pipeline_stage": og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND,
    },
    {
        keys.CREATE_NODES: [("tick", "omni.graph.action.OnTick"), ("print", "omni.graph.ui_nodes.PrintText")],
        keys.SET_VALUES: [("print.inputs:text", "On Demand Graph"), ("print.inputs:logLevel", "Warning")],
        keys.CONNECT: [("tick.outputs:tick", "print.inputs:execIn")],
    },
)
