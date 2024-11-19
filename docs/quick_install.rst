:orphan:

.. _quick_install:

************
Installation
************

Dependancies
############

External software dependancies
------------------------------

SkullTo3d relies heavily on other neuroimaging Softwares, predominentyly:

* `FSL <http://www.fmrib.ox.ac.uk/fsl/index.html>`_
* `ANTS <http://stnava.github.io/ANTs/>`_
* `AFNI <https://afni.nimh.nih.gov/>`_
* `SPM <https://www.fil.ion.ucl.ac.uk/spm/>`_

Python packages dependancies
----------------------------

SkullTo3d relies on python packages. Here we provide installations using Anaconda

Creating environment with all packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you have access to a conda environment, here is the procedure to initialize your own environnment (called "skullTo3d", but can be called the name you prefer):

.. code-block:: bash

    $ conda init bash
    $ conda create -n skullTo3d_env python=3.7
    $ conda activate skullTo3d_env

Install skullTo3d package
########################

from github
-----------

.. _git_install:

Using git
~~~~~~~~~

.. code:: bash

    $ git clone https://github.com/Macatools/skullTo3d.git
    $ cd skullTo3d
    $ python setup.py develop --user

Using pip
~~~~~~~~~

.. code:: bash

    $ pip install git+https://github.com/Macatools/skullTo3d

.. _pip_install:

from pypi
---------

SkullTo3d is available on * `pypi.org <https://pypi.org/project/skullTo3d/>`_:

If 'pip' package is installed on your system, you can install the lastest stable version with:

.. code:: bash

    $ pip install skullTo3d


From conda
-----------

SkullTo3d is also available on `Anaconda cloud <https://anaconda.org/macatools/skullTo3d>`_:

If 'conda' (Anaconda, or miniconda) is installed on your system, you can type:

.. code:: bash

    $ conda install -c macatools skullTo3d

!!!! The lastest version of skullTo3d (0.2.1) is not available, due to the inclusion of packages that are not yet packaged in conda
use "pip install skullTo3d" or "git clone https://github.com/Macatools/skullTo3d.git" till further notice

Testing the install
###################


.. code:: bash

    $ ipython

.. code:: ipython

    In [1]: import skullTo3d; print (skullTo3d.__version__)
