
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _isaac_sim_app_tutorial_advanced_export_urdf:

.. _isaac_sim_app_tutorial_export_urdf:

=====================
Tutorial: Export URDF
=====================

Learning Objectives
===================
This tutorial explores exporting a URDF file from USD in |isaac-sim|.
After this tutorial, you will be able to convert robot USD files to URDF files using |isaac-sim|.

*10-20 Minute Tutorial*

Getting Started
===============

**Prerequisites**

- Review the :ref:`isaac_sim_intro_quickstart_series` prior to beginning this tutorial.

Exporting A Robot
=================

To convert a robot USD file to a URDF file and cover some advanced options:

Enable the Exporter Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enable the exporter extension:

#.  Navigate to **Windows > Extensions** and type ``urdf`` in the search bar, then enable the USD to URDF exporter extension.

    This will add the **File > Export to URDF** menu option. 

#. Select it to open the extension, verify that the user interface is similar to:

    .. image:: /images/usd_to_urdf_exporter/isim_5.1_full_ext-usd_to_urdf_exporter-1.3.3_gui_urdf_export.png
      :align: center
      :alt: The USD to URDF Exporter UI

#. Open the USD for the Franka robot, which is found in the Isaac asset root path at ``/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd``.

    After the USD finishes loading: 

#. Open the **File > Export to URDF** menu option. A select file dialog will appear. 
#. Select the destination file and folder.
#. Click **Export**.

    .. image:: /images/usd_to_urdf_exporter/isim_5.1_full_ext-usd_to_urdf_exporter-1.3.3_gui_urdf_export.png
      :align: center
      :alt: The USD to URDF Exporter UI

#. Open the output folder to view the resulting files.
#. Verify that a ``franka.urdf`` file and a ``meshes`` directory is present. The ``meshes`` directory contains the mesh files for the robot.

  To check the results: 
  
    - The URDF can be imported back to USD and opened in Isaac Sim. Refer to the :ref:`Import URDF<isaac_sim_app_tutorial_advanced_import_urdf>` tutorial for the steps to do that.

    - Review the results with this `URDF Viewer Example <https://gkjohnson.github.io/urdf-loaders/javascript/example/bundle/index.html>`__ website. Drag the output directory directly into the site to view the URDF file, and examine the joints.

.. image:: /images/usd_to_urdf_exporter/urdf_viewer_franka.png
  :align: center
  :alt: The Franka URDF viewed with the URDF Viewer Example website


Import Options
^^^^^^^^^^^^^^^

Mesh Folder Name
-------------------

The folder name for where the mesh ``.obj`` files are saved. Defaults to the name ``meshes``, and is placed in the same directory as where the URDF file is saved.

  .. image:: /images/usd_to_urdf_exporter/isim_5.1_full_ext-usd_to_urdf_exporter-1.3.3_gui_urdf_export.png
    :align: center
    :alt: Mesh directory path field

Mesh Path Prefix
----------------

There are three options for the mesh path prefix:

#. Absolute path (default), defined by the prefix ``file://``
#. package path, defined by the prefix ``package://``
#. Relative path, defined by the prefix ``./``

When using the ``package://`` prefix, the package name needs to be specified in the ``Package Name`` field. If left blank, the package name will be the name of the urdf file.

Root Prim Path
--------------

If you are exporting a robot directly from its asset file, the default prim would be the root prim for it, but if exporting from a scene that contains a robot and multiple other objects, you can elect to export only the robot by specifying which prim represents it.


Collision Objects
------------------

In a URDF file, a link often has two separate meshes associated with it: 

* a visual mesh
* a collision mesh
  
In USD there is no distinction between a visual mesh and a collision mesh.
USD prims can have the ``PhysicsCollisionAPI`` attached to them, which tells the physics engine to resolve the motion of the body as it touches other bodies.
Additionally, prims can be set to be visible or invisible.
The USD to URDF exporter creates visual meshes and collision meshes for each link based on if it has the ``PhysicsCollisionAPI`` applied to it and if it is visible.

To explore how geometry prims map to visual and collision meshes in the URDF, add a geometry prim to the Franka robot and export it in different ways to verify what is created with each of the resulting URDF files.

#. Open the USD for the Franka robot (found at ``/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd``).
#. Right click the ``panda_hand`` Xform prim, and from the contextual menu select **Create > Mesh > Sphere**.
#. Select the new ``Sphere`` Mesh prim, and change the scaling for the x, y, and z components to all be ``0.3``.

#. Verify that the Franka is similar to:

    .. image:: /images/usd_to_urdf_exporter/franka_usd_sphere_mesh_no_collision_visible.png
      :align: center
      :alt: The Franka USD with a mesh sphere that does not have collision API and is visible

#. Export your current stage by following the steps discussed above and outlined below (there is no need to save your changes).

    * Open the **USD to URDF Exporter** menu.
    * Select an output directory.
    * Press the **EXPORT** button.

#. Drag your output directory into the `URDF Viewer Example <https://gkjohnson.github.io/urdf-loaders/javascript/example/bundle/index.html>`__ website to view the results.
#. Verify that your results are similar to:

    .. image:: /images/usd_to_urdf_exporter/franka_urdf_sphere_mesh_no_collision_visible.png
      :align: center
      :alt: The Franka URDF with a mesh sphere that does not have the collision API and is visible

#. Enable the **Show Collision** option, which visualizes all the collisions meshes and highlights them with a gold color.
#. Observe how the sphere is not highlighted with the gold color, that is because in the URDF it is not a collision mesh it is a visual mesh.

#. Back in the Franka USD, add the collision API to the sphere.

   This can be done by selecting the ``Sphere`` prim and clicking the **+Add** button in the prim's property menu.

#. Select **Physics > Colliders Preset**.
#. After adding the collision API to the sphere, re-export the USD stage to URDF and drag the output directory into the URDF viewer again. You might need to refresh the viewer's webpage before dragging in the new URDF.

#. Verify that your Franka is similar to:

    .. image:: /images/usd_to_urdf_exporter/franka_urdf_sphere_mesh_collision_visible.png
      :align: center
      :alt: The Franka URDF with a mesh sphere that does have the collision API and is visible

#. Enable the **Show Collision** option.
#. Observe that this time the sphere is highlighted with the gold color.
    
    That is because the sphere is both a collision mesh and a visual mesh in the URDF file.

#. Back in the Franka USD, make the sphere invisible by disabling the "eye" icon next to the ``Sphere`` prim.

    .. image:: /images/usd_to_urdf_exporter/franka_usd_sphere_mesh_invisible.png
      :align: center
      :alt: The Franka USD with the sphere set to be invisible

#. After making the sphere invisible, re-export the USD stage to URDF and drag the output directory into the URDF viewer again.

    Initially the sphere is not there, but after enabling **Show Collision**, the sphere is highlighted with the gold color.
    This is because the sphere is a collision mesh, but not a visual mesh in the URDF file.

#. Verify that you have something similar to:

  .. image:: /images/usd_to_urdf_exporter/franka_urdf_sphere_mesh_collision_invisible.png
    :align: center
    :alt: The Franka URDF with a mesh sphere that does have the collision API and is invisible

To export link collision meshes correctly to URDF, they must have the collision API and must be set to invisible.
To make all collision API prims into visual meshes, regardless of the visibility state of the prim, enable the ``Visualize Collisions`` option under the advanced options of the USD to URDF Exporter.


Limitations
===========

The USD format offers much greater expressiveness and provides more capabilities compared to URDF.
The set of all scenes and robots that can be described using USD is a superset to those that can be described with URDF.
Meaning all scenes and robots that can be described by a URDF file can also be described by a USD file, but not vice versa.
Therefore, there is no direct one-to-one mapping between USDs and URDFs.
Consequently, when converting a USD file to a URDF file, several assumptions are made and constraints are imposed.

Here is list of constraints for the USD in order for the USD to URDF exporter to succeed.

* The kinematic structure of the robot must be a tree structure
* Scaling on sphere shapes must be the same for every axis
* Scaling on cylinder shapes must be the same for radius axes (that is, the non-height axes)
* The coordinates for each body frame of a joint must be co-located and aligned
* Parent link prims should be ``Body 0``, and child link prims should be ``Body 1`` of the joint
* Joint prims must be either ``prismatic``, ``revolute``, or ``fixed``
* Link prims must be ``Xform``.
* Sensor prims must be either ``Camera`` or ``IsaacImuSensor``
* Geometry prims must be either ``Cube``, ``Sphere``, ``Cylinder``, or ``Mesh``
* Geometry prims must be "leafs" in the kinematic tree

If your USD violates one of these constraints an error is thrown.

.. note::
  
   Depending on the robot structure, some body names might be overridden because of the merging of different frames. Review the output and verify that it is accurate.

Summary
=======

This tutorial covered the following topics:

#. Exporting URDF files using the exporter GUI
#. Validating the URDF result by viewing in a viewer
#. Understanding how collision and visual meshes in the URDF are controlled from the USD
#. Outline the limitation of the USD to URDF exporter

Further Learning
^^^^^^^^^^^^^^^^

Review :ref:`isaac_sim_app_extension_urdf_exporter` to learn more about other configuration options.
