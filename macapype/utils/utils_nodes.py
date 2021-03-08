from nipype.pipeline.engine import Node, MapNode
from nipype.interfaces.io import BIDSDataGrabber
from .misc import parse_key

from nipype.interfaces.base import (TraitedSpec, traits, BaseInterface,
                                    BaseInterfaceInputSpec)


def node_output_exists(node, output_name):
    return hasattr(node.outputs, output_name)


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
            print("\n**** setting indiv_params for {} ****".format(self.name))
            print(val, "\n")
            self.load_inputs_from_dict(val)
        else:
            super(NodeParams, self).set_input(parameter=parameter, val=val)


class MapNodeParams(MapNode):

    """
    Overloading of the class nodes for aloowing params reading directly from
    a dictionnary; ultimately should be added to nipype if required
    """
    def __init__(
            self,
            interface,
            name,
            iterfield,
            params={}):

        iterfield.extend(list(params.keys()))
        super(MapNodeParams, self).__init__(interface=interface, name=name,
                                            iterfield=iterfield)

        self.load_inputs_from_dict(params)

    def load_inputs_from_dict(self, params, overwrite=True):

        def_inputs = []
        if not overwrite:
            def_inputs = list(self.inputs.get_traitsfree().keys())

        new_inputs = list(set(list(params.keys())) - set(def_inputs))

        for key in new_inputs:
            assert hasattr(self.inputs, key), \
                print("Warning, Could not find {} in inputs {} for node {}".
                      format(key, self._interface.inputs, self._name))
            setattr(self.inputs, key, params[key])

    def _check_inputs(self, parameter):
        if parameter == "indiv_params":
            print("**** checking for indiv_params****")
            return True
        else:
            return super(MapNodeParams, self)._check_inputs(
                parameter=parameter)

    def set_input(self, parameter, val):
        if parameter == "indiv_params":
            print("**** setting indiv_params****")
            print(val)
            self.load_inputs_from_dict(val)
        else:
            super(MapNodeParams, self).set_input(parameter=parameter, val=val)


class BIDSDataGrabberParams(BIDSDataGrabber):
    def __init__(self, indiv_params={}, **kwargs):
        super(BIDSDataGrabberParams, self).__init__(**kwargs)
        self._indiv_params = indiv_params

    def _set_indiv_params(self, outputs):

        assert "subject" in self._infields and "session" in self._infields, \
            "Error, subject and session should be defined as iterables"

        keys = ("sub-" + getattr(self.inputs, "subject"),
                "ses-" + getattr(self.inputs, "session"))
        outputs["indiv_params"] = parse_key(self._indiv_params, keys)

        return outputs

    def _list_outputs(self):
        outputs = super(BIDSDataGrabberParams, self)._list_outputs()
        outputs = self._set_indiv_params(outputs)

        return outputs


###############################################################################
class ParseParamsInputSpec(BaseInterfaceInputSpec):

    params = traits.Dict(
        desc='Dictionnary to tap from')

    key = traits.Either(
        traits.String(),
        traits.Tuple(),
        desc='which key to tap from')


class ParseParamsOutputSpec(TraitedSpec):

    parsed_params = traits.Dict(
        desc="Part of the dict with key"
    )


class ParseParams(BaseInterface):
    """from a dict, give a sub dict corresponding to key

    Inputs
    --------
    params:
    Dict, 'Dictionnary to tap from')

    key:
    Tuple of String, 'which key to tap from')



    Outputs
    ---------
    parsed_params = traits.Dict(
        desc="Part of the dict with key"

    """
    input_spec = ParseParamsInputSpec
    output_spec = ParseParamsOutputSpec

    def _run_interface(self, runtime):

        params = self.inputs.params
        key = self.inputs.key

        self.parsed_params = parse_key(params, key)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["parsed_params"] = self.parsed_params

        return outputs
