
Example Usage
-------------

Here's a sample tension node in action:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-00-in-action.gif
    :align: center
    :width: 720

In this case, blue is compression, and red is stretching.

How to Use
----------

Enable the `omni.deform.tensionColor`:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-00-ext-name.png
    :align: center
    :width: 300

Select a rest (neutral) mesh. Then select a deforming mesh:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-01-select-prims.png
    :align: center
    :width: 600

Run the *Animation > Deformer > Create Tension Color* command:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-02-command.png
    :align: center
    :width: 300

The tension node with the necessary information will be created:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-03-created-nodes.png
    :align: center
    :width: 600

The tension node will add a *primvars:omni:tensionColor* primvar onto the deforming mesh:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-04-primvar.png
    :align: center
    :width: 600

To access the primvar in materials, add a *Primvar Lookup Color* node in MDL graph:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-05-primvar-lookup.png
    :align: center
    :width: 300

Make sure the primvar name set on the node is *omni:tensionColor*:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-05-primvar-lookup-set.png
    :align: center
    :width: 600

Then use the accessed primvar as color on materials:

.. image:: /images/ext_omnigraph-omni-deform-tensionColor-node-example-06-primvar-lookup-usage.png
    :align: center
    :width: 600