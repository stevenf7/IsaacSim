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
    """ A tool for monitoring a module file and loading/reloading it as necessary when the timestamp
    changes. It specifically watches the module at <watcher_file_path>/df_behavior_module.py.

    When the watcher is first created, the module is not loaded. It is loaded for the first time
    only when the file changes for the first time. Subsequently, whenever the file is touched, the
    module is reloaded. The pycache is cleared as needed to ensure a cached version is not loaded.

    Model: The active behavior is stored in df_behavior_module.py. On startup, no behavior is
    loaded. To activate a behavior, a behavior file is copied to the df_behavior_module.py location
    and it's automatically loaded by the watcher.

    A module can have a variable record_animation_state_trajectory which, when set to True, will
    register as a recording request in the property self.recording_requested. This watcher does not
    act on that information, but simply makes it availble.
    """

    def __init__(self, verbose=False):
        """ Initialize the watcher to watch the specific file
        <watcher_file_path>/df_behavior_module.py The module is not loaded on startup.
        """
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
        """ True if the behavior has been loaded. False otherwise.
        """
        return self.behavior is not None

    @property
    def recording_requested(self):
        """ True if the behavior module has the recording attribute.
        """
        if not hasattr(self.dbm, self.recording_attr):
            return False
        return getattr(self.dbm, self.recording_attr)

    def tick_behavior(self):
        """ If a behavior has been loaded, that behavior is ticked.
        """
        if self.has_behavior:
            self.behavior.tick()

    def deleted_recording_attribute_if_needed(self):
        """ Deletes the recording attribute from the loaded behavior module if it exists.
        """
        if hasattr(self.dbm, self.recording_attr):
            delattr(self.dbm, self.recording_attr)

    def check_new_stamp(self):
        """ Check the behavior module to see if the latest timestamp differs from the previous
        timestamp.

        Returns the new timestamp if the time stamp has changed (or it's the first time calling it).
        Returns None if the timestamp has not changed since the last time this method was called.
        """
        if self.stamp is None:
            if os.path.exists(self.dbm_path):
                return os.stat(self.dbm_path).st_mtime
        else:
            new_stamp = os.stat(self.dbm_path).st_mtime
            if new_stamp > self.stamp:
                return new_stamp

        return None

    def clear(self):
        """ Clear the currently loaded active behavior.
        """
        self.stamp = None
        self.behavior = None

    def check_reload(self, context_tools):
        """ Checks whether it needs to load or reload the behavior (the timestamp has changed). If
        so, it reloads the behavior module and calls self.build_behavior() on it.
        """

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
        """ Builds the behavior in the currently loaded behavior model by calling the module's
        build_behavior(context_tools) method.
        """
        try:
            self.behavior = self.dbm.build_behavior(context_tools)
        except Exception as e:
            print("\nProblem building behavior.")
            import traceback

            traceback.print_exc()
