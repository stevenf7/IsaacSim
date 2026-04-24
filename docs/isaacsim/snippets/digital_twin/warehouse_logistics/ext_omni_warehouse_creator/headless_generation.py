import omni.usd
from omni.warehouse.creator.api import CellData, GridConfig, GridEngine, StageSyncer

cells = {
    (0, 0): CellData(),
    (1, 0): CellData(),
    (1, 1): CellData(),
}

engine = GridEngine(GridConfig(cell_size=10.0))
stage = omni.usd.get_context().get_stage()

placed = StageSyncer().sync(cells, engine, stage)
