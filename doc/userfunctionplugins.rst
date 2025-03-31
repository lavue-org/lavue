.. _user-function-plugins:

User Function plugins
---------------------

A **User Function plugin** can be defined by a **class** or a **function** in a python package.

A **user function plugin** defined by a **function** is a simple python function with one argument: `results` which contain a python dictionary of **ToolResults**.

This function **returns** a python dictionary with `x` and  `y` *(list)* data to plot , `title`, `bottom` and `left` *(string)* labels  `color` and `hvscolor` *(string)*  or *(int)* . For user plots with mutli-curves the python dictionary can contains `nrplots` *(int)* , `x_%i`,  `y_%i` *(list)* data to plot, `name_%i`  *(list)* names of plots, `color_%i` and `hvscolor_%i` *(string)*  or *(int)* where `%i` runs from 1 to `nrplots`. If `y_%i` is set to ``None`` the previous plot will stay shown. Also if `legend` is set to ``True`` plots are discribed by its names in legend. A location of legend can be adjusted by `lengend_offset` *(int)*
, e.g.

.. code-block:: python

    def positive(results):
	""" plot positive function values on the LineCut tool

	:param results: dictionary with tool results
	:type results: :obj:`dict`
	:returns: dictionary with user plot data
	:rtype: :obj:`dict`
	"""
	userplot = {}
	if "linecut_1" in results:
	    userplot = {"x": results["linecut_1"][0],
			"y": [max(0.0, yy) for yy in results["linecut_1"][1]]}
	return userplot


A **user function plugin** defined by a **class** it should have defined **__call__** method with one argument: `results`.

This **__call__** function returns a python dictionary with `x` and  `y` *list* data to plot  and optionally `title`, `bottom` and `left` *string* labels.

Moreover, the class *constructor* has one configuration string argument initialized by an initialization parameter, e.g.

.. code-block:: python

    class LineCutFlat(object):

	"""Flatten line cut"""

	def __init__(self, configuration=None):
	    """ constructor

	    :param configuration: JSON list with horizontal gap pixels to add
	    :type configuration: :obj:`str`
	    """
	    #: (:obj:`list` <:obj: `str`>) list of indexes for gap
	    self.__index = 1
	    try:
		self.__flat = float(configuration)
	    except Exception:
		self.__flat = 100000000.
		pass

	def __call__(self, results):
	    """ call method

	    :param results: dictionary with tool results
	    :type results: :obj:`dict`
	    :returns: dictionary with user plot data
	    :rtype: :obj:`dict`
	    """
	    userplot = {}
        if "tool" in results and results["tool"] == "linecut":
            try:
                nrplots = int(results["nrlinecuts"])
            except Exception:
                nrplots = 0
            userplot["nrplots"] = nrplots
            userplot["title"] = "Linecuts flatten at '%s'" % (self.__flat)

            for i in range(nrplots):
                xlabel = "x_%s" % (i + 1)
                ylabel = "y_%s" % (i + 1)
                label = "linecut_%s" % (i + 1)
                cllabel = "hsvcolor_%s" % (i + 1)
                if label in results:
                    userplot[xlabel] = results[label][0]
                    userplot[ylabel] = [min(yy, self.__flat)
                                        for yy in results[label][1]]
                    userplot[cllabel] = i/float(nrplots)
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intensity"
	    return userplot

or

.. code-block:: python

    import json


    class DiffPDF(object):

	"""diffpy PDF user function"""

	def __init__(self, configuration=None):
	    """ constructor

	    :param configuration: JSON list with config file and diff index
	    :type configuration: :obj:`str`
	    """
	    #: (:obj:`list` <:obj: `str`>) list of indexes for gap
	    self.__configfile = None

	    config = None
	    try:
		config = json.loads(configuration)
		try:
		    self.__index = int(config[1])
		except Exception:
		    self.__index = 1
		self.__configfile = str(config[0])
	    except Exception:
		self.__index = 1
		self.__configfile = str(configuration)

	    from diffpy.pdfgetx import loadPDFConfig
	    self.__cfg = loadPDFConfig(self.__configfile)

	def __call__(self, results):
	    """ call method

	    :param results: dictionary with tool results
	    :type results: :obj:`dict`
	    :returns: dictionary with user plot data
	    :rtype: :obj:`dict`
	    """
	    userplot = {}
	    from diffpy.pdfgetx import PDFGetter
	    self.__pg = PDFGetter(config=self.__cfg)
	    label = "diff_%s" % self.__index
	    if label in results and self.__configfile:
		qq = results[label][0]
		df = results[label][1]
		data_gr = self.__pg(qq, df)
		x = data_gr[0]
		y = data_gr[1]

		userplot = {
		    "x": x, "y": y,
		    "title": "DiffPDF: %s with %s" % (label, self.__configfile)
		}
	    return userplot


or

.. code-block:: python

    import json


    class LineCut(object):

	""" LineCut selection"""

	def __init__(self, configuration=None):
	    """ constructor

	    :param configuration: JSON list with horizontal gap pixels to add
	    :type configuration: :obj:`str`
	    """
	    try:
		#: (:obj: `int`) line cut index
		self.__index = int(json.loads(configuration)[0])
	    except Exception:
		self.__index = 1
	    try:
		#: (:obj: `int`) buffer length
		self.__buflen = max(int(json.loads(configuration)[1]), 1)
	    except Exception:
		self.__buflen = 20

	    #: (:obj: `list`) buffer
	    self.__buffer = []

	def __call__(self, results):
	    """ call method

	    :param results: dictionary with tool results
	    :type results: :obj:`dict`
	    :returns: dictionary with user plot data
	    :rtype: :obj:`dict`
	    """
	    userplot = {}
	    label = "linecut_%s" % self.__index
	    if label in results:
		if len(self.__buffer) >= self.__buflen:
		    self.__buffer.pop(0)
		self.__buffer.append([results[label][0], results[label][1]])
		userplot["nrplots"] = len(self.__buffer)
		for i, xy in enumerate(self.__buffer):
		    userplot["x_%s" % (i + 1)] = xy[0]
		    userplot["y_%s" % (i + 1)] = xy[1]
		    if i != len(self.__buffer) - 1:
			userplot["color_%s" % (i + 1)] = i/float(self.__buflen)
		    else:
			userplot["color_%s" % (i + 1)] = 'r'

		userplot["title"] = "History of %s" % label
		if "unit" in results:
		    userplot["bottom"] = results["unit"]
		    userplot["left"] = "intensity"
	    return userplot


If `image` *(numpy.array)* is provided the user image is also plotted.
When both image and function plots need to be displayed
`function` has to be set to ``true``.
Also position and scale of the image can be set by
`image_scale` namely ``[position_x, postion_y, scale_x, scale_y]`` .
The `colormap` *(string)* sets a name of color maps.
The levels of colormap can be set by tuple `colormap_values` ``(low, high)``
or separately `colormap_low` *(float)* and `colormap_high` *(float)*
, e.g.

.. code-block:: python

    import json
    import numpy as np


    class DiffPDFImage(object):

	"""diffpy PDF user function"""

	def __init__(self, configuration=None):
	    """ constructor

	    :param configuration: JSON list with config file and diff index
	    :type configuration: :obj:`str`
	    """
	    #: (:obj:`list` <:obj: `str`>) list of indexes for gap
	    self.__configfile = None

	    #: (:obj: `int`) buffer length
	    self.__buflen = 20
	    #: (:obj: `float`) waterfall plot shift
	    self.__shift = 1.0
	    #: (:obj: `int`) diff label index
	    self.__index = 1
	    #: (:obj: `float`) number of characters cut from the image name
	    self.__cut = -28
	    #: (:obj: `list`) buffer
	    self.__buffer = []
	    #: (:obj: `int`) plot counter
	    self.__counter = -1
	    #: (:obj: `str`) plot mode i.e. all, image, function
	    self.__mode = "all"

	    self.__imgbuffer = None
	    self.__ximgbuffer = None

	    try:
		config = json.loads(configuration)
		self.__configfile = str(config[0])
		try:
		    self.__index = int(config[1])
		except Exception:
		    pass

		try:
		    self.__buflen = max(int(config[2]), 1)
		except Exception:
		    pass

		try:
		    #: (:obj: `float`) buffer length
		    self.__shift = float(config[3])
		except Exception:
		    pass

		try:
		    #: (:obj: `float`) buffer length
		    self.__cut = int(config[4])
		except Exception:
		    pass

		try:
		    #: (:obj: `float`) buffer length
		    self.__mode = str(config[5])
		except Exception:
		    pass
	    except Exception:
		self.__configfile = str(configuration)

	    self.__counter = - self.__buflen

	    from diffpy.pdfgetx import loadPDFConfig
	    #: configuration
	    self.__cfg = loadPDFConfig(self.__configfile)

	def __call__(self, results):
	    """ call method

	    :param results: dictionary with tool results
	    :type results: :obj:`dict`
	    :returns: dictionary with user plot data
	    :rtype: :obj:`dict`
	    """
	    userplot = {}
	    from diffpy.pdfgetx import PDFGetter
	    self.__pg = PDFGetter(config=self.__cfg)
	    label = "diff_%s" % self.__index

	    if label in results and self.__configfile and "imagename" in results:
		qq = results[label][0]
		df = results[label][1]
		data_gr = self.__pg(qq, df)
		x = data_gr[0]
		y = data_gr[1]

		self.__counter += 1

		if self.__mode != "image":
		    if len(self.__buffer) >= self.__buflen:
			self.__buffer.pop(0)
		    if self.__shift:
			for i in range(len(self.__buffer)):
			    self.__buffer[i][1] = [(y + self.__shift)
						   for y in self.__buffer[i][1]]
		    self.__buffer.append([x, y, results["imagename"]])

		    userplot["nrplots"] = len(self.__buffer)
		    for i, xy in enumerate(self.__buffer):
			userplot["x_%s" % (i + 1)] = xy[0]
			userplot["y_%s" % (i + 1)] = xy[1]
			userplot["name_%s" % (i + 1)] = "%s (+ %s)" % (
			    xy[2][self.__cut:],
			    ((len(self.__buffer) - i - 1) * self.__shift))
			userplot["hsvcolor_%s" % (i + 1)] = \
			    ((i + max(0, self.__counter)) % self.__buflen) \
			    / float(self.__buflen)

		    userplot["title"] = "History of %s" % label
		    userplot["legend"] = True
		    userplot["legend_offset"] = -1
		    userplot["title"] = "DiffPDFImage: %s with %s" % (
			label, self.__configfile)
		    userplot["function"] = True

		if self.__mode != "function":
		    newrow = np.array(y)
		    if self.__imgbuffer is not None and \
		       self.__imgbuffer.shape[1] == newrow.shape[0]:
			if self.__imgbuffer.shape[0] >= self.__buflen:
			    self.__imgbuffer = np.vstack(
				[self.__imgbuffer[
				    self.__imgbuffer.shape[0]
				    - self.__buflen + 1:,
				    :],
				 newrow]
			    )
			else:
			    self.__imgbuffer = np.vstack(
				[self.__imgbuffer, newrow])
		    else:
			self.__imgbuffer = np.array([y])
		    if self.__imgbuffer is not None:
			userplot["image"] = self.__imgbuffer.T
			xbuf = np.array(x)
			pos = 0.0
			sc = 1.0
			if len(xbuf) > 0:
			    pos = xbuf[0]
			if len(xbuf) > 1:
			    sc = float(xbuf[-1] - xbuf[0])/(len(xbuf) - 1)
			self.__ximgbuffer = results[label][0]
			userplot["iamge_scale"] = [
			    [pos, max(0, self.__counter)], [sc, 1]]

	    return userplot


To configure user functions see :ref:`user-function-plugins-settings`.
