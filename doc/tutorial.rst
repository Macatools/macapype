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

    my_node = pe.Node(interface = MyInterface(), name = "my_node")
    my_node.inputs.my_val = my_new_val

or

.. code-block:: python

    my_node = pe.Node(interface = MyInterface(my_val=my_new_val), name = "my_node")

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

(my_new_val possibly can be a string -> between "")

and in the code

.. code-block:: python

    my_node = pe.Node(interface = MyInterface(), name = "my_node")

    if "my_node" in params.keys() and "my_val" in params["my_node"]:
        my_node.inputs.my_val = my_new_val

the new way: using NodeParams
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Node params is a class inheriting from pipeline engine Node class, with a method load_inputs_from_dict allowing
to load inputs from a dictionnary. It is particularly useful if multiple inputs have to be set for a single node

.. code-block:: python

    from macapype.utils.utils_node import NodeParams

    my_node = NodeParams(interface = MyInterface(), name = "my_node")

    if "my_node" in params.keys():
        my_node.load_inputs_from_dict(params["my_node"])


Modifying an existing pipeline
________________________________

#TODO

Wrapping new nodes
___________________

#TODO
