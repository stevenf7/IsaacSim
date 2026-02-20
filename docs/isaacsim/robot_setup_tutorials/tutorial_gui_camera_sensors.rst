
.. _isaac_sim_app_tutorial_gui_camera_sensors:

=================================================
Tutorial 4: Add Camera and Sensors to a Robot
=================================================

|isaac-sim_short| provides a variety of sensors that can be used to sense the environment and robot's state.
This tutorial guides you through attaching a camera sensor to a mock robot, a process that can be generalized to other sensors.
Details regarding the camera and other types of sensors can be found in our Advanced Tutorials and Sensor Extensions.

Learning Objectives
=======================

This tutorial details how to:

- Add cameras
- Attach cameras to geometries

Prerequisites
=======================
- Complete :ref:`isaac_sim_app_tutorial_gui_simple_robot`.
- Review the :ref:`introduction to camera frames and axes<isaac_sim_cameras>`.

Start this tutorial using the ``Isaac Sim/Samples/Rigging/MockRobot/mock_robot_rigged.usd`` file provided, to have a standardized setup.

Adding a Camera
=======================

To add a camera:

#. Go to the Menu Bar and select **Create > Camera**. A camera appears on the stage tree, and a grey wireframe representing the camera's view appears on the stage.
#. You can move and rotate the camera's transform just like any other objects on the stage.

.. Note:: 
    The camera icon is hidden by default in the viewport. To see the camera icon, go to the **eye** menu on the top edge of the viewport, and select **Show By Type > Cameras**. The camera icon appears in the viewport.

You can also add a camera by moving the current view in the viewport to a view of your choosing, and then go to the **Camera** button on the upper left hand corner of the viewport display, and select **Camera > Create from View**.
A new camera appears on the Stage tree, and the list of cameras that can be selected in the **Camera** button is provided.

.. image:: /images/isim_4.5_base_ref_gui_camera_widget.png
    :align: center

Inspect the Camera
=======================

Use the :ref:`isaac_sim_app_tutorial_camera_inspector_extension` to inspect the camera image and modify the camera's states as needed.

#. Select **Tools > Robotics > Camera Inspector**.
#. Verify that you can see the camera in the dropdown. Click the **Refresh** button to find new cameras.
#. Select the camera you want to inspect. Create new viewports if necessary, and get and set camera poses as needed.


Attach a Camera to Robot
==========================

1. Rename the newly added camera to ``car_camera``.
2. It is easier to place the camera if you can see the desired camera input stream and where it is relative to the robot from an outside camera.
   Open up a second viewport window by going to the Menu Bar and click **Window > Viewports > Viewport 2**. A new viewport appears. Dock it wherever you'd like.
3. Keep one of the viewports in **Perspective** camera view, and change the other one to *car_camera* view. Find the **Cameras** menu on the top edge of the viewport, and switch to **Camera > car_camera**.
4. Validate that you have a view of the onboard camera and an overview of the scene.
5. Attach the camera to the robot's body by dragging the prim under :code:`body`. The camera moves together with the body. You may need to switch the camera view for the viewport again.
6. Point the camera slightly down and make it face forward so you can see the car and the ground. Set the camera transform translation to :code:`x=-6,y=0,z=2.2`, orientation to :code:`x=0,y=-80,z=-90`, and scale to :code:`x=1,y=1,z=1`.
7. Verify that you see the viewport showing the onboard camera view splitting the window between the robot's body and the ground and the relative position and orientation of the camera to the robot in the *Perspective* camera viewport.
8. Press **Play**. The camera onboard the robot moves with the robot.

A similar strategy is used to apply other onboard sensors.

.. note:: If the view of the camera is moved while displaying, it changes the camera's properties. Instead, affix a prim to the parent with the correct offset and affix the camera to that new prim. Then, if the camera position is accidentally moved, it can be reset by zeroing all its position and orientation parameters relative to the prim, which cannot be easily changed.

Summary
========

In this tutorial, you learned how to use the Camera Inspector Extension.  Additionally, you also learned how to add a camera to the robot.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

- Continue on to :ref:`isaac_sim_app_omniverse_script_editor` to learn how to run Python APIs inside the GUI.
- For rigging a more complex robot, go to :ref:`isaac_sim_app_tutorial_advanced_rigging_robot`.

.. Further Reading
.. ^^^^^^^^^^^^^^^^^^^^^^^^^

.. - More about :doc:`Cameras<materials-and-rendering:cameras>`.
.. - Tutorials about using other types of sensors :ref:`isaac_sim_app_tutorial_advanced_range_sensor_lidar` and :ref:`isaac_sim_app_tutorial_advanced_range_sensor_generic`.

