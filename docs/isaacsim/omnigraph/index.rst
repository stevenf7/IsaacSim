.. _isaac_sim_omnigraph_overview_page:

=========================================================
OmniGraph
=========================================================

|omnigraph_short| is Omniverse's visual programming framework. It provides a graph framework that connects functions from multiple systems inside Omniverse. It is also a compute framework that allows for highly customized nodes so that you can integrate your own functionality into Omniverse and automatically harness the efficient computation backend.

Inside |isaac-sim|, |omnigraph_short| is the main engine for the Replicators, ROS 2 bridge, sensor access, controllers, external input/output devices, UI, and much more.

To access OmniGraph's editor, go to **Window > Graph Editors > Action Graph**.

.. toctree::
    :maxdepth: 1

    :doc:`OmniGraph Interface<extensions:ext_omnigraph/interface>`
    :doc:`OmniGraph Core Concepts <extensions:ext_omnigraph/getting-started/core_concepts>`
    omnigraph_shortcuts
    omnigraph_custom_python_nodes
    omnigraph_custom_cpp_nodes
    omnigraph_custom_ipc_nodes
    :doc:`Additional Resources<extensions:ext_omnigraph>`



Tutorials
=========================================================

.. toctree::
    :maxdepth: 1

    :doc:`Basic OmniGraph Tutorial<extensions:ext_omnigraph/tutorials/gentle_intro>`
    omnigraph_tutorial    
    omnigraph_scripting
