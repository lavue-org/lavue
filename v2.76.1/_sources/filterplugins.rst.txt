.. _filter-plugins:

Filter plugins
--------------

A user **Filter plugin** can be defined by a **class** or a **function** in a python package.

A **filter plugin** defined by a **function** is a simple python function with four arguments: `numpy_image`, `image_name`, `JSON_metadata`, `ImageWidget`.

This function **returns** `new_numpy_image` or `None` or *tuple* (`new_numpy_image`, `filtermetadata_dict`) , e.g.

.. code-block:: python

    from scipy import ndimage

    def rot45(image, imagename, metadata, imagewg):
    """ rotate image by 45 deg

    :param image: numpy array with an image
    :type image: :class:`numpy.ndarray`
    :param imagename: image name
    :type imagename: :obj:`str`
    :param metadata: JSON dictionary with metadata
    :type metadata: :obj:`str`
    :param imagewg: image wigdet
    :type imagewg: :class:`lavuelib.imageWidget.ImageWidget`
    :returns: numpy array with an image
    :rtype: :class:`numpy.ndarray` or `None`
    """
    return ndimage.rotate(image, 45)


A **filter plugin** defined by a **class** it should have defined **__call__** method with four arguments: `numpy_image`, `image_name`, `JSON_metadata`, `ImageWidget`.

This **__call__** function returns `new_numpy_image` or `None` or *tuple*  (`new_numpy_image`, `filtermetadata_dict`) .

Moreover, the class *constructor* has one configuration string argument initialized by an initialization parameter, e.g.

.. code-block:: python

   import numpy as np
   import json


   class HGap(object):

   """ Horizontal gap filter"""

   def __init__(self, configuration=None):
       """ converts the configuration string into a list of indexes

       :param configuration: JSON list with horizontal gap pixels to add
       :type configuration: :obj:`str`
       """
       #: (:obj:`list` <:obj: `str`>) list of indexes for gap
       self.__indexes = [int(idx) for idx in json.loads(configuration)]

   def __call__(self, image, imagename, metadata, imagewg):
       """ inserts rows into the image

       :param image: numpy array with an image
       :type image: :class:`numpy.ndarray`
       :param imagename: image name
       :type imagename: :obj:`str`
       :param metadata: JSON dictionary with metadata
       :type metadata: :obj:`str`
       :param imagewg: image wigdet
       :type imagewg: :class:`lavuelib.imageWidget.ImageWidget`
       :returns: numpy array with an image
       :rtype: :class:`numpy.ndarray` or `None`
       """
       return np.insert(image, self.__indexes, 0, axis=1)



Moreover,  it can have an **initialize()** or **terminate()** method to perform an action of switching **on** or **off** filters respectively.

More sophisticated examples can be found at `lavuefilters <https://github.com/lavue-org/lavue-filters/tree/develop/lavuefilters>`_:

*    `lavuefilters.memoplugins.HistoryDump` contains a filter which collects distinct images displayed by lavue in memory
*    `lavuefilters.h5pyplugins.H5PYdumpdiff` contains a filter which dumps distict images displayed by lavue to an hdf5 file
*    `lavuefilters.h5pyplugins.H5PYdump` contains a filter which dumps images displayed by lavue to an hdf5 file

To configure filters see :ref:`filter-plugins-settings`.
