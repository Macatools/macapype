from nipype.pipeline.engine import Node
from nipype.interfaces.io import BIDSDataGrabber
from .misc import parse_key


class NodeParams(Node):

    """
    Overloading of the class nodes for aloowing params reading directly from
    a dictionnary; ultimately should be added to nipype if required
    """
    def __init__(
            self,
            interface,
            name,
            params={}):

        super(NodeParams, self).__init__(interface=interface, name=name)

        self.load_inputs_from_dict(params)

    def load_inputs_from_dict(self, params, overwrite=True):

        def_inputs = []
        if not overwrite:
            def_inputs = list(self.inputs.get_traitsfree().keys())

        new_inputs = list(set(list(params.keys())) - set(def_inputs))

        for key in new_inputs:
            assert hasattr(self._interface.inputs, key), \
                print("Warning, Could not find {} in inputs {} for node {}".
                      format(key, self._interface.inputs, self._name))
            setattr(self._interface.inputs, key, params[key])

    def _check_inputs(self, parameter):
        if parameter == "indiv_params":
            print("**** checking for indiv_params****")
            return True
        else:
            return super(NodeParams, self)._check_inputs(parameter=parameter)

    def set_input(self, parameter, val):
        if parameter == "indiv_params":
            print("**** setting indiv_params****")
            print(val)
            self.load_inputs_from_dict(val)
        else:
            super(NodeParams, self).set_input(parameter=parameter, val=val)


class BIDSDataGrabberParams(BIDSDataGrabber):
    def __init__(self, params={}, **kwargs):
        super(BIDSDataGrabberParams, self).__init__(**kwargs)
        self._params = params

    def _set_indiv_params(self, outputs):

        assert "subject" in self._infields and "session" in self._infields, \
            "Error, subject and session should be defined as iterables"

        keys = ("sub-" + getattr(self.inputs, "subject"),
                "ses-" + getattr(self.inputs, "session"))
        outputs["indiv_params"] = parse_key(self._params, keys)

        return outputs

    def _list_outputs(self):
        outputs = super(BIDSDataGrabberParams, self)._list_outputs()
        outputs = self._set_indiv_params(outputs)

        return outputs

def output_exists(node, output_name):
    print (node.outputs)
    if output_name in node.outputs:

        print("found {} in {}".format(output_name, node))

    0/0
