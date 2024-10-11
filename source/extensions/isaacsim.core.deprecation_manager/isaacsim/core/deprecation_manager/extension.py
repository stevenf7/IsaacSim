# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.ext
import omni.usd


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # get extension settings
        settings = carb.settings.get_settings()
        self._settings_entries = settings.get("/exts/isaacsim.core.deprecation_manager/settings")
        self._omnigraph_entries = settings.get("/exts/isaacsim.core.deprecation_manager/omnigraph")

        # update deprecated settings
        self._update_deprecated_settings()

        # subscribe to stage event to update OmniGraph nodes
        self._stage_event_subscription = None
        if self._omnigraph_entries:
            self._stage_event_subscription = (
                omni.usd.get_context()
                .get_stage_event_stream()
                .create_subscription_to_pop_by_type(int(omni.usd.StageEventType.OPENED), self._on_stage_event)
            )

    def on_shutdown(self):
        # delete stage event subscription
        self._stage_event_subscription = None

    def _update_deprecated_settings(self):
        settings = carb.settings.get_settings()
        # iterate through entries
        for entry in self._settings_entries:
            deprecated_setting = entry.get("deprecated", "")
            new_setting = entry.get("new", "")
            value = settings.get(deprecated_setting)
            if value is not None:
                deprecation_message = f"'{deprecated_setting}' has been deprecated in favor of '{new_setting}'."
                # update setting
                if entry.get("update", True):
                    settings.set(new_setting, value)
                    deprecation_message += f" Setting '{new_setting}' to {value}."
                # show deprecation message
                carb.log_warn(deprecation_message)

    def _on_stage_event(self, event):
        deprecation_changes = []
        for prim in omni.usd.get_context().get_stage().Traverse():
            # OmniGraph node
            if prim.HasAttribute("node:type"):
                attr = prim.GetAttribute("node:type")
                value = attr.Get()
                # iterate through entries
                for entry in self._omnigraph_entries:
                    if entry["deprecated"] in value:
                        new_value = value.replace(entry["deprecated"], entry["new"])
                        attr.Set(new_value)
                        deprecation_changes.append((entry["deprecated"], entry["new"], value, new_value))
        if not deprecation_changes:
            return
        deprecation_changes = sorted(list(set(deprecation_changes)), key=lambda item: item[2])
        # show deprecation message
        carb.log_warn(
            "The stage contains the following deprecated nodes that have been updated. Save it to preserve the changes"
        )
        for item in deprecation_changes:
            carb.log_warn(f"  |-- {item[2]} -> {item[3]}")
        # show notification in Kit window
        try:
            import omni.kit.notification_manager as notification_manager
        except ImportError:
            pass
        else:
            text = "The stage contains the following deprecated nodes that have been updated. Save it to preserve the changes\n"
            text += "\n".join([f" - {item[2]}" for item in deprecation_changes])
            notification_manager.post_notification(
                text,
                duration=0,
                hide_after_timeout=False,
                status=notification_manager.NotificationStatus.WARNING,
                button_infos=[notification_manager.NotificationButtonInfo("OK", on_complete=None)],
            )

        try:
            # reload all graphs if we made any changes
            # in some cases the omni.graph.core extension may not be enabled so this is optional
            import omni.graph.core as og

            all_graphs = og.get_all_graphs()
            for graph in all_graphs:
                graph.reload_from_stage()
        except Exception as e:
            carb.log_warn(f"Could not reload graphs after renaming nodes: {e}")
