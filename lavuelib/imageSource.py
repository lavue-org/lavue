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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#     Andre Rothkirch <andre.rothkirch@desy.de>
#

""" set of image sources """

from pyqtgraph import QtCore, QtGui
import json
import struct
import logging

from . import dataFetchThread
from .sardanaUtils import debugmethod

try:
    import requests
    #: (:obj:`bool`) requests imported
    REQUESTS = True
except ImportError:
    #: (:obj:`bool`) requests imported
    REQUESTS = False

try:
    import hidra
    #: (:obj:`bool`) hidra imported
    HIDRA = True
except ImportError:
    #: (:obj:`bool`) hidra imported
    HIDRA = False

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False

try:
    __import__("pyFAI")
    #: (:obj:`bool`) pyFAI imported
    PYFAI = True
except ImportError:
    #: (:obj:`bool`) pyFAI imported
    PYFAI = False

try:
    import pydoocs
    #: (:obj:`bool`) pydoocs imported
    PYDOOCS = True
except ImportError:
    #: (:obj:`bool`) pydoocs imported
    PYDOOCS = False

try:
    import PIL
    import PIL.Image
    #: (:obj:`bool`) PIL imported
    PILLOW = True
except ImportError:
    #: (:obj:`bool`) PIL imported
    PILLOW = False

try:
    import zmq
    #: (:obj:`str`,:obj:`str`) zmq major version, zmq minor version
    ZMQMAJOR, ZMQMINOR = list(map(int, zmq.zmq_version().split(".")))[:2]
except Exception:
    #: (:obj:`str`,:obj:`str`) zmq major version, zmq minor version
    ZMQMAJOR, ZMQMINOR = 0, 0

try:
    import epics
    #: (:obj:`bool`) pyepics imported
    PYEPICS = True
except ImportError:
    #: (:obj:`bool`) pyepics imported
    PYEPICS = False

try:
    import PyTine
    #: (:obj:`bool`) PyTine imported
    PyTine.get
    PYTINE = True
except ImportError:
    #: (:obj:`bool`) PyTine imported
    PYTINE = False
except AttributeError:
    #: (:obj:`bool`) PyTine imported
    PYTINE = False


import socket
import numpy as np
import random
import time
try:
    import cPickle
except Exception:
    import _pickle as cPickle
import sys

from io import BytesIO
from . import imageFileHandler

if sys.version_info > (3,):
    buffer = memoryview
    unicode = str
else:
    bytes = str


logger = logging.getLogger("lavue")


def tobytes(x):
    """ decode str to bytes

    :param x: string
    :type x: :obj:`str`
    :returns:  decode string in byte array
    :rtype: :obj:`bytes`
    """
    if isinstance(x, bytes):
        return x
    if sys.version_info > (3,):
        return bytes(x, "utf8")
    else:
        return bytes(x)


def tostr(x):
    """ decode bytes to str

    :param x: string
    :type x: :obj:`bytes`
    :returns:  decode string in byte array
    :rtype: :obj:`str`
    """
    if isinstance(x, str):
        return x
    if sys.version_info > (3,):
        return str(x, "utf8")
    else:
        return str(x)


class BaseSource(object):

    """ source base class"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        #: (:obj:`int`) timeout in ms
        self._timeout = timeout
        #: (:obj:`str`) configuration string
        self._configuration = None
        #: (:obj:`bool`) connection initiated  flag
        self._initiated = False
        #: (:obj:`int`) internal counter
        self.__counter = 0
        #: (:obj:`str`) errormessage
        self.errormessage = ""

    def getMetaData(self):
        """ get metadata

        :returns: dictionary with metadata
        :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
        """
        return {}

    @debugmethod
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self._initiated = False

    @debugmethod
    def setTimeOut(self, timeout):
        """ set timeout

        :param timeout: timeout in ms
        :type timeout: :obj:`int`
        """
        self._timeout = timeout

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        self.__counter += 1
        # if self.__counter % 20 == 0:
        #     return str("Test error"), "__ERROR__", ""
        return (np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ]),
            '__random_%s__' % self.__counter, "")

    @debugmethod
    def connect(self):
        """ connects the source
        """
        self._initiated = True
        self.__counter = 0
        return True

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        try:
            pass
        except Exception:
            pass

    @debugmethod
    def _updaterror(self):
        """ updates error  message
        """
        import traceback
        self.errormessage = str(traceback.format_exc())


class FixTestSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:obj:`int`) internal counter
        self.__counter = 0

        #: ([:obj:`int`, :obj:`int`]) image shape
        self.__shape = [2048, 4096]
        # self.__shape = [256, 512]
        # self.__shape = [1024, 2048]

        #: (:class:`numpy,ndarray`) index object
        self.__image = np.transpose(
            [
                [random.randint(0, 1000) for _ in range(self.__shape[0])]
                for _ in range(self.__shape[1])
            ])

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        self.__counter += 1
        return (self.__image,
                '__random_%s__' % self.__counter, "")

    @debugmethod
    def connect(self):
        """ connects the source
        """
        self._initiated = True
        self.__counter = 0
        return True

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        try:
            pass
        except Exception:
            pass


class NXSFileSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)

        #: (:obj:`str`) nexus file name with the full path
        self.__nxsfile = None
        #: (:obj:`str`) nexus field path
        self.__nxsfield = None
        #: (:obj:`int`) stacking dimension
        self.__gdim = 0
        #: (:obj:`int`) the current frame
        self.__frame = 0
        #: (:class:`lavuelib.imageFileHandler.NexusFieldHandler`)
        #: the nexus file handler
        self.__handler = None
        #: (:class:`lavuelib.filewriter.FTField`) field object
        self.__node = None
        #: (:obj:`bool`) nexus file source keeps the file open
        self.__nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.__nxslast = False

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        if self.__nxsfile is None:
            return "No file name defined", "__ERROR__", ""
        try:
            image = None
            metadata = ""
            try:
                if self.__handler is None:
                    self.__handler = imageFileHandler.NexusFieldHandler(
                        str(self.__nxsfile))
                if self.__node is None:
                    self.__node = self.__handler.getNode(self.__nxsfield)
                    metadata = self.__handler.getMetaData(self.__node)
                    # if metadata:
                    #     print("IMAGE Metadata = %s" % str(metadata))
                fid = self.__handler.getLastFrame(self.__node, self.__gdim)
                if self.__nxslast:
                    if fid - 1 > self.__frame or fid - 1 < self.__frame:
                        self.__frame = fid - 1
                else:
                    if fid - 1 < self.__frame:
                        self.__frame = fid - 1

                image = self.__handler.getImage(
                    self.__node, self.__frame, self.__gdim)
            # except Exception:
            except Exception:
                try:
                    self.__handler = imageFileHandler.NexusFieldHandler(
                        str(self.__nxsfile))
                    self.__node = self.__handler.getNode(self.__nxsfield)
                    fid = self.__handler.getLastFrame(
                        self.__node, self.__gdim)
                    if self.__nxslast:
                        if fid - 1 > self.__frame or fid - 1 < self.__frame:
                            self.__frame = fid - 1
                    else:
                        if fid - 1 < self.__frame:
                            self.__frame = fid - 1
                    image = self.__handler.getImage(
                        self.__node, self.__frame, self.__gdim)
                except Exception:
                    pass
            if not self.__nxsopen:
                self.__handler = None
                if hasattr(self.__node, "close"):
                    self.__node.close()
                self.__node = None
            if image is not None:
                if hasattr(image, "size"):
                    if image.size == 0:
                        return None, None, None
                filename = "%s/%s:%s" % (
                    self.__nxsfile, self.__nxsfield, self.__frame)
                self.__frame += 1
                return (np.transpose(image), '%s' % (filename), metadata)
        except Exception as e:
            self.__handler = None
            if hasattr(self.__node, "close"):
                self.__node.close()
            self.__node = None
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        try:
            self.__handler = None
            self.__node = None
            self.__frame = 0
            self.__nxsfile, self.__nxsfield, growdim, \
                nxsopen, nxslast = str(
                    self._configuration).strip().split(",", 4)
            try:
                self.__gdim = int(growdim)
            except Exception:
                self.__gdim = 0
            if nxsopen.lower() == "false":
                self.__nxsopen = False
            else:
                self.__nxsopen = True
            if nxslast.lower() == "false":
                self.__nxslast = False
            else:
                self.__nxslast = True
            return True
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            self._updaterror()
            return False

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        self.__handler = None
        self.__node = None


class TangoFileSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:class`PyTango.AttributeProxy`:)
        #:       device proxy for the image file name
        self.__fproxy = None
        #: (:class`PyTango.AttributeProxy`:)
        #:      device proxy for the image directory
        self.__dproxy = None
        #: (:dict: <:obj:`str`, :obj:`str`>)
        #:      translation dictionary for the image directory
        self.__dirtrans = {"/ramdisk/": "/gpfs/"}

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        if self.__fproxy is None:
            return "No file attribute defined", "__ERROR__", None
        try:
            filename = self.__fproxy.read().value
            if self.__dproxy:
                dattr = self.__dproxy.read().value
                filename = "%s/%s" % (dattr, filename)
                for key, val in self.__dirtrans.items():
                    filename = filename.replace(key, val)
            fh = imageFileHandler.ImageFileHandler(str(filename))
            image = fh.getImage()
            mdata = fh.getMetaData()
            if image is not None:
                if hasattr(image, "size"):
                    if image.size == 0:
                        return None, None, None
                return (np.transpose(image), '%s' % (filename), mdata)
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        try:
            fattr, dattr, dirtrans = str(
                self._configuration).strip().split(",", 2)
            self.__dirtrans = json.loads(dirtrans)
            if not self._initiated:
                self.__fproxy = PyTango.AttributeProxy(fattr)
                if dattr:
                    self.__dproxy = PyTango.AttributeProxy(dattr)
                else:
                    self.__dproxy = None
            return True
        except Exception as e:
            self._updaterror()
            logger.warning(str(e))
            # print(str(e))
            return False


class VDEOdecoder(object):

    """ VIDEO IMAGE LIMA decoder
    """

    @debugmethod
    def __init__(self):
        """ constructor

        :brief: It clears the local variables
        """
        #: (:obj:`str`) decoder name
        self.name = "LIMA_VIDEO_IMAGE"
        #: (:obj:`str`) decoder format
        self.format = None
        #: (:obj:`str`) data type
        self.dtype = None

        #: (:class:`numpy.ndarray`) image data
        self.__value = None
        #: ([:obj:`str`, :obj:`str`]) header and image data
        self.__data = None
        #: (:obj:`str`) struct header format
        self.__headerFormat = '!IHHqiiHHHH'
        #: (:obj:`dict` <:obj:`str`, :obj:`any` > ) header data
        self.__header = {}
        #: (:obj:`dict` <:obj:`int`, :obj:`str` > ) format modes
        self.__formatID = {0: 'B', 1: 'H', 2: 'I', 3: 'Q'}
        #: (:obj:`dict` <:obj:`int`, :obj:`str` > ) dtype modes
        self.__dtypeID = {0: 'uint8', 1: 'uint16', 2: 'uint32', 3: 'uint64'}

    # @debugmethod
    def load(self, data):
        """  loads encoded data

        :param data: encoded data
        :type data: [:obj:`str`, :obj:`str`]
        """
        logger.debug(
            "lavuelib.imageSource.VDEOdecoder.load:  %s" % str(data[0]))
        self.__data = data
        self.format = data[0]
        self._loadHeader(data[1][:struct.calcsize(self.__headerFormat)])
        self.__value = None

    @debugmethod
    def _loadHeader(self, headerData):
        """ loads the image header

        :param headerData: buffer with header data
        :type headerData: :obj:`str`
        """
        hdr = struct.unpack(self.__headerFormat, headerData)
        self.__header = {}
        self.__header['magic'] = hdr[0]
        self.__header['headerVersion'] = hdr[1]
        self.__header['imageMode'] = hdr[2]
        self.__header['frameNumber'] = hdr[3]
        self.__header['width'] = hdr[4]
        self.__header['height'] = hdr[5]
        self.__header['endianness'] = hdr[6]
        self.__header['headerSize'] = hdr[7]
        self.__header['padding'] = hdr[7:]

        self.dtype = self.__dtypeID[self.__header['imageMode']]

    @debugmethod
    def shape(self):
        """ provides the data shape

        :returns: the data shape if data was loaded
        :rtype: :obj:`list` <:obj:`int` >
        """
        if self.__header:
            return [self.__header['height'], self.__header['width']]

    @debugmethod
    def frameNumber(self):
        """ provides the frame number

        :returns: the frame number
        :rtype: :obj:`int`
        """
        if 'frameNumber' in self.__header.keys():
            return self.__header['frameNumber']

    @debugmethod
    def decode(self):
        """ provides the decoded data

        :returns: the decoded data if data was loaded
        :rtype: :class:`numpy.ndarray`
        """
        if not self.__header or not self.__data:
            return
        if not self.__value:
            image = self.__data[1][struct.calcsize(self.__headerFormat):]
            dformat = self.__formatID[self.__header['imageMode']]
            fSize = struct.calcsize(dformat)
            self.__value = np.array(
                struct.unpack(dformat * (len(image) // fSize), image),
                dtype=self.dtype).reshape(self.__header['height'],
                                          self.__header['width']).T
            fendian = self.__header['endianness']
            lendian = ord(struct.pack('=H', 1).decode()[-1])
            if fendian != lendian:
                try:
                    self.__value.byteswap(inplace=False)
                except TypeError:
                    self.__value = self.__value.byteswap()

        return self.__value


class TangoAttrSource(BaseSource):

    """ image source as IMAGE Tango attribute
    """

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:class`PyTango.AttributeProxy`:)
        #:      device proxy for the image attribute
        self.__aproxy = None
        #: (:dict: <:obj:`str`, :obj:`any`>)
        #:      dictionary of external decorders
        self.__decoders = {"LIMA_VIDEO_IMAGE": VDEOdecoder(),
                           "VIDEO_IMAGE": VDEOdecoder()}
        #: (:dict: <:obj:`str`, :obj:`str`>)
        #:      dictionary of tango decorders
        self.__tangodecoders = {
            "GRAY16": "decode_gray16",
            "GRAY8": "decode_gray8",
            "JPEG_GRAY8": "decode_gray8",
            "JPEG_RGB": "decode_rgb32",
            "RGB24": "decode_rgb32"
        }
        #: (:obj:`bool`) bytearray flag
        self.__bytearray = False

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        if self.__aproxy is None:
            return "No attribute name defined", "__ERROR__", None
        try:
            try:
                if not self.__bytearray:
                    attr = self.__aproxy.read()
                else:
                    attr = self.__aproxy.read(
                        extract_as=PyTango.ExtractAs.ByteArray)
            except Exception:
                if sys.version_info > (3,):
                    attr = self.__aproxy.read(
                        extract_as=PyTango.ExtractAs.ByteArray)
                    self.__bytearray = True
                else:
                    attr = self.__aproxy.read()
            if str(attr.type) == "DevEncoded":
                avalue = attr.value
                if avalue[0] in ["RGB24", "JPEG_RGB"]:
                    image = QtGui.QImage.fromData(avalue[1])
                    width = image.width()
                    height = image.height()
                    st = image.bits().asstring(width * height * 4)
                    data = np.fromstring(st, dtype=np.uint8).reshape(
                        (height, width, 4))
                    return (np.transpose(data),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
                elif avalue[0] in self.__tangodecoders:
                    da = self.__aproxy.read(
                        extract_as=PyTango.ExtractAs.Nothing)
                    enc = PyTango.EncodedAttribute()
                    data = getattr(enc, self.__tangodecoders[avalue[0]])(da)
                    return (np.transpose(data),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
                else:
                    dec = self.__decoders[avalue[0]]
                    dec.load(avalue)
                    fnumber = dec.frameNumber() or ""
                    shape = dec.shape()
                    if shape is None or shape[0] <= 0 or shape[1] <= 0:
                        return None, None, None
                    # no need to transpose
                    return (dec.decode(),
                            '%s %s (%s)' % (
                                self._configuration,
                                fnumber,
                                str(attr.time)), "")
            else:
                if attr.value is not None:
                    if hasattr(attr.value, "size"):
                        if attr.value.size == 0:
                            return None, None, None
                    return (np.transpose(attr.value),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        self.__bytearray = False
        try:
            if not self._initiated:
                self.__aproxy = PyTango.AttributeProxy(
                    str(self._configuration))
            return True
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            self._updaterror()
            return False


class TangoEventsCB(object):

    """ tango attribute callback class"""

    @debugmethod
    def __init__(self, client, name, mutex):
        """ constructor

        :param client: tango controller client
        :type client: :class:`str`
        :param name: attribute name
        :type name: :obj:`str`
        :param mutex: mutex lock for CB
        :type type: :class:`pyqtgraph.QtCore.QMutex`
        """
        self.__client = client
        self.__name = name
        self.__mutex = mutex

    # @debugmethod
    def push_event(self, event_data):
        """callback method receiving the event
        """

        if logger.getEffectiveLevel() >= 10:
            trunk = str(event_data)
            if len(trunk) > 1300:
                trunk = trunk[:800] + " ... " + trunk[-500:]
            logger.debug(
                "lavuelib.imageSource.TangoEventCB.push_event: %s"
                % trunk)
        if event_data.err:
            result = event_data.errors
            logger.warning(str(result))
            # print(str(result))
        else:
            if not self.__client.reading:
                with QtCore.QMutexLocker(self.__mutex):
                    try:
                        self.__client.reading = True
                        self.__client.attr = event_data.attr_value
                        self.__client.fresh = True
                    finally:
                        self.__client.reading = False


class TangoReadyEventsCB(object):

    """ tango attribute callback class"""

    @debugmethod
    def __init__(self, client, name, mutex):
        """ constructor

        :param client: tango controller client
        :type client: :class:`str`
        :param name: attribute name
        :type name: :obj:`str`
        :param mutex: mutex lock for CB
        :type type: :class:`pyqtgraph.QtCore.QMutex`
        """
        self.__client = client
        self.__name = name
        self.__mutex = mutex

    # @debugmethod
    def push_event(self, event_data):
        """callback method receiving the event
        """

        if logger.getEffectiveLevel() >= 10:
            trunk = str(event_data)
            if len(trunk) > 1300:
                trunk = trunk[:800] + " ... " + trunk[-500:]
            logger.debug(
                "lavuelib.imageSource.TangoEventCB.push_event: %s"
                % trunk)
        if event_data.err:
            result = event_data.errors
            logger.warning(str(result))
            # print(str(result))
        else:
            if not self.__client.reading:
                with QtCore.QMutexLocker(self.__mutex):
                    try:
                        self.__client.reading = True
                        _, attrnm = str(event_data.attr_name).rsplit("/", 1)
                        self.__client.attr = event_data.device.read_attribute(
                            attrnm)
                        self.__client.fresh = True
                    finally:
                        self.__client.reading = False


class TangoEventsSource(BaseSource):

    """ image source as IMAGE Tango attribute
    """

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:obj:`bool`) reading flag
        self.reading = False
        #: (:obj:`bool`) fresh attribute flag
        self.fresh = False
        #: (:class:`pyqtgraph.QtCore.QMutex`) mutex lock for CB
        self.__mutex = QtCore.QMutex()
        #: (:class`PyTango.DeviceProxy`:)
        #:      device proxy for the image attribute
        self.__proxy = None
        self.__attrid = None
        self.__rattrid = None
        self.attr = None
        #: (:dict: <:obj:`str`, :obj:`any`>)
        #:      dictionary of external decorders
        self.__decoders = {"LIMA_VIDEO_IMAGE": VDEOdecoder(),
                           "VIDEO_IMAGE": VDEOdecoder()}
        #: (:dict: <:obj:`str`, :obj:`str`>)
        #:      dictionary of tango decorders
        self.__tangodecoders = {
            "GRAY16": "decode_gray16",
            "GRAY8": "decode_gray8",
            "JPEG_GRAY8": "decode_gray8",
            "JPEG_RGB": "decode_rgb32",
            "RGB24": "decode_rgb32"
        }

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        if self.__proxy is None:
            return "No attribute name defined", "__ERROR__", None
        try:
            with QtCore.QMutexLocker(self.__mutex):
                if self.attr is None or not self.fresh:
                    return None, None, None
                self.fresh = False
                if str(self.attr.type) == "DevEncoded":
                    avalue = self.attr.value
                    if avalue[0] in ["RGB24", "JPEG_RGB"]:
                        image = QtGui.QImage.fromData(avalue[1])
                        width = image.width()
                        height = image.height()
                        st = image.bits().asstring(width * height * 4)
                        data = np.fromstring(st, dtype=np.uint8).reshape(
                            (height, width, 4))
                        return (np.transpose(data),
                                '%s  (%s)' % (
                                    self._configuration, str(self.attr.time)),
                                "")
                    elif avalue[0] in self.__tangodecoders:
                        # da = self.__aproxy.read(
                        #     extract_as=PyTango.ExtractAs.Nothing)
                        enc = PyTango.EncodedAttribute()
                        data = getattr(
                            enc, self.__tangodecoders[avalue[0]])(self.attr)
                        return (np.transpose(data),
                                '%s  (%s)' % (
                                    self._configuration,
                                    str(self.attr.time)),
                                "")
                    else:
                        dec = self.__decoders[avalue[0]]
                        dec.load(avalue)
                        # no need to transpose
                        shape = dec.shape()
                        if shape is None or shape[0] <= 0 or shape[1] <= 0:
                            return None, None, None
                        return (dec.decode(),
                                '%s  (%s)' % (
                                    self._configuration, str(self.attr.time)),
                                "")
                else:
                    if self.attr.value is not None:
                        if hasattr(self.attr.value, "size"):
                            if self.attr.value.size == 0:
                                return None, None, None
                        return (np.transpose(self.attr.value),
                                '%s  (%s)' % (
                                    self._configuration, str(self.attr.time)),
                                "")
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        try:
            if not self._initiated:
                self.disconnect()
                # with QtCore.QMutexLocker(self.__mutex):
                dvname, atname = str(self._configuration).rsplit('/', 1)
                attr_cb = TangoEventsCB(self, atname, self.__mutex)
                rattr_cb = TangoReadyEventsCB(self, atname, self.__mutex)
                self.__proxy = PyTango.DeviceProxy(dvname)
                exc = ""
                try:
                    self.__attrid = self.__proxy.subscribe_event(
                        atname,
                        PyTango.EventType.CHANGE_EVENT,
                        attr_cb)
                except Exception as e:
                    self.__attrid = None
                    exc += str(e)
                    try:
                        self.__rattrid = self.__proxy.subscribe_event(
                            atname,
                            PyTango.EventType.DATA_READY_EVENT,
                            rattr_cb)
                    except Exception as e:
                        self.__rattrid = None
                        exc += str(e)
                        raise Exception(exc)
                self._initiated = True
            return True
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            self._updaterror()
            return False

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        try:
            if self._initiated:
                with QtCore.QMutexLocker(self.__mutex):
                    self._initiated = False
                    proxy = self.__proxy
                if proxy is not None:
                    if self.__attrid is not None:
                        self.__proxy.unsubscribe_event(self.__attrid)
                        self.__attrid = None
                    if self.__rattrid is not None:
                        self.__proxy.unsubscribe_event(self.__rattrid)
                        self.__rattrid = None
        except Exception:
            self._updaterror()


class HTTPSource(BaseSource):

    """ image source as HTTP request response
    """

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:obj:`bool`) use tiff loader
        self.__tiffloader = True
        #: (:obj:`dict` <:obj:`str`, :obj:`any` > ) HTTP header data
        self.__header = {}

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        if self._configuration:
            try:
                response = self.__get()
                if response.ok:
                    name = self._configuration
                    data = response.content
                    if data[:10] == "###CBF: VE":
                        # print("[cbf source module]::metadata", name)
                        img = imageFileHandler.CBFLoader().load(
                            np.fromstring(data[:], dtype=np.uint8))
                        if img is None:
                            return None, None, None
                        if hasattr(img, "size") and img.size == 0:
                            return None, None, None
                        return (np.transpose(img),
                                "%s (%s)" % (name, time.ctime()), "")
                    else:
                        # print("[tif source module]::metadata", name)
                        if PILLOW and not self.__tiffloader:
                            try:
                                img = np.array(
                                    PIL.Image.open(BytesIO(str(data))))
                            except Exception:
                                img = imageFileHandler.TIFLoader().load(
                                    np.fromstring(data[:], dtype=np.uint8))
                                self.__tiffloader = True
                            if img is None:
                                return None, None, None
                            if hasattr(img, "size") and img.size == 0:
                                return None, None, None
                            return (np.transpose(img),
                                    "%s (%s)" % (name, time.ctime()), "")
                        else:
                            img = imageFileHandler.TIFLoader().load(
                                np.fromstring(data[:], dtype=np.uint8))
                            if img is None:
                                return None, None, None
                            if hasattr(img, "size") and img.size == 0:
                                return None, None, None
                            return (np.transpose(img),
                                    "%s (%s)" % (name, time.ctime()), "")
                else:
                    logger.info(
                        "HTTPSource.getData: %s" % str(response.content))
                    pass
            except Exception as e:
                # print(str(e))
                logger.warning(str(e))
                return str(e), "__ERROR__", ""
            else:
                if str(response.text) == 'Image not available':
                    return str(response.text), None, None
                else:
                    return str(response.text), "__ERROR__", None
        return "No url defined", "__ERROR__", None

    # @debugmethod
    def __get(self):
        """ get response

        :returns: response object
        :rtype: :class:`requests.Response`
        """
        if self.__header:
            try:
                return requests.get(
                    self._configuration, headers=self.__header,
                    timeout=(self._timeout/1000. if self._timeout else None))
            except AttributeError:
                return requests.get(
                    self._configuration, headers=self.__header)
        else:
            try:
                return requests.get(
                    self._configuration,
                    timeout=(self._timeout/1000. if self._timeout else None))
            except AttributeError:
                return requests.get(self._configuration)

    @debugmethod
    def connect(self):
        """ connects the source
        """
        self.__tiffloader = False
        try:
            if self._configuration:
                self.__header = {}
                if self._configuration.endswith("/images/monitor"):
                    sconf = self._configuration.split("/")
                    if len(sconf) > 4:
                        version = sconf[-3]
                        lst = [int(x, 10) for x in version.split('.')]
                        lst.reverse()
                        lversion = sum(
                            x * (100 ** i) for i, x in enumerate(lst))
                        if lversion >= 10800:
                            self.__header = {'Accept': 'application/tiff'}
                self.__get()
            return True
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            self._updaterror()
            return False


class ZMQSource(BaseSource):

    """ image source as ZMQ stream"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)

        #: (:class:`zmq.Context`) zmq context
        self.__context = zmq.Context()
        #: (:class:`zmq.Socket`) zmq socket
        self.__socket = None
        #: (:obj:`int`) internal counter
        self.__counter = 0
        #: (:obj:`bytes`) zmq topic
        self.__topic = b"10001"
        #: (:obj:`str`) zmq bind address
        self.__bindaddress = None
        #: (:class:`pyqtgraph.QtCore.QMutex`) mutex lock for zmq source
        self.__mutex = QtCore.QMutex()

    @debugmethod
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self._initiated = False
            with QtCore.QMutexLocker(self.__mutex):
                if self.__socket:
                    shost = str(self._configuration).split("/")
                    topic = shost[1] if len(shost) > 1 else ""
                    self.__socket.unbind(self.__bindaddress)
                    self.__socket.setsockopt(
                        zmq.UNSUBSCRIBE, self.__topic)
                    self.__socket.setsockopt(
                        zmq.UNSUBSCRIBE, b"datasources")
                    self.__socket.setsockopt(
                        zmq.SUBSCRIBE, b"datasources")
                    self.__socket.setsockopt(
                        zmq.SUBSCRIBE, tobytes(topic))
                    self.__topic = tobytes(topic)
                    self.__socket.connect(self.__bindaddress)

    @debugmethod
    def __loads(self, message, encoding=None):
        """ loads json or pickle string

        :param message: message to encode
        :type message: :obj:`str`
        :param encoding: JSON or PICKLE
        :type encoding: :obj:`str`
        :returns: encoded message object
        :rtype: :obj:`any`
        """

        smessage = tostr(message)
        if encoding == "JSON":
            metadata = json.loads(smessage)
        else:
            try:
                metadata = cPickle.loads(message)
            except Exception:
                metadata = json.loads(smessage)
        return metadata

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        encoding = None
        if self.__socket is None:
            return "No socket defined", "__ERROR__", None
        try:
            with QtCore.QMutexLocker(self.__mutex):
                message = self.__socket.recv_multipart(flags=zmq.NOBLOCK)
            topic = None
            _array = None
            shape = None
            dtype = None
            name = None
            lmsg = None
            metadata = None

            if isinstance(message, tuple) or isinstance(message, list):
                lmsg = len(message)
                topic = message[0]
            if message[-1] == b"JSON":
                encoding = "JSON"
                lmsg -= 1
                message.pop()
            elif message[-1] == b"PICKLE":
                encoding = "PICKLE"
                lmsg -= 1
                message.pop()

            # print("topic %s %s" % (topic, self.__topic))
            if topic == b"datasources" and lmsg == 2:
                (topic, _metadata) = message
                metadata = self.__loads(_metadata, encoding)
                if "shape" in metadata:
                    metadata.pop("shape")
                if "dtype" in metadata:
                    metadata.pop("dtype")
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return ("", "", jmetadata)
            elif topic == b"datasources" and lmsg == 3:
                (topic, _, _metadata) = message
                metadata = self.__loads(_metadata, encoding)
                if "shape" in metadata:
                    metadata.pop("shape")
                if "dtype" in metadata:
                    metadata.pop("dtype")
                jmetadata = ""
                if metadata:
                    jmetadata = json.dumps(metadata)
                return ("", "", jmetadata)
            elif self.__topic == b"" or tobytes(topic) == self.__topic:
                if lmsg == 3:
                    (topic, _array, _metadata) = message
                    metadata = self.__loads(_metadata, encoding)
                    shape = metadata["shape"]
                    dtype = metadata["dtype"]
                    if "name" in metadata:
                        name = metadata["name"]
                    else:
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, tostr(topic), self.__counter)
                else:
                    if lmsg == 4:
                        (topic, _array, _shape, _dtype) = message
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, tostr(topic), self.__counter)
                    elif lmsg == 5:
                        (topic, _array, _shape, _dtype, name) = message
                    dtype = self.__loads(_dtype, encoding)
                    shape = self.__loads(_shape, encoding)

            if _array is not None:
                array = np.frombuffer(buffer(_array), dtype=dtype)
                array = array.reshape(shape)
                array = np.transpose(array)
                self.__counter += 1
                jmetadata = ""
                if metadata:
                    metadata.pop("shape")
                    metadata.pop("dtype")
                    try:
                        jmetadata = json.dumps(metadata)
                    except Exception:
                        pass
                if hasattr(array, "size") and array.size == 0:
                    return ("", "", jmetadata)
                return (np.transpose(array), name, jmetadata)

        except zmq.Again:
            pass
        except Exception as e:
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        try:
            shost = str(self._configuration).split("/")
            host, port = str(shost[0]).split(":")
            self.__topic = tobytes(shost[1] if len(shost) > 1 else "")
            hwm = int(shost[2]) if (len(shost) > 2 and shost[2]) else 2
            if not self._initiated:
                if self.__socket:
                    self.disconnect()
                with QtCore.QMutexLocker(self.__mutex):
                    self.__socket = self.__context.socket(zmq.SUB)
                    if hwm is not None:
                        self.__socket.set_hwm(hwm)
                    self.__bindaddress = (
                        'tcp://'
                        + socket.gethostbyname(host)
                        + ':'
                        + str(port)
                    )
                    self.__socket.setsockopt(zmq.SUBSCRIBE,
                                             self.__topic)
                    self.__socket.setsockopt(zmq.SUBSCRIBE, b"datasources")
                    # self.__socket.setsockopt(zmq.SUBSCRIBE, "")
                    self.__socket.connect(self.__bindaddress)
                time.sleep(0.2)
            return True
        except Exception as e:
            self.disconnect()
            logger.warning(str(e))
            # print(str(e))
            self._updaterror()
            return False

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        try:
            with QtCore.QMutexLocker(self.__mutex):
                if self.__socket:
                    if self.__bindaddress:
                        self.__socket.unbind(self.__bindaddress)
                    self.__socket.close(linger=0)
                    self.__socket = None
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            pass
        with QtCore.QMutexLocker(self.__mutex):
            self.__bindaddress = None

    def __del__(self):
        """ destructor
        """
        self.disconnect()
        self.__context.destroy()


class HiDRASource(BaseSource):

    """ hidra image source"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """

        BaseSource.__init__(self, timeout)
        #: (:obj:`str`) hidra port number
        self.__portnumber = "50001"
        #: (:obj:`str`) hidra client server
        self.__targetname = socket.getfqdn()
        #: (:obj:`str`) server host
        self.__shost = None
        #: (:obj:`list` < :obj:`str`, :obj:`str`,
        #:   :obj:`int` :obj:`list` < :obj:`str`> >) hidra target:
        #:   [host name, portnumber, priority, a list of extensions]
        self.__target = [self.__targetname, self.__portnumber, 19,
                         [".cbf", ".tif", ".tiff"]]
        #: (:class:`hidra.transfer.Transfer`) hidra query
        self.__query = None
        #: (:class:`pyqtgraph.QtCore.QMutex`) mutex lock for hidra source
        self.__mutex = QtCore.QMutex()
        #: (:obj:`bool`) use tiff loader
        self.__tiffloader = False

    @debugmethod
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            try:
                self.__shost, self.__targetname, self.__portnumber \
                    = str(configuration).split()
            except Exception:
                self._initiated = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(
                (self.__targetname, int(self.__portnumber)))
            if result:
                self._configuration = configuration
                self.__target = [
                    self.__targetname, self.__portnumber, 19,
                    [".cbf", ".tif", ".tiff"]]
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query = hidra.Transfer(
                        "QUERY_NEXT", self.__shost)
            else:
                self.__query = None
            self._initiated = False

    @debugmethod
    def connect(self):
        """ connects the source
        """
        self.__tiffloader = False
        try:
            if self.__query is None:
                raise Exception(
                    "%s:%s is busy. Please change the port"
                    % (self.__targetname, self.__portnumber))
            if not self._initiated:
                with QtCore.QMutexLocker(self.__mutex):
                    # print("TARGET %s" % self.__target)
                    logger.info(
                        "HiDRASource.connect: TARGET %s" % self.__target)
                    self.__query.initiate(self.__target)
                self._initiated = True
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.start()
            return True
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
            self._updaterror()
            return False

    @debugmethod
    def disconnect(self):
        """ disconnects the source
        """
        try:
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
            self._initiated = False
        except Exception:
            self._updaterror()

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        metadata = None
        data = None
        if self.__query is None:
            return "No server defined", "__ERROR__", None
        if not self._initiated:
            return None, None, None
        try:
            with QtCore.QMutexLocker(self.__mutex):
                # [metadata, data] = self.__query.get()
                t1 = time.time()
                [metadata, data] = self.__query.get(self._timeout)
            if metadata is None and data is None \
               and time.time() - t1 < self._timeout/2000.:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
                    self.__query = hidra.Transfer(
                        "QUERY_NEXT", self.__shost)
                    self.__query.initiate(self.__target)
                    self._initiated = True
                    self.__query.start()
                    [metadata, data] = self.__query.get(self._timeout)
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            pass  # this needs a bit more care

        if metadata is not None and data is not None:
            # print("data", str(data)[:10])

            if data[:10] == "###CBF: VE":
                # print("[cbf source module]::metadata", metadata["filename"])
                logger.info(
                    "HiDRASource.getData: "
                    "[cbf source module]::metadata", metadata["filename"])
                npdata = np.fromstring(data[:], dtype=np.uint8)
                img = imageFileHandler.CBFLoader().load(npdata)

                mdata = imageFileHandler.CBFLoader().metadata(npdata)

                if hasattr(img, "size") and img.size == 0:
                    return None, None, None
                return np.transpose(img), metadata["filename"], mdata
            else:
                # elif data[:2] in ["II\x2A\x00", "MM\x00\x2A"]:
                logger.info(
                    "HiDRASource.getData:"
                    "[tif source module]::metadata", metadata["filename"])
                # print("[tif source module]::metadata", metadata["filename"])
                if PILLOW and not self.__tiffloader:
                    try:
                        img = np.array(PIL.Image.open(BytesIO(str(data))))
                    except Exception:
                        img = imageFileHandler.TIFLoader().load(
                            np.fromstring(data[:], dtype=np.uint8))
                        self.__tiffloader = True
                    if hasattr(img, "size") and img.size == 0:
                        return None, None, None
                    if img is not None:
                        return np.transpose(img), metadata["filename"], ""
                else:
                    img = imageFileHandler.TIFLoader().load(
                        np.fromstring(data[:], dtype=np.uint8))
                    if hasattr(img, "size") and img.size == 0:
                        return None, None, None
                    if img is not None:
                        return np.transpose(img), metadata["filename"], ""
            # else:
            #     print(
            #       "[unknown source module]::metadata", metadata["filename"])
        else:
            return None, None, None


class DOOCSPropSource(BaseSource):

    """ image source as IMAGE DOOCS property
    """

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            dt = pydoocs.read(self._configuration)
            npdata = dt['data']
            tstamp = dt['timestamp']
            return (np.transpose(npdata),
                    '%s  (%s)' % (
                        self._configuration, str(tstamp)),
                    "")

        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        return True


class EpicsPVSource(BaseSource):

    """ image source as Epics Process variable"""

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:class:`epics.PV`)
        #:       epics process variable
        self.__pv = None
        #: (:obj:`list` < :obj:`int` >)
        #:      process variable shape
        self.__shape = None
        #: (:obj:`list` < :obj:`int` >)
        #:      process variable size
        self.__size = 0

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        if self.__pv is None:
            return "No PV defined", "__ERROR__", None
        try:
            rawdata = self.__pv.get(as_numpy=True,
                                    timeout=float(self._timeout/1000.))
            if not hasattr(rawdata, "size"):
                return None, None, None
            else:
                if self.__shape and rawdata.size >= self.__size:
                    image = rawdata[:self.__size].reshape(self.__shape)
                else:
                    image = rawdata
                return (np.transpose(image),
                        '%s (%s)' % (self._configuration, time.time()), None)
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    @debugmethod
    def connect(self):
        """ connects the source
        """
        try:
            pvnm, pvsh = str(
                self._configuration).strip().split(",", 1)
            if not self._initiated:
                self.__pv = epics.PV(pvnm)
                try:
                    shape = json.loads(pvsh)
                    self.__shape = list(reversed([int(s) for s in shape]))
                    self.__size = np.prod(self.__shape)
                except Exception:
                    self.__size = 0
                    self.__shape = None
            return True
        except Exception as e:
            self._updaterror()
            logger.warning(str(e))
            # print(str(e))
            return False


class TinePropSource(BaseSource):

    """ image source as Tine Property """

    @debugmethod
    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:obj:`str`)
        #:       tine device address name
        self.__address = None
        #: (:obj:`str`)
        #:       tine property name
        self.__prop = None

    @classmethod
    def __dtype(cls, header):
        """ provides dtype of tine property

        :param header: tine frameHeader
        :type header: :obj:`dict` <:obj:`str`, `any`>
        :returns: numpy dtype
        :rtype: :obj:`str`
        """
        dtype = ""
        if not header or "bytesPerPixel" not in header:
            raise ValueError("bytesPerPixel not defined in the header")

        if header["bytesPerPixel"] == 1:
            dtype = "u1"
        elif header["bytesPerPixel"] == 2:
            dtype = "u2"
        else:
            raise ValueError("Invalid bytesPerPixel: %s"
                             % header["bytesPerPixel"])

        return dtype

    @classmethod
    def __height(cls, header):
        """ provides height of tine property

        :param header: tine frameHeader
        :type header: :obj:`dict` <:obj:`str`, `any`>
        :returns: numpy dtype
        :rtype: :obj:`str`
        """
        height = 0
        if "aoiHeight" in header and header["aoiHeight"] > 0:
            height = header["aoiHeight"]
        elif "sourceHeight" in header:
            height = header["sourceHeight"]

        if not 0 < height <= 65535:
            raise ValueError("Invalid height: %s" % height)

        return height

    @classmethod
    def __width(cls, header):
        """ provides width of tine property

        :param header: tine frameHeader
        :type header: :obj:`dict` <:obj:`str`, `any`>
        :returns: numpy dtype
        :rtype: :obj:`str`
        """
        width = 0
        if "aoiWidth" in header and header["aoiWidth"] > 0:
            width = header["aoiWidth"]
        elif "sourceWidth" in header:
            width = header["sourceWidth"]

        if not 0 < width <= 65535:
            raise ValueError("Invalid width: %s" % width)

        return width

    @debugmethod
    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        if not self.__address or not self.__prop:
            return "No Tine Property defined", "__ERROR__", None
        try:
            interval = int(dataFetchThread.GLOBALREFRESHRATE*1000)
            prop = PyTine.get(address=self.__address,
                              property=self.__prop,
                              timeout=interval)
            rawdata = prop["data"]

            if "imageMatrix" in rawdata:
                image = rawdata["imageMatrix"]
            else:
                header = rawdata["frameHeader"]
                dtype = self.__dtype(header)
                height = self.__height(header)
                width = self.__width(header)
                image = np.frombuffer(rawdata["imageBytes"], dtype=dtype)
                if len(image) != height * width:
                    raise ValueError(
                        "Dimension mismatch: size: %s != %s"
                        % (len(image), height * width))
                image = image.reshape((height, width))

            timestamp = prop["timestamp"]
            return (np.transpose(image),
                    '%s (%s)' % (self._configuration, timestamp), None)
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    @debugmethod
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self.__address, self.__prop = str(
                self._configuration).rsplit("/", 1)
