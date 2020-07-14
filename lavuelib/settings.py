# Copyright (C) 2017  DESY, Notkestr. 85, D-22607 Hamburg
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
#


""" live viewer image display base it on a qt dialog """


import zmq
import sys
import json
from pyqtgraph import QtCore

if sys.version_info > (3,):
    unicode = str

try:
    __import__("pyFAI")
    #: (:obj:`bool`) pyFAI imported
    PYFAI = True
except ImportError:
    #: (:obj:`bool`) pyFAI imported
    PYFAI = False


class Settings(object):

    """ lavue configuration settings """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) sardana enabled
        self.sardana = True
        #: (:obj:`bool`) add rois to sardana
        self.addrois = False
        #: (:obj:`bool`) fetch rois order enabled
        self.orderrois = False
        #: (:obj:`bool`) search for security stream port automatically
        self.secautoport = True
        #: (:obj:`bool`) show intensity hostogram
        self.showhisto = True
        #: (:obj:`bool`) show intensity hostogram
        self.showaddhisto = False
        #: (:obj:`bool`) show mask widget
        self.showmask = False
        #: (:obj:`bool`) show high mask value  widget
        self.showhighvaluemask = False
        #: (:obj:`bool`) show statistics widget
        self.showstats = True
        #: (:obj:`bool`) show image step widget
        self.showsteps = True
        #: (:obj:`bool`) calculate variance
        self.calcvariance = False
        #: (:obj:`bool`) show bakcground subtraction widget
        self.showsub = True
        #: (:obj:`bool`) show transformation widget
        self.showtrans = True
        #: (:obj:`bool`) show memory buffer widget
        self.showmbuffer = False
        #: (:obj:`bool`) show range window widget
        self.showrange = False
        #: (:obj:`bool`) show filter widget
        self.showfilters = False
        #: (:obj:`bool`) show intensity scale widget
        self.showscale = True
        #: (:obj:`bool`) show intensity levels widget
        self.showlevels = True
        #: (:obj:`bool`) show frame rate widget
        self.showframerate = True
        #: (:obj:`bool`) image aspect ratio locked
        self.aspectlocked = False
        #: (:obj:`bool`) auto down sample
        self.autodownsample = False
        #: (:obj:`bool`) keep original coordinates
        self.keepcoords = False
        #: (:obj:`bool`) lazy image slider
        self.lazyimageslider = True
        #: (:obj:`str`) security stream port
        self.secport = "5657"
        #: (:obj:`str`) hidra data port
        self.hidraport = "50001"
        #: (:obj:`str`) maximal number of images in memory buffer
        self.maxmbuffersize = "1000"
        #: (:obj:`int`) number of image sources
        self.nrsources = 1
        #: (:obj:`int`) image source timeout for connection
        self.timeout = 3000
        #: (:class:`zmq.Context`) zmq context
        self.seccontext = zmq.Context()
        #: (:class:`zmq.Socket`) zmq security stream socket
        self.secsocket = self.seccontext.socket(zmq.PUB)
        #: (:obj:`bool`) security stream enabled
        self.secstream = False
        #: (:obj:`bool`) zero mask enabled
        self.zeromask = False
        #: (:obj:`bool`) nan mask enabled
        self.nanmask = True
        #: (:obj:`bool`) security stream options
        self.secsockopt = b""
        #: (:obj:`float`) refresh rate is s
        self.refreshrate = 0.2
        #: (:obj:`float`) tool refresh rate time is s
        self.toolrefreshtime = 0.02
        #: (:obj:`float`) tool polling interval is s
        self.toolpollinginterval = 1.0
        #: (:obj:`bool`) interrupt on error
        self.interruptonerror = True
        #: (:obj:`str`) last image file name
        self.imagename = None
        #: (:obj:`str`) calibration file name
        self.calibrationfilename = None
        #: (:obj:`str`) last mask image file name
        self.maskimagename = None
        #: (:obj:`str`) last background image file name
        self.bkgimagename = None
        #: (:obj:`bool`) statistics without scaling
        self.statswoscaling = True
        #: (:obj:`list` < :obj:`str` > ) zmq source topics
        self.zmqtopics = []
        #: (:obj:`bool`) automatic zmq source topics
        self.autozmqtopics = False
        #: (:obj:`str`) file name translation json dictionary
        self.dirtrans = '{"/ramdisk/": "/gpfs/"}'
        #: (:obj:`str`) JSON dictionary with {label: tango attribute}
        #  for Tango Attribute source
        self.tangoattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: tango detector attribute}
        #  for Tango Attribute source
        self.tangodetattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: tina properties}
        #  for Tine Property source
        self.tineprops = '{}'
        #: (:obj:`str`) JSON dictionary with {label: epics PV name}
        #  for Epics PV source
        self.epicspvnames = '{}'
        #: (:obj:`str`) JSON dictionary with {label: epics PV shape}
        #  for Epics PV source
        self.epicspvshapes = '{}'
        #: (:obj:`str`) JSON dictionary with {label: doocs property}
        #  for DOOCS Property source
        self.doocsprops = '{}'
        #: (:obj:`str`) JSON dictionary with {label: tango attribute}
        #  for Tango Attribute Events source
        self.tangoevattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: file tango attribute}
        #  for Tango Attribute source
        self.tangofileattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: dir tango attribute}
        #  for Tango Attribute source
        self.tangodirattrs = '{}'
        #: (:obj:`str`) JSON dictionary with {label: url}
        #  for HTTP responce source
        self.httpurls = '{}'
        #: (:obj:`str`) JSON dictionary with {label: <server:port>}
        #  for ZMQ source
        self.zmqservers = '{}'
        #: (:obj:`str`) door device name
        self.doorname = ""
        #: (:obj:`str`) analysis device name
        self.analysisdevice = ""
        #: (:obj:`bool`) nexus file source keeps the file open
        self.nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.nxslast = False
        #: (:obj:`list` < :obj:`str`>) hidra detector server list
        self.detservers = "[]"
        #: (:obj:`bool`) use default detector servers
        self.defdetservers = True
        #: (:obj:`bool`) store detector geometry
        self.storegeometry = False
        #: (:obj:`bool`) fetch geometry from source
        self.geometryfromsource = False
        #: (:obj:`bool`) crosshair locker switched on
        self.crosshairlocker = True
        #: (:obj:`str`) json list with roi colors
        self.roiscolors = "[]"
        #: (:obj:`str`) float type for pixel intensity
        self.floattype = "float"

        #: (:obj:`str`) json list with filters
        self.filters = "[]"

        #: (:obj:`str`) json list with image source widget names
        self.imagesources = "[]"

        #: (:obj:`str`)  json list with tool widget names
        self.toolwidgets = "[]"

        #: (:class:`pyFAI.azimuthalIntegrator.AzimuthalIntegrator`)
        #       azimuthal integrator
        self.ai = None
        #: (:class:`pyFAI.azimuthalIntegrator.AzimuthalIntegrator`)
        #       azimuthal integrator
        #: (:class:`pyqtgraph.QtCore.QMutex`) ai mutex
        self.aimutex = QtCore.QMutex()

        #: (:obj:`float`) x-coordinates of the center of the image
        self.centerx = 0.0
        #: (:obj:`float`) y-coordinates of the center of the image
        self.centery = 0.0
        #: (:obj:`float`) energy in eV
        self.energy = 0.0
        #: (:obj:`float`) pixel x-size in um
        self.pixelsizex = 0.0
        #: (:obj:`float`) pixel y-size in um
        self.pixelsizey = 0.0
        #: (:obj:`float`) detector distance in mm
        self.detdistance = 0.0
        #: (:obj:`float`) poni1 parameter in m
        self.detponi1 = 0.0
        #: (:obj:`float`) poni2 parameter in m
        self.detponi2 = 0.0
        #: (:obj:`float`) rot1 parameter in rad
        self.detrot1 = 0.0
        #: (:obj:`float`) rot2 parameter in rad
        self.detrot2 = 0.0
        #: (:obj:`float`) rot3 parameter in rad
        self.detrot3 = 0.0
        #: (:obj:`str`) detector name
        self.detname = ""
        #: (:obj:`str`) detector splineFile
        self.detsplinefile = ""
        #: (:obj:`int`) number of points for diffractogram
        self.diffnpt = 1000
        #: (:obj:`bool`) correct solid angle flag
        self.correctsolidangle = True
        #: (:obj:`bool`) show all rois flag
        self.showallrois = False
        #: (:obj:`bool`) single rois flag
        self.singlerois = False
        #: (:obj:`bool`) send rois to LavueController flag
        self.sendrois = False
        #: (:obj:`bool`) send results to LavueController flag
        self.sendresults = False
        #: (:obj:`dict` < :obj:`str`, :obj:`dict` < :obj:`str`,`any`> >
        #                custom gradients
        self.__customgradients = {}
        #: (:obj:`bool`) store display parameters for specific sources
        self.sourcedisplay = False

        #: (:obj:`dict` < :obj:`str`, :obj:`dict` < :obj:`str`,`any`> >
        #                source display dictionary
        self.__sourcedisplay = {}

        self.__units = {
            'eV': ['eV'],
            'keV': ['keV'],
            'MeV': ['MeV'],
            'A': ['A', 'Angstrom'],
            'm': ['m', 'meter', 'metre'],
            'nm': ['nm', 'nanometer', 'nanometre'],
            'um': ['um', 'micrometer', 'micrometre'],
            'mm': ['mm', 'millimeter', 'millimetre'],
            'cm': ['cm', 'centimeter', 'centimetre'],
            'km': ['km', 'kilometer', 'kilometre'],
            'pixel': ['pixels', 'pixel'],
        }

        #: (:class:`pyqtgraph.QtCore.QMutex`) settings mutex
        self.__mutex = QtCore.QMutex()

    def setCustomGradients(self, gradients):
        """ sets custom gradients

        :param gradients: custom gradients
        :type gradients: :obj:`dict` <:obj:`str`, `any`>
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__customgradients = dict(gradients)

    def customGradients(self):
        """ sets source display parameters

        :returns: custom gradients
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """

        gradients = {}
        with QtCore.QMutexLocker(self.__mutex):
            gradients = dict(self.__customgradients)
        return gradients

    def setSourceDisplay(self, source, values):
        """ sets source display parameters

        :param source: source name
        :type source: :obj:`str`
        :param values: display parameter dictionary
        :type values: :obj:`dict` <:obj:`str`, `any`>
        """
        with QtCore.QMutexLocker(self.__mutex):
            if source and isinstance(values, dict):
                self.__sourcedisplay[str(source)] = values

    def sourceDisplay(self, source):
        """ gets source display parameters

        :param source: source name
        :type source: :obj:`str`
        :returns: display parameter dictionary
        :rtype: :obj:`dict` <:obj:`str`, `any`>
        """
        values = None
        with QtCore.QMutexLocker(self.__mutex):
            if source in self.__sourcedisplay.keys():
                values = dict(self.__sourcedisplay[str(source)])
        return values

    def load(self, settings):
        """ load settings

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        :returns: error messages list
        :rtype: :obj:`list` < (:obj:`str`, :obj:`str`) >
        """
        status = []
        qstval = str(settings.value("Configuration/Sardana", type=str))
        if qstval.lower() == "false":
            self.sardana = False
        else:
            self.sardana = True
        qstval = str(settings.value("Configuration/AddROIs", type=str))
        if qstval.lower() == "true":
            self.addrois = True
        qstval = str(settings.value("Configuration/OrderROIs", type=str))
        if qstval.lower() == "true":
            self.orderrois = True
        qstval = str(settings.value("Configuration/SecAutoPort", type=str))
        if qstval.lower() == "false":
            self.secautoport = False
        qstval = str(settings.value("Configuration/FloatType", type=str))
        if qstval.lower() in ["float", "float32", "float64"]:
            self.floattype = qstval.lower()
        else:
            self.floattype = "float"
        qstval = str(settings.value(
            "Configuration/ShowSubtraction", type=str))
        if qstval.lower() == "false":
            self.showsub = False
        qstval = str(settings.value(
            "Configuration/ShowTransformations", type=str))
        if qstval.lower() == "false":
            self.showtrans = False
        qstval = str(settings.value(
            "Configuration/ShowIntensityScaling", type=str))
        if qstval.lower() == "false":
            self.showscale = False
        qstval = str(settings.value(
            "Configuration/ShowIntensityLevels", type=str))
        if qstval.lower() == "false":
            self.showlevels = False
        qstval = str(settings.value(
            "Configuration/ShowFrameRate", type=str))
        if qstval.lower() == "false":
            self.showframerate = False
        qstval = str(settings.value("Configuration/ShowHistogram", type=str))
        if qstval.lower() == "false":
            self.showhisto = False
        qstval = str(settings.value("Configuration/ShowRangeWindowWidget",
                                    type=str))
        if qstval.lower() == "true":
            self.showrange = True
        qstval = str(settings.value("Configuration/ShowFilterWidget",
                                    type=str))
        if qstval.lower() == "true":
            self.showfilters = True
        qstval = str(settings.value("Configuration/ShowMemoryBuffer",
                                    type=str))
        if qstval.lower() == "true":
            self.showmbuffer = True
        qstval = str(settings.value("Configuration/ShowAdditionalHistogram",
                                    type=str))
        if qstval.lower() == "true":
            self.showaddhisto = True
        qstval = str(settings.value("Configuration/ShowMaskWidget", type=str))
        if qstval.lower() == "true":
            self.showmask = True
        qstval = str(settings.value(
            "Configuration/ShowHighValueMaskWidget", type=str))
        if qstval.lower() == "true":
            self.showhighvaluemask = True
        qstval = str(settings.value("Configuration/ShowStatistics", type=str))
        if qstval.lower() == "false":
            self.showstats = False
        qstval = str(settings.value("Configuration/ShowImageSteps", type=str))
        if qstval.lower() == "false":
            self.showsteps = False
        qstval = str(settings.value("Configuration/CrossHairLocker", type=str))
        if qstval.lower() == "false":
            self.crosshairlocker = False
        qstval = str(settings.value(
            "Configuration/CalculateVariance", type=str))
        if qstval.lower() == "true":
            self.calcvariance = True
        qstval = str(settings.value("Configuration/AspectLocked", type=str))
        if qstval.lower() == "true":
            self.aspectlocked = True
        qstval = str(settings.value("Configuration/AutoDownSample", type=str))
        if qstval.lower() == "true":
            self.autodownsample = True
        qstval = str(settings.value(
            "Configuration/KeepOriginalCoordinates", type=str))
        if qstval.lower() == "true":
            self.keepcoords = True
        qstval = str(settings.value(
            "Configuration/LazyImageSlider", type=str))
        if qstval.lower() == "false":
            self.lazyimageslider = False
        qstval = str(settings.value("Configuration/NXSFileOpen", type=str))
        if qstval.lower() == "true":
            self.nxsopen = True
        qstval = str(settings.value("Configuration/NXSLastImage", type=str))
        if qstval.lower() == "true":
            self.nxslast = True
        qstval = str(settings.value(
            "Configuration/SingleROIAliases", type=str))
        if qstval.lower() == "true":
            self.singlerois = True
        qstval = str(settings.value("Configuration/SendROIs", type=str))
        if qstval.lower() == "true":
            self.sendrois = True
        qstval = str(settings.value("Configuration/SendToolResults", type=str))
        if qstval.lower() == "true":
            self.sendresults = True
        qstval = str(settings.value("Configuration/ShowAllROIs", type=str))
        if qstval.lower() == "true":
            self.showallrois = True
        qstval = str(settings.value("Configuration/SecPort", type=str))
        try:
            int(qstval)
            self.secport = str(qstval)
        except Exception:
            pass
        qstval = str(settings.value("Configuration/HidraDataPort", type=str))
        try:
            int(qstval)
            self.hidraport = str(qstval)
        except Exception:
            pass
        qstval = str(settings.value("Configuration/MaxBufferSize", type=str))
        try:
            self.maxmbuffersize = str(qstval)
            int(self.maxmbuffersize)
        except Exception:
            self.maxmbuffersize = "1000"
        qstval = str(settings.value("Configuration/SourceTimeout", type=str))
        try:
            int(qstval)
            self.timeout = int(qstval)
        except Exception:
            pass
        qstval = str(settings.value(
            "Configuration/NumberOfImageSources", type=str))
        try:
            int(qstval)
            self.nrsources = int(qstval)
        except Exception:
            pass
        qstval = str(settings.value(
            "Configuration/MaskingWithZeros", type=str))
        if qstval.lower() == "true":
            self.zeromask = True
        qstval = str(settings.value(
            "Configuration/MaskingAsNAN", type=str))
        if qstval.lower() == "false":
            self.nanmask = False

        qstval = str(settings.value("Configuration/SecStream", type=str))
        if qstval.lower() == "true":
            try:
                if self.secautoport:
                    self.secsockopt = b"tcp://*:*"
                    self.secsocket.bind(self.secsockopt)
                    self.secport = unicode(self.secsocket.getsockopt(
                        zmq.LAST_ENDPOINT)).split(":")[-1]
                    if self.secport.endswith("'"):
                        self.secport = self.secport[:-1]
                else:
                    self.secsockopt = b"tcp://*:%s" % self.secport
                    self.secsocket.bind(self.secsockopt)
                self.secstream = True
            except Exception:
                self.secstream = False
                import traceback
                value = traceback.format_exc()
                text = "lavue: Cannot connect to: %s" % self.secsockopt
                status = [(text, value)]

        try:
            self.refreshrate = float(
                settings.value("Configuration/RefreshRate", type=str))
        except Exception:
            pass

        try:
            self.toolrefreshtime = float(
                settings.value("Configuration/ToolRefreshTime", type=str))
        except Exception:
            pass

        try:
            self.toolpollinginterval = float(
                settings.value("Configuration/ToolPollingInterval", type=str))
        except Exception:
            pass

        qstval = str(
            settings.value("Configuration/InterruptOnError", type=str))
        if qstval.lower() == "false":
            self.interruptonerror = False
        elif qstval.lower() == "true":
            self.interruptonerror = True
        qstval = str(
            settings.value("Configuration/LastImageFileName", type=str))
        if qstval:
            self.imagename = qstval
        qstval = str(
            settings.value("Configuration/LastMaskImageFileName", type=str))
        if qstval:
            self.maskimagename = qstval
        qstval = str(
            settings.value(
                "Configuration/LastBackgroundImageFileName", type=str))
        if qstval:
            self.bkgimagename = qstval
        qstval = str(
            settings.value("Configuration/LastCalibrationFileName", type=str))
        if qstval:
            self.calibrationfilename = qstval

        qstval = str(
            settings.value(
                "Configuration/StatisticsWithoutScaling", type=str))
        if qstval.lower() == "false":
            self.statswoscaling = False

        qstval = \
            settings.value(
                "Configuration/ImageSources", type=str)
        if qstval:
            self.imagesources = str(qstval)

        qstval = \
            settings.value(
                "Configuration/ToolWidgets", type=str)
        if qstval:
            self.toolwidgets = str(qstval)

        qstval = \
            settings.value(
                "Configuration/ZMQStreamTopics", type=str)
        if qstval:
            self.zmqtopics = [str(tp) for tp in qstval]

        qstval = \
            settings.value(
                "Configuration/HidraDetectorServers", type=str)
        if qstval:
            try:
                json.loads(qstval)
                self.detservers = qstval
            except Exception:
                self.detsetvers = json.dumps([str(tp) for tp in qstval])

        qstval = str(
            settings.value(
                "Configuration/HidraDefaultDetectorServers", type=str))
        if qstval.lower() == "false":
            self.defdetservers = False

        qstval = str(settings.value(
            "Configuration/AutoZMQStreamTopics", type=str))
        if qstval.lower() == "true":
            self.autozmqtopics = True
        qstval = str(
            settings.value("Configuration/DirectoryTranslation", type=str))
        if qstval:
            self.dirtrans = qstval

        qstval = str(
            settings.value("Configuration/TangoAttributes", type=str))
        if qstval:
            self.tangoattrs = qstval

        qstval = str(
            settings.value("Configuration/TangoDetectorAttributes", type=str))
        if qstval:
            self.tangodetattrs = qstval

        qstval = str(
            settings.value("Configuration/TineProperties", type=str))
        if qstval:
            self.tineprops = qstval

        qstval = str(
            settings.value("Configuration/EpicsPVNames", type=str))
        if qstval:
            self.epicspvnames = qstval
        qstval = str(
            settings.value("Configuration/EpicsPVShapes", type=str))
        if qstval:
            self.epicspvshapes = qstval

        qstval = str(
            settings.value("Configuration/DOOCSProperties", type=str))
        if qstval:
            self.doocsprops = qstval

        qstval = str(
            settings.value("Configuration/TangoEventsAttributes", type=str))
        if qstval:
            self.tangoevattrs = qstval

        qstval = str(
            settings.value("Configuration/TangoFileAttributes", type=str))
        if qstval:
            self.tangofileattrs = qstval

        qstval = str(
            settings.value("Configuration/TangoDirAttributes", type=str))
        if qstval:
            self.tangodirattrs = qstval

        qstval = str(
            settings.value("Configuration/HTTPURLs", type=str))
        if qstval:
            self.httpurls = qstval

        qstval = str(
            settings.value("Configuration/ZMQServers", type=str))
        if qstval:
            self.zmqservers = qstval

        qstval = str(
            settings.value("Configuration/StoreGeometry", type=str))
        if qstval.lower() == "true":
            self.storegeometry = True

        qstval = str(
            settings.value("Configuration/GeometryFromSource", type=str))
        if qstval.lower() == "true":
            self.geometryfromsource = True

        qstval = str(
            settings.value("Configuration/ROIsColors", type=str))
        if qstval:
            self.roiscolors = qstval

        qstval = str(
            settings.value("Configuration/Filters", type=str))
        if qstval:
            self.filters = qstval

        qstval = str(
            settings.value(
                "Configuration/SourceDisplayParams", type=str))
        if qstval.lower() == "true":
            self.sourcedisplay = True

        try:
            self.centerx = float(
                settings.value("Tools/CenterX", type=str))
        except Exception:
            pass
        try:
            self.centery = float(
                settings.value("Tools/CenterY", type=str))
        except Exception:
            pass
        try:
            self.energy = float(
                settings.value("Tools/Energy", type=str))
        except Exception:
            pass

        try:
            self.pixelsizex = float(
                settings.value("Tools/PixelSizeX", type=str))
        except Exception:
            pass
        try:
            self.pixelsizey = float(
                settings.value("Tools/PixelSizeY", type=str))
        except Exception:
            pass
        try:
            self.detdistance = float(
                settings.value("Tools/DetectorDistance", type=str))
        except Exception:
            pass
        try:
            self.detponi1 = float(
                settings.value("Tools/DetectorPONI1", type=str))
        except Exception:
            pass
        try:
            self.detponi2 = float(
                settings.value("Tools/DetectorPONI2", type=str))
        except Exception:
            pass
        try:
            self.diffnpt = float(
                settings.value("Tools/DiffractogramNPT", type=str))
        except Exception:
            pass
        qstval = str(settings.value(
            "Tools/CorrectSolidAngle", type=str))
        if qstval.lower() == "false":
            self.correctsolidangle = False
        try:
            self.detrot1 = float(
                settings.value("Tools/DetectorRot1", type=str))
        except Exception:
            pass
        try:
            self.detrot2 = float(
                settings.value("Tools/DetectorRot2", type=str))
        except Exception:
            pass
        try:
            self.detrot3 = float(
                settings.value("Tools/DetectorRot3", type=str))
        except Exception:
            pass
        qstval = str(
            settings.value("Tools/DetectorName", type=str))
        if qstval:
            self.detname = qstval
        qstval = str(
            settings.value("Tools/DetectorSplineFile",
                           type=str))
        if qstval:
            self.detsplinefile = qstval

        self.__loadDisplayParams(settings)
        self.__loadCustomGradients(settings)
        self.updateAISettings()
        return status

    def updateAISettings(self):
        """ update AI settings
        """
        if PYFAI:
            wvln = self.energy2m(self.energy)
            pixel1 = self.distance2m((self.pixelsizey, "um"))
            pixel2 = self.distance2m((self.pixelsizex, "um"))
            splineFile = self.detsplinefile or None
            detector = self.detname or None
            detdistance = self.distance2m((self.detdistance, "mm"))

            with QtCore.QMutexLocker(self.aimutex):
                if wvln and detdistance and pixel1 and pixel2:
                    from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
                    self.ai = AzimuthalIntegrator(
                        dist=detdistance,
                        poni1=self.detponi1,
                        poni2=self.detponi2,
                        rot1=self.detrot1,
                        rot2=self.detrot2,
                        rot3=self.detrot3,
                        pixel1=pixel1,
                        pixel2=pixel2,
                        splineFile=splineFile,
                        detector=detector,
                        wavelength=wvln)
                    if not self.detponi1 and not self.detponi2 \
                       and self.centerx and self.centery:
                        aif = self.ai.getFit2D()
                        self.ai.setFit2D(aif["directDist"],
                                         self.centerx,
                                         self.centery,
                                         aif["tilt"],
                                         aif["tiltPlanRotation"])

    def store(self, settings):
        """ Stores settings in QSettings object

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        """
        settings.setValue(
            "Configuration/AddROIs",
            self.addrois)
        settings.setValue(
            "Configuration/OrderROIs",
            self.orderrois)
        settings.setValue(
            "Configuration/ShowSubtraction",
            self.showsub)
        settings.setValue(
            "Configuration/ShowTransformations",
            self.showtrans)
        settings.setValue(
            "Configuration/ShowIntensityScaling",
            self.showscale)
        settings.setValue(
            "Configuration/ShowIntensityLevels",
            self.showlevels)
        settings.setValue(
            "Configuration/ShowFrameRate",
            self.showframerate)
        settings.setValue(
            "Configuration/ShowHistogram",
            self.showhisto)
        settings.setValue(
            "Configuration/ShowAdditionalHistogram",
            self.showaddhisto)
        settings.setValue(
            "Configuration/ShowMaskWidget",
            self.showmask)
        settings.setValue(
            "Configuration/ShowRangeWindowWidget",
            self.showrange)
        settings.setValue(
            "Configuration/ShowFilterWidget",
            self.showfilters)
        settings.setValue(
            "Configuration/ShowMemoryBuffer",
            self.showmbuffer)
        settings.setValue(
            "Configuration/ShowHighValueMaskWidget",
            self.showhighvaluemask)
        settings.setValue(
            "Configuration/ShowStatistics",
            self.showstats)
        settings.setValue(
            "Configuration/ShowImageSteps",
            self.showsteps)
        settings.setValue(
            "Configuration/CrossHairLocker",
            self.crosshairlocker)
        settings.setValue(
            "Configuration/CalculateVariance",
            self.calcvariance)
        settings.setValue(
            "Configuration/RefreshRate",
            self.refreshrate)
        settings.setValue(
            "Configuration/ToolRefreshTime",
            self.toolrefreshtime)
        settings.setValue(
            "Configuration/ToolPollingInterval",
            self.toolpollinginterval)
        settings.setValue(
            "Configuration/SecPort",
            self.secport)
        settings.setValue(
            "Configuration/FloatType",
            self.floattype)
        settings.setValue(
            "Configuration/HidraDataPort",
            self.hidraport)
        settings.setValue(
            "Configuration/MaxBufferSize",
            self.maxmbuffersize)
        settings.setValue(
            "Configuration/SecAutoPort",
            self.secautoport)
        settings.setValue(
            "Configuration/SecStream",
            self.secstream)
        settings.setValue(
            "Configuration/MaskingWithZeros",
            self.zeromask)
        settings.setValue(
            "Configuration/MaskingAsNAN",
            self.nanmask)
        settings.setValue(
            "Configuration/Sardana",
            self.sardana)
        settings.setValue(
            "Configuration/InterruptOnError",
            self.interruptonerror)
        settings.setValue(
            "Configuration/SourceTimeout",
            self.timeout)
        settings.setValue(
            "Configuration/NumberOfImageSources",
            self.nrsources)
        settings.setValue(
            "Configuration/AspectLocked",
            self.aspectlocked)
        settings.setValue(
            "Configuration/AutoDownSample",
            self.autodownsample)
        settings.setValue(
            "Configuration/KeepOriginalCoordinates",
            self.keepcoords)
        settings.setValue(
            "Configuration/LazyImageSlider",
            self.lazyimageslider)
        settings.setValue(
            "Configuration/LastImageFileName",
            self.imagename)
        settings.setValue(
            "Configuration/LastMaskImageFileName",
            self.maskimagename)
        settings.setValue(
            "Configuration/LastCalibrationFileName",
            self.calibrationfilename)
        settings.setValue(
            "Configuration/LastBackgroundImageFileName",
            self.bkgimagename)
        settings.setValue(
            "Configuration/StatisticsWithoutScaling",
            self.statswoscaling)
        settings.setValue(
            "Configuration/ImageSources",
            self.imagesources)
        settings.setValue(
            "Configuration/ToolWidgets",
            self.toolwidgets)
        settings.setValue(
            "Configuration/ZMQStreamTopics",
            self.zmqtopics)
        settings.setValue(
            "Configuration/HidraDetectorServers",
            self.detservers)
        settings.setValue(
            "Configuration/HidraDefaultDetectorServers",
            self.defdetservers)
        settings.setValue(
            "Configuration/AutoZMQStreamTopics",
            self.autozmqtopics)
        settings.setValue(
            "Configuration/DirectoryTranslation",
            self.dirtrans)
        settings.setValue(
            "Configuration/TangoAttributes",
            self.tangoattrs)
        settings.setValue(
            "Configuration/TangoDetectorAttributes",
            self.tangodetattrs)
        settings.setValue(
            "Configuration/TineProperties",
            self.tineprops)
        settings.setValue(
            "Configuration/EpicsPVNames",
            self.epicspvnames)
        settings.setValue(
            "Configuration/EpicsPVShapes",
            self.epicspvshapes)
        settings.setValue(
            "Configuration/DOOCSProperties",
            self.doocsprops)
        settings.setValue(
            "Configuration/TangoEventsAttributes",
            self.tangoevattrs)
        settings.setValue(
            "Configuration/TangoFileAttributes",
            self.tangofileattrs)
        settings.setValue(
            "Configuration/TangoDirAttributes",
            self.tangodirattrs)
        settings.setValue(
            "Configuration/ZMQServers",
            self.zmqservers)
        settings.setValue(
            "Configuration/HTTPURLs",
            self.httpurls)
        settings.setValue(
            "Configuration/NXSLastImage",
            self.nxslast)
        settings.setValue(
            "Configuration/NXSFileOpen",
            self.nxsopen)
        settings.setValue(
            "Configuration/StoreGeometry",
            self.storegeometry)
        settings.setValue(
            "Tools/CorrectSolidAngle",
            self.correctsolidangle)
        settings.setValue(
            "Configuration/GeometryFromSource",
            self.geometryfromsource)
        settings.setValue(
            "Configuration/ROIsColors",
            self.roiscolors)
        settings.setValue(
            "Configuration/Filters",
            self.filters)
        settings.setValue(
            "Configuration/SendROIs",
            self.sendrois)
        settings.setValue(
            "Configuration/SendToolResults",
            self.sendresults)
        settings.setValue(
            "Configuration/SingleROIAliases",
            self.singlerois)
        settings.setValue(
            "Configuration/ShowAllROIs",
            self.showallrois)
        settings.setValue(
            "Configuration/SourceDisplayParams",
            self.sourcedisplay)

        if not self.storegeometry:
            self.centerx = 0.0
            self.centery = 0.0
            self.energy = 0.0
            self.pixelsizex = 0.0
            self.pixelsizey = 0.0
            self.detdistance = 0.0
            self.detrot1 = 0.0
            self.detrot2 = 0.0
            self.detrot3 = 0.0
            self.detponi1 = 0.0
            self.detponi2 = 0.0

        settings.setValue(
            "Tools/CenterX",
            self.centerx)
        settings.setValue(
            "Tools/CenterY",
            self.centery)
        settings.setValue(
            "Tools/Energy",
            self.energy)
        settings.setValue(
            "Tools/PixelSizeX",
            self.pixelsizex)
        settings.setValue(
            "Tools/PixelSizeY",
            self.pixelsizey)
        settings.setValue(
            "Tools/DetectorDistance",
            self.detdistance)
        settings.setValue(
            "Tools/DetectorPONI1",
            self.detponi1)
        settings.setValue(
            "Tools/DetectorPONI2",
            self.detponi2)
        settings.setValue(
            "Tools/DiffractogramNPT",
            self.diffnpt)
        settings.setValue(
            "Tools/DetectorRot1",
            self.detrot1)
        settings.setValue(
            "Tools/DetectorRot2",
            self.detrot2)
        settings.setValue(
            "Tools/DetectorRot3",
            self.detrot3)
        settings.setValue(
            "Tools/DetectorName",
            self.detname)
        settings.setValue(
            "Tools/DetectorSplineFile",
            self.detsplinefile)

        self.__storeDisplayParams(settings)
        self.__storeCustomGradients(settings)

    def length2ev(self, length):
        """ converts length to energy  in eV

        :param length: length as value in A or tuple with units
        :type length: :obj:`float` or (:obj:`float`, :obj:`str`)
        :returns: energy in eV
        :rtype: :obj:`float`
        """
        energy = None
        #: :obj:`float`  value of hc in eV * um
        hc = 1.23984193
        if length is not None:
            if type(length) in [list, tuple]:
                if len(length) == 1:
                    if length[0]:
                        energy = hc * 10000 / length[0]
                elif len(length) > 1:
                    if length[1] in self.__units['A']:
                        if length[0]:
                            energy = hc * 10000 / length[0]
                    elif length[1] in self.__units['nm']:
                        if length[0]:
                            energy = hc * 1000 / length[0]
                    elif length[1] in self.__units['um']:
                        if length[0]:
                            energy = hc / length[0]
                    elif length[1] in self.__units['m']:
                        if length[0]:
                            energy = hc * 1e-6 / length[0]
                    elif length[1] in self.__units['mm']:
                        if length[0]:
                            energy = hc * 1e-3 / length[0]
                    elif length[1] in self.__units['cm']:
                        if length[0]:
                            energy = hc * 1e-4 / length[0]
            else:
                if length:
                    energy = hc * 10000 / length
        return energy

    def energy2m(self, energy):
        """ converts energy to m

        :param energy: energy as value in eV or tuple with units
        :type energy: :obj:`float` or (:obj:`float`, :obj:`str`)
        :returns: length in m
        :rtype: :obj:`float`
        """
        length = None
        #: :obj:`float`  value of hc in eV * um
        hc = 1.23984193
        if energy is not None:
            if type(energy) in [list, tuple]:
                if len(energy) == 1:
                    if energy[0]:
                        length = hc * 1e-6 / energy[0]
                elif len(energy) > 1:
                    if energy[1] in self.__units['eV']:
                        if energy[0]:
                            length = hc * 1e-6 / energy[0]
                    elif energy[1] in self.__units['keV']:
                        if energy[0]:
                            length = hc * 1e-3 / energy[0]
                    elif energy[1] in self.__units['MeV']:
                        if energy[0]:
                            length = hc / energy[0]
            elif energy:
                length = hc * 1e-6 / energy
        return length

    def distance2mm(self, distance):
        """ converts distance to mm units

        :param distance: distance as value in m or tuple with units
        :type distance: :obj:`float` or (:obj:`float`, :obj:`str`)
        :returns: distance in mm
        :rtype: :obj:`float`
        """
        res = None
        if distance is not None:
            if type(distance) in [list, tuple]:
                if len(distance) == 1:
                    res = distance[0] * 1e+3
                elif len(distance) > 1:
                    if distance[1] in self.__units['A']:
                        res = distance[0] * 1e-7
                    elif distance[1] in self.__units['nm']:
                        res = distance[0] * 1e-6
                    elif distance[1] in self.__units['um']:
                        res = distance[0] * 1e-3
                    elif distance[1] in self.__units['km']:
                        res = distance[0] * 1e+6
                    elif distance[1] in self.__units['m']:
                        res = distance[0] * 1e+3
                    elif distance[1] in self.__units['mm']:
                        res = distance[0]
                    elif distance[1] in self.__units['cm']:
                        res = distance * 1e+1
            else:
                res = distance * 1e+3
        return res

    def distance2m(self, distance):
        """ converts distance to m units

        :param distance: distance as value in m or tuple with units
        :type distance: :obj:`float` or (:obj:`float`, :obj:`str`)
        :returns: distance in m
        :rtype: :obj:`float`
        """
        res = None
        if distance is not None:
            if type(distance) in [list, tuple]:
                if len(distance) == 1:
                    res = distance[0] * 1e+3
                elif len(distance) > 1:
                    if distance[1] in self.__units['A']:
                        res = distance[0] * 1e-10
                    elif distance[1] in self.__units['nm']:
                        res = distance[0] * 1e-9
                    elif distance[1] in self.__units['um']:
                        res = distance[0] * 1e-6
                    elif distance[1] in self.__units['km']:
                        res = distance[0] * 1e+3
                    elif distance[1] in self.__units['m']:
                        res = distance[0]
                    elif distance[1] in self.__units['mm']:
                        res = distance[0] * 1e-3
                    elif distance[1] in self.__units['cm']:
                        res = distance * 1e-2
            else:
                res = distance * 1e+3
        return res

    def distance2um(self, distance):
        """ converts distance to um units

        :param distance: distance as value in m or tuple with units
        :type distance: :obj:`float` or (:obj:`float`, :obj:`str`)
        :returns: distance in um
        :rtype: :obj:`float`
        """
        res = None
        if distance is not None:
            if type(distance) in [list, tuple]:
                if len(distance) == 1:
                    res = distance[0] * 1e+6
                elif len(distance) > 1:
                    if distance[1] in self.__units['A']:
                        res = distance[0] * 1e-4
                    elif distance[1] in self.__units['nm']:
                        res = distance[0] * 1e-3
                    elif distance[1] in self.__units['um']:
                        res = distance[0]
                    elif distance[1] in self.__units['km']:
                        res = distance[0] * 1e+9
                    elif distance[1] in self.__units['m']:
                        res = distance[0] * 1e+6
                    elif distance[1] in self.__units['mm']:
                        res = distance[0] * 1e+3
                    elif distance[1] in self.__units['cm']:
                        res = distance * 1e+4
            else:
                res = distance * 1e+6
        return res

    def distance2pixels(self, distance, psize):
        """ converts distance to pixels

        :param distance: distance as value in pixels or tuple with units
        :type distance: :obj:`float` or (:obj:`float`, :obj:`str`)
        :param psize: pixel size
        :type psize: :obj:`float`
        :returns: distance in pixels
        :rtype: :obj:`float`
        """
        res = None
        if distance is not None:
            if type(distance) in [list, tuple]:
                if len(distance) == 1:
                    res = distance[0]
                elif len(distance) > 1:
                    if distance[1] in self.__units['pixel']:
                        res = distance[0]
                    elif distance[1] in self.__units['nm']:
                        res = distance[0] * 1e+3 / psize
                    elif distance[1] in self.__units['um']:
                        res = distance[0] / psize
                    elif distance[1] in self.__units['m']:
                        res = distance[0] * 1e-6 / psize
                    if distance[1] in self.__units['A']:
                        res = distance[0] * 1e+4 / psize
                    elif distance[1] in self.__units['mm']:
                        res = distance[0] * 1e-3 / psize
                    elif distance[1] in self.__units['cm']:
                        res = distance[0] * 1e-4 / psize
            else:
                res = distance
        return res

    def pixelsize2um(self, psize):
        """ converts pixel size to um units

        :param psize: pixelsize as value in m or tuple with units
        :type psize: :obj:`float` or
               (:obj:`float`, :obj:`str`, :obj:`float`, :obj:`str`)
        :returns: pixelsize in  um
        :rtype: (:obj:`float`, :obj:`float`)
        """
        resx = None
        resy = None
        if psize is not None:
            if type(psize) in [list, tuple]:
                if len(psize) == 2:
                    if type(psize[0]) in [list, tuple]:
                        resx = self.distance2um(psize[0])
                    else:
                        resx = psize[0] * 1e+6
                    if type(psize[1]) in [list, tuple]:
                        resy = self.distance2um(psize[1])
                    else:
                        resy = psize[1] * 1e+6
                elif len(psize) > 2:
                    if len(psize) == 3:
                        px, py, ux = psize
                        uy = ux
                    elif len(psize) >= 4:
                        px, ux,  py, uy = psize
                    resx = self.distance2um([px, ux])
                    resy = self.distance2um([py, uy])
        return resx, resy

    def xyposition2pixels(self, xypos):
        """ converts xy position to pixel units

        :param xypos: xy-position a tuple value or tuple with units
        :type xypos: :obj:`float` or
               (:obj:`float`, :obj:`str`, :obj:`float`, :obj:`str`)
        :returns: xy-position in  pixels
        :rtype: (:obj:`float`, :obj:`float`)
        """
        resx = None
        resy = None
        if xypos is not None:
            if type(xypos) in [list, tuple]:
                if len(xypos) == 2:
                    if type(xypos[0]) in [list, tuple]:
                        resx = self.distance2pixels(xypos[0], self.pixelsizex)
                    else:
                        resx = xypos[0]
                    if type(xypos[1]) in [list, tuple]:
                        resy = self.distance2pixels(xypos[1], self.pixelsizey)
                    else:
                        resy = xypos[1]

                elif len(xypos) > 2:
                    if len(xypos) == 3:
                        px, py, ux = xypos
                        uy = ux
                    elif len(xypos) >= 4:
                        px, ux,  py, uy = xypos
                    resx = self.distance2pixels([px, ux], self.pixelsizex)
                    resy = self.distance2pixels([py, uy], self.pixelsizey)
        return resx, resy

    def updateDetectorParameters(self):
        """ update physical parameters

        """
        if PYFAI:
            with QtCore.QMutexLocker(self.aimutex):
                aic = self.ai.get_config()
                self.pixelsizex = self.distance2um(
                    (self.ai.get_pixel2(), "m"))
                self.pixelsizey = self.distance2um(
                    (self.ai.get_pixel1(), "m"))
            self.detponi1 = aic["poni1"]
            self.detponi2 = aic["poni2"]
            self.detrot1 = aic["rot1"]
            self.detrot2 = aic["rot2"]
            self.detrot3 = aic["rot3"]
            self.detsplinefile = self.ai.splineFile
            self.detname = aic["detector"]
            self.detdistance = self.distance2mm(
                (aic["dist"], "m"))
            self.energy = self.length2ev(
                (float(aic["wavelength"]), "m"))
            with QtCore.QMutexLocker(self.aimutex):
                aif = self.ai.getFit2D()
                self.centerx = float(aif["centerX"])
                self.centery = float(aif["centerY"])

    def updateMetaData(self, **kargs):
        """ update physical parameters

        :param kargs:  physical parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        # #: (:obj:`float`) x-coordinates of the center of the image
        # self.centerx = 0.0
        # #: (:obj:`float`) y-coordinates of the center of the image
        # self.centery = 0.0
        # #: (:obj:`float`) energy in eV
        # self.energy = 0.0
        # #: (:obj:`float`) pixel x-size in um
        # self.pixelsizex = 0.0
        # #: (:obj:`float`) pixel y-size in um
        # self.pixelsizey = 0.0
        # #: (:obj:`float`) detector distance in mm
        # self.detdistance = 0.0
        # beam_xy pixels
        # wavelength A
        # detector_distance m
        # pixel_size m
        if "wavelength" in kargs.keys():
            energy = self.length2ev(kargs["wavelength"])
            if energy is not None:
                self.energy = energy

        if "detector_distance" in kargs.keys():
            detdistance = self.distance2mm(kargs["detector_distance"])
            if detdistance is not None:
                self.detdistance = detdistance
        if "distance" in kargs.keys():
            detdistance = self.distance2mm(kargs["distance"])
            if detdistance is not None:
                self.detdistance = detdistance

        if "pixel_size" in kargs.keys():
            psizex, psizey = self.pixelsize2um(kargs["pixel_size"])
            if psizex is not None and psizey is not None:
                self.pixelsizex = psizex
                self.pixelsizey = psizey

        if "x_pixel_size" in kargs.keys():
            psizex = self.distance2um(kargs["x_pixel_size"])
            if psizex is not None:
                self.pixelsizex = psizex
        if "y_pixel_size" in kargs.keys():
            psizey = self.distance2um(kargs["y_pixel_size"])
            if psizey is not None:
                self.pixelsizey = psizey

        if "beam_xy" in kargs.keys():
            cx, cy = self.xyposition2pixels(kargs["beam_xy"])
            if psizex is not None and psizey is not None:
                self.centerx = cx
                self.centery = cy
        if "beam_x" in kargs.keys():
            cx = self.distance2pixels(kargs["beam_x"], self.pixelsizex)
            if cx is not None:
                self.centerx = cx
        if "beam_y" in kargs.keys():
            cy = self.distance2pixels(kargs["beam_y"], self.pixelsizey)
            if cy is not None:
                self.centery = cy

        if "beam_center_x" in kargs.keys():
            cx = self.distance2pixels(kargs["beam_center_x"], self.pixelsizex)
            if cx is not None:
                self.centerx = cx
        if "beam_center_y" in kargs.keys():
            cy = self.distance2pixels(kargs["beam_center_y"], self.pixelsizey)
            if cy is not None:
                self.centery = cy

    def __storeCustomGradients(self, settings):
        """ Stores custom color gradients settings in QSettings object

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        """
        with QtCore.QMutexLocker(self.__mutex):
            for name, value in self.__customgradients.items():
                settings.setValue(
                    "CustomColorGradients/%s" % (name), str(value))
            try:
                settings.beginGroup("CustomColorGradients")
                oldkeys = set([str(key) for key in settings.allKeys()]) - \
                    set(self.__customgradients.keys())
                for key in oldkeys:
                    settings.remove(key)
            finally:
                settings.endGroup()

    def __loadCustomGradients(self, settings):
        """ Loads custom color gradients settings in QSettings object

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        """
        with QtCore.QMutexLocker(self.__mutex):
            settings.beginGroup("CustomColorGradients")
            try:
                for key in settings.allKeys():
                    qstval = str(
                        settings.value(
                            "%s" % str(key), type=str))
                    self.__customgradients[str(key)] = eval(str(qstval))
            finally:
                settings.endGroup()

    def __storeDisplayParams(self, settings):
        """ Stores display parameters settings in QSettings object

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        """
        with QtCore.QMutexLocker(self.__mutex):
            for source, dct in self.__sourcedisplay.items():
                for key, value in dct.items():
                    settings.setValue(
                        "Source_%s/%s" % (source, key),
                        value)
                try:
                    settings.beginGroup("Source_%s" % source)
                    oldkeys = set([str(key) for key in settings.allKeys()]) - \
                        set(dct.keys())
                    for key in oldkeys:
                        settings.remove(key)
                finally:
                    settings.endGroup()

    def __loadDisplayParams(self, settings):
        """ loads display parameters settings

        :param settings: QSettings object
        :type settings: :class:`pyqtgraph.QtCore.QSettings`
        """
        with QtCore.QMutexLocker(self.__mutex):
            qgroups = list(settings.childGroups())
            groups = [str(f) for f in qgroups
                      if str(f).startswith("Source_")]

            for gr in groups:
                source = gr[7:]
                if source not in self.__sourcedisplay.keys():
                    self.__sourcedisplay[source] = {}
                settings.beginGroup(gr)
                try:
                    for key in settings.allKeys():
                        qstval = str(
                            settings.value(
                                "%s" % str(key), type=str))
                        self.__sourcedisplay[source][str(key)] = str(qstval)
                finally:
                    settings.endGroup()
