
def apply_atlasBREX(t1_restored_file):
    """
    Wrap of atlasBREX_fslfrioul.sh, the dirty way...
    """
    import os
    import shutil

    from nipype.utils.filemanip import split_filename as split_f

    cur_dir = os.path.abspath("")
    print cur_dir

    script_dir = "/hpc/meca/users/loh.k/macaque_preprocessing/preproc_cloud/processing_scripts/"
    script_atlas_BREX = os.path.join(script_dir,"atlasBREX_fslfrioul.sh")
    shutil.copy(script_atlas_BREX,cur_dir)

    ### all files need to be copied in cur_dir
    nmt_dir="/hpc/meca/users/loh.k/macaque_preprocessing/NMT_v1.2/"
    nmt_file = os.path.join(nmt_dir,"NMT.nii.gz")
    shutil.copy(nmt_file,cur_dir)

    nmt_ss_file = os.path.join(nmt_dir,"NMT_SS.nii.gz")
    shutil.copy(nmt_ss_file,cur_dir)

    path, fname, ext = split_f(t1_restored_file)
    print(path, fname, ext)
    shutil.copy(t1_restored_file,cur_dir)


    ## just to be sure...
    os.chdir(cur_dir)

    if ext == ".nii":
        print("zipping {} as expected by atlas_brex".format(t1_restored_file))
        os.system("gzip {}".format(fname+ ext))
        ext = ".nii.gz"

    os.system("bash {} -b {} -nb {} -h {} -f 0.5 -reg 1 -w 10,10,10 -msk a,0,0".format("atlasBREX_fslfrioul.sh", "NMT_SS.nii.gz", "NMT.nii.gz", fname + ext))

    ##get mask filename
    brain_file=os.path.abspath(fname + "_brain" + ext)

    return brain_file
