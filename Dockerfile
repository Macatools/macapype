# Generated by: Neurodocker version 0.7.0+15.ga4940e3.dirty
# Latest release: Neurodocker version 0.7.0
#
# Thank you for using Neurodocker. If you discover any issues
# or ways to improve this software, please submit an issue or
# pull request on our GitHub repository:
#
#     https://github.com/ReproNim/neurodocker
#
# Timestamp: 2020/12/02 18:33:44 UTC

FROM macatools/macapype_env:v0.2-spm

USER root

ARG DEBIAN_FRONTEND="noninteractive"

MAINTAINER David Meunier "david.meunier@univ-amu.fr"
######################## Python packages

RUN apt-get update && apt-get install -y git libpng-dev libfreetype6-dev libxft-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libxml2-dev libxslt1-dev wget graphviz

RUN apt-get install -y python3-pil python3-pil.imagetk


RUN python -m pip install -U pillow
#RUN pip3 install pillow

#RUN apt-get install libx11-6 libxext6 libxt6 # matlab
RUN pip install xvfbwrapper \
    psutil \
    numpy \
    scipy \
    matplotlib \
    statsmodels \
    pandas \
    networkx\
    mock \
    prov \
    click \
    funcsigs \
    pydotplus \
    pydot \
    rdflib \
    pbr \
    nibabel==3.2.2 \
    packaging \
    pytest \
    install \
    graphviz \
    pybids \
    nipype \
    nilearn \
    scikit-image \
    brain-slam

############################################# install macapype

RUN  pip install --pre macapype && python -c "import macapype; print(macapype.__version__)"

################################################## Finishing
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN rm -rf \
     /tmp/hsperfdata* \
     /var/*/apt/*/partial \
     /var/log/apt/term*
