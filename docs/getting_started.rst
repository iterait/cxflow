Getting Started
###############

Before we dive in, cxflow has to be installed properly.

Requirements
************
In order to run and install cxflow, the following utilities must be installed:

- Python 3.5+
- ``pip`` 9.0+

Cxflow depends on additional dependencies which are listed in the ``requirements.txt`` file.
Nevertheless, these dependencies are automatically installed by ``pip`` (see below).

Installation
************

The simplest way of installing cxflow is using pip.
This is the recommended option for majority of users.

.. code-block:: bash

    pip install cxflow

Optionally, install additional plugins by installing ``cxflow-<plugin-name>``.
TensorFlow backend for cxflow can be installed by:

.. code-block:: bash

    pip install cxflow-tensorflow

In order to use cxflow nightly builds, install it directly from the source code 
repository (``dev`` branch).

.. code-block:: bash

    pip install -U git+https://github.com/iterait/cxflow.git@dev

Developer Installation
**********************

Finally, cxflow might be installed directly for development purposes.

.. code-block:: bash

    git clone git@github.com:iterait/cxflow.git
    cd cxflow
    pip install -e .

The cxflow test suite can be executed by running the following command in the 
cloned repository:

.. code-block:: bash

    python setup.py test
