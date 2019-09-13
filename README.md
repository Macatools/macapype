# Resources & Dependencies

## Documents
[Segmentation Tools For Monkey Brains](https://docs.google.com/document/d/11zeyjY46AsLZcf-Y5Q_LjIoE_aYkN8DaLwZIElF2ctE/edit)

## Image & Templates

To run examples, you will need to download and unzip this file:
[Example Resources](https://intcloud.intlocal.univ-amu.fr/index.php/s/8bCJ5CWWPfHRyHs)


# How to install

$ git clone https://framagit.org/mars-hackat2019/anat-mri-pipeline/pipeline-anat-macaque.git
$ cd pipeline-anat-macaque  
$ python setup.py develop  
OR if you do not have sudo access:  
$ python setup.py develop --user  

$ git remote add public git@framagit.org:mars-hackat2019/anat-mri-pipeline/macapype.git

# How to run examples
python examples/segment_pnh_regis.py -data /hpc/crise/cagna.b/Prima  -resources /hpc/crise/cagna.b/Primavoice  -out ./local_test_cropped -subjects Elouk



