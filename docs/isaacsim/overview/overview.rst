..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. meta::
    :title: What Is Isaac Sim
    :keywords: lang=en isaac isaac-sim robotics simulation introduction


.. rst-class:: isaacsim-hidden-title

==========================================
What Is Isaac Sim?
==========================================

.. raw:: html

   <div class="isaacsim-hero">
    <div class="isaacsim-hero__content">
     <div aria-hidden="true" class="isaacsim-hero__title">
     </div>
     <p class="isaacsim-hero__sub">
      <span>
       Import robots and scenes from URDF, MJCF, Onshape CAD, or USD. Simulate with PhysX or Newton, add RTX and physics-based sensors, generate synthetic data, prepare robots for Isaac Lab, and validate robot stacks with ROS 2.
      </span>
     </p>
     <div class="isaacsim-hero__btns isaacsim-action-row">
      <a class="sd-btn sd-btn-primary isaacsim-homepage-cta isaacsim-action" href="installation/quick-install.html">
       Quick Install
      </a>
      <a class="sd-btn sd-btn-outline-light isaacsim-homepage-cta isaacsim-action" href="#tutorials">
       Browse Tutorials
      </a>
     </div>
     <ul aria-label="Project signals" class="isaacsim-hero__badges">
      <li class="isaacsim-hero__badge-item">
       <a class="isaacsim-hero__badge" href="https://github.com/isaac-sim" rel="noopener noreferrer" target="_blank">
        <svg aria-hidden="true" fill="none" height="14" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" viewbox="0 0 24 24" width="14">
         <path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 00-1.3-3.2 4.2 4.2 0 00-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 00-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 00-.1 3.2A4.6 4.6 0 004 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21">
         </path>
        </svg>
        Open source on GitHub
       </a>
      </li>
     </ul>
    </div>
   </div>

Getting Started
==========================================

.. isaacsim-lead::

   Pick the setup that matches how you work. Most users should start
   with **Quick Install**. Choose Python or containers when you need
   pip, conda, CI, or remote workflows.

.. grid:: 1 2 2 4
   :gutter: 3

   .. grid-item-card::
      :link: isaac_sim_quick_install
      :link-type: ref
      :class-card: isaacsim-doc-card

      .. isaacsim-card-body::
         :icon: bolt
         :title: Quick Install
         :desc: Fastest path to a working local setup

   .. grid-item-card::
      :link: isaac_sim_app_install_workstation
      :link-type: ref
      :class-card: isaacsim-doc-card

      .. isaacsim-card-body::
         :icon: monitor
         :title: Workstation Setup
         :desc: Install the full app and local dependencies

   .. grid-item-card::
      :link: isaac_sim_app_install_container
      :link-type: ref
      :class-card: isaacsim-doc-card

      .. isaacsim-card-body::
         :icon: cube
         :title: Container Setup
         :desc: Run Isaac Sim in Docker for repeatable setups

   .. grid-item-card::
      :link: isaac_sim_app_install_python
      :link-type: ref
      :class-card: isaacsim-doc-card

      .. isaacsim-card-body::
         :icon: prompt
         :title: Python Environment
         :desc: Use pip or conda for Python-first workflows

.. tip::

   **Running into issues?** See :doc:`Setup Tips </installation/install_faq>` for common fixes or the :ref:`isaac_sim_troubleshooting` page.

----

Tutorials
==========================================

.. isaacsim-lead::

   Start with the topics users look for most: first simulation, robot
   import, sensors, ROS 2, synthetic data, and robot learning.

.. isaacsim-difficulty:: beginner

   Learn the app, scenes, and core robot workflows

.. grid:: 1 2 3 3
   :gutter: 3
   :class-container: isaacsim-tut-row

   .. grid-item-card:: Basic Usage Tutorial
      :img-top: /images/isim_4.5_base_tut_gui_add_cube.webp
      :link: isaac_sim_app_intro_quickstart
      :link-type: ref

      First steps: navigate the UI, load a scene, and run your first simulation.

   .. grid-item-card:: Python Scripting Intro
      :img-top: /images/WorldSceneStage.png
      :link: isaac_sim_app_python_scripting_overview
      :link-type: ref

      Write your first standalone script to control robots and environments.

   .. grid-item-card:: Import Your First URDF
      :img-top: /images/isim_6.0_tut_urdf_import.png
      :link: isaac_sim_app_tutorial_advanced_import_urdf
      :link-type: ref

      Bring a URDF robot into Isaac Sim, configure it, and simulate it on a stage.

.. isaacsim-difficulty:: intermediate

   Connect ROS 2 and build data generation workflows

.. grid:: 1 2 3 3
   :gutter: 3
   :class-container: isaacsim-tut-row

   .. grid-item-card:: TurtleBot with ROS 2
      :img-top: /images/isim_6.0_ros_tut_gui_tb_urdf_import.png
      :link: isaac_sim_app_tutorial_ros2_turtlebot
      :link-type: ref

      Set up a ROS 2 bridge and drive a TurtleBot in simulation.

   .. grid-item-card:: Synthetic Data with Replicator
      :img-top: /images/isim_6.0_replicator_tut_external_workflow.jpg
      :link: isaac_sim_app_tutorial_replicator_sdg_workflows
      :link-type: ref

      Generate labeled training data from Isaac Sim scenes with Replicator.

   .. grid-item-card:: Publish an RTX Camera to ROS 2
      :img-top: /images/isaac_tutorial_ros_camera_publishing_simview.png
      :link: isaac_sim_app_tutorial_ros2_camera_publishing
      :link-type: ref

      Stream ray-traced camera frames from Isaac Sim to a ROS 2 topic.

.. isaacsim-difficulty:: advanced

   Train policies, randomize scenes, and deploy results

.. grid:: 1 2 3 3
   :gutter: 3
   :class-container: isaacsim-tut-row

   .. grid-item-card:: Prep a Robot for Isaac Lab
      :img-top: /images/isaac_orbit_tasks.jpg
      :link: isaac_lab_tutorials_page
      :link-type: ref

      Rig your robot and stage a scene in Isaac Sim so Isaac Lab can train policies on it.

   .. grid-item-card:: AMR Navigation Synthetic Data
      :img-top: /images/isaac_tutorial_replicator_amr_0.gif
      :link: isaac_sim_app_tutorial_replicator_amr_navigation
      :link-type: ref

      Drive an AMR through randomized warehouse scenes and capture stereo camera data when it nears objects of interest.

   .. grid-item-card:: Policy Evaluation
      :img-top: /images/tutorial_lab_h1_walk_thumb.gif
      :link: isaac_sim_app_tutorial_policy_deployment
      :link-type: ref

      Exercise a trained policy or VLA in richer Isaac Sim scenes before deployment.

----

Isaac Sim Workflow Overview
==========================================

.. raw:: html

   <div class="isaacsim-platform">
    <div class="isaacsim-platform__frame isaacsim-frame isaacsim-frame--soft">
     <div class="isaacsim-platform__topbar">
      <div>
       <div class="isaacsim-platform__eyebrow isaacsim-kicker">
        Isaac Sim
       </div>
      </div>
      <div class="isaacsim-platform__meta">
       <a class="isaacsim-chip" href="https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer.html" rel="noopener noreferrer" target="_blank">
        RTX
       </a>
       <a class="isaacsim-chip" href="https://developer.nvidia.com/newton-physics" rel="noopener noreferrer" target="_blank">
        Newton
       </a>
       <a class="isaacsim-chip" href="https://nvidia-omniverse.github.io/PhysX/" rel="noopener noreferrer" target="_blank">
        PhysX
       </a>
       <a class="isaacsim-chip" href="https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph.html" rel="noopener noreferrer" target="_blank">
        OmniGraph
       </a>
       <a class="isaacsim-chip" href="https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html" rel="noopener noreferrer" target="_blank">
        Replicator
       </a>
       <a class="isaacsim-chip" href="https://openusd.org/" rel="noopener noreferrer" target="_blank">
        OpenUSD
       </a>
      </div>
     </div>
     <div class="isaacsim-platform__canvas isaacsim-surface">
      <div class="isaacsim-platform__loop-title">
       <div>
        <span class="isaacsim-title-md">
         Simulation Development Loop
        </span>
        <p class="isaacsim-copy-sm">
         Bring assets in, configure the robot and scene, simulate behavior, then connect external stacks.
        </p>
        <div aria-label="Highlight workflow-specific steps" class="isaacsim-tabset__tabs isaacsim-platform__lens-inline" role="radiogroup">
         <input checked="" class="isaacsim-tabset__radio isaacsim-platform__lens-input" id="isaacsim-platform-lens-core" name="isaacsim-platform-lens" type="radio"/>
         <label class="isaacsim-tabset__tab isaacsim-platform__lens-pill isaacsim-platform__lens-pill--core isaacsim-chip isaacsim-chip--strong isaacsim-chip--button" for="isaacsim-platform-lens-core">
          Overview
         </label>
         <input class="isaacsim-tabset__radio isaacsim-platform__lens-input" id="isaacsim-platform-lens-sdg" name="isaacsim-platform-lens" type="radio"/>
         <label class="isaacsim-tabset__tab isaacsim-platform__lens-pill isaacsim-platform__lens-pill--sdg isaacsim-chip isaacsim-chip--strong isaacsim-chip--button" for="isaacsim-platform-lens-sdg">
          Synthetic Data Generation
         </label>
         <input class="isaacsim-tabset__radio isaacsim-platform__lens-input" id="isaacsim-platform-lens-sil" name="isaacsim-platform-lens" type="radio"/>
         <label class="isaacsim-tabset__tab isaacsim-platform__lens-pill isaacsim-platform__lens-pill--sil isaacsim-chip isaacsim-chip--strong isaacsim-chip--button" for="isaacsim-platform-lens-sil">
          Software-in-the-loop Testing
         </label>
        </div>
        <div class="isaacsim-platform__lens-copy">
         <p class="isaacsim-platform__lens-copy-item isaacsim-platform__lens-copy-item--core isaacsim-copy-sm">
          Each stage stays reusable: asset prep, robot and scene configuration, simulation, and stack connection all operate on the shared Isaac Sim scene.
         </p>
         <p class="isaacsim-platform__lens-copy-item isaacsim-platform__lens-copy-item--sdg isaacsim-copy-sm">
          For SDG, label the scene, vary conditions, simulate behavior, and render sensor outputs for downstream datasets.
         </p>
         <p class="isaacsim-platform__lens-copy-item isaacsim-platform__lens-copy-item--sil isaacsim-copy-sm">
          For SIL, configure robot physics, sensors, and communication graphs, then validate the external robot stack before hardware.
         </p>
        </div>
       </div>
      </div>
      <div aria-label="Isaac Sim core loop" class="isaacsim-platform__loop" role="group">
       <div aria-hidden="true" class="isaacsim-platform__rail isaacsim-platform__rail--top">
        <span class="isaacsim-platform__rail-arrow isaacsim-flow-arrow isaacsim-flow-arrow--head-only isaacsim-flow-arrow--right">
        </span>
       </div>
       <div aria-hidden="true" class="isaacsim-platform__rail isaacsim-platform__rail--right">
        <span class="isaacsim-platform__rail-arrow isaacsim-flow-arrow isaacsim-flow-arrow--head-only isaacsim-flow-arrow--down">
        </span>
       </div>
       <div aria-hidden="true" class="isaacsim-platform__rail isaacsim-platform__rail--bottom">
        <span class="isaacsim-platform__rail-arrow isaacsim-flow-arrow isaacsim-flow-arrow--head-only isaacsim-flow-arrow--left">
        </span>
       </div>
       <div aria-hidden="true" class="isaacsim-platform__rail isaacsim-platform__rail--left">
        <span class="isaacsim-platform__rail-arrow isaacsim-flow-arrow isaacsim-flow-arrow--head-only isaacsim-flow-arrow--up">
        </span>
       </div>
       <article class="isaacsim-platform__loop-node isaacsim-platform__loop-node--import isaacsim-diagram-node isaacsim-surface isaacsim-surface--muted">
        <div class="isaacsim-platform__loop-node-head isaacsim-diagram-node__head">
         <span class="isaacsim-step-badge isaacsim-step-badge--node isaacsim-marker">
          01
         </span>
         <strong class="isaacsim-diagram-node__title isaacsim-title-sm">
          Import
         </strong>
        </div>
        <div class="isaacsim-platform__loop-node-copy isaacsim-diagram-node__copy isaacsim-copy-sm">
         Scenes, robots, sensors, assets
        </div>
        <div class="isaacsim-platform__loop-node-facets isaacsim-chip-list">
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Scene assets
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Target objects
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Sensor assets
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Robot assets
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Robot descriptions
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          CAD / USD / NuRec
         </span>
        </div>
       </article>
       <article class="isaacsim-platform__loop-node isaacsim-platform__loop-node--configure isaacsim-diagram-node isaacsim-surface isaacsim-surface--muted">
        <div class="isaacsim-platform__loop-node-head isaacsim-diagram-node__head">
         <span class="isaacsim-step-badge isaacsim-step-badge--node isaacsim-marker">
          02
         </span>
         <strong class="isaacsim-diagram-node__title isaacsim-title-sm">
          Configure
         </strong>
        </div>
        <div class="isaacsim-platform__loop-node-copy isaacsim-diagram-node__copy isaacsim-copy-sm">
         Shared setup, then workflow-specific wiring
        </div>
        <div class="isaacsim-platform__loop-node-facets isaacsim-chip-list">
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Materials
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Sensors
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Scenarios
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Semantics
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Randomization
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Tune robot physics
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Communication graph
         </span>
        </div>
       </article>
       <article class="isaacsim-platform__loop-node isaacsim-platform__loop-node--simulate isaacsim-diagram-node isaacsim-surface isaacsim-surface--muted">
        <div class="isaacsim-platform__loop-node-head isaacsim-diagram-node__head">
         <span class="isaacsim-step-badge isaacsim-step-badge--node isaacsim-marker">
          03
         </span>
         <strong class="isaacsim-diagram-node__title isaacsim-title-sm">
          Simulate
         </strong>
        </div>
        <div class="isaacsim-platform__loop-node-copy isaacsim-diagram-node__copy isaacsim-copy-sm">
         Run the world and capture evidence
        </div>
        <div class="isaacsim-platform__loop-node-facets isaacsim-chip-list">
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Physics stepping
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Sensor output
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Randomization
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Annotation capture
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Rendered frames
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Control loop
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Stack behavior
         </span>
        </div>
       </article>
       <article class="isaacsim-platform__loop-node isaacsim-platform__loop-node--deploy isaacsim-diagram-node isaacsim-surface isaacsim-surface--muted">
        <div class="isaacsim-platform__loop-node-head isaacsim-diagram-node__head">
         <span class="isaacsim-step-badge isaacsim-step-badge--node isaacsim-marker">
          04
         </span>
         <strong class="isaacsim-diagram-node__title isaacsim-title-sm">
          Connect / Deploy
         </strong>
        </div>
        <div class="isaacsim-platform__loop-node-copy isaacsim-diagram-node__copy isaacsim-copy-sm">
         Send results to training or robot stacks
        </div>
        <div class="isaacsim-platform__loop-node-facets isaacsim-chip-list">
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Dataset writers
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg">
          Training pipelines
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sdg isaacsim-platform__facet--sil">
          Model evaluation
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Failure-case tests
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Robot stack
         </span>
         <span class="isaacsim-platform__facet isaacsim-chip isaacsim-chip--compact isaacsim-platform__facet--sil">
          Pre-hardware tests
         </span>
        </div>
       </article>
       <div class="isaacsim-platform__hub">
        <div class="isaacsim-platform__hub-title">
         Shared Isaac Sim Scene
        </div>
        <div class="isaacsim-platform__hub-copy">
         USD scene, physics state, sensors, semantics, and graphs in one runtime.
        </div>
       </div>
      </div>
     </div>
     <div class="isaacsim-platform__steps">
      <div class="isaacsim-platform__stepcopy isaacsim-step-card isaacsim-surface">
       <strong class="isaacsim-step-card__title isaacsim-kicker">
        <span class="isaacsim-step-badge isaacsim-marker">
         01
        </span>
        Import
       </strong>
       Bring robot, scene, sensor, CAD, DCC, and reconstructed assets into a shared USD workspace.
      </div>
      <div class="isaacsim-platform__stepcopy isaacsim-step-card isaacsim-surface">
       <strong class="isaacsim-step-card__title isaacsim-kicker">
        <span class="isaacsim-step-badge isaacsim-marker">
         02
        </span>
        Configure
       </strong>
       Set materials, sensors, scenarios, semantics, robot physics, and communication graphs.
      </div>
      <div class="isaacsim-platform__stepcopy isaacsim-step-card isaacsim-surface">
       <strong class="isaacsim-step-card__title isaacsim-kicker">
        <span class="isaacsim-step-badge isaacsim-marker">
         03
        </span>
        Simulate
       </strong>
       Run physics, sensor output, Replicator capture, and stack behavior on the assembled scene.
      </div>
      <div class="isaacsim-platform__stepcopy isaacsim-step-card isaacsim-surface">
       <strong class="isaacsim-step-card__title isaacsim-kicker">
        <span class="isaacsim-step-badge isaacsim-marker">
         04
        </span>
        Connect / Deploy
       </strong>
       Export datasets to training pipelines or connect external robot stacks for pre-hardware validation.
      </div>
     </div>
    </div>
   </div>

----

Robotics Ecosystem
==========================================

.. isaacsim-lead::

   Understanding the components of the NVIDIA robotics ecosystem and
   where Isaac Sim fits among them.

.. tab-set::

   .. tab-item:: Software-in-the-Loop Testing
      :selected:

      .. raw:: html

         <div aria-label="Software-in-the-Loop Testing workflow map" class="isaacsim-flow-rows" role="region">
          <p class="isaacsim-flow-rows__intro">
           Each row shows the workflow step and the NVIDIA component that supports it.
          </p>
          <ol class="isaacsim-flow-rows__list">
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 118,185,0;">
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              01
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Build the scene &amp; rig the robot
              </strong>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="isaac-sim">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Isaac Sim
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                Robotics simulator
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://docs.isaacsim.omniverse.nvidia.com/" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Assemble USD scenes, run physics and sensors, connect external robot stacks.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 44,95,163;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              02
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Train an RL or IL policy
              </strong>
              <span class="isaacsim-flow-row__badge">
               Optional
              </span>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="isaac-lab">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Isaac Lab
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                RL / IL framework
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://isaac-sim.github.io/IsaacLab/" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Train RL and imitation-learning policies with parallel environments.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 80,130,195;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              03
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Evaluate policy at scale
              </strong>
              <span class="isaacsim-flow-row__badge">
               Optional
              </span>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="lab-arena">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Lab - Arena
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                Policy benchmark
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://developer.nvidia.com/isaac/lab-arena" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Benchmark and compare trained policies across many scenes and seeds.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 118,185,0;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              04
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Run the integrated SIL test
              </strong>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="isaac-sim-sil">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Isaac Sim
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                SIL test stack
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://docs.isaacsim.omniverse.nvidia.com/" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Run software-in-the-loop tests with your ROS 2 or Isaac ROS robot stack.
             </p>
            </article>
           </li>
          </ol>
         </div>

   .. tab-item:: Synthetic Data Generation

      .. raw:: html

         <div aria-label="Synthetic Data Generation workflow map" class="isaacsim-flow-rows" role="region">
          <p class="isaacsim-flow-rows__intro">
           Each row shows the workflow step and the NVIDIA component that supports it.
          </p>
          <ol class="isaacsim-flow-rows__list">
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 30,140,160;">
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              01
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Bring in real-world environments
              </strong>
              <span class="isaacsim-flow-row__badge">
               Optional
              </span>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="nurec">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                NuRec
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                Reconstructed scenes
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://developer.nvidia.com/omniverse/nurec" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Gaussian-splat reconstructions of real environments, loaded as USD assets.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 118,185,0;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              02
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Assemble &amp; configure the scene
              </strong>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="isaac-sim">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Isaac Sim
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                Robotics simulator
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://docs.isaacsim.omniverse.nvidia.com/" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Assemble USD scenes, configure robots and sensors, run physics and rendering.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 80,150,35;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              03
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Define variation, simulate, &amp; write annotations
              </strong>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="replicator">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Replicator
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                SDG framework in Isaac Sim
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Script randomization, capture sensor outputs, and write labeled datasets.
             </p>
            </article>
           </li>
           <li class="isaacsim-flow-row" style="--isaacsim-flow-row-tone: 196,58,138;">
            <span aria-hidden="true" class="isaacsim-flow-arrow isaacsim-flow-arrow--down isaacsim-flow-row__arrow">
            </span>
            <div class="isaacsim-flow-row__stage isaacsim-surface">
             <span class="isaacsim-flow-row__marker isaacsim-marker isaacsim-marker--square">
              04
             </span>
             <div class="isaacsim-flow-row__copy">
              <strong class="isaacsim-flow-row__title isaacsim-title-sm">
               Photoreal augmentation
              </strong>
              <span class="isaacsim-flow-row__badge">
               Optional
              </span>
             </div>
            </div>
            <article class="isaacsim-flow-row__detail isaacsim-surface" data-tool="cosmos">
             <div class="isaacsim-flow-row__detail-head">
              <div>
               <strong class="isaacsim-flow-row__detail-title isaacsim-title-sm">
                Cosmos Transfer
               </strong>
               <span class="isaacsim-flow-row__detail-meta isaacsim-meta">
                Photoreal augmentation
               </span>
              </div>
              <a class="isaacsim-flow-row__detail-link" href="https://docs.nvidia.com/cosmos/latest/transfer2.5/index.html" rel="noopener noreferrer" target="_blank">
               Open docs
              </a>
             </div>
             <p class="isaacsim-flow-row__detail-copy isaacsim-copy-sm">
              Convert rendered RGB plus a text prompt into varied photoreal images, offline.
             </p>
            </article>
           </li>
          </ol>
         </div>

----

Open Source & Community
==========================================

.. isaacsim-lead::

   Isaac Sim is open source and built to fit into existing robotics
   stacks. Use the shipped tools, read the code, or extend the
   simulator with Python and Kit.

.. raw:: html

   <div class="isaacsim-open isaacsim-frame isaacsim-frame--accent">
    <div class="isaacsim-open__main">
     <div class="isaacsim-open__eyebrow isaacsim-kicker">
      Open-source platform
     </div>
     <div class="isaacsim-open__title isaacsim-title-md">
      Read the code, extend the simulator, and fit it into your stack.
     </div>
     <div class="isaacsim-open__desc isaacsim-copy-md">
      Start with the built-in tools, then automate with Python, build custom Kit apps, or integrate Isaac Sim into your own ROS 2 and ML workflows.
     </div>
     <div class="isaacsim-open__actions">
      <a class="sd-btn sd-btn-primary sd-shadow-sm isaacsim-open__button isaacsim-action isaacsim-action--wide" href="https://github.com/isaac-sim" rel="noopener noreferrer" target="_blank">
       <svg aria-hidden="true" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" viewbox="0 0 24 24" width="16">
        <path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 00-1.3-3.2 4.2 4.2 0 00-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 00-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 00-.1 3.2A4.6 4.6 0 004 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21">
        </path>
       </svg>
       Browse GitHub
      </a>
      <a class="sd-btn sd-btn-outline-primary isaacsim-open__button isaacsim-action isaacsim-action--wide" href="https://pypi.org/project/isaacsim/" rel="noopener noreferrer" target="_blank">
       <svg aria-hidden="true" fill="currentColor" height="16" viewbox="0 0 24 24" width="16">
        <path d="M11.91 0C5.4 0 5.81 2.82 5.81 2.82l.01 2.92h6.2v.88H3.36S0 6.24 0 12.81 2.93 19.7 2.93 19.7H5.5v-3.05s-.15-2.93 2.83-2.93h6.15s2.79.04 2.79-2.7v-5.07S17.7 0 11.91 0zM8.49 1.96c.62 0 1.12.5 1.12 1.12s-.5 1.12-1.12 1.12-1.12-.5-1.12-1.12.5-1.12 1.12-1.12z">
        </path>
        <path d="M12.09 24c6.51 0 6.1-2.82 6.1-2.82l-.01-2.92h-6.2v-.88h8.66S24 17.76 24 11.19c0-6.57-2.93-6.89-2.93-6.89H18.5v3.05s.15 2.93-2.83 2.93H9.52s-2.79-.04-2.79 2.7v5.07S6.3 24 12.09 24zm3.42-1.96c-.62 0-1.12-.5-1.12-1.12s.5-1.12 1.12-1.12 1.12.5 1.12 1.12-.5 1.12-1.12 1.12z">
        </path>
       </svg>
       Install via pip
      </a>
     </div>
    </div>
    <div class="isaacsim-fact-grid isaacsim-grid isaacsim-grid--4">
     <div class="isaacsim-fact-card isaacsim-surface">
      <strong class="isaacsim-title-sm">
       Apache 2.0
      </strong>
      <span class="isaacsim-copy-sm">
       Open-source licensing for the simulator stack.
      </span>
     </div>
     <div class="isaacsim-fact-card isaacsim-surface">
      <strong class="isaacsim-title-sm">
       USD-native
      </strong>
      <span class="isaacsim-copy-sm">
       One scene representation from asset import to deployment.
      </span>
     </div>
     <div class="isaacsim-fact-card isaacsim-surface">
      <strong class="isaacsim-title-sm">
       PhysX + Newton
      </strong>
      <span class="isaacsim-copy-sm">
       Switch between supported physics backends in one simulator.
      </span>
     </div>
     <div class="isaacsim-fact-card isaacsim-surface">
      <strong class="isaacsim-title-sm">
       RTX + Physics Sensors
      </strong>
      <span class="isaacsim-copy-sm">
       Use rendering and physics-based sensor models in one place.
      </span>
     </div>
    </div>
   </div>
.. isaacsim-link-grid::

   speech         | https://forums.developer.nvidia.com/c/omniverse/simulation/69 | Forum         | Ask questions and get help from the NVIDIA developer community.
   external-link  | https://discord.gg/4ZsTFksGh8                                 | Discord       | Chat with other Isaac Sim users and developers in real time.
   doc            | overview/release_notes.html                                   | Release Notes | Track the latest features, fixes, and version changes across Isaac Sim releases.
   help           | overview/help.html                                            | Help & FAQ    | Start with common installation fixes, troubleshooting, and support guidance.
