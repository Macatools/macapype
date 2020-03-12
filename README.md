# Resources & Dependencies

## Documents
[Segmentation Tools For Monkey Brains](https://docs.google.com/document/d/11zeyjY46AsLZcf-Y5Q_LjIoE_aYkN8DaLwZIElF2ctE/edit)

## Image & Templates

To run examples, you will need to download and unzip this file:
[Example Resources](https://cloud.int.univ-amu.fr/index.php/s/8bCJ5CWWPfHRyHs)


# How to install

$ git clone git@github.com:davidmeunier79/macapype.git/
OR
$ git clone https://github.com/Macatools/macapype.git

$ cd macapype  

$ python setup.py develop  
OR if you do not have sudo access:  
$ python setup.py develop --user  

# How to run examples

Following the BIDS format:  

$ python examples/segment_pnh_regis.py -data /hpc/crise/cagna.b/Prima -out ./local_test_cropped -subjects Elouk -sess 01  
$ python examples/segment_pnh_regis.py -data /hpc/crise/cagna.b/Prima -out ./local_test_cropped -subjects Elouk  

Will find the corresponding data if follows BIDS :  
$ python examples/segment_pnh_regis.py -data /hpc/crise/cagna.b/Prima -out ./local_test_cropped  
-- Warning-- cropped data should be used for more efficient processing  
-- Warning-- cropped data should also be saved as 'T1w.nii' instead of 'T1wCropped.nii'  

$ python examples/segment_pnh_kepkee.py -data /hpc/crise/cagna.b/Prima -out ./local_test_cropped -cropped True  
-- Warning-- cropped data should be used for more efficient processing  
-- Warning-- cropped T1 should also be saved as 'T1w.nii' instead of 'T1wCropped.nii'  
-- Warning-- cropped T2 should also be saved as 'T2w.nii' instead of 'T2wRegT1wCropped.nii'  

if already cropped, or no cropbox is provided:
python segment_pnh_kepkee.py -data /hpc/meca/data/Macaques/Macaque_hiphop/sbri/ -out /hpc/crise/meunier.d/Data/ -subjects 032311 -ses ses-001

Add the -crop_req if cropping is required, and .cropbox is provided

# TODO : follow the same syntax for datagrabber with pybids or not

# docker

In the directory where the Dockerfile is located:  
$ docker build -t macapype .  

Example of pipelines:  
$ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_regis.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01  
$ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_kepkee.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01  
$ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_regis.py -data /data/macapype -out /data/macapype  
$ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_kepkee.py -data /data/macapype -out /data/macapype -cropped True  

# docker pull

Can also be downloaded directly from DockerHub repo:
$ docker pull macatools/macapype
$ docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macatools/macapype:latest python3 /root/packages/macapype/examples/segment_pnh_regis.py -data /data/macapype -out /data/macapype
