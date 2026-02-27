
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_custom_interactive_examples:

==========================================
Custom Interactive Examples
==========================================

You can create custom examples in |isaac-sim| Examples Browser, so that your examples are accessible in the same browser as rest of the examples.


BaseSampleUITemplate & BaseSample Classes
=====================================================

The `BaseSampleUITemplate` and `BaseSample` classes provide the basic structure for creating an interactive examples that looks similar to our other examples in the Examples Browser. It produces a `Load` button and a `Reset` button, each button abstracts away the complexity of asynchronously interacting with the simulator and making the interactiveness work. 

To create your own, follow the steps below:

#. Copy the current files to the ``user_examples`` folder under ``isaacsim/examples/interactive``.

    .. code-block:: console

        cd exts/isaacsim.examples.interactive/isaacsim/examples/interactive
        cp hello_world/hello_world* user_examples/

#. Edit the highlighted lines in :code:`exts/isaacsim.examples.interactive/isaacsim/examples/interactive/user_examples/hello_world_extension.py`:

    .. literalinclude:: ../snippets/utilities/custom_interactive_examples/edit_the_highlighted_lines_in_codeextsisaacsimexam.py
        :language: python

#. Add the following lines to :code:`exts/isaacsim.examples.interactive/isaacsim/examples/interactive/user_examples/__init__.py`.

    .. literalinclude:: ../snippets/utilities/custom_interactive_examples/add_the_following_lines_to_codeextsisaacsimexample.py
        :language: python

.. note:: Every time the code is edited or changed, Press **Ctrl+S** to save the code and hot-reload |isaac-sim|.


If you want to add more complexity and more buttons, feel free to browse through the other Examples. You can always access the underlying script by clicking on the folder icon in the upper right hand corner of the Example Browser.


