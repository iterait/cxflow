Dataset
*******

Dataset is the essential component of every machine learning problem. In fact, the dataset is often the problem itself.
Regardless of sizes, complexities and formats, all datasets are beautiful. At some point, though, we need to
iterate through the data points or *examples* if you wish.

As a matter of fact, the ability of providing example iterators is the only requirement from **cxflow** on datasets.
A dataset used for training has to implement a ``train_stream`` method and similarly
the dataset has to implement ``predict_stream`` when used for prediction later.

To make a dataset compatible with **cxflow** one must implement a class which complies
to the :py:class:`cxflow.datasets.AbstractDataset` concept.
With that, **cxflow** can create and manage the dataset for you.

To use the dataset in training, specify its fully-qualified name in ``dataset`` section of **cxflow** configuration
file. See the `configuration section <config.html>`_ for more information.

.. note::
    **cxflow** datasets are configured from **cxflow** configuration files. When creating a dataset,
    **cxflow** encodes the parameters as YAML string in order to ease interoperability in the case the dataset is
    implemented in a different language such as in c++.

BaseDataset
-----------

To write your very first dataset in python, we recommend to inherit from :py:class:`cxflow.datasets.BaseDataset`
as it parses the YAML string automatically. Parsed arguments are passed to the
:py:meth:`cxflow.datasets.BaseDataset._configure_dataset` which is required from you implementation.

To give an example, we ll write a skeleton of ``MyDataset`` in ``datasets.my_dataset.py``:

.. code-block:: python
    :caption: ``datasets.my_dataset.py``

     from cxflow import BaseDataset

     class MyDataset(BaseDataset):
         def _configure_dataset(batch_size: int, augment: dict, **kwargs):
           # ...

This class requires two arguments, ``batch_size`` and ``augment``. Any other argument
is ignored and hidden in the ``**kwargs``.

Next, we define the ``dataset`` section in the config file:

.. code-block:: yaml
    :caption: example usage of ``MyDataset`` in **cxflow** configuration

    dataset:
      class: datasets.MyDataset
      batch_size: 16
      augment:
        rotate: true     # enable random rotations
        blur_prob: 0.05  # probability of blurring

Now given this configuration, **cxflow** can find, create and configure new ``MyDataset`` instance seamlessly.

Data Streams
------------

In most cases, datasets are quite large and can not be fed to the model as whole. For this reason, **cxflow** operates
with streams of so called *mini-batches*, i.e. small portions of the dataset.
In particular, **cxflow** works with data on the following levels:

- **stream** in an iterable of *batches* (:py:attr:`cxflow.Stream`)
- **batch** is a dictionary of *stream sources* (:py:attr:`cxflow.BatchData`)
- **stream source** is a list of example *fields*

For instance, imagine you are classifying images of animals.
An *example* in this case would be a tuple of two fields, *image* and *label*.

Now, the *stream* would yield *batches* with *image* and *label* stream sources similar to this one:

.. code-block:: python
    :caption: *batch* example

    {
      'image': [img1, img2, img3, img4],
      'label': ['cat', 'cat', 'dog', 'rabbit']
    }

Implementing a ``<name>_stream`` method which returns *stream* iterator allows **cxflow** to use the respective *stream*.

When training, **cxflow** requires the train *stream* to be provided by ``train_stream`` method similar to the following one:

.. code-block:: python
    :caption: ``train_stream`` method example

    def train_stream(self):
        for i in range(10):
            yield load_training_batch(num=i)

Analogously, additional methods such as ``valid_stream`` and ``test_stream`` can be easily implemented.
If they are registered in the config file under ``main_loop.extra_streams``, they will be evaluated
along with the train stream. The configuration may look as follows:

.. code-block:: yaml
    :caption: configuring extra stream to be evaluated

    main_loop:
      extra_streams: [valid, test]

The extra streams, however, *are not* used for training, that is, the model is won`t be updated when it iterates through them.

Finally, **cxflow** requires predict *stream* for the prediction command ``cxflow predict ..``.

Additional Methods
------------------

Alongside providing the streams, the dataset may implement additional methods
downloading, validating or visualizing the data.

For example, is can contain a ``download`` method, which checks whether the dataset has all the data it requires.
If not, it downloads them from the internet/database/drive. These methods may be easily invoked with

.. code-block:: bash

    cxflow dataset <method-name> <config>

Additional useful method could be ``statistics``, which would print various statistics of provided data,
plot some figures etc.
Sometimes, we need to split the whole dataset into training, validation and testing sets.
For this purpose, we would implement a ``split`` function.

The suggested methods are completely arbitrary. The key concept is to keep data-related functions
bundled together in the dataset object, so that one doesn't need to implement
several separate scripts for fetching/visualization/statistics etc.

A typical pipeline contains the following commands.
We leave them without further comments as they are self-describing.

- ``cxflow dataset download config/my-data.yaml``
- ``cxflow dataset validate config/my-data.yaml``
- ``cxflow dataset print_statistics config/my-data.yaml``
- ``cxflow dataset plot_histogram config/my-data.yaml``
- ``cxflow train config/my-data.yaml``
- ``cxflow predict config/my-data.yaml``

The Philosophy of Laziness
--------------------------

In our experience, the best practice for the dataset is to perform all the initialization on demand.
This technique is sometimes called *lazy initialization*.
That is, the constructor should not perform any time-consuming operation such as loading and decoding the data.
Instead, the data should be loaded and decoded in the first moment they are truly necessary (e.g.,
in the ``train_stream`` method).

The main reason for laziness is that the dataset doesn't know for which purpose it was constructed.
It might be queried to provide the training data or only to print some simple checksums.
In the cases of extremely big datasets, it is useless and annoying to waste the time by loading the data
without their actual use.