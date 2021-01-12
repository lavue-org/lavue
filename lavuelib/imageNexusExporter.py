# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" image Nexus exporter """

import numpy as np
import os
import logging
from pyqtgraph import QtGui
from pyqtgraph.exporters import Exporter
from pyqtgraph.parametertree import Parameter

from . import filewriter

#: (:obj:`dict` <:obj:`str`, :obj:`module`> ) nexus writer modules
WRITERS = {}
try:
    from . import h5pywriter
    WRITERS["h5py"] = h5pywriter
except Exception:
    pass
try:
    from . import h5cppwriter
    WRITERS["h5cpp"] = h5cppwriter
except Exception:
    pass

__all__ = ['ImageNexusExporter']

logger = logging.getLogger("lavue")


def getcompression(compression):
    """ converts compression string to a deflate level parameter
        or list with [filterid, opt1, opt2, ...]

    :param compression: compression string
    :type compression: :obj:`str`
    :returns: deflate level parameter
              or list with [filterid, opt1, opt2, ...]
    :rtype: :obj:`int` or :obj:`list` < :obj:`int` > or `None`

    """
    if compression:
        if isinstance(compression, int) or ":" not in compression:
            level = None
            try:
                level = int(compression)
            except Exception:
                raise Exception(
                    "Error: argument compression: "
                    "invalid int value: '%s'\n" % compression)
            return level
        else:
            opts = None
            try:
                sfid, sopts = compression.split(":")
                opts = [int(sfid)]
                opts.extend([int(opt) for opt in sopts.split(",")])
            except Exception:
                raise Exception(
                    "Error: argument compression: "
                    "invalid format: '%s'\n" % compression)
            return opts
        return


class ImageNexusExporter(Exporter):

    """ NeXus Raw Image Exporter """

    Name = "NeXus Raw Image"
    windows = []
    allowCopy = False

    def __init__(self, item):
        """ constructor

        :param item: image item
        :param item: :class: `pyqtgraph.PlotItem` or `pyqtgraph.GraphicsScene`
        """
        Exporter.__init__(self, item)

        #: (:class:`pyqtgraph.parametertree.Parameter`) exporter parameters
        self.params = Parameter(name='params', type='group', children=[
            {'name': 'FieldName', 'type': 'str', 'value': 'data'},
            {'name': 'Compression', 'type': 'str', 'value': '2'},
            {'name': 'FileName', 'type': 'str', 'value': ''},
        ])

    def parameters(self):
        """ parameters

        :returns: exporter parameters
        :rtype: :class:`pyqtgraph.parametertree.Parameter`
        """
        return self.params

    def export(self, fileName=None):
        """ export data image to NeXus file

        :param fileName: output file name
        :rtype fileName: :obj:`str`
        """
        if self.params['FileName']:
            filename = self.params['FileName']
        elif fileName:
            filename = str(fileName)
            self.params['FileName'] = str(fileName)
        else:
            filename = None
        if "h5cpp" in WRITERS.keys():
            writer = "h5cpp"
        else:
            writer = "h5py"
        if writer not in WRITERS.keys():
            raise Exception("Writer '%s' cannot be opened" % writer)
        wrmodule = WRITERS[writer.lower()]

        if isinstance(self.item, QtGui.QGraphicsItem):
            scene = self.item.scene()
        else:
            scene = self.item
        if not hasattr(scene, "rawdata"):
            raise Exception(
                "Scene object without rawdata")
        rawdata = np.transpose(np.array(scene.rawdata))
        if rawdata is None or not isinstance(rawdata, np.ndarray):
            raise Exception("Empty image")
        if filename is None:
            self.fileSaveDialog(
                filter=["*.nxs", "*.ndf", "*.n5", "*.nx",
                        "*.h5", "*.hdf", "*.hd5"])
            return
        fieldname = self.params['FieldName']
        try:
            if os.path.exists(filename):
                fl = filewriter.open_file(
                    str(filename), readonly=False, writer=wrmodule)
            else:
                fl = filewriter.create_file(
                    str(filename), overwrite=False, writer=wrmodule)
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            raise Exception(
                "File '%s' cannot be created \n" % (filename))
        root = fl.root()
        if "data" in root.names():
            node = root.open("data")
        else:
            node = root.create_group("data", "NXdata")
        if fieldname in node.names():
            field = node.open(fieldname)
        else:
            fieldcompression = self.params['Compression']
            if fieldcompression:
                opts = getcompression(fieldcompression)
                if isinstance(opts, int):
                    cfilter = filewriter.data_filter(node)
                    cfilter.rate = opts
                elif isinstance(opts, list) and opts:
                    cfilter = filewriter.data_filter(node)
                    cfilter.filterid = opts[0]
                    cfilter.options = tuple(opts[1:])
            shape = list(rawdata.shape)
            dtype = str(rawdata.dtype)
            fdshape = [0] + shape
            fdchunk = [1] + shape
            field = node.create_field(
                fieldname,
                dtype,
                shape=fdshape,
                chunk=fdchunk,
                dfilter=cfilter)
        field.grow(0, 1)
        field[-1, ...] = rawdata
        field.close()
        node.close()
        root.close()
        fl.close()


if WRITERS:
    ImageNexusExporter.register()
