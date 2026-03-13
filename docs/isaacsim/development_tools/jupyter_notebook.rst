.. _JupyterLab: https://jupyter.org
.. _Jupyter Notebook: https://jupyter.org

.. _isaac_sim_app_jupyter_notebook:

==========================================
Jupyter Notebook
==========================================

Interactive Scripting
-----------------------

The ``isaacsim.code_editor.jupyter`` extension allows you to to open a `JupyterLab`_ (or `Jupyter Notebook`_) app in the current Isaac Sim application scope and edit and execute Python code interactively.

#. To begin, enable this extension using the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.code_editor.jupyter``.

    .. note::

        This may take several seconds (and Isaac Sim will freeze) if this is the first time the ``isaacsim.code_editor.jupyter`` is enabled.
        Several Python dependencies will be installed.

#. Once the extension is enabled, go to the top menu bar and click on `Window > Jupyter Notebook` to open a Jupyter app in the default web browser.
#. In the Jupyter app, click on the *Omniverse (Python 3)* kernel (the one with the Omniverse logo) to create a new Untitled notebook.
#. Execute code by clicking the `Run` button at the top of the notebook. Try it yourself with the same code snippet from above!

    .. warning::

        * The *Omniverse (Python 3)* kernel is designed to run Python code, via the ``isaacsim.code_editor.jupyter`` extension, on a running Isaac Sim instance (where the Kit application has control over the update/simulation loop). 
        * The *Isaac Sim Python 3* kernel is used to run standalone applications (see :ref:`isaac_sim_python_jupyter_notebook_config` for more details).

    .. image:: /images/isaac_tutorial_advanced_code_editors_jupyter.png
        :align: center

.. warning::

    Execution of blocking code freezes Isaac Sim.

.. hint::

    * Use the :guilabel:`Tab` key for code autocompletion.
    * Use the :guilabel:`Ctrl + I` keys for code introspection (display docstring if available).

.. note::

    The notebooks are saved, by default, in a folder within the extension itself: ``exts/isaacsim.code_editor.jupyter/data/notebooks``. See the location for Isaac Sim packages/extensions in :ref:`isaac_sim_misc_paths`.

**Limitations**

- IPython magic commands are not available.
- Matplotlib plotting is not available in the notebooks.
- Printing, inside callbacks, is not displayed in the notebooks but in the Omniverse terminal.

|br| |hr|

.. _isaac_sim_python_jupyter_notebook_config:

Running Standalone Isaac Sim from Jupyter Notebook
----------------------------------------------------

.. warning::

    - This workflow is only supported on Linux.

Configuration Files
==========================

In order for |isaac-sim_short| to work inside of a Jupyter Notebook we provide a custom Jupyter kernel that is installed the first time you run ``./jupyter_notebook.sh``. 
The kernel.json itself is fairly simple:

.. literalinclude:: ../snippets/development_tools/jupyter_notebook/configuration_files.json
    :language: json

The important part is that ``AUTOMATICALLY_REPLACED`` gets replaced by ``jupyter_notebook.sh`` with the absolute path to the Python executable that is located in the kit/python directory at runtime. Once the variable is replaced, the kernel is installed and the notebook is started. There is an extra variable ``ISAAC_JUPYTER_KERNEL`` that is used inside of |isaac-sim_short| to setup for notebook usage properly.

Because notebooks require asyncio support, and |isaac-sim_short| itself uses asyncio internally, we automatically execute the following two lines when loading the ``isaacsim`` module (or the ``isaacsim.simulation_app`` extension) which provides the ``SimulationApp`` class:

.. literalinclude:: ../snippets/development_tools/jupyter_notebook/configuration_files_1.py
    :language: python

This ensures that asyncio calls can be nested inside of the Jupyter Notebook properly.

When writing code in notebooks, it is necessary to first instantiate the ``SimulationApp`` class (from ``isaacsim`` or ``isaacsim.simulation_app``) after perform any Isaac Sim / Omniverse imports:

.. literalinclude:: ../snippets/development_tools/jupyter_notebook/configuration_files_2.py
    :language: python

Then, to run the notebook just execute the following commands and play the notebook cells:

.. code-block:: bash

    ./jupyter_notebook.sh PATH_TO_NOTEBOOK.ipynb
