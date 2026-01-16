class PalletizingSDGDemo:
    BINS_FOLDER_PATH = "/World/Ur10Table/bins"
    FLIP_HELPER_PATH = "/World/Ur10Table/pallet_holder"
    PALLET_PRIM_MESH_PATH = "/World/Ur10Table/pallet/Xform/Mesh_015"

    def __init__(self):
        # There are 36 bins in total
        self._bin_counter = 0
        self._num_captures = MAX_BINS
        self._bin_flip_frames = DEFAULT_BIN_FLIP_FRAMES
        self._pallet_frames = DEFAULT_PALLET_FRAMES
        self._stage = None
        self._active_bin = None

        # Cleanup in case the user closes the stage
        self._stage_event_sub = None

        # Simulation state flags
        self._in_running_state = False
        self._bin_flip_scenario_done = False

        # Used to pause/resume the simulation
        self._timeline = None

        # Used to actively track the active bins surroundings (e.g., in contact with pallet)
        self._timeline_sub = None
        self._overlap_extent = None

        # SDG
        self._rep_camera = None
        self._output_dir = os.path.join(os.getcwd(), "_out_palletizing_sdg_demo")
