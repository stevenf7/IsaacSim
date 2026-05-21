from isaacsim import SimulationApp

# Start the application
simulation_app = SimulationApp({"headless": True})

# Get the utility to enable extensions
from isaacsim.core.utils.extensions import enable_extension

# Enable the incident extension
enable_extension("isaacsim.replicator.incident.core")
enable_extension("isaacsim.storage.native")
simulation_app.update()


# <start-tutorial-snippet>
import carb
import isaacsim.core.utils.prims as prims_utils
import omni.kit.commands
import omni.usd
from isaacsim.replicator.incident.core import get_instance
from isaacsim.replicator.incident.core.extension import IncidentExt
from isaacsim.replicator.incident.core.settings import IncidentSettings
from isaacsim.storage.native import get_assets_root_path
from omni.metropolis.pipeline.triggers import TriggersManager
from pxr import Gf, UsdLux

SEED = 12345
SKY_TEXTURE = "/NVIDIA/Assets/Skies/Clear/evening_road_01_4k.hdr"

stage = omni.usd.get_context().get_stage()
assets_root = get_assets_root_path()

# Skybox backdrop via dome light HDRI (skipped if assets are unreachable)
if assets_root is not None:
    dome = UsdLux.DomeLight.Define(stage, "/World/SkyDome")
    dome.GetIntensityAttr().Set(1000.0)
    dome.GetTextureFileAttr().Set(assets_root + SKY_TEXTURE)
    dome.GetTextureFormatAttr().Set(UsdLux.Tokens.latlong)
else:
    carb.log_warn("Could not find Isaac Sim assets folder; skipping sky backdrop")

# Get the incident manager and create pyro event manager
incident_manager = get_instance().get_incident_manager()

# Create a TimeTrigger and add callback
time_trigger = TriggersManager.get_instance().create_trigger_by_dict({"trigger": {"type": "time", "time": 1.0}})
time_trigger.add_callback(lambda trigger: carb.log_info("Trigger fired!"))

# Create 3 cubes with incident tags
# Cube 1: Flammable item (for fire events)
prims_utils.create_prim(
    prim_path="/World/FlammableCube",
    prim_type="Cube",
    position=[-1.0, 0.0, 0.5],
    attributes={"size": 0.5},
)

omni.kit.commands.execute("ApplyFlammableItemTagCommand", prims="/World/FlammableCube", flammable_item_type="Box")
# Create randomly selected fire event
pyro_event_manager = incident_manager.create_pyro_event_manager(
    data_path=IncidentExt.data_path, seed=SEED, report=incident_manager.get_incident_report()
)

pyro_event_manager.generate_pyro_event(
    name="fire event",
    selected_flammable_item_prim_path=IncidentSettings.RANDOM_FLAMMABLE_ITEM,
    pyro_nearby_radius=0.0,
    trigger=time_trigger,
)

# Cube 2: Loose item (for topple events)
prims_utils.create_prim(
    prim_path="/World/LooseCube",
    prim_type="Cube",
    position=[0.0, 0.0, 0.5],
    attributes={"size": 0.5},
)

omni.kit.commands.execute("ApplyLooseItemTagCommand", prims="/World/LooseCube", loose_item_type="RandomDir")
# Create randomly selected topple event
topple_event_manager = incident_manager.create_topple_event_manager(
    seed=SEED, report=incident_manager.get_incident_report()
)
topple_event_manager.generate_topple_event(
    name="topple event",
    selected_loose_item=IncidentSettings.RANDOM_LOOSE_ITEM,
    topple_nearby_radius=0.01,
    trigger=time_trigger,
)

# Cube 3: Leakable item (for spill events)
prims_utils.create_prim(
    prim_path="/World/LeakableCube",
    prim_type="Cube",
    position=[1.0, 0.0, 0.5],
    attributes={"size": 0.5},
)
omni.kit.commands.execute("ApplyLeakableItemTagCommand", prims="/World/LeakableCube", leakable_item_type="Item")

# Create a plane for the floor and tag it as a spillable area
omni.kit.commands.execute(
    "AddGroundPlaneCommand",
    stage=stage,
    planePath="/World/Floor",
    axis="Z",  # Normal along Z-axis for x-y plane (ground)
    size=25.0,
    position=Gf.Vec3f(0.0, 0.0, 0.0),
    color=Gf.Vec3f(0.5, 0.5, 0.5),
)
omni.kit.commands.execute("ApplySpillableAreaTagCommand", prims="/World/Floor", spillable_area_type="Floor")
# Create randomly selected spill event
spill_event_manager = incident_manager.create_spill_event_manager(
    seed=SEED, report=incident_manager.get_incident_report()
)
spill_event_manager.generate_spill_event(
    name="spill event",
    selected_spillable_item=IncidentSettings.RANDOM_LEAKABLE_ITEM,
    target_size=1.0,
    leak_duration=1.0,
    trigger=time_trigger,
)


# <end-tutorial-snippet>

simulation_app.close()
