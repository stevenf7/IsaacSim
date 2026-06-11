# Public API for module isaacsim.util.clash_detection:

## Classes

- class ClashDetector
  - def __init__(self, stage: Usd.Stage, searchset_path: str = '', tolerance: float = 0.0, clash_data_layer: bool = True, logging: bool = False)
  - def set_scope(self, searchset_path: str)
  - def get_scope(self) -> str
  - def get_current_query_id(self) -> int
  - def get_query_id_by_query_name(self, query_name: str) -> int
  - def export_to_json(self, json_path_name: str, query_id: int = 0, prim_view: bool = False) -> bool
  - def is_prim_clashing(self, prim: Usd.Prim, query_name: str = '') -> bool
  - def detect_prim_view_clashes(self, prim_view: Prim, prim_view_query_name: str = '') -> list
