FROM ubuntu:18.04

MAINTAINER David Meunier "david.meunier@univ-amu.fr"

RUN apt-get update
RUN apt-get install -y git python3-pip libpng-dev libfreetype6-dev libxft-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libxml2-dev libxslt1-dev wget
#RUN apt-get install -y python3-tk

#RUN apt-get install libx11-6 libxext6 libxt6 # matlab
RUN pip3 install xvfbwrapper psutil numpy scipy matplotlib statsmodels pandas networkx==1.9
RUN pip3 install mock prov click funcsigs pydotplus pydot rdflib pbr nibabel packaging pytest
#nipype==0.12
RUN mkdir -p /root/packages/
########## nipype
RUN pip3 install nipype
#WORKDIR /root/packages/
#RUN git clone https://github.com/davidmeunier79/nipype.git
#WORKDIR /root/packages/nipype
#RUN python3 setup.py develop

# Error with dot packages:
RUN pip3 install graphviz
RUN apt-get -y install graphviz



#--------------------
# Install AFNI latest
#--------------------

#removed installed of python3-tk and tzdata
#
ARG DEBIAN_FRONTEND=noninteractive
#
# ENV PATH=/opt/afni:$PATH
# RUN apt-get update -qq
# RUN apt-get install -yq --no-install-recommends ed gsl-bin libglu1-mesa-dev libglib2.0-0 libglw1-mesa \
#     libgomp1 libjpeg62 libxm4 netpbm tcsh xfonts-base xvfb python python3 python3-pip python3-setuptools python3-tk
# RUN apt-get install -y curl
# RUN libs_path=/usr/lib/x86_64-linux-gnu \
#     && if [ -f $libs_path/libgsl.so.19 ]; then \
#            ln $libs_path/libgsl.so.19 $libs_path/libgsl.so.0; \
#        fi
#
# RUN echo "Install libxp (not in all ubuntu/debian repositories)" \
#     && apt-get install -yq --no-install-recommends libxp6 \
#     || /bin/bash -c " \
#        curl --retry 5 -o /tmp/libxp6.deb -sSL http://mirrors.kernel.org/debian/pool/main/libx/libxp/libxp6_1.0.2-2_amd64.deb \
#        && dpkg -i /tmp/libxp6.deb && rm -f /tmp/libxp6.deb"
#
# RUN echo "Install libpng12 (not in all ubuntu/debian repositories" \
#     && apt-get install -yq --no-install-recommends libpng12-0 \
#     || /bin/bash -c " \
#        curl -o /tmp/libpng12.deb -sSL http://mirrors.kernel.org/debian/pool/main/libp/libpng/libpng12-0_1.2.49-1%2Bdeb7u2_amd64.deb \
#        && dpkg -i /tmp/libpng12.deb && rm -f /tmp/libpng12.deb"
#
# RUN apt-get clean \
#     && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
#     && echo "Downloading AFNI ..." \
#     && mkdir -p /opt/afni \
#     && curl -sSL --retry 5 https://afni.nimh.nih.gov/pub/dist/tgz/linux_openmp_64.tgz \
#     | tar zx -C /opt/afni --strip-components=1 \
#     && pip3 install jinja2 pandas matplotlib

##################################################
# SPM stand alone

# Update system
RUN apt-get -qq update && apt-get -qq install -y \
    unzip \
    xorg \
    wget && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install MATLAB MCR
ENV MATLAB_VERSION R2018b
RUN mkdir /opt/mcr_install && \
    mkdir /opt/mcr && \
    wget -P /opt/mcr_install http://www.mathworks.com/supportfiles/downloads/${MATLAB_VERSION}/deployment_files/${MATLAB_VERSION}/installers/glnxa64/MCR_${MATLAB_VERSION}_glnxa64_installer.zip && \
    unzip -q /opt/mcr_install/MCR_${MATLAB_VERSION}_glnxa64_installer.zip -d /opt/mcr_install && \
    /opt/mcr_install/install -destinationFolder /opt/mcr -agreeToLicense yes -mode silent && \
    rm -rf /opt/mcr_install /tmp/*

# Configure environment
ENV MCR_VERSION v95
ENV LD_LIBRARY_PATH /opt/mcr/${MCR_VERSION}/runtime/glnxa64:/opt/mcr/${MCR_VERSION}/bin/glnxa64:/opt/mcr/${MCR_VERSION}/sys/os/glnxa64:/opt/mcr/${MCR_VERSION}/sys/opengl/lib/glnxa64
ENV MCR_INHIBIT_CTF_LOCK 1

# Install SPM Standalone
ENV SPM_VERSION 12
ENV SPM_REVISION r7487
ENV SPM_DIR /opt/spm${SPM_VERSION}
ENV SPM_EXEC ${SPM_DIR}/spm${SPM_VERSION}
RUN wget -P /opt http://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/spm${SPM_VERSION}_${SPM_REVISION}_Linux_${MATLAB_VERSION}.zip
RUN unzip -q /opt/spm${SPM_VERSION}_${SPM_REVISION}_Linux_${MATLAB_VERSION}.zip -d /opt
RUN rm -f /opt/spm${SPM_VERSION}_${SPM_REVISION}_Linux_${MATLAB_VERSION}.zip
RUN cp /opt/mcr/${MCR_VERSION}/runtime/glnxa64/* /opt/mcr/${MCR_VERSION}/bin/glnxa64
RUN ${SPM_EXEC} function exit
#
# # Configure SPM BIDS App entry point
#COPY run.sh spm_BIDS_App.m pipeline_participant.m pipeline_group.m /opt/spm${SPM_VERSION}/

### error with compiler runtime
#RUN chmod +x /opt/spm${SPM_VERSION}/run.sh
RUN chmod +x /opt/spm${SPM_VERSION}/spm${SPM_VERSION}
RUN chmod +x /opt/spm${SPM_VERSION}/run_spm12.sh

#COPY version /version

#
# ENTRYPOINT ["/opt/spm12/run.sh"]
# #ENTRYPOINT ["/opt/spm12/spm12","script","/opt/spm12/spm_BIDS_App.m"]

############################################### FSL


RUN apt-get update && apt-get install -y wget jq vim

#install neurodebian
RUN wget -O- http://neuro.debian.net/lists/bionic.de-m.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --no-tty --keyserver hkp://pool.sks-keyservers.net:80 --recv-keys 0xA5D32F012649A5A9

#install fsl
RUN apt-get update
RUN apt-get install -y fsl-core
RUN apt-get install -y fsl

ENV FSLDIR=/usr/share/fsl/5.0
ENV PATH=$PATH:$FSLDIR/bin
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0:/usr/share/fsl/5.0/bin

#simulate . ${FSLDIR}/etc/fslconf/fsl.sh
ENV FSLBROWSER=/etc/alternatives/x-www-browser
ENV FSLCLUSTER_MAILOPTS=n
ENV FSLLOCKDIR=
ENV FSLMACHINELIST=
ENV FSLMULTIFILEQUIT=TRUE
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV FSLREMOTECALL=
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish
ENV POSSUMDIR=/usr/share/fsl/5.0

#make it work under singularity
RUN ldconfig && mkdir -p /N/u /N/home /N/dc2 /N/soft

#https://wiki.ubuntu.com/DashAsBinSh
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

############################################# Ants

RUN apt-get install -y ants # python3 python3-pip wget unzip && \

RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ENV ANTSPATH=/usr/lib/ants/
ENV PATH=$ANTSPATH:$PATH

############################################# AFNI

### avec la neurodebian
RUN apt-get install -y afni #
ENV PATH=/usr/lib/afni/bin:$PATH

# ############################################## denoise
# RUN pip3 install cython
# WORKDIR /root/packages/
# ADD https://api.github.com/repos/davidmeunier79/denoise/git/refs/heads/master version.json
# RUN git clone https://github.com/davidmeunier79/denoise.git
# WORKDIR /root/packages/denoise/aonlm
# RUN python3 setup.py install

############################################# install macapype
ADD https://api.github.com/repos/macatools/macapype/git/refs/heads/master version.json
WORKDIR /root/packages/
RUN git clone https://github.com/macatools/macapype.git
WORKDIR /root/packages/macapype
RUN git checkout master
RUN python3 setup.py develop

#####################################################################################################
############################################ extra (exemple of a line to launch) ####################
#####################################################################################################

## pipeline regis
#docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_kepkee.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01

### pipepline kepkee # takes ~ 5 hours to run
# docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/segment_pnh_regis.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01

## test_denoise
# docker run -ti -v ~/Data_maca/Primavoice:/data/macapype macapype python3 /root/packages/macapype/examples/test_denoise.py -data /data/macapype -out /data/macapype -subjects Apache -sess ses-01
