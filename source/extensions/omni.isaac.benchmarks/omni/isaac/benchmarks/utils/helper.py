from omni.kit.viewport.utility import get_num_viewports
from omni.isaac.core.utils.viewports import get_id_from_index, get_window_from_id


def delete_all_viewports():
    for i in reversed(range(get_num_viewports())):
        window = get_window_from_id(get_id_from_index(i))
        if window:
            window.destroy()
