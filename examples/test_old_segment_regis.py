from macapype.pipelines.extract_brain import create_old_segment_extraction_pipe
import os.path as op

if __name__ =='__main__':

    ### main_workflow
    wf = create_old_segment_extraction_pipe()
    wf.base_dir = op.join(op.split(__file__)[0], "../tests/")

    wf.write_graph(graph2use = "colored")
    wf.config['execution'] = {'remove_unnecessary_outputs':'false'}

    wf.inputs.inputnode.T1 = "/hpc/crise/cagna.b/Primavoice/Elouk/sub-Elouk_ses-01_T1w.nii"
    wf.run()
    #wf.run(plugin='MultiProc', plugin_args={'n_procs' : 2})
