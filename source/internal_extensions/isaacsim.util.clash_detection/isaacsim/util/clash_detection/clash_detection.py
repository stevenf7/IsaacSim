# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Clash detection engine for identifying overlapping 3D meshes."""

from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from isaacsim.core.experimental.prims import Prim

import carb
import omni.client
import yaml  # type: ignore[import-untyped]
from omni.physxclashdetectioncore.clash_data import ClashData
from omni.physxclashdetectioncore.clash_data_serializer_sqlite import ClashDataSerializerSqlite
from omni.physxclashdetectioncore.clash_detect import ClashDetection
from omni.physxclashdetectioncore.clash_detect_export import ExportColumnDef, export_to_json
from omni.physxclashdetectioncore.clash_detect_settings import SettingId
from omni.physxclashdetectioncore.clash_query import ClashQuery
from omni.physxclashdetectioncore.utils import OptimizedProgressUpdate
from pxr import Usd, UsdUtils


class ClashDetector:
    """Perform clash detection on 3D meshes.

    It supports checking Prims and Prim Views. Option to export clash detection results
    to JSON format for further analysis.

    Args:
        stage: Usd stage to be processed.
        searchset_path: Absolute prim path to define the scope of the clash detection search.
            Defaults to full current scene.
        tolerance: Tolerance distance for overlap queries. Use zero for hard clashes, non-zero
            for soft (clearance) clashes. Defaults to 0.0.
        clash_data_layer: If True, saves clash detection info to data layer to support exporting
            results to JSON for further analysis. Defaults to True.
        logging: If True, logs info & perf results to console. Defaults to False.

    """

    def __init__(
        self,
        stage: Usd.Stage,
        searchset_path: str = "",
        tolerance: float = 0.0,
        clash_data_layer: bool = True,
        logging: bool = False,
    ) -> None:
        """Initialize the clash detector.

        Args:
            stage: The USD stage to perform clash detection on.
            searchset_path: Path to the searchset prim defining detection scope.
            tolerance: Distance tolerance for overlap detection.
            clash_data_layer: If True, write clash results to a USD data layer.
            logging: If True, log info and performance results to console.

        """
        self._stage = stage
        UsdUtils.StageCache.Get().Insert(self._stage)
        self._object_b_path = searchset_path
        self._tolerance = tolerance
        self._clash_data_layer = clash_data_layer
        self._logging = logging
        self._num_overlaps = 0  # number of overlaps found in current clash detection query

        self._query = ClashQuery(
            query_name="",
            object_a_path="",
            object_b_path="",
            clash_detect_settings={
                SettingId.SETTING_LOGGING.name: self._logging is True,
                SettingId.SETTING_TOLERANCE.name: float(self._tolerance),
                SettingId.SETTING_DYNAMIC.name: False,
                SettingId.SETTING_DYNAMIC_START_TIME.name: float(0.0),
                SettingId.SETTING_DYNAMIC_END_TIME.name: float(0.0),
            },
            comment="",
        )
        self._prim_queries: dict[str, int] = {}

        if self._clash_data_layer:
            self._clash_data = ClashData(ClashDataSerializerSqlite())
            self._clash_data.open(UsdUtils.StageCache.Get().GetId(self._stage).ToLongInt(), True)

        self._is_prim_view = False
        self._prim_view_counter = 0
        self._prim_view_query_name = ""
        self._clashing_view_prims: list[Any] = []
        self._prim_view_queries: dict[str, dict[str, Any]] = {}

    def set_scope(self, searchset_path: str):
        """Set the searchset defining the scope of the clash detection.

        Args:
            searchset_path: Absolute prim path to define the scope of the clash detection search.

        """
        self._object_b_path = searchset_path

    def get_scope(self):
        """Get the current searchset used for clash detection.

        Returns:
            searchset_path (str): The current searchset used for clash detection.

        """
        return self._object_b_path

    def get_current_query_id(self):
        """Get the query ID of the most recent clash detection run.

        Returns:
            query.identifier (int): The unique identifier of the clash detection query.

        """
        if self._is_prim_view:
            return self._prim_view_counter
        else:
            return self._query.identifier

    def get_query_id_by_query_name(self, query_name: str) -> int:
        """Get the query ID associated with any named query from completed clash detection runs.

        Args:
            query_name: Unique query name assigned to a clash detection run.

        Returns:
            The unique identifier associated with the given query name.

        """
        if not query_name:
            carb.log_warn("No query name provided. Returning invalid query id.")
            return 0
        try:
            return self._prim_queries[str(query_name)]
        except:
            try:
                return self._prim_view_queries[str(query_name)]["prim_view_id"]
            except:
                carb.log_warn(f"Query name {query_name} not found. Returning invalid query id.")
                return 0

    def export_to_json(self, json_path_name: str, query_id: int = 0, prim_view: bool = False) -> bool:
        """Export detailed clash detection data to JSON format.

        Args:
            json_path_name: Absolute file path to export data.
            query_id: Unique query ID of clash detection results to export. Defaults to most recent
                clash detection run.
            prim_view: If True, export clash info for all clashing prims in the prim view.
                Defaults to False.

        Returns:
            True on success, False otherwise.

        """
        if not self._clash_data_layer:
            carb.log_warn("No clash data layer created. JSON export failed.")
            return False

        if query_id < 1:
            if prim_view:
                view_name = self._prim_view_query_name
            else:
                query_id = self._query.identifier
        else:
            if prim_view:
                for key, value in self._prim_view_queries.items():
                    if value["prim_view_id"] == query_id:
                        view_name = key
                if not view_name:
                    carb.log_warn(f"Prim view query ID {query_id} not found. JSON export failed.")
            else:
                query_id = query_id

        column_defs = [
            ExportColumnDef(0, "Clash ID"),
            ExportColumnDef(1, "Tolerance"),
            ExportColumnDef(2, "Overlapping Tris", True),
            ExportColumnDef(5, "Clashing Frames", True),
            ExportColumnDef(6, "Object A"),
            ExportColumnDef(7, "Object B"),
        ]

        if prim_view and self._prim_view_counter != 0:
            query_group = self._prim_view_queries[view_name]["query_ids"]
            overlaps = {}
            for query_id in query_group:
                temp_overlaps = self._clash_data.find_all_overlaps_by_query_id(query_id, False)
                if temp_overlaps:
                    overlaps.update(temp_overlaps)
        else:
            overlaps = self._clash_data.find_all_overlaps_by_query_id(query_id, False)

        rows = [
            [
                o.overlap_id,
                f"{o.tolerance:.3f}",
                str(o.overlap_tris),
                str(o.num_records),
                o.object_a_path,
                o.object_b_path,
            ]
            for o in overlaps.values()
        ]

        carb.log_info(f"Exporting to JSON file '{json_path_name}'...")
        json_bytes = export_to_json(column_defs, rows)
        if not json_bytes or len(json_bytes) == 0:
            carb.log_warn("JSON export failed.")
            return False
        if omni.client.write_file(json_path_name, json_bytes) != omni.client.Result.OK:
            carb.log_warn(f"Failed writing JSON file to '{json_path_name}'.")
            return False
        json_bytes = None

        return True

    def is_prim_clashing(self, prim: Usd.Prim, query_name: str = "") -> bool:
        """Check if the input prim is clashing with any mesh in the searchset.

        Args:
            prim: The prim to be checked for clashes.
            query_name: Unique query name for this clash detection run. Required if not storing
                query IDs and need to search query ID after subsequent run(s). Defaults to empty string.

        Returns:
            True if clash detected, False otherwise.

        """
        self._is_prim_view = False
        stage = self._stage

        if prim.IsValid():
            prim_path = prim.GetPath()
        else:
            carb.log_warn("Invalid prim. Aborting clash detection.")
            return False

        # Defaut searchset to entire current scene
        if not self._object_b_path:
            default_prim = stage.GetDefaultPrim().GetPath()
            if not default_prim:
                self._object_b_path = "/"
            else:
                self._object_b_path = default_prim
        searchset_path = self._object_b_path

        self._query = ClashQuery(
            query_name=query_name,
            object_a_path=str(prim_path),
            object_b_path=str(searchset_path),
            clash_detect_settings={
                SettingId.SETTING_LOGGING.name: self._logging is True,
                SettingId.SETTING_TOLERANCE.name: float(self._tolerance),
                SettingId.SETTING_DYNAMIC.name: False,
                SettingId.SETTING_DYNAMIC_START_TIME.name: float(0.0),
                SettingId.SETTING_DYNAMIC_END_TIME.name: float(0.0),
            },
            comment="",
        )

        success = self._run(stage)

        if not success:
            carb.log_warn(f"Failed to run clash detection for {prim_path}")

        if self._num_overlaps == 0:
            return False

        return True

    def detect_prim_view_clashes(self, prim_view: Prim, prim_view_query_name: str = "") -> list:
        """Check if any prims in the input prim view are clashing with any mesh in the searchset.

        Args:
            prim_view: The prim view to be checked for clashes.
            prim_view_query_name: Unique query name for this clash detection run. Required if not storing
                query IDs and need to search query ID after subsequent run(s). Note: A top level prim view ID; each
                prim in the view has own unique query ID, reported with results. Defaults to empty string.

        Returns:
            List of namedtuple('Clash', 'prim_path query_name'): Clashing prims and corresponding prim query ID.
            Empty list if no clashes detected.

        """
        self._is_prim_view = True
        self._clashing_view_prims = []
        stage = self._stage

        # Defaut searchset to entire current scene
        if not self._object_b_path:
            default_prim = stage.GetDefaultPrim().GetPath()
            if not default_prim:
                self._object_b_path = "/"
            else:
                self._object_b_path = default_prim
        searchset_path = self._object_b_path

        if prim_view.valid:
            self._prim_view_counter += 1
            self._prim_view_query_name = prim_view_query_name
            for prim in prim_view.prims:
                prim_path = str(prim.GetPath())
                query_name = f"Query {prim.GetName()}"
                self._query = ClashQuery(
                    query_name=query_name,
                    object_a_path=str(prim_path),
                    object_b_path=str(searchset_path),
                    clash_detect_settings={
                        SettingId.SETTING_LOGGING.name: self._logging is True,
                        SettingId.SETTING_TOLERANCE.name: float(self._tolerance),
                        SettingId.SETTING_DYNAMIC.name: False,
                        SettingId.SETTING_DYNAMIC_START_TIME.name: float(0.0),
                        SettingId.SETTING_DYNAMIC_END_TIME.name: float(0.0),
                    },
                    comment="",
                )
                success = self._run(stage, self._prim_view_counter)
                if not success:
                    carb.log_warn(f"Failed to run clash detection for {prim_path}")
                if self._num_overlaps != 0:
                    Clash = namedtuple("Clash", "prim_path query_name")
                    self._clashing_view_prims.append(Clash(prim_path, query_name))

        else:
            carb.log_warn("Prim View contains an invalid prim. Aborting clash detection.")

        return self._clashing_view_prims

    def _run(self, stage: Usd.Stage, prim_view_id: int = 0) -> bool:
        """Perform the clash detection.

        Args:
            stage: The stage on which the clash detection is run.
            prim_view_id: Tracks prim view queries for data storage/retrieval.

        Returns:
            True if run was successful, False otherwise.

        """
        if self._clash_data_layer:
            new_query_id = self._clash_data.insert_query(self._query, True, True)
            if not new_query_id or new_query_id < 1:
                carb.log_warn("Failed to save clash detection query...")
                return False

        clash_detect = ClashDetection()
        if not clash_detect.set_scope(stage, self._query.object_a_path, self._query.object_b_path):
            carb.log_warn("Failed to set clash detection scope.")
            return False
        if not clash_detect.set_settings(self._query.clash_detect_settings, stage):
            carb.log_warn("Failed to set clash detection settings.")
            return False

        self._num_overlaps = self._detect_overlaps(stage, clash_detect)

        if self._clash_data_layer:
            if self._is_prim_view and prim_view_id != 0:
                if self._num_overlaps != 0:
                    self._store_query_name(self._query.query_name, new_query_id)
                    self._store_query_id_to_view_group(prim_view_id, new_query_id)
            else:
                self._store_query_name(self._query.query_name, new_query_id)

        return True

    def _store_query_name(self, query_name: str, query_id: int) -> None:
        """Store query names with their associated IDs for data retrieval.

        Args:
            query_name: The query name to store.
            query_id: The query ID to associate with the name.

        """
        self._prim_queries[str(query_name)] = query_id

    def _store_query_id_to_view_group(self, prim_view_id: int, new_query_id: int) -> None:
        """Store prim view query names with their associated prim query names and IDs for data retrieval.

        Args:
            prim_view_id: The prim view ID to group queries under.
            new_query_id: The new query ID to add to the view group.

        """
        if not self._prim_view_query_name:
            self._prim_view_query_name = f"Prim_view_{prim_view_id}_query"

        view_name = self._prim_view_query_name
        curr_query_name = self._query.query_name
        try:
            self._prim_view_queries[view_name]["query_ids"].append(new_query_id)
            self._prim_view_queries[view_name]["query_names"].append(curr_query_name)
        except:
            self._prim_view_queries[view_name] = {
                "prim_view_id": prim_view_id,
                "query_ids": [new_query_id],
                "query_names": [curr_query_name],
            }
        return

    def _fetch_overlaps(
        self, stage: Usd.Stage, clash_detect: ClashDetection, clash_query: ClashQuery, num_overlaps: int
    ) -> bool:
        """Fetch overlaps and writes the clash info to log file. Used if clash data layer is not created.

        Args:
            stage: The stage on which the clash detection is run.
            clash_detect: The clash detection engine instance.
            clash_query: The clash query containing detection parameters.
            num_overlaps: The number of overlaps to fetch.

        Returns:
            True if fetching overlaps is a success.

        """
        setting_tolerance = clash_query.clash_detect_settings.get(SettingId.SETTING_TOLERANCE.name, 0.0)
        setting_depth_epsilon = clash_query.clash_detect_settings.get(SettingId.SETTING_DEPTH_EPSILON.name, -1.0)

        data = []

        progress_update = OptimizedProgressUpdate()
        for idx in range(num_overlaps):
            temp_data = []
            progress_update.update(float(idx) / float(num_overlaps))
            new_clash_info = clash_detect.process_overlap(
                stage, idx, {}, clash_query.identifier, setting_tolerance, setting_depth_epsilon
            )
            if new_clash_info:
                temp_data.append(f"Clash ID: {new_clash_info.overlap_id}")
                temp_data.append(f"Tolerance: {new_clash_info.tolerance}")
                temp_data.append(f"Overlapping Tris: {new_clash_info.overlap_tris}")
                temp_data.append(f"Clashing Frames: {new_clash_info.num_records}")
                temp_data.append(f"Object A: {new_clash_info.object_a_path}")
                temp_data.append(f"Object B: {new_clash_info.object_b_path}")

            data.append(temp_data)

        if num_overlaps > 0:
            output = dict()
            if self._is_prim_view:
                output[f"View Query/Prim Query: {self._prim_view_query_name}/{clash_query.query_name}"] = data
            else:
                output[f"Query Name: {clash_query.query_name}"] = data
            carb.log_info(yaml.dump(output))

        return True

    def _detect_overlaps(self, stage: Usd.Stage, clash_detect: ClashDetection) -> int:
        """Run clash detection engine, fetches results and serializes them.

        Args:
            stage: The stage on which the clash detection is run.
            clash_detect: The clash detection engine instance.

        Returns:
            Number of overlaps found.

        """
        progress_update = OptimizedProgressUpdate()
        num_steps = clash_detect.create_pipeline()
        for i in range(num_steps):
            step_data = clash_detect.get_pipeline_step_data(i)
            clash_detect.run_pipeline_step(i)
            progress_update.update(step_data.progress)

        num_overlaps = clash_detect.get_nb_overlaps()

        if self._clash_data_layer:
            _ = list(clash_detect.fetch_and_save_overlaps(stage, self._clash_data, self._query))
        else:
            self._fetch_overlaps(stage, clash_detect, self._query, num_overlaps)

        return num_overlaps
