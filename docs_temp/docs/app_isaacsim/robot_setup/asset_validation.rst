.. _isaac_sim_app_reference_asset_validation:

Asset Validation 
================================

Isaac Sim comes with the :ref:`isaacsim.asset.validation <isaac_sim_app_reference_asset_validation>` extension that provides a set of validation rules to ensure that USD assets are properly configured for use in Isaac Sim.

While some of the rules are related to recommended guidelines, such as the :ref:`isaac_sim_app_reference_asset_structure`, many are fundamental for the asset to work properly in Isaac Sim.

This document provides a comprehensive overview of all validation rules available in the Isaac Sim Asset Validation extension. The rules are organized by their registration categories and help ensure that USD assets are properly configured for use in Isaac Sim.

The Isaac Sim asset validation comes enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.asset.validation``.

To open the **Asset Validation** window, navigate to **Window > Asset Validator**. For more information on the Asset Validation window, refer to `Asset Validator <https://docs.omniverse.nvidia.com/kit/docs/asset-validator/latest/index.html>`_.  

There are many validation rules available in the Asset validation window. You can choose to run all validation rules, but specifically for Isaac Sim, there are three categories of rules to review.

The Isaac Simvalidation rules are grouped into the following categories:

- IsaacSim.PhysicsRules
    - Fundamental rules related to physics simulation
- IsaacSim.RobotRules
    - Rules related to robot assets
- IsaacSim.SimReadyAssetRules
    - Rules related to sim ready assets

This document will go through each of the rules and provide a detailed explanation of what it checks.

IsaacSim.PhysicsRules
=====================

.. list-table:: Physics Validation Rules
   :widths: 25 75
   :header-rows: 1

   * - Rule Name
     - Description and Checks
   * - **PhysicsJointHasDriveOrMimicAPI**
     - Validates that joints have a drive or mimic API.
       
       * Non-fixed joints must have either a drive API or mimic API
       * Joints excluded from articulation are exempt from this requirement
       * When both drive and mimic APIs are present, drive stiffness and damping must be 0.0
   * - **PhysicsJointMaxVelocity**
     - Validates that joints have a positive max velocity set.
       
       * Max joint velocity attribute is defined on joints with PhysxJointAPI
       * Max joint velocity value is greater than zero
   * - **PhysicsDriveAndJointState**
     - Validates that joint drives have proper force limits and matching state values.
       
       * Drive max force is defined and positive (not zero or infinite)
       * Drive target positions match joint state positions within tolerance (1e-2)
       * Drive target velocities match joint state velocities within tolerance (1e-2)
       
   * - **DriveJointValueReasonable**
     - Validates that joint drive stiffness values are within reasonable ranges.
       
       * Drive stiffness is within range (0.0 to 1,000,000.0)
       * Mimic joints have stiffness and damping set to 0.0
       * Non-mimic joints have stiffness values defined
       * Maximum natural frequency warning threshold: 500.0 Hz
   * - **JointHasCorrectTransformAndState**
     - Validates that joint transforms and states are consistent with the connected bodies.
       
       * Joint position consistency between connected bodies
       * Joint orientation consistency between connected bodies
       * Joint state values match the robot pose configuration
       * Applies to revolute and prismatic joints
   * - **JointHasJointStateAPI**
     - Validates that joints have the JointStateAPI applied.
       
       * Prismatic joints have JointStateAPI with "linear" type
       * Revolute joints have JointStateAPI with "angular" type
       * Provides automatic fix suggestion to apply missing APIs
   * - **MimicAPICheck**
     - Validates proper configuration of mimic joint APIs.
       
       * Reference joint relationship has exactly one target
       * Gear ratio, natural frequency, and damping ratio are defined and non-zero
       * Joint limits are properly configured relative to reference joint limits
       * Limit compatibility based on gear ratio sign (positive/negative)
   * - **RigidBodyHasMassAPI**
     - Validates that rigid bodies have properly configured mass properties.
       
       * Rigid bodies have MassAPI applied
       * Mass attribute is authored and non-zero
       * Diagonal inertia is authored and non-zero
       * Principal axes are authored and normalized
   * - **RigidBodyHasCollider**
     - Validates that enabled rigid bodies have collision geometry.
       
       * Enabled rigid bodies have collision geometry in their hierarchy
       * Searches through prim range including instance proxies
   * - **NonAdjacentCollisionMeshesDoNotClash**
     - Validates that non-adjacent collision meshes don't intersect.
       
       * Performs physics simulation to detect colliding pairs
       * Verifies that colliding bodies are connected by joints
       * Reports errors for non-adjacent colliding meshes
   * - **InvisibleCollisionMeshHasPurposeGuide**
     - Validates that invisible collision meshes have purpose set to 'guide'.
       
       * Collision meshes with invisible visibility
       * Purpose attribute is set to 'guide' for invisible collision meshes
   * - **HasArticulationRoot**  
     - Validates that at least one prim in the stage has the ArticulationRootAPI.
       
       * At least one prim in the stage has ArticulationRootAPI applied

IsaacSim.RobotRules
===================

.. list-table:: Robot Validation Rules
   :widths: 25 75
   :header-rows: 1

   * - Rule Name
     - Description and Checks
   * - RobotNaming
     - Validates that robot assets follow the standard naming convention.
       
       * Minimum folder nesting depth (at least 3 levels)
       * Folder name matches robot filename
       * Supports versioned folder structure: <Manufacturer>/<robot>/<robot.usd> or <Manufacturer>/<robot>/<version>/<robot.usd>
   * - **CleanFolder**
     - Validates that robot asset folders don't contain unexpected files.
       
       * Robot asset folders only contain expected files
       * Warns about unexpected files in the asset directory
   * - **NoOverrides**
     - Validates that prims don't have overridden attributes.
       
       * Prims don't have overridden attributes (excluding /Render paths)
       * Detects attributes with authored values in layer stack
       * Only applies for the open stage
   * - **RobotSchema**
     - Validates that robot assets have the required RobotAPI and relationships.
       
       * Default prim is set on the stage
       * Default prim has RobotAPI applied
       * robotLinks relationship exists and has targets
       * robotJoints relationship exists and has targets
   * - **JointsExist**
     - Validates that robot assets contain at least one joint.
       
       * At least one prim in the stage has JointAPI applied
   * - **LinksExist**
     - Validates that robot assets contain at least one link.
       
       * At least one prim in the stage has LinkAPI applied
   * - **ThumbnailExists**
     - Validates that robot assets have a thumbnail image.
       
       * Thumbnail image exists at expected path: ``<folder>/.thumbs/256x256/<filename>.png``
   * - **CheckRobotRelationships**
     - Validates that robot relationships are properly defined and prepended.
       
       * robotLinks and robotJoints relationships exist
       * Relationships are prepended for proper USD composition
       * Provides automatic fix suggestions for missing or non-prepended relationships
   * - **VerifyRobotPhysicsAttributesSourceLayer**
     - Validates that physics attributes are authored in the physics layer.
       
       * Physics attributes (starting with "physics:") are authored in _physics.usd layer
       * Warns when physics attributes are found in other layers
   * - **VerifyRobotPhysicsSchemaSourceLayer**
     - Validates that physics schemas are applied in the physics layer.
       
       * Physics schemas (starting with "Physx" or "Physics") are applied in _physics.usd layer
       * Warns when physics schemas are found in other layers

IsaacSim.SimReadyAssetRules
===========================

.. list-table:: Sim Ready Asset Validation Rules
   :widths: 25 75
   :header-rows: 1

   * - Rule Name
     - Description and Checks
   * - **NoNestedMaterials**
     - Validates that materials don't contain nested materials.
       
       * Material prims don't contain child materials in their hierarchy
       * Warns about nested material configurations
   * - **MaterialsOnTopLevelOnly**
     - Validates that materials are only defined in the top-level Looks prim.
       
       * All materials are children of the top-level Looks prim
       * Materials are not scattered throughout the stage hierarchy
       * Skips materials in referenced/payload content

Running the Validation Rules
============================

See video below for a demonstration of running the validation rules. We navigate to **Window > Asset Validator**, then select the **Isaac Sim** category rules. We can then select individual rules to run, but we chose to select all rules for each category.


.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">        
        <div align="center">
        <script src="https://cdnapisec.kaltura.com/p/2935771/sp/293577100/embedIframeJs/uiconf_id/56632652/partner_id/2935771"></script>
        <div id="kaltura_player_1759965147" style="width: 560px; height: 395px;"></div>
        <script>
        kWidget.embed({
          "targetId": "kaltura_player_1759965147",
          "wid": "_2935771",
          "uiconf_id": 56632652,
          "flashvars": {},
          "cache_st": 1759965147,
          "entry_id": "1_ty9ztcof"
        });
        </script>
        </div>
    </div>