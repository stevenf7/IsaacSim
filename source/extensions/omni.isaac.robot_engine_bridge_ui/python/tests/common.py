import omni


def get_selected_path():
    selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

    if len(selectedPrims) > 0:
        curr_prim = selectedPrims[-1]
    else:
        curr_prim = None
    return curr_prim
