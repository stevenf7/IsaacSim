# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os

from omni.isaac.cortex.tools import dynamic_reload


class DfBehaviorWatcher:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.dbm = None
        self.stamp = None
        self.behavior = None

        self.dirname = os.path.dirname(os.path.realpath(__file__))
        self.dbm_path = "%s/df_behavior_module.py" % self.dirname

        self.recording_attr = "record_animation_state_trajectory"

        self.is_first = True

    @property
    def has_behavior(self):
        return self.behavior is not None

    @property
    def recording_requested(self):
        if not hasattr(self.dbm, self.recording_attr):
            return False
        return getattr(self.dbm, self.recording_attr)

    def tick_behavior(self):
        if self.has_behavior:
            self.behavior.tick()

    def deleted_recording_attribute_if_needed(self):
        if hasattr(self.dbm, self.recording_attr):
            delattr(self.dbm, self.recording_attr)

    def check_new_stamp(self):
        if self.stamp is None:
            if os.path.exists(self.dbm_path):
                return os.stat(self.dbm_path).st_mtime
        else:
            new_stamp = os.stat(self.dbm_path).st_mtime
            if new_stamp > self.stamp:
                return new_stamp

        return None

    def clear(self):
        self.stamp = None
        self.behavior = None

    def check_reload(self, context_tools):

        # The first time through, set the stamp to the new stamp. If it's None, that does nothing,
        # but if there is a current stamp, this will prevent the behavior from being loaded until
        # the user explicitly activates a different behavior.
        if self.is_first:
            self.stamp = self.check_new_stamp()
            self.is_first = False

        if not os.path.exists(self.dbm_path):
            self.clear()
            return

        new_stamp = self.check_new_stamp()
        if new_stamp is not None:
            try:
                if self.dbm is None:
                    print("<load dbm>")
                    import omni.isaac.cortex.df_behavior_module as dbm

                    self.dbm = dbm
                else:
                    print("<reloading dbm>")
                    self.deleted_recording_attribute_if_needed()
                    dynamic_reload(self.dbm)

                self.build_behavior(context_tools)

                # Set the stamp only after everything so it's not recorded if there's an exception.
                self.stamp = new_stamp
                return True
            except Exception as e:
                print("\nProblem dynamically reloading behavior.")
                import traceback

                traceback.print_exc()
        return False

    def build_behavior(self, context_tools):
        try:
            self.behavior = self.dbm.build_behavior(context_tools)
        except Exception as e:
            print("\nProblem building behavior.")
            import traceback

            traceback.print_exc()
