.. _tutorial:

********
Tutorial
********

Changing parameters
____________________

Most of the parameters are described through a "params.json" file, that is given as input of the processing pipeline
Some example files are given in the workflow directory

.. code-block:: console

    {
        "my_node":
        {
            "my_val": my_old_val
        }
    }

becomes

.. code-block:: console

    {
        "my_node":
        {
            "my_val": my_new_val
        }
    }

Adding a parameter to a node absent from params.json
___________________________________________________________________

the "old fashioned" way:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

forcing a node input to a value


.. code-block:: python

    my_node = pe.Node(interface=MyInterface(), name="my_node")
    my_node.inputs.my_val = my_new_val

or

.. code-block:: python

    my_node = pe.Node(interface=MyInterface(my_val=my_new_val), name="my_node")

the "semi-dirty" way
~~~~~~~~~~~~~~~~~~~~~

adding to the json:

.. code-block:: console

    {
        "my_node":
        {
            "my_val": my_new_val
        }
    }

(*my_new_val* possibly can be a string -> between "")

and in the code

.. code-block:: python

    my_node = pe.Node(interface=MyInterface(), name = "my_node")

    if "my_node" in params.keys() and "my_val" in params["my_node"]:
        my_node.inputs.my_val = my_new_val

the new way: using NodeParams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*NodeParams* is a class inheriting from pipeline engine Node class, with a method *load_inputs_from_dict* allowing
to load inputs from a dictionnary. It is particularly useful if multiple inputs have to be set for a single node

.. code-block:: python

    from macapype.utils.utils_node import NodeParams

    my_node = NodeParams(interface=MyInterface(), name="my_node")

    if "my_node" in params.keys():
        my_node.load_inputs_from_dict(params["my_node"])

Or even better, using parse_key at the creation of the *NodeParams* and fill the parameter *params*:

.. code-block:: python

    from macapype.utils.utils_node import NodeParams
    from macapype.utils.misc import parse_key

    my_node = NodeParams(interface=MyInterface(),
                         params=parse_key(params, "my_node")
                         name="my_node")

New: multi_params
~~~~~~~~~~~~~~~~~~

Since version 0.1.2, it is possible to add a multi_params json file, containing specific parameter for specific instance of pipelines (e.g., a specific subject or session). The parameter of the params.json will be overloaded for that specific instance if defined in the multi_params.json

To include a parameter specific *my_val* in *my_node* to an instance *sub-001/ses-001*, you have to fill a multi_params.json like this example:

.. code-block:: console

    {
        "sub-001":
        {
            "ses-001":
            {
                "my_node":
                {
                    "my_val": my_new_val
                }
            }
        }
    }

and add the path to the multi_params.json with -multi_params:

.. code-block:: bash

    workflows/segment_pnh.py -data path/to/dataset -out path/to/res -soft ANTS -params path/to/params.json -multi_params path/to/multi_params.json

**N.B.: the sub-pipeline name or incoporated in the params.json (i.e. data_preparation/crop/args), but are dropped in multi_params (only crop/args are specified); this was done because the subpart of the dictionnary can not be passed along with nipype at each step, and would require to specify all the sub-pipeline tree names leading to a node). Thus, be careful with ambiguous node names (same node name in different sub-pipelines)**

Modifying an existing pipeline
________________________________

#TODO

Wrapping new nodes
___________________

#TODO
