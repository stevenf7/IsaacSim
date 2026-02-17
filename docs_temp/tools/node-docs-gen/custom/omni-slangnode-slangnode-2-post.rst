.. _slang:

What is Slang
##########################

Slang is a shading language backward compatible with HLSL that makes it easier to build and maintain large shader codebases in a modular and extensible fashion, while also maintaining the highest possible performance on modern GPUs and graphics APIs. Slang is based on years of collaboration between researchers at NVIDIA, Carnegie Mellon University, and Stanford.

For better understanding of language usage and features, please refer to the `User's Guide <https://shader-slang.com/slang/user-guide/index.html>`_ provided by Slang developers.

When should I use Slang Node
#################################

The node allows users to write their own functions executed in OmniGraph. Slang code is compiled once during the stage load or on user request in the Code Editor. The node execution does not bring any additional overhead during the OmniGraph updates.

The current implementation only runs the Slang code single-threaded on the CPU target. Multithreaded and GPU support will be added in future releases.

How to use Slang node in OmniGraph
---------------------------------------

.. _video_tutorial:

Video Tutorial
##########################

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_1" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_1",
            provider:
            { partnerId: 2935771, uiConfId: 46302491 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_et8g7041'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

The example code from the tutorial is listed :ref:`here <demo_code>`.

Slang Function
##############

When you use Slang Node in a :term:`Push Graph`, it only has the :ref:`Code<code>` token and :ref:`Instance count<instance_count>` input attributes. When you use it in an :term:`Action Graph`, it also has **Exec In** and **Exec Out** pins. You can preview the Slang function's code in the *Slang Code Editor* by clicking **Edit** in the node's Property window next to the **Code** attribute. You can add or remove node attributes for variables used in the function by clicking the dedicated buttons in the *Add and Remove Attributes* section in the top part of the Property window.

.. image:: /images/omnigraph_slang_action_graph_node.png
	:align: center
	:alt: Action Graph Node

.. _code:

Code
^^^^^^^^^^^^^^^^^^^^^

The code attribute should always contain at least an empty ``compute`` function.

.. code-block:: hlsl
    :linenos:

    void compute(uint instanceId)
    {
    }

.. important::

    Defining non-static global variables in a Slang function is not allowed. You must create a node attribute to declare a resource buffer.

.. _instance_count:

Instance Count
^^^^^^^^^^^^^^^^^^^^^

Slang node's **Instance count** attribute input specifies how many times the function will be executed and the size of an output array. The ``uint instanceId`` parameter of the main `compute` function then defines the position in the output array where the computed result can be stored (an :ref:`example <arrays_code>` of the usage).

.. important::

    Arrays are zero-indexed bounds checked which means, if an access to array is out of bounds, the value at the zero index is returned. An empty array thus always contains at least one element with a zero value by default.

Node Attributes
^^^^^^^^^^^^^^^

User-added node attributes can be used in a Slang function as variables. The attribute types are *input*, *output*, and *state*. Input attributes are read-only. Output and state can be accessed for both reads and writes. You can find a conversion table between OGN, USD, and Slang data types `here <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/flow-usd/104.1/source/extensions/omni.slangnode/docs/types.html>`__.

.. image:: /images/omnigraph_slang_create_attribute.png
	:align: center
	:alt: Create Attribute

---------------------------------------------------------------------------------------

    To create a node from the demo scene shown in the :ref:`tutorial video <video_tutorial>`, follow the next steps:

    1. Drop a node called **Slang Function** in the Action Graph
    2. In the Property window of the node, click *Add* button
    3. Create **input** attribute of type `double` and name it `time`
    4. Create **output** attribute of type `double3` and name it `position`
    5. Continue with opening the Slang Code Editor

---------------------------------------------------------------------------------------

.. _code_editor:

Slang Code Editor
##################

To use the node's attribute as a variable in the code, the attribute name has to be adjusted by a simple pattern. Please refer to the *Variables from Attributes Syntax* section to see examples of this pattern.

.. image:: /images/omnigraph_slang_code_editor.png
	:align: center
	:alt: Code Editor

.. _demo_code:

An example of a compute function from the :ref:`tutorial <video_tutorial>` can be copy pasted into the editor and compiled by hitting **Save & Compile**. The green tick next to the button indicates that the compilation was successful. Any errors, in case of failed compilation, are displayed in the Console window and a red cross appears next to the compile button. Handling compilation errors is described :ref:`further <compilation_error>` in the text.

.. code-block:: hlsl
    :linenos:
    :emphasize-lines: 3-14

    void compute(uint instanceId)
    {
        double time = inputs_time_get();

        double k = 0.1f;
        double r = 100.f # 10.f * sin(time);
        double x = 100.f * sin(k * time);
        double y = 100.f * cos(k * time);

        double3 pos = double(x, 50.f, y);

        outputs_position_set(pos);

        outputs_execOut_set(EXEC_OUT_ENABLED);
    }

Slang Settings
^^^^^^^^^^^^^^^^^^^^^

    * **Use Slang LLVM**

        Slang code is compiled by `Slang LLVM compiler <https://github.com/shader-slang/slang-llvm>`_. The library is included in the extension and the compiler is used to compile Slang code by default. When turned off in *Slang Settings*, Slang looks for a default system C## compiler.

    * **Multithreaded Compilation**

        Each node would be compiled on a single thread to accelerate the initialization of multiple Slang nodes in the Stage during the scene load. This is only relevant when Slang LLVM is off.

    * **Show Generated Code**

        This toggle shows a separate editor tab after switching to *Generated Slang Code* where the user can preview what functions are auto-generated from the node's attribute before the actual code compilation is run.

        .. image:: /images/omnigraph_slang_generated_code.png
            :align: center
            :alt: Generated Code

        .. _compilation_error:

        Also, when a compilation error occurs, the line number refers to a position in the generated code not in the *Compute Function* tab.

        .. image:: /images/omnigraph_slang_generated_code_error.png
            :align: center
            :alt: Generated Code Error

The code can be edited and compiled even while the OmniGraph is running. The Slang node won't be updated and does not output any data in case of failed compilation.

Slang Function Examples
############################

    * *Reading and writing arrays*

        .. _arrays_code:

        .. code-block:: hlsl
            :linenos:

            void compute(uint instanceId)
            {
                float3 pos = inputs_pointsIn_get(instanceId);

                float time = float(inputs_time_get());

                pos.x #= 10.f * cos(time);
                pos.z #= 10.f * sin(time);

                outputs_pointsOut_set(instanceId, pos);

                outputs_execOut_set(EXEC_OUT_ENABLED);
            }
