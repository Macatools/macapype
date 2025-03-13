:orphan:

.. _quick_install:

************
Installation
************

Dependancies
############

External software dependancies
------------------------------

Macapype relies heavily on other neuroimaging Softwares, predominentyly:

* `FSL <http://www.fmrib.ox.ac.uk/fsl/index.html>`_
* `ANTS <http://stnava.github.io/ANTs/>`_
* `AFNI <https://afni.nimh.nih.gov/>`_
* `SPM <https://www.fil.ion.ucl.ac.uk/spm/>`_
* `NiftiReg <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftyReg>`_

Python packages dependancies
----------------------------

Macapype relies on python packages. Here we provide installations using Anaconda

Creating environment with all packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you have access to a conda environment, here is the procedure to initialize your own environnment (called "macapype", but can be called the name you prefer):

.. code-block:: bash

    $ conda init bash
    $ conda create -n macapype_env python=3.10
    $ conda activate macapype_env

Install macapype package
########################

from github
-----------

.. _git_install:

Using git
~~~~~~~~~

.. code:: bash

    $ git clone https://github.com/Macatools/macapype.git
    $ cd macapype
    $ python setup.py develop --user

Using pip
~~~~~~~~~

.. code:: bash

    $ pip install git+https://github.com/Macatools/macapype

.. _pip_install:

from pypi
---------

Macapype is available on * `pypi.org <https://pypi.org/project/macapype/>`_:

If 'pip' package is installed on your system, you can install the lastest stable version with:

.. code:: bash

    $ pip install macapype


From conda
-----------

Macapype is also available on `Anaconda cloud <https://anaconda.org/macatools/macapype>`_:

If 'conda' (Anaconda, or miniconda) is installed on your system, you can type:

.. code:: bash

    $ conda install -c macatools macapype

!!!! The latest versions of macapype (from > 0.2.1) are not available, due to the inclusion of packages that are not yet packaged in conda
use "pip install macapype" or "git clone https://github.com/Macatools/macapype.git" till further notice

Testing the install
###################


.. code:: bash

    $ ipython

.. code:: ipython

    In [1]: import macapype; print (macapype.__version__)


See :ref:`Quick test <quick_test>` for testing if your installation works properly on test datasets.
