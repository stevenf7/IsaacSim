from omni.isaac.cortex.dfb import DfDiagnosticsMonitor
from omni.isaac.examples.cortex.behaviors.franka import (
    block_stacking_behavior,
    peck_decider_network,
    peck_game,
    peck_state_machine,
)
from omni.isaac.examples.cortex.behaviors.franka.simple import simple_decider_network, simple_state_machine


behaviors = {
    "block_stacking_behavior": block_stacking_behavior,
    "peck_decider_network": peck_decider_network,
    "peck_game": peck_game,
    "peck_state_machine": peck_state_machine,
    "simple_decider_network": simple_decider_network,
    "simple_state_machine": simple_state_machine,
}


class ContextStateMonitor(DfDiagnosticsMonitor):
    """
    State monitor to read the context and pass it to the UI.
    For these behaviors, the context has a `diagnostic_message` that contains the text to be displayed, and each
    behavior implements its own monitor to update that.

    """

    def __init__(self, print_dt, diagnostic_fn=None):
        super().__init__(print_dt=print_dt)

    def print_diagnostics(self, context):
        if hasattr(context, "diagnostics_message"):
            print("====================================")
            print(context.diagnostics_message)
