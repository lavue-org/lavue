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

from PyQt4 import QtCore
import json
import struct

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


class BaseSource(object):

    """ source base class"""

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

    @QtCore.pyqtSlot(str)
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:
            self._configuration = configuration
            self._initiated = False

    def setTimeOut(self, timeout):
        """ set timeout

        :param timeout: timeout in ms
        :type timeout: :obj:`int`
        """
        self._timeout = timeout

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

    def connect(self):
        """ connects the source
        """
        self._initiated = True
        self.__counter = 0
        return True

    def disconnect(self):
        """ disconnects the source
        """
        try:
            pass
        except Exception:
            pass

    def _updaterror(self):
        """ updates error  message
        """
        import traceback
        self.errormessage = str(traceback.format_exc())


class FixTestSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

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

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        self.__counter += 1
        return (self.__image,
                '__random_%s__' % self.__counter, "")

    def connect(self):
        """ connects the source
        """
        self._initiated = True
        self.__counter = 0
        return True

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

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            image = None
            try:
                if self.__handler is None:
                    self.__handler = imageFileHandler.NexusFieldHandler(
                        str(self.__nxsfile))
                if self.__node is None:
                    self.__node = self.__handler.getNode(self.__nxsfield)
                if self.__nxslast:
                    fid = self.__handler.getLastFrame(self.__node, self.__gdim)
                    if fid > self.__frame or fid < self.__frame:
                        self.__frame = fid - 1
                image = self.__handler.getImage(
                    self.__node, self.__frame, self.__gdim)
            # except Exception:
            except Exception as e:
                print(str(e))
                try:
                    self.__handler = imageFileHandler.NexusFieldHandler(
                        str(self.__nxsfile))
                    self.__node = self.__handler.getNode(self.__nxsfield)
                    if self.__nxslast:
                        fid = self.__handler.getLastFrame(
                            self.__node, self.__gdim)
                        if fid > self.__frame or fid < self.__frame:
                            self.__frame = fid - 1
                    image = self.__handler.getImage(
                        self.__node, self.__frame, self.__gdim)
                except Exception as e:
                    print(str(e))
                    pass
            if not self.__nxsopen:
                self.__handler = None
                if hasattr(self.__node, "close"):
                    self.__node.close()
                self.__node = None
            if image is not None:
                filename = "%s/%s:%s" % (
                    self.__nxsfile, self.__nxsfield, self.__frame)
                self.__frame += 1
                return (np.transpose(image), '%s' % (filename), "")
        except Exception as e:
            self.__handler = None
            if hasattr(self.__node, "close"):
                self.__node.close()
            self.__node = None
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

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
            print(str(e))
            self._updaterror()
            return False

    def disconnect(self):
        """ disconnects the source
        """
        self.__handler = None
        self.__node = None


class TangoFileSource(BaseSource):

    """ image source as Tango attributes describing
        an image file name and its directory"""

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

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            filename = self.__fproxy.read().value
            if self.__dproxy:
                dattr = self.__dproxy.read().value
                filename = "%s/%s" % (dattr, filename)
                for key, val in self.__dirtrans.items():
                    filename = filename.replace(key, val)
            image = imageFileHandler.ImageFileHandler(
                str(filename)).getImage()

            return (np.transpose(image), '%s' % (filename), "")
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

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
            print(str(e))
            return False


class VDEOdecoder(object):

    """ VIDEO IMAGE LIMA decoder
    """

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

    def load(self, data):
        """  loads encoded data

        :param data: encoded data
        :type data: [:obj:`str`, :obj:`str`]
        """
        self.__data = data
        self.format = data[0]
        self._loadHeader(data[1][:struct.calcsize(self.__headerFormat)])
        self.__value = None

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

    def shape(self):
        """ provides the data shape

        :returns: the data shape if data was loaded
        :rtype: :obj:`list` <:obj:`int` >
        """
        if self.__header:
            return [self.__header['width'], self.__header['height']]

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
                dtype=self.dtype).reshape(self.__header['width'],
                                          self.__header['height'])
        return self.__value


class TangoAttrSource(BaseSource):

    """ image source as IMAGE Tango attribute
    """

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

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """

        try:
            attr = self.__aproxy.read()
            if str(attr.type) == "DevEncoded":
                avalue = attr.value
                if avalue[0] in self.__tangodecoders:
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
                    return (np.transpose(dec.decode()),
                            '%s  (%s)' % (
                                self._configuration, str(attr.time)), "")
            else:
                return (np.transpose(attr.value),
                        '%s  (%s)' % (
                            self._configuration, str(attr.time)), "")
        except Exception as e:
            print(str(e))
            return str(e), "__ERROR__", ""
            pass  # this needs a bit more care
        return None, None, None

    def connect(self):
        """ connects the source
        """
        try:
            if not self._initiated:
                self.__aproxy = PyTango.AttributeProxy(
                    str(self._configuration))
            return True
        except Exception as e:
            print(str(e))
            self._updaterror()
            return False


class HTTPSource(BaseSource):

    """ image source as HTTP request response
    """

    def __init__(self, timeout=None):
        """ constructor

        :param timeout: timeout for setting connection in ms
        :type timeout: :obj:`int`
        """
        BaseSource.__init__(self, timeout)
        #: (:obj:`bool`) use tiff loader
        self.__tiffloader = True

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        if self._configuration:
            try:
                response = requests.get(self._configuration)
                if response.ok:
                    name = self._configuration
                    data = response.content
                    if data[:10] == "###CBF: VE":
                        # print("[cbf source module]::metadata", name)
                        img = imageFileHandler.CBFLoader().load(
                            np.fromstring(data[:], dtype=np.uint8))
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
                            return (np.transpose(img),
                                    "%s (%s)" % (name, time.ctime()), "")
                        else:
                            img = imageFileHandler.TIFLoader().load(
                                np.fromstring(data[:], dtype=np.uint8))
                            return (np.transpose(img),
                                    "%s (%s)" % (name, time.ctime()), "")
                else:
                    print("HTTP Source: %s" % str(response.content))
                    pass
            except Exception as e:
                print(str(e))
                return str(e), "__ERROR__", ""
        return None, None, None

    def connect(self):
        """ connects the source
        """
        self.__tiffloader = False
        try:
            if self._configuration:
                requests.get(self._configuration)
            return True
        except Exception as e:
            print(str(e))
            self._updaterror()
            return False


class ZMQSource(BaseSource):

    """ image source as ZMQ stream"""

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
        #: (:obj:`str`) zmq topic
        self.__topic = "10001"
        #: (:obj:`str`) zmq bind address
        self.__bindaddress = None
        #: (:class:`PyQt4.QtCore.QMutex`) zmq bind address
        self.__mutex = QtCore.QMutex()

    @QtCore.pyqtSlot(str)
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
                    self.__socket.setsockopt(zmq.UNSUBSCRIBE, self.__topic)
                    self.__socket.setsockopt(zmq.UNSUBSCRIBE, "datasources")
                    self.__socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    self.__socket.setsockopt(zmq.SUBSCRIBE, topic)
                    self.__topic = topic
                    self.__socket.connect(self.__bindaddress)

    def __loads(self, message, encoding=None):
        """ loads json or pickle string

        :param message: message to encode
        :type message: :obj:`str`
        :param encoding: JSON or PICKLE
        :type encoding: :obj:`str`
        :returns: encoded message object
        :rtype: :obj:`any`
        """

        if encoding == "JSON":
            metadata = json.loads(message)
        else:
            try:
                metadata = cPickle.loads(message)
            except Exception:
                metadata = json.loads(message)
        return metadata

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        encoding = None
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
            if message[-1] == "JSON":
                encoding = "JSON"
                lmsg -= 1
                message.pop()
            elif message[-1] == "PICKLE":
                encoding = "PICKLE"
                lmsg -= 1
                message.pop()

            # print("topic %s %s" % (topic, self.__topic))
            if topic == "datasources" and lmsg == 2:
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
            elif topic == "datasources" and lmsg == 3:
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
            elif self.__topic == "" or topic == self.__topic:
                if lmsg == 3:
                    (topic, _array, _metadata) = message
                    metadata = self.__loads(_metadata, encoding)
                    shape = metadata["shape"]
                    dtype = metadata["dtype"]
                    if "name" in metadata:
                        name = metadata["name"]
                    else:
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, topic, self.__counter)
                else:
                    if lmsg == 4:
                        (topic, _array, _shape, _dtype) = message
                        name = '%s/%s (%s)' % (
                            self.__bindaddress, topic, self.__counter)
                    elif lmsg == 5:
                        (topic, _array, _shape, _dtype, name) = message
                    dtype = self.__loads(_dtype, encoding)
                    shape = self.__loads(_shape, encoding)

            if _array:
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
                return (np.transpose(array), name, jmetadata)

        except zmq.Again as e:
            pass
        except Exception as e:
            # print(str(e))
            return str(e), "__ERROR__", ""
        return None, None, None

    def connect(self):
        """ connects the source
        """
        try:
            shost = str(self._configuration).split("/")
            host, port = str(shost[0]).split(":")
            self.__topic = shost[1] if len(shost) > 1 else ""
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
                    self.__socket.setsockopt(zmq.SUBSCRIBE, self.__topic)
                    self.__socket.setsockopt(zmq.SUBSCRIBE, "datasources")
                    # self.__socket.setsockopt(zmq.SUBSCRIBE, "")
                    self.__socket.connect(self.__bindaddress)
                time.sleep(0.2)
            return True
        except Exception as e:
            self.disconnect()
            print(str(e))
            self._updaterror()
            return False

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
            print(str(e))
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
        #: (:class:`PyQt4.QtCore.QMutex`) zmq bind address
        self.__mutex = QtCore.QMutex()
        #: (:obj:`bool`) use tiff loader
        self.__tiffloader = False

    @QtCore.pyqtSlot(str)
    def setConfiguration(self, configuration):
        """ set configuration

        :param configuration:  configuration string
        :type configuration: :obj:`str`
        """
        if self._configuration != configuration:

            self.__shost, self.__targetname, self.__portnumber \
                = str(configuration).split()
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
                    self.__query.initiate(self.__target)
                self._initiated = True
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.start()
            return True
        except Exception as e:
            print(str(e))
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
            self._updaterror()
            return False

    def disconnect(self):
        """ disconnects the source
        """
        try:
            if self.__query is not None:
                with QtCore.QMutexLocker(self.__mutex):
                    self.__query.stop()
        except Exception:
            self._updaterror()

    def getData(self):
        """ provides image name, image data and metadata

        :returns:  image name, image data, json dictionary with metadata
        :rtype: (:obj:`str` , :class:`numpy.ndarray` , :obj:`str`)
        """
        metadata = None
        data = None
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
            print(str(e))
            pass  # this needs a bit more care

        if metadata is not None and data is not None:
            # print("data", str(data)[:10])

            if data[:10] == "###CBF: VE":
                print("[cbf source module]::metadata", metadata["filename"])
                img = imageFileHandler.CBFLoader().load(
                    np.fromstring(data[:], dtype=np.uint8))
                return np.transpose(img), metadata["filename"], ""
            else:
                # elif data[:2] in ["II\x2A\x00", "MM\x00\x2A"]:
                print("[tif source module]::metadata", metadata["filename"])
                if PILLOW and not self.__tiffloader:
                    try:
                        img = np.array(PIL.Image.open(BytesIO(str(data))))
                    except Exception:
                        img = imageFileHandler.TIFLoader().load(
                            np.fromstring(data[:], dtype=np.uint8))
                        self.__tiffloader = True

                    return np.transpose(img), metadata["filename"], ""
                else:
                    img = imageFileHandler.TIFLoader().load(
                        np.fromstring(data[:], dtype=np.uint8))
                    return np.transpose(img), metadata["filename"], ""
            # else:
            #     print(
            #       "[unknown source module]::metadata", metadata["filename"])
        else:
            return None, None, None
