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

FROM debian:buster

USER root

ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8" \
    ND_ENTRYPOINT="/neurodocker/startup.sh"
RUN export ND_ENTRYPOINT="/neurodocker/startup.sh" \
    && apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           apt-utils \
           bzip2 \
           ca-certificates \
           curl \
           locales \
           unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG="en_US.UTF-8" \
    && chmod 777 /opt && chmod a+s /opt \
    && mkdir -p /neurodocker \
    && if [ ! -f "$ND_ENTRYPOINT" ]; then \
         echo '#!/usr/bin/env bash' >> "$ND_ENTRYPOINT" \
    &&   echo 'set -e' >> "$ND_ENTRYPOINT" \
    &&   echo 'export USER="${USER:=`whoami`}"' >> "$ND_ENTRYPOINT" \
    &&   echo 'if [ -n "$1" ]; then "$@"; else /usr/bin/env bash; fi' >> "$ND_ENTRYPOINT"; \
    fi \
    && chmod -R 777 /neurodocker && chmod a+s /neurodocker

ENTRYPOINT ["/neurodocker/startup.sh"]

ENV FSLDIR="/opt/fsl-5.0.10" \
    PATH="/opt/fsl-5.0.10/bin:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLTCLSH="/opt/fsl-5.0.10/bin/fsltclsh" \
    FSLWISH="/opt/fsl-5.0.10/bin/fslwish" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           dc \
           file \
           libfontconfig1 \
           libfreetype6 \
           libgl1-mesa-dev \
           libgl1-mesa-dri \
           libglu1-mesa-dev \
           libgomp1 \
           libice6 \
           libxcursor1 \
           libxft2 \
           libxinerama1 \
           libxrandr2 \
           libxrender1 \
           libxt6 \
           sudo \
           wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FSL ..." \
    && mkdir -p /opt/fsl-5.0.10 \
    && curl -fsSL --retry 5 https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-5.0.10-centos6_64.tar.gz \
    | tar -xz -C /opt/fsl-5.0.10 --strip-components 1 \
    && sed -i '$iecho Some packages in this Docker container are non-free' $ND_ENTRYPOINT \
    && sed -i '$iecho If you are considering commercial use of this container, please consult the relevant license:' $ND_ENTRYPOINT \
    && sed -i '$iecho https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Licence' $ND_ENTRYPOINT \
    && sed -i '$isource $FSLDIR/etc/fslconf/fsl.sh' $ND_ENTRYPOINT \
    && echo "Installing FSL conda environment ..." \
    && bash /opt/fsl-5.0.10/etc/fslconf/fslpython_install.sh -f /opt/fsl-5.0.10

ENV PATH="/opt/afni-latest:$PATH" \
    AFNI_PLUGINPATH="/opt/afni-latest"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           ed \
           gsl-bin \
           libglib2.0-0 \
           libglu1-mesa-dev \
           libglw1-mesa \
           libgomp1 \
           libjpeg62 \
           libxm4 \
           multiarch-support \
           netpbm \
           tcsh \
           xfonts-base \
           xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL --retry 5 -o /tmp/toinstall.deb http://mirrors.kernel.org/debian/pool/main/libx/libxp/libxp6_1.0.2-2_amd64.deb \
    && dpkg -i /tmp/toinstall.deb \
    && rm /tmp/toinstall.deb \
    && curl -sSL --retry 5 -o /tmp/toinstall.deb http://snapshot.debian.org/archive/debian-security/20160113T213056Z/pool/updates/main/libp/libpng/libpng12-0_1.2.49-1%2Bdeb7u2_amd64.deb \
    && dpkg -i /tmp/toinstall.deb \
    && rm /tmp/toinstall.deb \
    && apt-get install -f \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && gsl2_path="$(find / -name 'libgsl.so.19' || printf '')" \
    && if [ -n "$gsl2_path" ]; then \
         ln -sfv "$gsl2_path" "$(dirname $gsl2_path)/libgsl.so.0"; \
    fi \
    && ldconfig \
    && echo "Downloading AFNI ..." \
    && mkdir -p /opt/afni-latest \
    && curl -fsSL --retry 5 https://afni.nimh.nih.gov/pub/dist/tgz/linux_openmp_64.tgz \
    | tar -xz -C /opt/afni-latest --strip-components 1

ENV ANTSPATH="/opt/ants-2.3.1" \
    PATH="/opt/ants-2.3.1:$PATH"
RUN echo "Downloading ANTs ..." \
    && mkdir -p /opt/ants-2.3.1 \
    && curl -fsSL --retry 5 https://dl.dropbox.com/s/1xfhydsf4t4qoxg/ants-Linux-centos6_x86_64-v2.3.1.tar.gz \
    | tar -xz -C /opt/ants-2.3.1 --strip-components 1

RUN echo '{ \
    \n  "pkg_manager": "apt", \
    \n  "instructions": [ \
    \n    [ \
    \n      "base", \
    \n      "debian:buster" \
    \n    ], \
    \n    [ \
    \n      "ants", \
    \n      { \
    \n        "version": "2.3.1" \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "fsl", \
    \n      { \
    \n        "version": "5.0.10" \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "afni", \
    \n      { \
    \n        "version": "latest" \
    \n      } \
    \n    ], \
    \n    [ \
    \n      "ants", \
    \n      { \
    \n        "version": "2.3.1" \
    \n      } \
    \n    ] \
    \n  ] \
    \n}' > /neurodocker/neurodocker_specs.json

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ca-certificates cmake gcc g++ git make \
    && git clone https://github.com/KCL-BMEIS/niftyreg.git /tmp/niftyreg-src \
    && mkdir /tmp/niftyreg-build \
    && cd /tmp/niftyreg-build \
    && cmake -DCMAKE_INSTALL_PREFIX=/opt/niftyreg /tmp/niftyreg-src \
    && make \
    && make install
ENV PATH=/opt/niftyreg/bin:$PATH

MAINTAINER David Meunier "david.meunier@univ-amu.fr"
######################## Python packages

RUN apt-get update && apt-get install -y git python3-pip libpng-dev libfreetype6-dev libxft-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libxml2-dev libxslt1-dev wget graphviz

RUN apt-get install -y python3-pil python3-pil.imagetk


RUN python3 -m pip install -U pip
RUN python3 -m pip install -U pillow
#RUN pip3 install pillow

#RUN apt-get install libx11-6 libxext6 libxt6 # matlab
RUN pip3 install xvfbwrapper \
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
#
# RUN mkdir -p /opt/packages/
#
# ADD https://api.github.com/repos/macatools/macapype/git/refs/heads/master version.json
# WORKDIR /opt/packages/
#
# RUN git clone https://github.com/macatools/macapype.git
# WORKDIR /opt/packages/macapype
#
# RUN git checkout master
# RUN python3 setup.py develop

RUN echo $(which python) && \
    echo $(which python3) && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip

RUN  pip install --pre macapype && python -c "import macapype; print(macapype.__version__)"

#####################################################################################################
############################################ extra (exemple of a line to launch) ####################
#####################################################################################################

# using docker image on DockerHub
# docker pull macatools/macapype:latest

# docker run -ti -v /home/INT/meunier.d/Data/Data-Hackaton/Data_CIRMf_INT/PRIME-DE/site-amu:/data/macapype macatools/macapype:latest python /root/packages/macapype/workflows/segment_multi_pnh_ants_based.py -data /data/macapype -out /data/macapype -params /root/packages/macapype/workflows/params_segment_pnh_ants_based_crop.json

# Building your image from the Dockerfile
# docker built -t macapype_docker

# docker run -ti -v /home/INT/meunier.d/Data/Data-Hackaton/Data_CIRMf_INT/PRIME-DE/site-amu:/data/macapype macapype_docker python /root/packages/macapype/workflows/segment_multi_pnh_ants_based.py -data /data/macapype -out /data/macapype -params /root/packages/macapype/workflows/params_segment_pnh_ants_based_crop.json


