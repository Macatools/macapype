

# Equivalent of flirt_average in FSL
def average_align(list_img):

    import os
    import nibabel as nib
    import numpy as np

    from nipype.utils.filemanip import split_filename as split_f
    import nipype.interfaces.fsl as fsl

    print(list_img)

    if isinstance(list_img, list):

        assert len(list_img) > 0, "Error, list should have at least one file"

        if len(list_img) == 1:
            assert os.path.exists(list_img[0])
            av_img_file = list_img[0]
        else:

            img_0 = nib.load(list_img[0])
            path, fname, ext = split_f(list_img[0])

            list_data = [img_0.get_data()]
            for i, img in enumerate(list_img[1:]):

                print("running flirt on {}".format(img))
                flirt = fsl.FLIRT(dof=6)
                flirt.inputs.in_file = img
                flirt.inputs.reference = list_img[0]
                flirt.inputs.interp = "sinc"
                flirt.inputs.no_search = True
                out_file = flirt.run().outputs.out_file
                print(out_file)

                data = nib.load(out_file).get_data()
                list_data.append(data)

            avg_data = np.mean(np.array(list_data), axis=0)
            print(avg_data.shape)

            av_img_file = os.path.abspath("avg_" + fname + ext)
            nib.save(nib.Nifti1Image(avg_data, header=img_0.get_header(),
                                     affine=img_0.get_affine()),
                     av_img_file)

    else:
        assert os.path.exists(list_img)
        av_img_file = list_img

    return av_img_file
