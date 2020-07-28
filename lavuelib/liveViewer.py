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
#


""" live viewer settings """

from __future__ import print_function
from __future__ import unicode_literals


import time
import socket
import json
from .qtuic import uic
import numpy as np
import pyqtgraph as _pg
from pyqtgraph import QtCore, QtGui
import os
import zmq
import sys
import argparse
import ntpath
import logging
import scipy.ndimage

from . import imageSource as isr
from . import messageBox

# from . import sourceGroupBox
from . import sourceTabWidget
from . import toolWidget
from . import sourceWidget
from . import preparationGroupBox
from . import memoryBufferGroupBox
from . import scalingGroupBox
from . import levelsGroupBox
from . import channelGroupBox
from . import statisticsGroupBox
from . import imageWidget
from . import imageField
from . import configDialog
from . import release
from . import edDictDialog
from . import filters
from . import rangeWindowGroupBox
from . import filtersGroupBox
from . import helpForm
from .sardanaUtils import debugmethod
# from . import imageNexusExporter

try:
    from . import controllerClient
    TANGOCLIENT = True
except Exception:
    TANGOCLIENT = False

from . import imageFileHandler
from . import sardanaUtils
from . import dataFetchThread
from . import settings

from .hidraServerList import HIDRASERVERLIST


logger = logging.getLogger("lavue")

if sys.version_info > (3,):
    basestring = str
    unicode = str

__import__("lavuelib.imageNexusExporter")

#: ( (:obj:`str`,:obj:`str`,:obj:`str`) )
#:         pg major version, pg minor verion, pg patch version
_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".")[:3] \
    if _pg.__version__ else ("0", "9", "0")

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MainDialog.ui"))


_logginglevel = 'info'


def setLoggerLevel(logger, level):
    global _logginglevel
    """ sets logging level from string
    :param logger: logger
    :type logger: :obj:`logging.logger`
    :param level: logging level
    :type level: :obj:`str`
    """
    levels = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}
    _logginglevel = level if level in levels else "info"
    dlevel = levels.get(level, logging.INFO)
    logger.setLevel(dlevel)


class MainWindow(QtGui.QMainWindow):

    @debugmethod
    def __init__(self, options, parent=None):
        """ constructor

        :param options: commandline options
        :type options: :class:`argparse.Namespace`
        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QMainWindow.__init__(self, parent)
        self.__lavue = LiveViewer(options, self)
        self.centralwidget = QtGui.QWidget(self)
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.addWidget(self.__lavue, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        if hasattr(options, "instance") and options.instance:
            self.setWindowTitle(
                "laVue: Live Image Viewer (v%s) [%s]" %
                (str(release.__version__), options.instance))
        else:
            self.setWindowTitle(
                "laVue: Live Image Viewer (v%s)" %
                str(release.__version__))

    @debugmethod
    def closeEvent(self, event):
        """ stores the setting before finishing the application

        :param event: close event
        :type event:  :class:`pyqtgraph.QtCore.QEvent`:
        """
        self.__lavue.closeEvent(event)
        QtGui.QMainWindow.closeEvent(self, event)


class LavueState(object):
    """ lavue state
    """
    @debugmethod
    def __init__(self):
        """  constructor
        """
        #: (:obj:`dict` < :obj:`str`, :obj:`any`>) lavue state dictionary
        self.__state = {}

    def updateState(self, dct):
        """update lavue state dictonary

        :param dct: lavue state dictionary
        :type dct: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if dct is not None:
            self.__state.update(dct)
            self.__state["__timestamp__"] = time.time()

    def dump(self):
        """ returns string representation

        :returns: string representation
        :rtype: :obj:`str`
        """
        return json.dumps(self.__state)


class PartialData(object):
    """ partial data
    """

    #: ( :obj:`dict < :obj:`str`, :obj:'bool`> `)
    #    transformation transpose map
    tpose = {
        "none": False,
        "fup": False,
        "flr": False,
        "t": True,
        "r90": True,
        "r180": False,
        "r270": True,
        "r180t": True,
    }

    @debugmethod
    def __init__(self, name, rawdata, metadata, x, y, tr):
        """ constructor

        :param name: data name
        :type name: :obj:`str`
        :param rawdata: raw data
        :type rawdata: :obj:`numpy.ndarray`
        :param metadata:  json dictionary with metadata
        :type metadata: :obj:`str`
        :param x: x translation
        :type x: :obj:`int`
        :param y: y translation
        :type y: :obj:`int`
        :param tr: transformation, e.g. fup, flr, t, r90, r180, r270, r180t
        :type tr: :obj:`str`
        """
        #: (:obj:`str`) data name
        self.name = name
        #: (:class:`numpy.ndarray`) raw data
        self.__rawdata = rawdata
        #: (:class:`numpy.ndarray`) transformed data
        self.__data = None
        #: (:obj:`str`) json dictionary with metadata
        self.metadata = metadata
        #: (:obj:`int`) x translation
        self.x = x
        #: (:obj:`int`) y translation
        self.y = y
        #: (:obj:`int`) x size
        self.sx = 1
        #: (:obj:`int`) y size
        self.sy = 1
        #: (:obj:`str`) transformation
        self.tr = tr
        self.data()
        if hasattr(self.__data, "shape"):
            if len(self.__data.shape) > 0:
                self.sx = self.__data.shape[0]
            if len(self.__data.shape) > 1:
                self.sy = self.__data.shape[1]

    def dtype(self):
        """ provides data type

        :returns: numpy data type
        :rtype: :obj:`numpy.dtype`
        """
        if hasattr(self.__data, "dtype"):
            return self.__data.dtype
        else:
            return None

    def data(self):
        """ provides transformed data

        :returns: transformed data
        :rtype: :obj:`numpy.ndarray`
        """
        if self.__data is None:
            if not self.tr or self.tr == "none":
                self.__data = self.__rawdata
            elif self.tr == 'fud':
                self.__data = np.fliplr(self.__rawdata)
            elif self.tr == 'flr':
                self.__data = np.flipud(self.__rawdata)
            elif self.tr == 't':
                self.__data = np.swapaxes(self.__rawdata, 0, 1)
            elif self.tr == 'r90':
                self.__data = np.swapaxes(np.flipud(self.__rawdata), 0, 1)
            elif self.tr == 'r180':
                self.__data = np.flipud(np.fliplr(self.__rawdata))
            elif self.tr == 'r270':
                self.__data = np.swapaxes(np.fliplr(self.__rawdata), 0, 1)
            elif self.tr == 'r180t':
                self.__data = np.swapaxes(
                    np.fliplr(np.flipud(self.__rawdata)), 0, 1)
            else:
                try:
                    if self.tr.startswith("rot") and self.tr.endswith("t"):
                        rot = -float(self.tr[3:-1])
                        self.__data = scipy.ndimage.rotate(
                            self.__rawdata, rot).T
                    elif self.tr.startswith("rot"):
                        rot = -float(self.tr[3:])
                        self.__data = scipy.ndimage.rotate(self.__rawdata, rot)
                    elif self.tr.startswith("r") and self.tr.endswith("t"):
                        rot = -float(self.tr[1:-1])
                        self.__data = scipy.ndimage.rotate(
                            self.__rawdata, rot).T
                    elif self.tr.startswith("r"):
                        rot = -float(self.tr[1:])
                        self.__data = scipy.ndimage.rotate(self.__rawdata, rot)
                    else:
                        self.__data = self.__rawdata
                except Exception as e:
                    logger.debug(str(e))
                    self.__data = self.__rawdata
        return self.__data

    @debugmethod
    def tolist(self):
        """ converts partial data to a list

        :returns: a list: [name, rawdata, metadata, x, y, sx, sy, tr]
        :rtype: [:obj:`str`, :obj:`numpy.ndarray', :obj:`str`, :obj:`int`,
                 :obj:`int`, :obj:`int`, :obj:`int`, :obj:`str`]
        """
        return [self.name, self.__rawdata, self.metadata,
                self.x, self.y, self.sx, self.sy, self.tr]


class LiveViewer(QtGui.QDialog):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) state updated signal
    _stateUpdated = QtCore.pyqtSignal(bool)

    @debugmethod
    def __init__(self, options, parent=None):
        """ constructor

        :param options: commandline options
        :type options: :class:`argparse.Namespace`
        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        if options.mode and options.mode.lower() in ["expert"]:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "expert"
        else:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "user"

        #: (:obj:`str`) instance name
        self.__instance = options.instance
        #: (:obj:`bool`) histogram should be updated
        self.__updatehisto = False
        #: (:obj:`int`) program pid
        self.__apppid = os.getpid()
        #: (:obj:`str`) host name
        self.__targetname = socket.getfqdn()

        #: (:obj:`list` < :obj:`str` > ) allowed source metadata
        self.__allowedmdata = ["datasources"]
        #: (:obj:`list` < :obj:`str` > ) allowed widget metadata
        self.__allowedwgdata = ["axisscales", "axislabels"]

        #: (:class:`lavuelib.sardanaUtils.SardanaUtils`)
        #:  sardana utils
        self.__sardana = None

        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings.Settings()
        self.__settings.load(QtCore.QSettings())

        self.__lavuestate = LavueState()

        # (:class:`lavuelib.imageSource.BaseSource`) data source object
        self.__datasources = [isr.BaseSource()
                              for _ in range(self.__settings.nrsources)]

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__sourcetypes = []

        #: (:obj:`list` < :obj:`str` > ) all source aliases
        self.__allsourcealiases = []
        #: (:obj:`dict` < :obj:`str`, :obj:`str` > ) source alias names
        self.__srcaliasnames = {}

        #: (:obj:`list` < :obj:`str` > ) tool class names
        self.__tooltypes = []

        #: (:obj:`list` < :obj:`str` > ) all tool aliases
        self.__alltoolaliases = []
        #: (:obj:`dict` < :obj:`str`, :obj:`str` > ) tool alias names
        self.__tlaliasnames = {}

        self.__updateTypeList(
            sourceWidget.swproperties, self.__sourcetypes,
            self.__allsourcealiases, self.__srcaliasnames
        )
        self.__updateTypeList(
            toolWidget.twproperties, self.__tooltypes,
            self.__alltoolaliases, self.__tlaliasnames
        )

        #: (:obj:`list` < :obj:`str` > ) rgb tool class names
        self.__rgbtooltypes = []
        self.__rgbtooltypes.append("RGBIntensityToolWidget")

        #: (:class:`lavuelib.controllerClient.ControllerClient`)
        #:   tango controller client
        self.__tangoclient = None

        #: (:obj:`int`) stacking dimension
        self.__growing = None
        #: (:obj:`int`) current frame id
        self.__frame = None
        #: (:obj:`str`) nexus field path
        self.__fieldpath = None
        #: (:obj:`bool`) closing flag
        self.__closing = False
        #: (:obj:`bool`) ploting flag
        self.__ploting = False

        #: (:class:`filters.FilterList` ) user filters
        self.__filters = filters.FilterList()

        #: (:obj:`int`) filter state
        self.__filterstate = 0

        #: (:obj:`float`) last time read
        self.__lasttime = 0
        #: (:obj:`float`) current time
        self.__currentime = 0

        # WIDGET DEFINITIONS
        #: (:class:`lavuelib.sourceTabWidget.SourceTabWidget`) source groupbox
        self.__sourcewg = sourceTabWidget.SourceTabWidget(
            parent=self, sourcetypes=self.__sourcetypes,
            expertmode=(self.__umode == 'expert'),
            nrsources=self.__settings.nrsources
        )
        self.__sourcewg.updateSourceComboBox(
            [self.__srcaliasnames[twn]
             for twn in json.loads(str(self.__settings.imagesources))
             if twn in self.__srcaliasnames.keys()]
        )

        #: (:class:`lavuelib.rangeWindowGroupBox.RangeWindowGroupBox`)
        #: memory buffer groupbox
        self.__rangewg = rangeWindowGroupBox.RangeWindowGroupBox(
            parent=self)
        self.__rangewg.factorChanged.connect(self._resizePlot)
        self.__rangewg.rangeWindowChanged.connect(self._resizePlot)
        self.__rangewg.functionChanged.connect(self._resizePlot)
        #: (:class:`lavuelib.memoryBufferGroupBox.MemoryBufferGroupBox`)
        #: memory buffer groupbox
        self.__mbufferwg = memoryBufferGroupBox.MemoryBufferGroupBox(
            parent=self)
        self.__mbufferwg.setMaxBufferSize(self.__settings.maxmbuffersize)
        #: (:class:`lavuelib.filtersGroupBox.FiltersGroupBox`)
        #  filters widget
        self.__filterswg = filtersGroupBox.FiltersGroupBox(
            parent=self)
        #: (:class:`lavuelib.preparationGroupBox.PreparationGroupBox`)
        #: preparation groupbox
        self.__prepwg = preparationGroupBox.PreparationGroupBox(
            parent=self, settings=self.__settings)
        #: (:class:`lavuelib.scalingGroupBox.ScalingGroupBox`) scaling groupbox
        self.__scalingwg = scalingGroupBox.ScalingGroupBox(parent=self)
        #: (:class:`lavuelib.levelsGroupBox.LevelsGroupBox`) level groupbox
        self.__levelswg = levelsGroupBox.LevelsGroupBox(
            parent=self, settings=self.__settings,
            expertmode=(self.__umode == 'expert'))
        #: (:class:`lavuelib.levelsGroupBox.LevelsGroupBox`) channel groupbox
        self.__channelwg = channelGroupBox.ChannelGroupBox(
            parent=self, settings=self.__settings,
            expertmode=(self.__umode == 'expert'))
        #: (:class:`lavuelib.statisticsGroupBox.StatisticsGroupBox`)
        #:     statistic groupbox
        self.__statswg = statisticsGroupBox.StatisticsGroupBox(parent=self)
        #: (:class:`lavuelib.imageWidget.ImageWidget`) image widget
        self.__imagewg = imageWidget.ImageWidget(
            parent=self, tooltypes=self.__tooltypes,
            settings=self.__settings,
            rgbtooltypes=self.__rgbtooltypes)
        self.__imagewg.updateToolComboBox(
            [self.__tlaliasnames[twn]
             for twn in json.loads(str(self.__settings.toolwidgets))
             if twn in self.__tlaliasnames.keys()]
        )

        self.__levelswg.setImageItem(self.__imagewg.image())
        self.__levelswg.showGradient(True)
        self.__channelwg.showGradient(True)
        self.__levelswg.updateHistoImage(autoLevel=True)

        #: (:class:`lavuelib.maskWidget.MaskWidget`) mask widget
        self.__maskwg = self.__prepwg.maskWidget
        #: (:class:`lavuelib.highValueMaskWidget.HighValueMaskWidget`)
        #               high value mask widget
        self.__highvaluemaskwg = self.__prepwg.highValueMaskWidget
        #: (:class:`lavuelib.bkgSubtractionWidget.BkgSubtractionWidget`)
        #:    background subtraction widget
        self.__bkgsubwg = self.__prepwg.bkgSubWidget
        #: (:class:`lavuelib.transformationsWidget.TransformationsWidget`)
        #:    transformations widget
        self.__trafowg = self.__prepwg.trafoWidget

        # keep a reference to the "raw" image and the current filename
        #: (:class:`numpy.ndarray`) raw image
        self.__rawimage = None
        #: (:class:`numpy.ndarray`) raw image
        self.__filteredimage = None
        #: (:class:`numpy.ndarray`) raw gray image
        self.__rawgreyimage = None
        #: (:obj:`str`) image name
        self.__imagename = None
        #: (:obj:`str`) last image name
        self.__lastimagename = None
        #: (:obj:`str`) metadata JSON dictionary
        self.__metadata = ""
        #: (:obj:`str`) metadata dictionary
        self.__mdata = {}
        #: (:class:`numpy.ndarray`) displayed image after preparation
        self.__displayimage = None
        #: (:class:`numpy.ndarray`) scaled displayed image
        self.__scaledimage = None

        #: (:class:`numpy.ndarray`) background image
        self.__backgroundimage = None
        #: (:obj:`bool`) apply background image subtraction
        self.__dobkgsubtraction = False

        #: (:class:`numpy.ndarray`) mask image
        self.__maskimage = None

        #: (:obj:`str`) source configuration string
        self.__sourceconfiguration = None

        #: (:obj:`str`) source label
        self.__sourcelabel = None

        #: (:obj:`list`< ( :obj:`int`,:obj:`int` ) > )
        #        image module translations
        self.__translations = [(0, 0)]

        #: (:obj:`list`< (:obj:`str`) > ) image module transformations
        self.__transformations = ['']
        #: (:obj:`list`< (:obj:`str`) >) image module
        #                translations and transformations
        self.__trans = ['']

        #: (:obj:`dict`<  (:obj:`str`, :obj:`str`)) transformation names map
        self.__transmap = {
            "flipud": "fud",
            "flip-up-down": "fud",
            "r90t": "fud",
            "rot90t": "fud",
            "rot90+transpose": "fud",
            "fliplr": "flr",
            "flip-left-right": "flr",
            "r270t": "flr",
            "rot270t": "flr",
            "rot270+transpose": "flr",
            "transpose": "t",
            "rot90": "r90",
            "rot180": "r180",
            "rot270": "r270",
            "rot180t": "r180t",
            "rot180+transpose": "r180t",
        }

        #: (:obj:`str`) reload flag
        self.__reloadflag = False

        #: (:obj:`str`) transformation name
        self.__trafoname = "None"

        #: (:obj:`bool`) lazy image slider
        self.__lazyimageslider = False

        #: (:obj: dict < :obj:`str` , :obj:`str` >) unsigned/signed int map
        self.__unsignedmap = {
            "uint8": "int16",
            "uint16": "int32",
            "uint32": "int64",
            "uint64": "int64"
            # "uint64": "float64"
        }
        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        # # LAYOUT DEFINITIONS
        self.__ui.confVerticalLayout.addWidget(self.__sourcewg)
        self.__ui.confVerticalLayout.addWidget(self.__rangewg)
        self.__ui.confVerticalLayout.addWidget(self.__filterswg)
        self.__ui.confVerticalLayout.addWidget(self.__mbufferwg)
        self.__ui.confVerticalLayout.addWidget(self.__channelwg)
        self.__ui.confVerticalLayout.addWidget(self.__prepwg)
        self.__ui.confVerticalLayout.addWidget(self.__scalingwg)
        self.__ui.confVerticalLayout.addWidget(self.__levelswg)
        self.__ui.confVerticalLayout.addWidget(self.__statswg)
        self.__ui.imageVerticalLayout.addWidget(self.__imagewg)
        spacer = QtGui.QSpacerItem(
            0, 0,
            QtGui.QSizePolicy.Minimum,
            QtGui.QSizePolicy.Expanding
        )
        self.__ui.confVerticalLayout.addItem(spacer)
        self.__ui.splitter.setStretchFactor(0, 1)
        self.__ui.splitter.setStretchFactor(1, 10)

        # SIGNAL LOGIC::

        # signal from intensity scaling widget:
        # self.__scalingwg.scalingChanged.connect(self.scale)
        self.__scalingwg.simpleScalingChanged.connect(self._plot)
        self.__scalingwg.scalingChanged.connect(
            self._setScalingState)

        # signal from limit setting widget
        self.__levelswg.minLevelChanged.connect(self._setMinLevelState)
        self.__levelswg.maxLevelChanged.connect(self._setMaxLevelState)
        self.__levelswg.autoLevelsChanged.connect(self._setAutoLevelsState)
        self.__levelswg.levelsChanged.connect(self._setLevelState)
        self.__levelswg.gradientChanged.connect(
            self._setGradientState)
        self.__ui.cnfPushButton.clicked.connect(self._configuration)
        self.__ui.quitPushButton.clicked.connect(self.close)
        self.__ui.loadPushButton.clicked.connect(self._clickloadfile)
        self.__ui.helpPushButton.clicked.connect(self._showhelp)
        if self.__umode in ["user"]:
            self.__ui.cnfPushButton.hide()
        if QtGui.QIcon.hasThemeIcon("applications-system"):
            icon = QtGui.QIcon.fromTheme("applications-system")
            self.__ui.cnfPushButton.setIcon(icon)
            self.__ui.cnfPushButton.setText("")
        if QtGui.QIcon.hasThemeIcon("document-open"):
            icon = QtGui.QIcon.fromTheme("document-open")
            self.__ui.loadPushButton.setIcon(icon)
            # self.__ui.loadPushButton.setText("")
        if QtGui.QIcon.hasThemeIcon("application-exit"):
            icon = QtGui.QIcon.fromTheme("application-exit")
            self.__ui.quitPushButton.setIcon(icon)
            # self.__ui.quitPushButton.setText("")
        if QtGui.QIcon.hasThemeIcon("help-browser"):
            icon = QtGui.QIcon.fromTheme("help-browser")
            self.__ui.helpPushButton.setIcon(icon)
            # self.__ui.helpPushButton.setText("")
        self.__imagewg.roiCoordsChanged.connect(self._calcUpdateStatsSec)
        self.__imagewg.currentToolChanged.connect(self._setToolState)
        # connecting signals from source widget:

        # gradient selector
        self.__channelwg.rgbChanged.connect(self._setRGBState)
        self.__channelwg.channelChanged.connect(self._setChannelState)
        self.__imagewg.aspectLockedToggled.connect(self._setAspectLocked)
        self.__levelswg.storeSettingsRequested.connect(
            self._storeSettings)

        self.__imagewg.replotImage.connect(self._replot)
        # simple mutable caching object for data exchange with thread
        #: (:class:`lavuelib.dataFetchTread.ExchangeList`)
        #:    exchange list
        self.__exchangelists = []
        for ds in self.__datasources:
            self.__exchangelists.append(dataFetchThread.ExchangeList())

        #: (:class:`lavuelib.dataFetchTread.DataFetchThread`)
        #:    data fetch thread
        self.__dataFetchers = []
        for i, ds in enumerate(self.__datasources):
            dft = dataFetchThread.DataFetchThread(ds, self.__exchangelists[i])
            self.__dataFetchers.append(dft)
            self._stateUpdated.connect(dft.changeStatus)
        self.__dataFetchers[0].newDataNameFetched.connect(self._getNewData)
        self.__sourcewg.sourceStateChanged.connect(self._updateSource)
        self.__sourcewg.sourceChanged.connect(self._onSourceChanged)
        self.__sourcewg.sourceConnected.connect(self._connectSource)
        self.__sourcewg.sourceDisconnected.connect(self._disconnectSource)

        self.__bkgsubwg.bkgFileSelected.connect(self._prepareBkgSubtraction)
        self.__bkgsubwg.useCurrentImageAsBkg.connect(
            self._setCurrentImageAsBkg)
        self.__bkgsubwg.applyStateChanged.connect(self._checkBkgSubtraction)

        self.__maskwg.maskFileSelected.connect(self._prepareMasking)
        self.__maskwg.applyStateChanged.connect(self._checkMasking)

        self.__highvaluemaskwg.maskHighValueChanged.connect(
            self._checkHighMasking)
        self.__highvaluemaskwg.applyStateChanged.connect(
            self._checkHighMasking)

        # signals from transformation widget
        self.__trafowg.transformationChanged.connect(
            self._assessTransformation)

        # signals from transformation widget
        self.__filterswg.filtersChanged.connect(
            self._assessFilters)

        # signals from transformation widget
        self.__mbufferwg.bufferSizeChanged.connect(
            self._setBufferSizeState)

        # set the right target name for the source display at initialization

        self.__sourcewg.sourceLabelChanged.connect(
            self._switchSourceDisplay)
        self.__sourcewg.addIconClicked.connect(
            self._addLabel)
        self.__sourcewg.removeIconClicked.connect(
            self._removeLabel)
        self.__sourcewg.translationChanged.connect(self._setTranslation)

        self.__ui.frameLineEdit.textChanged.connect(self._spinreloadfile)
        self.__ui.lowerframePushButton.clicked.connect(
            self._lowerframepushed)
        self.__ui.higherframePushButton.clicked.connect(
            self._higherframepushed)
        self.__ui.frameHorizontalSlider.valueChanged.connect(
            self._sliderreloadfilelazy)
        self.__connectslider()

        self.__sourcewg.updateLayout()
        self.__sourcewg.emitSourceChanged()
        self.__imagewg.showCurrentTool()

        self.__loadSettings()

        self.__resetFilters(self.__settings.filters)

        self.__updateframeview()

        self.__updateframeratetip(self.__settings.refreshrate)
        self.__imagewg.setExtensionsRefreshTime(
            self.__settings.toolrefreshtime)

        start = self.__applyoptions(options)
        self._plot()
        self.setState()
        if start:
            self.__sourcewg.start()

        self.__updateTool(options.tool)

    @debugmethod
    def setState(self):
        """ set current state """

        dssa = ";".join(self.__sourcewg.currentDataSourceAlias())
        configuration = ";".join(self.__sourcewg.configuration())
        if not self.__levelswg.isAutoLevel():
            levels = self.__levelswg.levels()
            autofactor = None
        else:
            autofactor = self.__levelswg.autoFactor()
            levels = ""
        bkgfile = ""
        if self.__bkgsubwg.isBkgSubApplied():
            bkgfile = str(self.__settings.bkgimagename)
        maskfile = ""
        if self.__maskwg.isMaskApplied():
            maskfile = str(self.__settings.maskimagename)
        maskhighvalue = ""
        if self.__settings.showhighvaluemask:
            maskhighvalue = str(self.__highvaluemaskwg.mask() or "")
        self.setLavueState(
            {
                "connected": self.__sourcewg.isConnected(),
                "source": dssa,
                "configuration": configuration,
                "offset": self._translations(),
                "mode": self.__umode,
                "instance": self.__instance or "",
                "scaling": str(self.__scalingwg.currentScaling()),
                "transformation": str(self.__trafowg.transformation()),
                "tool": str(self.__imagewg.tool()),
                "levels": levels,
                "autofactor": autofactor,
                "gradient": self.__levelswg.gradient(),
                "maskhighvalue": maskhighvalue,
                "maskfile": maskfile,
                "bkgfile": bkgfile,
                "channel": self.__channelwg.channelLabel(),
                "mbuffer": (self.__mbufferwg.bufferSize() or None),
                "doordevice": self.__settings.doorname,
                "tangodevice": (self.__tangoclient.device()
                                if self.__tangoclient else ""),
                "analysisdevice": self.__settings.analysisdevice,
                "rangewindow": self.__rangewg.rangeWindow(),
                "dsfactor": self.__rangewg.factor(),
                "dsreduction": str(self.__rangewg.function()),
                "filters": self.__filterstate,
                "imagefile": (self.__settings.imagename or ""),
                "version": str(release.__version__),
            })

    @QtCore.pyqtSlot(str)
    def _setScalingState(self, scaling):
        """ sets scaling state

        :param scalingtype: scaling type, i.e. log, linear, sqrt
        :type scalingtype: :obj:`str`
        """
        self.__levelswg.setScalingLabel(scaling)
        self.setLavueState({"scaling": str(scaling)})

    @QtCore.pyqtSlot()
    def _setChannelState(self):
        """ sets gradient state
        """
        self.setLavueState({"channel": self.__channelwg.channelLabel()})
        self._plot()

    @QtCore.pyqtSlot()
    def _setGradientState(self):
        """ sets gradient state
        """
        self.setLavueState({"gradient": self.__levelswg.gradient()})

    @QtCore.pyqtSlot(str)
    def _setToolState(self, _):
        """ sets tool state
        """
        self.setLavueState({"tool": self.__imagewg.tool()})

    @QtCore.pyqtSlot(int)
    def _setBufferSizeState(self, size):
        """ sets buffer size state
        """
        self.setLavueState({"mbuffer": size or None})

    def __setLevelState(self):
        """ sets intensity level state
        """
        if not self.__levelswg.isAutoLevel():
            levels = self.__levelswg.levels()
            autofactor = None
        else:
            autofactor = self.__levelswg.autoFactor()
            levels = ""
        self.setLavueState({"levels": levels, "autofactor": autofactor})

    def _setLevelState(self):
        """ sets intensity level state and plot
        """
        self.__setLevelState()
        self._plot()

    @QtCore.pyqtSlot(float)
    def _setMinLevelState(self, level=None):
        """ sets minimum intensity level

        :param level: minimum intensity
        :type level: :obj:`float`
        """
        self.__imagewg.setMinLevel(level)
        self.__setLevelState()

    @QtCore.pyqtSlot(float)
    def _setMaxLevelState(self, level=None):
        """ sets maximum intensity level

        :param level: maximum intensity
        :type level: :obj:`float`
        """
        self.__imagewg.setMaxLevel(level)
        self.__setLevelState()

    @QtCore.pyqtSlot(int)
    def _setAutoLevelsState(self, autolevels):
        """ sets auto levels

        :param autolevels: 2: auto levels enabled 1: with autofactor
        :type autolevels: :obj:'int`
        """
        self.__imagewg.setAutoLevels(autolevels)
        self.__setLevelState()

    @debugmethod
    def setLavueState(self, dct=None):
        """ update LavueState of LavueController

        :param dct: lavue state dictionary
        :type dct: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if dct is not None:
            self.__lavuestate.updateState(dct)
        self.__lavuestate.updateState({
            "viewrange": self.__imagewg.viewRange()
        })
        self.__imagewg.writeAttribute(
            "LavueState", self.__lavuestate.dump())

    @debugmethod
    @QtCore.pyqtSlot()
    def _showhelp(self):
        """ shows the detail help
        """
        form = helpForm.HelpForm("index.html", self)
        form.show()

    @debugmethod
    def _translations(self):
        """ povides translations and optional transformations
            of the given sources

        :returns: x,y tranlation or x,y,transformations, e.g. 2345,354,r90
        :rtype: :obj:`str`
        """
        nrsources = min(len(self.__datasources), len(self.__trans))
        return ";".join(self.__trans[:nrsources])

    @debugmethod
    @QtCore.pyqtSlot(str, int)
    def _setTranslation(self, trans, sid):
        """ sets translation and optional transfromation of the given source

        :param trans: x,y tranlation or x,y,transformations, e.g. 2345,354
        :type trans: :obj:`str`
        :param sid: source id
        :type sid: :obj:`int`
        """
        try:
            x = None
            y = None
            tr = ''
            strans = trans.split(",")
            if len(strans) > 0:
                try:
                    x = int(strans[0].replace("m", "-"))
                except Exception:
                    pass
            if len(strans) > 1:
                try:
                    y = int(strans[1].replace("m", "-"))
                except Exception:
                    pass
            if len(strans) > 2:
                try:
                    tr = str(strans[2]).lower()
                except Exception:
                    pass
            while len(self.__translations) <= sid:
                self.__translations.append((None, None))
            while len(self.__transformations) <= sid:
                self.__transformations.append('')
            while len(self.__trans) <= sid:
                self.__trans.append('')
            self.__translations[sid] = (x, y)
            self.__transformations[sid] = self.__transmap.get(tr, tr)
            self.__trans[sid] = trans
        except Exception:
            pass
        offset = self._translations()
        self.setLavueState({"offset": offset})

    # @debugmethod
    def __updateTypeList(self, properties, typelist,
                         allaliases, snametoname):
        """ updates type list, i.e. typelist, allaliases and snametoname

        :param properties: dictionary with properies, i.e.
                            {"requires": ("<PACKAGE1>","<PACKAGE2>"),
                             "alias": "<alias>",
                             "widget": "<widgettype>",
                             "name": "<name>"}
        :type properties: :obj:`dict` < :obj:`str`, :obj:`str`>
        :param typelist: type list
        :type typelist: :obj:`list` < :obj:`str`>
        :param allaliases: a list of aliases
        :type allaliases: :obj:`list` < :obj:`str`>
        :param snametoname: alias to name dictionary
        :type snametoname: :obj:`dict` < :obj:`str`, :obj:`str`>
        """
        typelist[:] = []
        allaliases[:] = []
        for wp in properties:
            avail = True
            for req in wp["requires"]:
                if not getattr(isr, req):
                    avail = False
                    break
            if avail:
                if wp["alias"] not in typelist:
                    typelist.append(wp["widget"])
            allaliases.append(wp["alias"])
            snametoname[wp["alias"]] = wp["name"]

    # @debugmethod
    def __switchlazysignals(self, lazy=False):
        """switch lazy signals

        :param lazy: lazy image slider flag
        :type lazy: :obj:`bool`
        """
        if lazy:
            self.__ui.frameHorizontalSlider.sliderReleased.connect(
                self._sliderreloadfile)
            self.__lazyimageslider = True
        else:
            self.__ui.frameHorizontalSlider.sliderReleased.disconnect(
                self._sliderreloadfile)
            self.__lazyimageslider = False

    # @debugmethod
    def __disconnectslider(self):
        """switch lazy signals

        :param lazy: lazy image slider flag
        :type lazy: :obj:`bool`
        """
        if self.__lazyimageslider:
            self.__ui.frameHorizontalSlider.sliderReleased.disconnect(
                self._sliderreloadfile)

    # @debugmethod
    def __connectslider(self):
        """switch lazy signals

        :param lazy: lazy image slider flag
        :type lazy: :obj:`bool`
        """
        if self.__lazyimageslider:
            self.__ui.frameHorizontalSlider.sliderReleased.connect(
                self._sliderreloadfile)

    # @debugmethod
    def __resetFilters(self, filters):
        """ resets filters

        :param filters: filters settings
        :type filters: :obj:`str`
        """
        try:
            fsettings = json.loads(filters)
            self.__filters.reset(fsettings)
            label = " | ".join([flt[0].split(".")[-1]
                                for flt in fsettings if flt[0]])
            if len(label) > 32:
                label = label[:32] + " ..."
            self.__filterswg.setLabel(label)
            self.__filterswg.setToolTip(
                "\n".join(
                    ["%s(%s)" %
                     (flt[0],
                      ("'%s'" % flt[1]) if flt[1] else "")
                     for flt in fsettings if flt[0]])
            )
            if self.__settings.filters != filters:
                self.__settings.filters = filters
        except Exception as e:
            self.__filterswg.setState(0)
            import traceback
            value = traceback.format_exc()
            messageBox.MessageBox.warning(
                self, "lavue: problems in setting filters",
                "%s" % str(e),
                "%s" % value)
            # print(str(e))

    @debugmethod
    @QtCore.pyqtSlot(str, str)
    def _addLabel(self, name, value):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value
        :type value: :obj:`str`
        """
        name = str(name)
        value = str(value)
        labelvalues = json.loads(getattr(self.__settings, name) or '{}')
        dform = edDictDialog.EdDictDialog(self)
        dform.record = labelvalues
        dform.newvalues = [value]
        # dform.title = self.__objtitles[repr(obj)]
        dform.createGUI()
        dform.exec_()
        if dform.dirty:
            labelvalues = dform.record
            for key in list(labelvalues.keys()):
                if not str(key).strip():
                    labelvalues.pop(key)
            setattr(self.__settings, name, json.dumps(labelvalues))
            self.__updateSource()
            self._storeSettings()

    @debugmethod
    @QtCore.pyqtSlot(str, str)
    def _removeLabel(self, name, label):
        """ emits addIconClicked signal

        :param name: object name
        :type name: :obj:`str`
        :param value: text value label to remove
        :type value: :obj:`str`
        """
        name = str(name)
        label = str(label)
        labelvalues = json.loads(getattr(self.__settings, name) or '{}')
        if label in labelvalues.keys():
            labelvalues.pop(label)
            setattr(self.__settings, name, json.dumps(labelvalues))
            self.__updateSource()
            self._storeSettings()

    @debugmethod
    def __updateSource(self):
        detservers = json.loads(self.__settings.detservers)
        if detservers:
            if self.__settings.defdetservers:
                serverdict = dict(HIDRASERVERLIST)
                defpool = set(serverdict["pool"])
                defpool.update(detservers)
                serverdict["pool"] = list(defpool)
            else:
                serverdict = {"pool": list(detservers)}
        elif self.__settings.defdetservers:
            serverdict = HIDRASERVERLIST
        else:
            serverdict = {"pool": []}
        self.__sourcewg.updateMetaData(
            zmqtopics=self.__settings.zmqtopics,
            dirtrans=self.__settings.dirtrans,
            tangoattrs=self.__settings.tangoattrs,
            tangoevattrs=self.__settings.tangoevattrs,
            tangofileattrs=self.__settings.tangofileattrs,
            tangodirattrs=self.__settings.tangodirattrs,
            zmqservers=self.__settings.zmqservers,
            httpurls=self.__settings.httpurls,
            autozmqtopics=self.__settings.autozmqtopics,
            nxslast=self.__settings.nxslast,
            nxsopen=self.__settings.nxsopen,
            serverdict=serverdict,
            hidraport=self.__settings.hidraport,
            doocsprops=self.__settings.doocsprops,
            tineprops=self.__settings.tineprops,
            epicspvnames=self.__settings.epicspvnames,
            epicspvshapes=self.__settings.epicspvshapes
        )

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _updateLavueState(self, state):
        """ updates lavue state configuration

        :param state: json dictionary with configuration
        :type state: :obj:`str`
        """
        if state:
            dctcnf = json.loads(str(state))
            if dctcnf:
                srccnf = "source" in dctcnf.keys() or \
                    "configuration" in dctcnf.keys()
                stop = dctcnf["stop"] if "stop" in dctcnf.keys() else None
                start = dctcnf["start"] if "start" in dctcnf.keys() else None
                tool = dctcnf["tool"] if "tool" in dctcnf.keys() else None
                if "connected" in dctcnf.keys() and \
                   stop is None and start is None:
                    if dctcnf["connected"]:
                        start = True
                    else:
                        stop = True
                running = self.__sourcewg.isConnected()
                if srccnf or stop is True or start is True:
                    if self.__sourcewg.isConnected():
                        self.__sourcewg.toggleServerConnection()
                self.__applyoptionsfromdict(dctcnf)
                if not self.__sourcewg.isConnected():
                    if start is True:
                        self.__sourcewg.toggleServerConnection()
                    elif running and srccnf and stop is not True:
                        self.__sourcewg.toggleServerConnection()
                self.__updateTool(tool)
            if not dctcnf or \
               ("__update__" in dctcnf.keys() and dctcnf["__update__"]):
                self.setLavueState()

    # @debugmethod
    def __updateTool(self, tool):
        """ update current tool

        :param tool: alias tool name
        :type tool: :obj:`str`
        """
        if tool:
            if not self.__imagewg.rgb() and \
               tool in self.__tlaliasnames.keys():
                QtCore.QTimer.singleShot(
                    10, self.__imagewg.showCurrentTool)
            elif self.__imagewg.rgb():
                QtCore.QTimer.singleShot(
                    10, self.__imagewg.showCurrentRGBTool)

    # @debugmethod
    def __applyoptionsfromdict(self, dctcnf):
        """ apply options

        :param dctcnf: commandline options
        :type dctcnf: :obj:`dict` <:obj:`str`, any >
        """
        if dctcnf:
            options = argparse.Namespace()
            for key, vl in dctcnf.items():
                setattr(options, key, vl)
            self.__applyoptions(options)
            if 'levels' not in dctcnf.keys():
                self.__levelswg.setAutoLevels(2)
            if 'bkgfile' not in dctcnf.keys():
                self.__bkgsubwg.checkBkgSubtraction(0)
                self.__dobkgsubtraction = None
            if 'maskfile' not in dctcnf.keys():
                self.__maskwg.noImage()
                self.__imagewg.setApplyMask(False)

    @debugmethod
    def __applyoptions(self, options):
        """ apply options

        :param options: commandline options
        :type options: :class:`argparse.Namespace`
        :returns: start flag
        :rtype: :obj:`bool`
        """
        if hasattr(options, "log") and options.log is not None:
            setLoggerLevel(logger, options.log)
            self.setLavueState({"log": _logginglevel})

        if hasattr(options, "doordevice") and options.doordevice is not None:
            self.__settings.doorname = str(options.doordevice)
            self.setLavueState({"doordevice": self.__settings.doorname})

        if hasattr(options, "analysisdevice") and \
           options.analysisdevice is not None:
            self.__settings.analysisdevice = str(options.analysisdevice)
            self.setLavueState(
                {"analysisdevice": self.__settings.analysisdevice})

        # load image file
        if hasattr(options, "imagefile") and options.imagefile is not None:
            oldname = self.__settings.imagename
            oldpath = self.__fieldpath
            oldgrowing = self.__growing
            try:
                self.__settings.imagename = str(options.imagefile)
                if ":/" in self.__settings.imagename:
                    self.__settings.imagename, self.__fieldpath =  \
                        self.__settings.imagename.split(":/", 1)
                else:
                    self.__fieldpath = None
                self.__growing = 0
                imagename = self.__settings.imagename
                if not imagename.endswith(".nxs") \
                   and not imagename.endswith(".h5") \
                   and not imagename.endswith(".nx") \
                   and not imagename.endswith(".ndf") \
                   and not imagename.endswith(".hdf"):
                    fid = self.__findfid(imagename)
                else:
                    fid = 0
                self._loadfile(fid=fid)
            except Exception:
                self.__settings.imagename = oldname
                self.__fieldpath = oldpath
                self.__growing = oldgrowing
            self.setLavueState(
                {"imagefile": (self.__settings.imagename or "")})

        # set image source
        sourcechanged = False
        if hasattr(options, "source") and options.source is not None:
            srcnames = str(options.source).split(";")
            self.__setNumberOfSources(max(len(srcnames), 1))
            for i, srcname in enumerate(srcnames):
                if srcname in self.__srcaliasnames.keys():
                    self.__sourcewg.setSourceComboBoxByName(
                        i, self.__srcaliasnames[srcname])
            sourcechanged = True

        QtCore.QCoreApplication.processEvents()
        if hasattr(options, "configuration") and \
           options.configuration is not None:
            cnfs = str(options.configuration).split(";")
            for i, cnf in enumerate(cnfs):
                if i < self.__sourcewg.count():
                    self.__sourcewg.configure(i, str(cnf))
            if sourcechanged:
                self._setSourceConfiguration(options.configuration)

        QtCore.QCoreApplication.processEvents()

        if hasattr(options, "offset") and options.offset is not None:
            offs = str(options.offset).split(";")
            for i, offset in enumerate(offs):
                if i < self.__sourcewg.count():
                    self._setTranslation(str(offset), i)
                    self.__sourcewg.setTranslation(str(offset), i)

        if hasattr(options, "rangewindow") and \
           options.rangewindow is not None:
            if not self.__settings.showrange:
                self.__settings.showrange = True
                self.__rangewg.changeView(True)
                self._resizePlot(True)
            self.__rangewg.setFactor(str(options.dsfactor))
            self.__rangewg.setRangeWindow(str(options.rangewindow))

        if hasattr(options, "dsfactor") and \
           options.dsfactor is not None:
            if not self.__settings.showrange:
                try:
                    dsf = int(options.dsfactor)
                except Exception:
                    dsf = 1
                if dsf != 1:
                    self.__settings.showrange = True
                    self.__rangewg.changeView(True)
                    self._resizePlot(True)
            self.__rangewg.setFactor(str(options.dsfactor))

        if hasattr(options, "dsreduction") and \
           options.dsreduction is not None:
            if not self.__settings.showrange:
                try:
                    dsf = int(options.dsfactor)
                except Exception:
                    dsf = 1
                if dsf != 1:
                    self.__settings.showrange = True
                    self.__rangewg.changeView(True)
                    self._resizePlot(True)
            self.__rangewg.setFunction(str(options.dsreduction))

        if hasattr(options, "mbuffer") and options.mbuffer is not None:
            if not self.__settings.showmbuffer:
                self.__settings.showmbuffer = True
                self.__mbufferwg.changeView(True)
            self.__mbufferwg.onOff(True)
            try:
                self.__mbufferwg.setBufferSize(int(options.mbuffer))
            except Exception:
                pass

        if hasattr(options, "bkgfile") and options.bkgfile is not None:
            if not self.__settings.showsub:
                self.__settings.showsub = True
                self.__prepwg.changeView(showsub=True)
            self.__bkgsubwg.setBackground(str(options.bkgfile))

        if hasattr(options, "channel") and options.channel is not None:
            try:
                ich = int(options.channel) + 1
            except Exception:
                if options.channel == "mean":
                    ich = -2
                elif options.channel == "rgb":
                    ich = -1
                elif "," in options.channel:
                    try:
                        ich = [int(ch) for ch in options.channel.split(",")]
                    except Exception:
                        ich = 0
                else:
                    ich = 0
            self.__channelwg.setDefaultColorChannel(ich)

        if hasattr(options, "maskfile") and options.maskfile is not None:
            if not self.__settings.showmask:
                self.__settings.showmask = True
                self.__prepwg.changeView(True)
            self.__maskwg.setMask(str(options.maskfile))

        if hasattr(options, "maskhighvalue") and \
           options.maskhighvalue is not None:
            if not self.__settings.showhighvaluemask:
                self.__settings.showhighvaluemask = True
                self.__prepwg.changeView(showhighvaluemask=True)
            self.__highvaluemaskwg.setMask(str(options.maskhighvalue))
            self._checkHighMasking()
        if hasattr(options, "transformation") and \
           options.transformation is not None:
            if not self.__settings.showtrans:
                self.__settings.showtrans = True
                self.__prepwg.changeView(showtrans=True)
            self.__trafowg.setTransformation(str(options.transformation))

        if hasattr(options, "filters"):
            if options.filters is True:
                if not self.__settings.showfilters:
                    self.__settings.showfilters = True
                    self.__filterswg.changeView(
                        showfilters=True)
                self.__filterswg.setState(2)
            elif options.filters is False:
                self.__filterswg.setState(0)

        if hasattr(options, "scaling") and options.scaling is not None:
            if not self.__settings.showscale:
                self.__settings.showscale = True
                self.__scalingwg.changeView(True)
            self.__scalingwg.setScaling(str(options.scaling))

        QtCore.QCoreApplication.processEvents()
        if hasattr(options, "levels") and options.levels is not None:
            if not self.__settings.showlevels:
                self.__settings.showslevels = True
                self.__levelswg.changeView(showlevels=True)
                self.__channelwg.changeView(showlevels=True)
            self.__levelswg.setLevels(str(options.levels))

        if hasattr(options, "autofactor") and options.autofactor is not None:
            if not self.__settings.showlevels:
                self.__settings.showslevels = True
                self.__levelswg.changeView(showlevels=True)
                self.__channelwg.changeView(showlevels=True)
            self.__levelswg.setAutoFactor(str(options.autofactor))

        if hasattr(options, "gradient") and options.gradient is not None:
            if not self.__settings.showlevels:
                self.__settings.showslevels = True
                self.__levelswg.changeView(showlevels=True)
                self.__channelwg.changeView(showlevels=True)
            self.__levelswg.setGradient(str(options.gradient))

        if hasattr(options, "tool") and options.tool is not None:
            tlname = str(options.tool)
            if tlname in self.__tlaliasnames.keys() and \
               not self.__imagewg.rgb():
                self.__imagewg.setTool(self.__tlaliasnames[tlname])

        if hasattr(options, "tangodevice") and \
           TANGOCLIENT and options.tangodevice is not None:
            if self.__tangoclient is not None:
                self.__tangoclient.unsubscribe()
            self.__tangoclient = controllerClient.ControllerClient(
                str(options.tangodevice))
            self.__tangoclient.energyChanged.connect(
                self.__imagewg.updateEnergy)
            self.__tangoclient.detectorDistanceChanged.connect(
                self.__imagewg.updateDetectorDistance)
            self.__tangoclient.beamCenterXChanged.connect(
                self.__imagewg.updateBeamCenterX)
            self.__tangoclient.beamCenterYChanged.connect(
                self.__imagewg.updateBeamCenterY)
            self.__tangoclient.pixelSizeXChanged.connect(
                self.__imagewg.updatePixelSizeX)
            self.__tangoclient.pixelSizeYChanged.connect(
                self.__imagewg.updatePixelSizeY)
            self.__tangoclient.detectorROIsChanged.connect(
                self.__imagewg.updateDetectorROIs)
            self.__imagewg.setTangoClient(self.__tangoclient)
            self.__tangoclient.subscribe()
            self.__tangoclient.lavueStateChanged.connect(
                self._updateLavueState)
            self.setLavueState({"tangodevice": self.__tangoclient.device()})
        else:
            self.__tangoclient = None
            self.setLavueState({"tangodevice": ""})

        QtCore.QCoreApplication.processEvents()
        if hasattr(options, "viewrange") and options.viewrange is not None:
            self.__imagewg.setViewRange(str(options.viewrange))
        self.__sourcewg.updateLayout()
        if hasattr(options, "start"):
            return options.start is True
        else:
            return False

    def __loadSettings(self):
        """ loads settings from QSettings object
        """
        settings = QtCore.QSettings()
        if self.parent() is not None:
            self.parent().restoreGeometry(settings.value(
                "Layout/Geometry", type=QtCore.QByteArray))
        self.restoreGeometry(settings.value(
            "Layout/DialogGeometry", type=QtCore.QByteArray))
        status = self.__settings.load(settings)
        logger.debug("lavuelib.liveViewer.LiveViewer.__loadSettings %s"
                     % self.__settings.__dict__)
        self.__levelswg.updateCustomGradients(
            self.__settings.customGradients())
        for topic, value in status:
            text = messageBox.MessageBox.getText(topic)
            messageBox.MessageBox.warning(self, topic, text, str(value))

        self.__setSardana(self.__settings.sardana)
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
        self.__imagewg.setAutoDownSample(self.__settings.autodownsample)
        self._assessTransformation(self.__trafoname)
        for i, ds in enumerate(self.__datasources):
            ds.setTimeOut(self.__settings.timeout)
        dataFetchThread.GLOBALREFRESHRATE = self.__settings.refreshrate
        self.__imagewg.setStatsWOScaling(self.__settings.statswoscaling)
        self.__imagewg.setColors(self.__settings.roiscolors)

        self.__updateSource()

        self.__statswg.changeView(
            self.__settings.showstats,
            self.__settings.calcvariance)
        self.__viewFrameRate(False)
        self.__levelswg.changeView(
            self.__settings.showhisto,
            self.__settings.showlevels,
            self.__settings.showaddhisto
        )
        self.__channelwg.changeView(
            self.__settings.showlevels
        )
        self.__prepwg.changeView(
            self.__settings.showmask,
            self.__settings.showsub,
            self.__settings.showtrans,
            self.__settings.showhighvaluemask
        )
        self.__rangewg.changeView(self.__settings.showrange)
        self._resizePlot(self.__settings.showrange)
        self.__filterswg.changeView(self.__settings.showfilters)
        self.__mbufferwg.changeView(self.__settings.showmbuffer)

        self.__scalingwg.changeView(self.__settings.showscale)
        self.__levelswg.changeView()
        self.__channelwg.changeView()
        if self.__lazyimageslider != self.__settings.lazyimageslider:
            self.__switchlazysignals(self.__settings.lazyimageslider)

    # @debugmethod
    def __viewFrameRate(self, status):
        """ show/hide frame rate
        :param status: True for show and False for hide
        :type status: :obj:`bool`
        """
        if status:
            self.__ui.framerateLineEdit.show()
        else:
            self.__ui.framerateLineEdit.hide()

    @debugmethod
    @QtCore.pyqtSlot()
    def _storeSettings(self):
        """ stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        if self.parent() is not None and self.parent().parent() is not None:
            settings.setValue(
                "Layout/Geometry",
                QtCore.QByteArray(self.parent().parent().saveGeometry()))
        settings.setValue(
            "Layout/DialogGeometry",
            QtCore.QByteArray(self.saveGeometry()))

        self.__settings.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        self.__settings.sardana = True if self.__sardana is not None else False
        self.__settings.store(settings)

    @debugmethod
    @QtCore.pyqtSlot(bool)
    def _setAspectLocked(self, status):
        self.__settings.aspectlocked = status
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)

    @debugmethod
    def closeEvent(self, event):
        """ stores the setting before finishing the application

        :param event: close event
        :type event:  :class:`pyqtgraph.QtCore.QEvent`:
        """
        if not self.__closing:
            if self.__tangoclient:
                self.__tangoclient.unsubscribe()
            self._storeSettings()
            self.__settings.secstream = False
            for dft in self.__dataFetchers:
                try:
                    dft.newDataNameFetched.disconnect(self._getNewData)
                except Exception:
                    pass
            # except Exception as e:
            #     print (str(e))

            if self.__sourcewg.isConnected():
                self.__sourcewg.toggleServerConnection()
            self._disconnectSource()
            for df in self.__dataFetchers:
                df.stop()
                df.wait()
            self.__settings.seccontext.destroy()
            self.__closing = True
            QtGui.QApplication.closeAllWindows()
        if event is not None:
            event.accept()

    @debugmethod
    @QtCore.pyqtSlot()
    def _clickloadfile(self):
        """ reloads the image file
        """
        self._loadfile()

    @debugmethod
    def _loadfile(self, fid=None):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int`
         """
        self._reloadfile(fid, showmessage=True)

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _spinreloadfile(self, fid=None, showmessage=False):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int` or :obj:`str`
        :param showmessage: no image message
        :type showmessage: :obj:`bool`
         """
        try:
            if not self.__reloadflag:
                self.__reloadflag = True
                if fid is None:
                    fid = self.__ui.frameLineEdit.text()
                try:
                    fid = int(fid)
                    self._reloadfile(fid, showmessage)
                except Exception:
                    pass
                time.sleep(0.1)
        finally:
            self.__reloadflag = False

    @debugmethod
    @QtCore.pyqtSlot()
    def _lowerframepushed(self):
        step = self.__ui.framestepSpinBox.value()
        try:
            frame = int(self.__ui.frameLineEdit.text())
        except Exception:
            frame = self.__frame or 0
        nframe = frame - step
        if frame >= 0:
            nframe = max(nframe, 0)
        self.__ui.frameLineEdit.setText(str(nframe))

    @debugmethod
    @QtCore.pyqtSlot()
    def _higherframepushed(self):
        step = self.__ui.framestepSpinBox.value()
        try:
            frame = int(self.__ui.frameLineEdit.text())
        except Exception:
            frame = self.__frame or 0
        nframe = frame + step
        if frame < 0:
            nframe = min(nframe, -1)
        self.__ui.frameLineEdit.setText(str(nframe))

    @debugmethod
    @QtCore.pyqtSlot(int)
    def _sliderreloadfilelazy(self, _=None):
        """ reloads the image file or
        if lazy flag it displays only splider value
        """
        if self.__lazyimageslider:
            fid = self.__ui.frameHorizontalSlider.value()
            self.__ui.frameLineEdit.textChanged.disconnect(
                self._spinreloadfile)
            self.__ui.frameLineEdit.setText(str(fid))
            self.__ui.frameLineEdit.textChanged.connect(
                self._spinreloadfile)
        else:
            self._sliderreloadfile()

    @debugmethod
    @QtCore.pyqtSlot()
    def _sliderreloadfile(self, fid=None, showmessage=False):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int`
        :param showmessage: no image message
        :type showmessage: :obj:`bool`
         """
        try:
            if not self.__reloadflag:
                self.__reloadflag = True
                if fid is None:
                    fid = self.__ui.frameHorizontalSlider.value()
                self._reloadfile(fid, showmessage)
        finally:
            self.__reloadflag = False

    def __findfid(self, imagename):
        """ find file id
        """
        try:
            ipath, iname = ntpath.split(imagename)
            basename, ext = os.path.splitext(iname)
            ival = True
            w = 0
            while ival:
                try:
                    int(basename[(- w - 1):])
                    w += 1
                    if w == len(basename):
                        ival = False
                except Exception:
                    ival = False
            ffid = basename[-w:]
            fid = int(ffid)
        except Exception:
            fid = 0
        return fid

    @debugmethod
    def _reloadfile(self, fid=None, showmessage=False, nexus=None):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int`
        :param showmessage: no image message
        :type showmessage: :obj:`bool`
        :param nexus: nexus image name
        :type nexus: :obj:`str`
         """
        newimage = None
        metadata = None
        if fid is not None:
            imagename = self.__settings.imagename
            if nexus \
               or imagename.endswith(".nxs") \
               or imagename.endswith(".h5") \
               or imagename.endswith(".nx") \
               or imagename.endswith(".ndf") \
               or imagename.endswith(".hdf"):
                self.__frame = int(fid)
            else:
                try:
                    ipath, iname = ntpath.split(imagename)
                    basename, ext = os.path.splitext(iname)
                    ival = True
                    w = 0
                    while ival:
                        try:
                            int(basename[(- w - 1):])
                            w += 1
                            if w == len(basename):
                                ival = False
                        except Exception:
                            ival = False
                    fprefix, ffid = basename[:-w], basename[-w:]
                    if w:
                        fmt = "%sd" % w
                        fmtfid = ("%0" + fmt) % fid
                    else:
                        fmtfid = ""
                        fprefix = ffid
                        ffid = ""
                    self.__frame = int(fid)

                    iname = "%s%s%s" % (fprefix, fmtfid, ext)
                    imagename = os.path.join(ipath, iname)
                except Exception:
                    imagename = None
                    fid = None
        if fid is None:
            if nexus:
                imagename = nexus
            else:
                fileDialog = QtGui.QFileDialog()
                fileout = fileDialog.getOpenFileName(
                    self, 'Load file', self.__settings.imagename or '.')
                if isinstance(fileout, tuple):
                    imagename = str(fileout[0])
                else:
                    imagename = str(fileout)
        if imagename:
            if nexus \
               or imagename.endswith(".nxs") \
               or imagename.endswith(".h5") \
               or imagename.endswith(".nx") \
               or imagename.endswith(".ndf") \
               or imagename.endswith(".hdf"):
                try:
                    handler = imageFileHandler.NexusFieldHandler(
                        str(imagename))
                    fields = handler.findImageFields()
                    self.__settings.imagename = imagename
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
                    fields = None
                self.setLavueState(
                    {"imagefile": (self.__settings.imagename or "")})
                currentfield = None
                if fields:
                    if fid is None or self.__fieldpath is None:
                        imgfield = imageField.ImageField(self)
                        imgfield.fields = fields
                        imgfield.createGUI()
                        if imgfield.exec_():
                            self.__fieldpath = imgfield.field
                            self.__growing = imgfield.growing
                            self.__frame = imgfield.frame
                        else:
                            return
                    currentfield = fields[self.__fieldpath]
                    try:
                        newimage = handler.getImage(
                            currentfield["node"],
                            self.__frame, self.__growing, refresh=False)
                    except Exception as e:
                        logger.warning(str(e))
                        # print(str(e))

                    metadata = handler.getMetaData(currentfield["node"])
                    # if metadata:
                    #     print("Metadata = %s" % str(metadata))
                    self.__ui.frameLineEdit.textChanged.disconnect(
                        self._spinreloadfile)
                    self.__disconnectslider()
                    self.__ui.frameHorizontalSlider.valueChanged.disconnect(
                        self._sliderreloadfilelazy)
                    try:
                        if len(currentfield["shape"]) < 3:
                            gsize = 0
                        else:
                            gsize = currentfield["shape"][self.__growing] - 1
                        if gsize >= 0:
                            self.__ui.frameLineEdit.setToolTip(
                                "current frame (max: %s)" % gsize)
                            self.__ui.frameHorizontalSlider.setMaximum(gsize)
                            self.__ui.frameHorizontalSlider.setToolTip(
                                "current frame (max: %s)" % gsize)
                        else:
                            self.__ui.frameLineEdit.setToolTip("current frame")
                            self.__ui.frameHorizontalSlider.setMaximum(0)
                            self.__ui.frameHorizontalSlider.setToolTip(
                                "current frame")
                    except Exception:
                        self.__ui.frameLineEdit.setToolTip("current frame")
                    while newimage is None and self.__frame > 0:
                        self.__frame -= 1
                        newimage = handler.getImage(
                            currentfield["node"],
                            self.__frame, self.__growing, refresh=False)
                    if currentfield and len(currentfield["shape"]) > 2:
                        self.__updateframeview(True, True)
                    else:
                        self.__updateframeview()
                    self.__ui.frameLineEdit.textChanged.connect(
                        self._spinreloadfile)
                    self.__ui.frameHorizontalSlider.valueChanged.connect(
                        self._sliderreloadfilelazy)
                    self.__connectslider()
                else:
                    if showmessage:
                        text = messageBox.MessageBox.getText(
                            "lavue: Image %s cannot be loaded"
                            % self.__settings.imagename)
                        messageBox.MessageBox.warning(
                            self,
                            "lavue: File %s cannot be loaded"
                            % self.__settings.imagename,
                            "File %s without images"
                            % self.__settings.imagename)
                    return
                if imagename:
                    imagename = "%s:/%s" % (
                        self.__settings.imagename,
                        currentfield["nexus_path"])
                    if currentfield and len(currentfield["shape"]) > 2:
                        self.__updateframeview(True, True)
                    else:
                        self.__updateframeview()
            else:
                try:
                    fh = imageFileHandler.ImageFileHandler(
                        str(imagename))
                    newimage = fh.getImage()
                    if hasattr(newimage, "dtype") \
                       and str(newimage.dtype) == 'object':
                        self._reloadfile(fid, showmessage, nexus=imagename)
                        return
                    if isinstance(newimage, float) and newimage == -1.0:
                        newimage = None
                    if newimage is None:
                        raise Exception(
                            "Cannot read the image %s" % str(imagename))
                    metadata = fh.getMetaData()
                    self.__settings.imagename = imagename
                    self.setLavueState(
                        {"imagefile": (self.__settings.imagename or "")})
                    try:
                        ipath, iname = ntpath.split(imagename)
                        basename, ext = os.path.splitext(iname)
                        ival = True
                        w = 0
                        while ival:
                            try:
                                int(basename[(- w - 1):])
                                w += 1
                                if w == len(basename):
                                    ival = False
                            except Exception:
                                ival = False
                        fprefix, ffid = basename[:-w], basename[-w:]
                        self.__frame = int(ffid)
                        iname = "%s%s%s" % (fprefix, ffid, ext)
                        imagename = os.path.join(ipath, iname)
                    except Exception:
                        self.__frame = None
                    self.__updateframeview(self.__frame is not None)
                    self.__fieldpath = None
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if newimage is not None:
                self.__metadata = metadata
                if metadata:
                    self.__mdata = json.loads(str(metadata))
                    if self.__settings.geometryfromsource:
                        self.__settings.updateMetaData(**self.__mdata)
                        self.__imagewg.updateCenter(
                            self.__settings.centerx, self.__settings.centery)
                        self.__imagewg.mouseImagePositionChanged.emit()
                        self.__imagewg.geometryChanged.emit()
                else:
                    self.__mdata = {}
                self.__imagename = imagename
                self.__rawimage = np.transpose(newimage)
                self._plot()
                if fid is None:
                    self.__imagewg.autoRange()
            else:
                text = messageBox.MessageBox.getText(
                    "lavue: File %s cannot be loaded"
                    % self.__settings.imagename)
                messageBox.MessageBox.warning(
                    self,
                    "lavue: File %s cannot be loaded"
                    % self.__settings.imagename,
                    text,
                    str("lavue: File %s cannot be loaded"
                        % self.__settings.imagename))

    @debugmethod
    @QtCore.pyqtSlot()
    def _configuration(self):
        """ launches the configuration dialog
        """
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.__settings.doorname and self.__sardana is not None:
            self.__settings.doorname = self.__sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.__sardana is not None else False
        cnfdlg.door = self.__settings.doorname
        cnfdlg.crosshairlocker = self.__settings.crosshairlocker
        cnfdlg.addrois = self.__settings.addrois
        cnfdlg.orderrois = self.__settings.orderrois
        cnfdlg.showsub = self.__settings.showsub
        cnfdlg.showtrans = self.__settings.showtrans
        cnfdlg.showscale = self.__settings.showscale
        cnfdlg.showlevels = self.__settings.showlevels
        cnfdlg.showframerate = self.__settings.showframerate
        cnfdlg.showhisto = self.__settings.showhisto
        cnfdlg.showaddhisto = self.__settings.showaddhisto
        cnfdlg.showmask = self.__settings.showmask
        cnfdlg.showhighvaluemask = self.__settings.showhighvaluemask
        cnfdlg.showmbuffer = self.__settings.showmbuffer
        cnfdlg.showrange = self.__settings.showrange
        cnfdlg.showfilters = self.__settings.showfilters
        cnfdlg.showstats = self.__settings.showstats
        cnfdlg.showsteps = self.__settings.showsteps
        cnfdlg.calcvariance = self.__settings.calcvariance
        cnfdlg.filters = self.__settings.filters
        cnfdlg.secautoport = self.__settings.secautoport
        cnfdlg.secport = self.__settings.secport
        cnfdlg.hidraport = self.__settings.hidraport
        cnfdlg.maxmbuffersize = self.__settings.maxmbuffersize
        cnfdlg.floattype = self.__settings.floattype
        cnfdlg.secstream = self.__settings.secstream
        cnfdlg.zeromask = self.__settings.zeromask
        cnfdlg.nanmask = self.__settings.nanmask
        cnfdlg.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        cnfdlg.toolrefreshtime = self.__settings.toolrefreshtime
        cnfdlg.toolpollinginterval = self.__settings.toolpollinginterval
        cnfdlg.timeout = self.__settings.timeout
        cnfdlg.nrsources = self.__settings.nrsources
        cnfdlg.aspectlocked = self.__settings.aspectlocked
        cnfdlg.autodownsample = self.__settings.autodownsample
        cnfdlg.keepcoords = self.__settings.keepcoords
        cnfdlg.lazyimageslider = self.__settings.lazyimageslider
        cnfdlg.statswoscaling = self.__settings.statswoscaling
        cnfdlg.zmqtopics = self.__settings.zmqtopics
        cnfdlg.autozmqtopics = self.__settings.autozmqtopics
        cnfdlg.interruptonerror = self.__settings.interruptonerror
        cnfdlg.dirtrans = self.__settings.dirtrans
        cnfdlg.tangoattrs = self.__settings.tangoattrs
        cnfdlg.tineprops = self.__settings.tineprops
        cnfdlg.epicspvnames = self.__settings.epicspvnames
        cnfdlg.epicspvshapes = self.__settings.epicspvshapes
        cnfdlg.doocsprops = self.__settings.doocsprops
        cnfdlg.tangoevattrs = self.__settings.tangoevattrs
        cnfdlg.tangofileattrs = self.__settings.tangofileattrs
        cnfdlg.tangodirattrs = self.__settings.tangodirattrs
        cnfdlg.httpurls = self.__settings.httpurls
        cnfdlg.zmqservers = self.__settings.zmqservers
        cnfdlg.nxslast = self.__settings.nxslast
        cnfdlg.nxsopen = self.__settings.nxsopen
        cnfdlg.sendrois = self.__settings.sendrois
        cnfdlg.sendresults = self.__settings.sendresults
        cnfdlg.singlerois = self.__settings.singlerois
        cnfdlg.showallrois = self.__settings.showallrois
        cnfdlg.storegeometry = self.__settings.storegeometry
        cnfdlg.geometryfromsource = self.__settings.geometryfromsource
        cnfdlg.roiscolors = self.__settings.roiscolors
        cnfdlg.sourcedisplay = self.__settings.sourcedisplay
        cnfdlg.imagesources = self.__settings.imagesources
        cnfdlg.imagesourcenames = self.__srcaliasnames
        cnfdlg.toolwidgets = self.__settings.toolwidgets
        cnfdlg.toolwidgetnames = {}
        cnfdlg.diffnpt = self.__settings.diffnpt
        cnfdlg.correctsolidangle = self.__settings.correctsolidangle
        cnfdlg.availimagesources = self.__allsourcealiases
        cnfdlg.availtoolwidgets = self.__alltoolaliases
        cnfdlg.defdetservers = self.__settings.defdetservers
        cnfdlg.detservers = json.dumps(self.__mergeDetServers(
            HIDRASERVERLIST if cnfdlg.defdetservers else {"pool": []},
            json.loads(self.__settings.detservers)))
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__updateConfig(cnfdlg)
            self._storeSettings()

    @debugmethod
    def __updateConfig(self, dialog):
        """ updates the configuration
        """
        replot = False
        self.__settings.doorname = dialog.door
        self.setLavueState({"doordevice": self.__settings.doorname})
        if dialog.sardana != (True if self.__sardana is not None else False):
            self.__setSardana(dialog.sardana)
            self.__settings.sardana = dialog.sardana
        self.__settings.addrois = dialog.addrois
        self.__settings.orderrois = dialog.orderrois
        self.__settings.floattype = dialog.floattype
        self.__settings.crosshairlocker = dialog.crosshairlocker

        if self.__settings.showsub != dialog.showsub:
            self.__prepwg.changeView(showsub=dialog.showsub)
            self.__settings.showsub = dialog.showsub
        if self.__settings.showtrans != dialog.showtrans:
            self.__prepwg.changeView(showtrans=dialog.showtrans)
            self.__settings.showtrans = dialog.showtrans
        if self.__settings.showmask != dialog.showmask:
            self.__settings.showmask = dialog.showmask
            self.__prepwg.changeView(dialog.showmask)
        if self.__settings.showhighvaluemask != dialog.showhighvaluemask:
            self.__settings.showhighvaluemask = dialog.showhighvaluemask
            self.__prepwg.changeView(
                showhighvaluemask=dialog.showhighvaluemask)
            self._checkHighMasking()
            replot = True
        if self.__settings.showrange != dialog.showrange:
            self.__settings.showrange = dialog.showrange
            self.__rangewg.changeView(dialog.showrange)
            self._resizePlot(self.__settings.showrange)
        if self.__settings.showfilters != dialog.showfilters:
            self.__settings.showfilters = dialog.showfilters
            self.__filterswg.changeView(
                showfilters=dialog.showfilters)
        if self.__settings.showmbuffer != dialog.showmbuffer:
            self.__settings.showmbuffer = dialog.showmbuffer
            self.__mbufferwg.changeView(dialog.showmbuffer)

        if self.__settings.showscale != dialog.showscale:
            self.__scalingwg.changeView(dialog.showscale)
            self.__settings.showscale = dialog.showscale

        if self.__settings.showlevels != dialog.showlevels:
            self.__levelswg.changeView(showlevels=dialog.showlevels)
            self.__channelwg.changeView(showlevels=dialog.showlevels)
            self.__settings.showlevels = dialog.showlevels

        if self.__settings.showframerate != dialog.showframerate:
            self.__settings.showframerate = dialog.showframerate
            self.__viewFrameRate(self.__settings.showframerate
                                 and self.__sourcewg.isConnected())
        if self.__settings.showhisto != dialog.showhisto:
            self.__levelswg.changeView(dialog.showhisto)
            self.__settings.showhisto = dialog.showhisto
        if self.__settings.showaddhisto != dialog.showaddhisto:
            self.__levelswg.changeView(showadd=dialog.showaddhisto)
            self.__settings.showaddhisto = dialog.showaddhisto
        if self.__settings.showsteps != dialog.showsteps:
            self.__settings.showsteps = dialog.showsteps
            self.__updateframeview(self.__frame is not None)
        statschanged = False
        if self.__settings.showstats != dialog.showstats:
            self.__settings.showstats = dialog.showstats
            statschanged = True
        if self.__settings.calcvariance != dialog.calcvariance:
            self.__settings.calcvariance = dialog.calcvariance
            statschanged = True
        if statschanged:
            self.__statswg.changeView(
                dialog.showstats, dialog.calcvariance)
        if self.__settings.imagesources != dialog.imagesources:
            self.__settings.imagesources = dialog.imagesources
            self.__sourcewg.updateSourceComboBox(
                [self.__srcaliasnames[twn]
                 for twn in json.loads(str(self.__settings.imagesources))],
                self.__sourcewg.currentDataSourceNames())
        if self.__settings.toolwidgets != dialog.toolwidgets:
            self.__settings.toolwidgets = dialog.toolwidgets
            self.__imagewg.updateToolComboBox(
                [self.__tlaliasnames[twn]
                 for twn in json.loads(self.__settings.toolwidgets)],
                self.__imagewg.currentTool())
        dataFetchThread.GLOBALREFRESHRATE = dialog.refreshrate

        if self.__settings.refreshrate != dialog.refreshrate:
            self.__settings.refreshrate = dialog.refreshrate
            self.__updateframeratetip(self.__settings.refreshrate)
        if self.__settings.toolrefreshtime != dialog.toolrefreshtime:
            self.__settings.toolrefreshtime = dialog.toolrefreshtime
            self.__imagewg.setExtensionsRefreshTime(
                self.__settings.toolrefreshtime)
        if self.__settings.toolpollinginterval != dialog.toolpollinginterval:
            self.__settings.toolpollinginterval = dialog.toolpollinginterval
            self.__imagewg.setExtensionsRefreshTime(
                self.__settings.toolrefreshtime)
        if self.__settings.filters != dialog.filters:
            self.__resetFilters(dialog.filters)
            replot = True

        if self.__settings.secstream != dialog.secstream or (
                self.__settings.secautoport != dialog.secautoport
                and dialog.secautoport):
            if self.__settings.secstream:
                # workaround for a bug in libzmq
                try:
                    self.__settings.secsocket.unbind(
                        self.__settings.secsockopt)
                except Exception:
                    pass
                if self.__sourcewg.isConnected():
                    self.__sourcewg.connectSuccess(None)
            if dialog.secstream:
                if dialog.secautoport:
                    self.__settings.secsockopt = b"tcp://*:*"
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                    dialog.secport = unicode(
                        self.__settings.secsocket.getsockopt(
                            zmq.LAST_ENDPOINT)).split(":")[-1]
                else:
                    self.__settings.secsockopt = b"tcp://*:%s" % dialog.secport
                    self.__settings.secsocket.bind(self.__settings.secsockopt)
                if self.__sourcewg.isConnected():
                    self.__sourcewg.connectSuccess(dialog.secport)
        self.__settings.secautoport = dialog.secautoport
        self.__settings.secport = dialog.secport
        self.__settings.timeout = dialog.timeout
        for i, ds in enumerate(self.__datasources):
            ds.setTimeOut(self.__settings.timeout)
        self.__settings.aspectlocked = dialog.aspectlocked
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
        self.__settings.autodownsample = dialog.autodownsample
        self.__imagewg.setAutoDownSample(self.__settings.autodownsample)
        remasking = False
        if self.__settings.keepcoords != dialog.keepcoords:
            self.__settings.keepcoords = dialog.keepcoords
            self._assessTransformation(self.__trafoname)
            replot = True
        if self.__settings.lazyimageslider != dialog.lazyimageslider:
            self.__settings.lazyimageslider = dialog.lazyimageslider
            self.__switchlazysignals(self.__settings.lazyimageslider)

        setsrc = False
        if self.__settings.nrsources != dialog.nrsources:
            setsrc = True
            oldsize = self.__settings.nrsources
            if self.__sourcewg.isConnected():
                self.__sourcewg.toggleServerConnection()
                QtCore.QCoreApplication.processEvents()
                time.sleep(1)
            self.__setNumberOfSources(dialog.nrsources)
            self.__settings.nrsources = dialog.nrsources
            self.__sourcewg.updateSourceComboBox(
                [self.__srcaliasnames[twn]
                 for twn in json.loads(str(self.__settings.imagesources))],
                self.__sourcewg.currentDataSourceNames()[:oldsize])
        self.__settings.secstream = dialog.secstream
        self.__settings.storegeometry = dialog.storegeometry
        self.__settings.geometryfromsource = dialog.geometryfromsource
        self.__settings.interruptonerror = dialog.interruptonerror
        self.__settings.sourcedisplay = dialog.sourcedisplay
        if self.__settings.hidraport != dialog.hidraport:
            self.__settings.hidraport = dialog.hidraport
            setsrc = True
        if self.__settings.dirtrans != dialog.dirtrans:
            self.__settings.dirtrans = dialog.dirtrans
            setsrc = True
        if self.__settings.tangoattrs != dialog.tangoattrs:
            self.__settings.tangoattrs = dialog.tangoattrs
            setsrc = True
        if self.__settings.tineprops != dialog.tineprops:
            self.__settings.tineprops = dialog.tineprops
            setsrc = True
        if self.__settings.epicspvnames != dialog.epicspvnames:
            self.__settings.epicspvnames = dialog.epicspvnames
            setsrc = True
        if self.__settings.epicspvshapes != dialog.epicspvshapes:
            self.__settings.epicspvshapes = dialog.epicspvshapes
            setsrc = True
        if self.__settings.doocsprops != dialog.doocsprops:
            self.__settings.doocsprops = dialog.doocsprops
            setsrc = True
        if self.__settings.tangoevattrs != dialog.tangoevattrs:
            self.__settings.tangoevattrs = dialog.tangoevattrs
            setsrc = True
        if self.__settings.tangofileattrs != dialog.tangofileattrs:
            self.__settings.tangofileattrs = dialog.tangofileattrs
            setsrc = True
        if self.__settings.tangodirattrs != dialog.tangodirattrs:
            self.__settings.tangodirattrs = dialog.tangodirattrs
            setsrc = True
        if self.__settings.httpurls != dialog.httpurls:
            self.__settings.httpurls = dialog.httpurls
            setsrc = True
        if self.__settings.zmqservers != dialog.zmqservers:
            self.__settings.zmqservers = dialog.zmqservers
            setsrc = True
        if self.__settings.zmqtopics != dialog.zmqtopics:
            self.__settings.zmqtopics = dialog.zmqtopics
            setsrc = True
        if self.__settings.defdetservers != dialog.defdetservers:
            self.__settings.defdetservers = dialog.defdetservers
            setsrc = True
        detservers = json.dumps(self.__retrieveUserDetServers(
            HIDRASERVERLIST if dialog.defdetservers else {"pool": []},
            json.loads(dialog.detservers)))
        if self.__settings.detservers != detservers:
            self.__settings.detservers = detservers
            setsrc = True
        if self.__settings.autozmqtopics != dialog.autozmqtopics:
            self.__settings.autozmqtopics = dialog.autozmqtopics
            setsrc = True
        if self.__settings.nxsopen != dialog.nxsopen:
            self.__settings.nxsopen = dialog.nxsopen
            setsrc = True
        if self.__settings.nxslast != dialog.nxslast:
            self.__settings.nxslast = dialog.nxslast
            setsrc = True
        if self.__settings.sendrois != dialog.sendrois:
            self.__settings.sendrois = dialog.sendrois
        if self.__settings.sendresults != dialog.sendresults:
            self.__settings.sendresults = dialog.sendresults
        if self.__settings.singlerois != dialog.singlerois:
            self.__settings.singlerois = dialog.singlerois
        if self.__settings.showallrois != dialog.showallrois:
            self.__settings.showallrois = dialog.showallrois
        if setsrc:
            self.__updateSource()
        if self.__settings.maxmbuffersize != dialog.maxmbuffersize:
            self.__settings.maxmbuffersize = dialog.maxmbuffersize
            self.__mbufferwg.setMaxBufferSize(self.__settings.maxmbuffersize)

        self.__settings.statswoscaling = dialog.statswoscaling
        replot = replot or \
            self.__imagewg.setStatsWOScaling(
                self.__settings.statswoscaling)

        if self.__settings.zeromask != dialog.zeromask:
            self.__settings.zeromask = dialog.zeromask
            remasking = True
            replot = True

        if self.__settings.diffnpt != dialog.diffnpt:
            self.__settings.diffnpt = dialog.diffnpt
            replot = True

        if self.__settings.correctsolidangle != dialog.correctsolidangle:
            self.__settings.correctsolidangle = dialog.correctsolidangle
            replot = True

        if self.__settings.nanmask != dialog.nanmask:
            self.__settings.nanmask = dialog.nanmask
            remasking = True
            replot = True

        if self.__settings.roiscolors != dialog.roiscolors:
            self.__settings.roiscolors = dialog.roiscolors
            self.__imagewg.setColors(self.__settings.roiscolors)

        if remasking:
            self.__remasking()

        if replot:
            self._plot()

    @debugmethod
    def __setNumberOfSources(self, nrsources):
        """ set a number of image sources

        :param nrsources: a number of image sources
        :type nrsources: :obj:`int`
        """
        nrsources = max(int(nrsources), 1)
        if len(self.__dataFetchers) > nrsources:
            for _ in reversed(range(nrsources, len(self.__dataFetchers))):
                df = self.__dataFetchers.pop()
                df.stop()
                df.wait()
                df = None
                self.__datasources.pop()
                self.__exchangelists.pop()
        elif len(self.__dataFetchers) < nrsources:
            for i in reversed(range(len(self.__dataFetchers), nrsources)):
                self.__datasources.append(isr.BaseSource())
                self.__exchangelists.append(dataFetchThread.ExchangeList())
                dft = dataFetchThread.DataFetchThread(
                    self.__datasources[-1], self.__exchangelists[-1])
                self.__dataFetchers.append(dft)
                self._stateUpdated.connect(dft.changeStatus)
        self.__sourcewg.setNumberOfSources(nrsources)
        self._setSourceConfiguration()
        self.__settings.nrsources = nrsources
        self.__sourcewg.updateLayout()
        QtCore.QCoreApplication.processEvents()

    # @debugmethod
    def __mergeDetServers(self, detserverdict, detserverlist):
        """ merges detector servers from
        a dictionary and a list

        :param detserverdict: detector server dictionary
        :type detserverdict: :obj:`dict` <:obj:`str`, :obj:`list`<:obj:`str`>>
        :param detserverklist: detector server list
        :type detserverlist: :obj:`list` < :obj:`str`>
        :returns: merged detector server list
        :rtype: :obj:`list` < :obj:`str`>

        """
        servers = set(detserverdict["pool"])
        if self.__targetname in detserverdict.keys():
            servers.update(detserverdict[self.__targetname])
        if detserverlist:
            servers.update(detserverlist)
        return list(servers)

    # @debugmethod
    def __retrieveUserDetServers(self, detserverdict, detserverlist):
        """ retrives user detector servers from a list
             which are not in a dictionary

        :param detserverdict: detector server dictionary
        :type detserverdict: :obj:`dict` <:obj:`str`, :obj:`list`<:obj:`str`>>
        :param detserverklist: detector server list
        :type detserverlist: :obj:`list` < :obj:`str`>
        :returns: user detector server list
        :rtype: :obj:`list` < :obj:`str`>
        """
        servers = []
        if detserverlist:
            defservers = set(detserverdict["pool"])
            if self.__targetname in detserverdict.keys():
                defservers.update(detserverdict[self.__targetname])
            servers = list(set(detserverlist) - defservers)
        return list(servers)

    @debugmethod
    def _setSourceConfiguration(self, sourceConfiguration=None):
        """ sets the source configuration

        :param sourceConfiguration: source configuration string
        :type sourceConfiguration: :obj:`str
        """
        if sourceConfiguration is None:
            sourceConfiguration = self.__sourcewg.configuration()
        self.__sourceconfiguration = sourceConfiguration
        cdss = self.__sourcewg.currentDataSources()
        for i, ds in enumerate(cdss):
            if ds == \
               str(type(self.__datasources[i]).__name__):
                self.__datasources[i].setConfiguration(sourceConfiguration[i])
        self.setLavueState(
            {"configuration": ";".join(self.__sourceconfiguration or "")})

    @debugmethod
    def _switchSourceDisplay(self, label):
        """switches source display parameters

        :param sourceConfiguration: source configuration string
        :type sourceConfiguration: :obj:`str
        """
        if self.__sourcelabel != str(label) and label and \
           self.__settings.sourcedisplay:
            self.__sourcelabel = str(label)
            values = self.__settings.sourceDisplay(
                self.__sourcelabel)
            self.__applyoptionsfromdict(values)

    # @debugmethod
    def __setSourceLabel(self):
        """sets source display parameters
        """
        if self.__sourcelabel and self.__settings.sourcedisplay:
            label = self.__sourcelabel
            values = {}
            values["transformation"] = self.__trafowg.transformation()
            values["tool"] = self.__imagewg.tool()
            values["scaling"] = self.__scalingwg.currentScaling()
            if not self.__levelswg.isAutoLevel():
                values["levels"] = self.__levelswg.levels()
                values["autofactor"] = None
            else:
                values["autofactor"] = self.__levelswg.autoFactor()
            values["gradient"] = self.__levelswg.gradient()
            if self.__bkgsubwg.isBkgSubApplied():
                values["bkgfile"] = str(self.__settings.bkgimagename)
            if self.__maskwg.isMaskApplied():
                values["maskfile"] = str(self.__settings.maskimagename)
            mvalue = self.__highvaluemaskwg.mask()
            if mvalue is not None:
                values["maskhighvalue"] = str(mvalue)
            else:
                values["maskhighvalue"] = ""
            values["viewrange"] = self.__imagewg.viewRange()
            values["offset"] = self._translations()
            self.__settings.setSourceDisplay(label, values)

    # @debugmethod
    def __setSardana(self, status):
        """ sets the sardana utils
        """
        if status is False:
            self.__sardana = None
        else:
            self.__sardana = sardanaUtils.SardanaUtils()
        self.__imagewg.setSardanaUtils(self.__sardana)

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _onSourceChanged(self, status):
        """ update a list of sources according to the status

        :param status: json list on status, i.e source type ids
        :type status: :obj:`str`
        """
        lstatus = json.loads(str(status))
        dss = self.__sourcewg.currentDataSources()
        for i, ds in enumerate(dss):
            if lstatus[i]:
                if ds != str(type(self.__datasources[i]).__name__):
                    self.__datasources[i] = getattr(
                        isr, ds)(self.__settings.timeout)
            self.__sourcewg.updateSourceMetaData(
                i, **self.__datasources[i].getMetaData())
        dssa = ";".join(self.__sourcewg.currentDataSourceAlias())
        self.setLavueState({"source": dssa})

    @debugmethod
    @QtCore.pyqtSlot(int, int)
    def _updateSource(self, status, sid):
        """ update the current source

        :param status: current source combobox status id from starting from 1,
                       0 is disconnected, -1 current source
        :type status: :obj:`int`
        :param sid: source tab id starting from 0 and -1 for all
        :type sid: :obj:`int`
        """
        if status:
            dss = self.__sourcewg.currentDataSources()
            if sid == -1:
                for i, ds in enumerate(self.__datasources):
                    ds.setTimeOut(self.__settings.timeout)
                    self.__dataFetchers[i].setDataSource(ds)
                    if self.__sourceconfiguration and \
                       self.__sourceconfiguration[i] and \
                       dss[i] == str(type(ds).__name__):
                        ds.setConfiguration(self.__sourceconfiguration[i])
                    self.__sourcewg.updateSourceMetaData(i, **ds.getMetaData())
            else:
                ds = self.__datasources[sid]
                ds.setTimeOut(self.__settings.timeout)
                self.__dataFetchers[sid].setDataSource(ds)
                if self.__sourceconfiguration and \
                   self.__sourceconfiguration[sid] and \
                   dss[sid] == str(type(ds).__name__):
                    ds.setConfiguration(self.__sourceconfiguration[sid])
                    self.__sourcewg.updateSourceMetaData(
                        sid, **ds.getMetaData())
        self._stateUpdated.emit(bool(status))

    @debugmethod
    @QtCore.pyqtSlot(bool)
    def _replot(self, autorange):
        """ The main command of the live viewer class:
        draw a numpy array with the given name and autoRange.
        """
        self._plot()
        if autorange:
            self.__imagewg.autoRange()

    @debugmethod
    @QtCore.pyqtSlot()
    def _plot(self):
        """ The main command of the live viewer class:
        draw a numpy array with the given name.
        """
        if self.__ploting:
            return
        self.__ploting = True
        try:
            self.__filteredimage = self.__rawimage
            # apply user range
            self.__applyRange()
            # apply user filters
            self.__applyFilters()
            if self.__settings.showmbuffer:
                result = self.__mbufferwg.process(
                    self.__filteredimage, self.__imagename)
                if isinstance(result, tuple) and len(result) == 2:
                    self.__filteredimage, mdata = result
                    self.__mdata.update(mdata)

            if "channellabels" in self.__mdata:
                self.__channelwg.updateChannelLabels(
                    self.__mdata["channellabels"])

            # prepare or preprocess the raw image if present:
            self.__prepareImage()

            # perform transformation
            # (crdtranspose, crdleftrightflip, crdupdownflip,
            # orgtranspose, orgleftrightflip, orgupdownflip)
            allcrds = self.__transform()
            self.__imagewg.setTransformations(*allcrds)
            # use the internal raw image to create a display image with chosen
            # scaling
            self.__scale(self.__scalingwg.currentScaling())
            # calculate and update the stats for this
            self.__calcUpdateStats()
            # calls internally the plot function of the plot widget
            if self.__imagename is not None and self.__scaledimage is not None:
                self.__ui.fileNameLineEdit.setText(
                    self.__imagename.replace("\n", " "))
                self.__ui.fileNameLineEdit.setToolTip(self.__imagename)
            self.__imagewg.plot(
                self.__scaledimage,
                self.__displayimage
                if self.__settings.statswoscaling else self.__scaledimage,
                self.__imagename
            )
            if self.__settings.showhisto and self.__updatehisto:
                self.__levelswg.updateHistoImage()
                self.__updatehisto = False
        finally:
            self.__ploting = False

    @debugmethod
    @QtCore.pyqtSlot()
    def _calcUpdateStatsSec(self):
        """ calcuates statistics without  sending security stream
        """
        self.__calcUpdateStats(secstream=False)

    # @debugmethod
    def __calcUpdateStats(self, secstream=True):
        """ calcuates statistics

        :param secstream: send security stream flag
        :type secstream: :obj:`bool`
        """
        # calculate the stats for this

        auto = self.__levelswg.isAutoLevel()
        stream = secstream and self.__settings.secstream and \
            self.__scaledimage is not None
        display = self.__settings.showstats
        calcvariance = self.__settings.calcvariance
        maxval, meanval, varval, minval, maxrawval, maxsval = \
            self.__calcStats(
                (stream or display,
                 stream or display,
                 display and calcvariance,
                 stream or auto,
                 stream,
                 auto)
            )
        smaxval = "%.4f" % maxval
        smeanval = "%.4f" % meanval
        svarval = "%.4f" % varval
        sminval = "%.3f" % minval
        smaxrawval = "%.4f" % maxrawval
        calctime = time.time()
        currentscaling = self.__scalingwg.currentScaling()
        # update the statistics display
        if stream:
            messagedata = {
                'command': 'alive', 'calctime': calctime, 'maxval': smaxval,
                'maxrawval': smaxrawval,
                'minval': sminval, 'meanval': smeanval, 'pid': self.__apppid,
                'scaling': (
                    'linear'
                    if self.__settings.statswoscaling
                    else currentscaling)}
            topic = 10001
            message = "%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii"))
            self.__settings.secsocket.send_string(str(message))

        self.__statswg.updateStatistics(
            smeanval, smaxval, svarval,
            'linear' if self.__settings.statswoscaling else currentscaling)

        # if needed, update the level display
        if auto:
            self.__levelswg.updateAutoLevels(minval, maxsval)

    @debugmethod
    def _startPlotting(self):
        """ mode changer: start plotting mode.
        It starts plotting if the connection is really established.
        """
        #
        if not self.__sourcewg.isConnected():
            return
        for dft in self.__dataFetchers:
            dft.changeStatus(True)
            if not dft.isRunning():
                dft.start()

    @debugmethod
    def _stopPlotting(self):
        """ mode changer: stop plotting mode
        """

        for dft in self.__dataFetchers:
            if dft is not None:
                dft.changeStatus(False)

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _connectSource(self, status):
        """  calls the connect function of the source interface

        :param status: current source status id
        :type status: :obj:`int`
        """
        lstatus = json.loads(str(status))
        status = lstatus[0]
        self.__viewFrameRate(self.__settings.showframerate)
        for i, status in enumerate(lstatus):
            self._updateSource(status, i)

        for ds in self.__datasources:
            if ds is None:
                messageBox.MessageBox.warning(
                    self, "lavue: No data source is defined",
                    "No data source is defined",
                    "Please select the image source")
        self._setSourceConfiguration()
        consuccess = bool(len(self.__datasources))
        for ds in self.__datasources:
            if not ds.connect():
                self.__sourcewg.connectFailure()
                messageBox.MessageBox.warning(
                    self, "lavue: The %s connection could not be established"
                    % type(ds).__name__,
                    "The %s connection could not be established"
                    % type(ds).__name__,
                    str(ds.errormessage))
                consuccess = False
        if consuccess:
            self.__sourcewg.connectSuccess(
                self.__settings.secport if self.__settings.secstream else None)
        if self.__settings.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'start', 'calctime': calctime, 'pid': self.__apppid}
            topic = 10001
            # print(str(messagedata))
            self.__settings.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self.__updatehisto = True
        self.__setSourceLabel()
        self.setLavueState({"connected": self.__sourcewg.isConnected()})
        self._startPlotting()

    @debugmethod
    @QtCore.pyqtSlot()
    def _disconnectSource(self):
        """ calls the disconnect function of the source interface
        """
        self._stopPlotting()
        for ds in self.__datasources:
            ds.disconnect()
        self.__viewFrameRate(False)
        if self.__settings.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'stop', 'calctime': calctime, 'pid': self.__apppid}
            # print(str(messagedata))
            topic = 10001
            self.__settings.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self._updateSource(0, -1)
        self.__setSourceLabel()
        self.setLavueState({"connected": self.__sourcewg.isConnected()})
        # self.__datasources[0] = None

    # @debugmethod
    def __mergeData(self, fulldata, oldname):
        """ merge data parts to (name, rawdata, metadata)

        :param fulldata: a list of PartialData objects
        :type fulldata: :obj:`list` <:class:`PartialData`>
        :param oldname: old name
        :type oldname: :obj:`str`
        :returns: tuple of exchange object (name, data, metadata)
        :rtype: :obj:`list` <:obj:`str`, :class:`numpy.ndarray`, :obj:`str` >
        """

        names = [pdata.name for pdata in fulldata if pdata.name]
        rawimage = None
        metadata = None
        if "__ERROR__" in names:
            name = "__ERROR__"
            rawimage = " ".join(
                [str(pdata.tolist()[1])
                 for pdata in fulldata
                 if pdata.name == "__ERROR__"]
            )
            return name, rawimage, metadata

        name = "\n".join(names).strip()
        name = name or None

        mdata = [pdata.metadata for pdata in fulldata if pdata.metadata]
        if oldname == name and not mdata:
            return None, None, None
        if mdata:
            dmdata = {}
            for md in mdata:
                dmdata.update(json.loads(mdata))
            metadata = str(json.dumps(dmdata))
        if name:
            ldata = [pdata for pdata in fulldata if pdata.name]
            if len(ldata) == 1:
                name, rawimage, metadata = ldata[0].tolist()[:3]
            elif len(ldata) > 1:
                pd = ldata[0]
                shape = [pd.sx, pd.sy]
                dtype = pd.dtype()
                while len(shape) < 2:
                    shape.append(1)
                pd.x = pd.x or 0
                pd.y = pd.y or 0
                shape[0] += pd.x
                shape[1] += pd.y
                nx = min(0, pd.x)
                ny = min(0, pd.y)
                for pd in ldata[1:]:
                    pd.x = pd.x or 0
                    if pd.y is None:
                        pd.y = shape[1]
                    psh = [pd.sx, pd.sy]
                    while len(psh) < 2:
                        psh.append(1)
                    psh[0] += pd.x
                    psh[1] += pd.y
                    if dtype != pd.dtype():
                        dtype = self.__settings.floattype
                    shape[0] = max(shape[0], psh[0])
                    shape[1] = max(shape[1], psh[1])
                    nx = min(nx, pd.x)
                    ny = min(ny, pd.y)
                if self.__settings.nanmask:
                    rawimage = np.zeros(
                        shape=(shape[0] - nx, shape[1] - ny),
                        dtype=self.__settings.floattype)
                    rawimage.fill(np.nan)
                else:
                    rawimage = np.zeros(
                        shape=(shape[0] - nx, shape[1] - ny),
                        dtype=dtype)
                for pd in ldata:
                    if len(shape) == 2:
                        rawimage[
                            pd.x - nx: pd.sx + pd.x - nx,
                            pd.y - ny: pd.sy + pd.y - ny] = \
                            pd.data()
                    else:
                        rawimage[
                            pd.x - nx: pd.sx + pd.x - nx,
                            pd.y - ny: pd.sy + pd.y - ny, ...] = \
                            pd.data()
        return name, rawimage, metadata

    @debugmethod
    @QtCore.pyqtSlot(str, str)
    def _getNewData(self, name, metadata=None):
        """ checks if data is there at all

        :param name: image name
        :type name: :obj:`str`
        :param metadata: JSON dictionary with metadata
        :type metadata: :obj:`str`
        """
        fulldata = []
        states = self.__sourcewg.tabCheckBoxStates()
        for i, df in enumerate(self.__dataFetchers):
            if states[i]:
                cnt = 0
                name = None
                while (not df.fetching() and self.__sourcewg.isConnected()
                       and cnt < 100 and not name):
                    time.sleep(self.__settings.refreshrate/100.)
                    cnt += 1
                if cnt < 100:
                    name, rawimage, metadata = \
                        self.__exchangelists[i].readData()
                else:
                    name, rawimage, metadata = None, None, None
                if i < len(self.__translations):
                    x, y = self.__translations[i]
                else:
                    x, y = None, None
                if i < len(self.__transformations):
                    tr = self.__transformations[i]
                else:
                    tr = ''
                logger.debug(
                    "lavuelib.liveViewer.LiveViewer.__getNewData "
                    "%s: %s %s %s, [%s, %s]" %
                    (i, name, metadata,
                     rawimage.shape if hasattr(rawimage, "shape") else "",
                     x or "", y or "")
                )
                fulldata.append(
                    PartialData(name, rawimage, metadata, x, y, tr))
        if not self.__sourcewg.isConnected():
            return
        if len(fulldata) == 1:
            name, rawimage, metadata = fulldata[0].tolist()[:3]
        else:
            name, rawimage, metadata = self.__mergeData(
                fulldata, str(self.__imagename).strip())

        if str(self.__imagename).strip() == str(name).strip() and not metadata:
            for dft in self.__dataFetchers:
                dft.ready()
            return
        if name == "__ERROR__":
            if self.__settings.interruptonerror:
                if self.__sourcewg.isConnected():
                    self.__sourcewg.toggleServerConnection()
                errortext = rawimage
                messageBox.MessageBox.warning(
                    self, "lavue: Error in reading data",
                    "Viewing will be interrupted", str(errortext))
            else:
                self.__sourcewg.setErrorStatus(name)
            for dft in self.__dataFetchers:
                dft.ready()
            return
        self.__sourcewg.setErrorStatus("")

        if name is None:
            for dft in self.__dataFetchers:
                dft.ready()
            return
        # first time:
        if str(self.__metadata) != str(metadata) and str(metadata).strip():
            imagename, self.__metadata = name, metadata
            if str(imagename).strip() and \
               not isinstance(rawimage, basestring):
                if not hasattr(rawimage, "size") or rawimage.size != 0:
                    self.__imagename = imagename
                    self.__rawimage = rawimage
            try:
                if metadata:
                    self.__mdata = json.loads(str(metadata))
                else:
                    self.__mdata = {}
                if self.__mdata and isinstance(self.__mdata, dict):
                    resdata = dict((k, v) for (k, v) in self.__mdata.items()
                                   if k in self.__allowedmdata)
                    wgdata = dict((k, v) for (k, v) in self.__mdata.items()
                                  if k in self.__allowedwgdata)
                    if wgdata:
                        self.__imagewg.updateMetaData(**wgdata)
                    if resdata:
                        self.__sourcewg.updateMetaData(**resdata)
                    if self.__settings.geometryfromsource:
                        self.__settings.updateMetaData(**self.__mdata)
                        self.__imagewg.updateCenter(
                            self.__settings.centerx, self.__settings.centery)
                        self.__imagewg.mouseImagePositionChanged.emit()
                        self.__imagewg.geometryChanged.emit()
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))
        elif str(name).strip():
            if self.__imagename is None or str(self.__imagename) != str(name):
                self.__imagename, self.__metadata \
                    = name, metadata
                if not isinstance(rawimage, basestring):
                    if not hasattr(rawimage, "size") or rawimage.size != 0:
                        self.__rawimage = rawimage
        if not str(metadata).strip():
            self.__mdata = {}

        self.__updateframeview()
        self.__currenttime = time.time()
        if self.__settings.showframerate and self.__lasttime:
            self.__updateframerate(self.__currenttime - self.__lasttime)
        self.__lasttime = self.__currenttime

        self._plot()
        QtCore.QCoreApplication.processEvents()
        for dft in self.__dataFetchers:
            dft.ready()

    # @debugmethod
    def __updateframeview(self, status=False, slider=False):
        if status and self.__settings.showsteps:
            if self.__frame is not None:
                self.__ui.frameLineEdit.setText(str(self.__frame))
                if slider:
                    if self.__frame >= 0:
                        self.__ui.frameHorizontalSlider.setValue(self.__frame)
                    else:
                        self.__ui.frameHorizontalSlider.setValue(
                            self.__ui.frameHorizontalSlider.maximum())
                self.__ui.framestepSpinBox.show()
                self.__ui.framestepLabel.show()
                self.__ui.lowerframePushButton.show()
                self.__ui.higherframePushButton.show()
                self.__ui.frameLineEdit.show()
        else:
            # self.__fieldpath = None
            self.__ui.lowerframePushButton.hide()
            self.__ui.higherframePushButton.hide()
            self.__ui.framestepSpinBox.hide()
            self.__ui.frameLineEdit.hide()
            self.__ui.framestepLabel.hide()
        if slider:
            self.__ui.frameHorizontalSlider.show()
        else:
            self.__ui.frameHorizontalSlider.hide()

    # @debugmethod
    def __updateframerate(self, ratetime):
        if ratetime:
            fr = 1.0/float(ratetime)
            if fr >= 9.9:
                self.__ui.framerateLineEdit.setText("%.0f Hz" % fr)
            else:
                self.__ui.framerateLineEdit.setText("%.1f Hz" % fr)
        else:
            self.__ui.framerateLineEdit.setText("")

    # @debugmethod
    def __updateframeratetip(self, ratetime):
        if ratetime:
            fr = 1.0/float(ratetime)
            if fr >= 9.9:
                self.__ui.framerateLineEdit.setToolTip(
                    "Set frame rate: %.0f Hz" % fr)
            else:
                self.__ui.framerateLineEdit.setToolTip(
                    "Set frame rate: %.1f Hz" % fr)
        else:
            self.__ui.framerateLineEdit.setToolTip("Frame rate in Hz")

    # @debugmethod
    def __prepareImage(self):
        """applies: make image gray, substracke the background image and
           apply the mask
        """
        if self.__filteredimage is None:
            return

        if len(self.__filteredimage.shape) == 3:
            self.__channelwg.setNumberOfChannels(self.__filteredimage.shape[0])
            if not self.__channelwg.colorChannel():
                if "skipfirst" in self.__mdata.keys() and \
                   self.__mdata["skipfirst"]:
                    self.__rawgreyimage = np.nansum(
                        self.__filteredimage[1:, :, :], 0)
                else:
                    self.__rawgreyimage = np.nansum(self.__filteredimage, 0)
                if self.rgb():
                    self.setrgb(False)
            else:
                try:
                    if len(self.__filteredimage) >= \
                       self.__channelwg.colorChannel():
                        self.__rawgreyimage = self.__filteredimage[
                            self.__channelwg.colorChannel() - 1]
                        if self.rgb():
                            self.setrgb(False)
                            self.__levelswg.showGradient(True)
                    elif (len(self.__filteredimage) + 1 ==
                          self.__channelwg.colorChannel()):
                        if self.rgb():
                            self.setrgb(False)
                            self.__levelswg.showGradient(True)
                        if "skipfirst" in self.__mdata.keys() and \
                           self.__mdata["skipfirst"]:
                            self.__rawgreyimage = np.nanmean(
                                self.__filteredimage[1:, :, :], 0)
                        else:
                            self.__rawgreyimage = np.nanmean(
                                self.__filteredimage, 0)
                    elif self.__filteredimage.shape[0] > 1:
                        if not self.rgb():
                            self.setrgb(True)
                            self.__levelswg.showGradient(False)
                        self.__rawgreyimage = np.moveaxis(
                            self.__filteredimage, 0, -1)
                        rgbs = self.__channelwg.rgbchannels()
                        if rgbs == (0, 1, 2):
                            if self.__rawgreyimage.shape[-1] > 3:
                                self.__rawgreyimage = \
                                    self.__rawgreyimage[:, :, :3]
                            elif self.__filteredimage.shape[-1] == 2:
                                nshape = list(self.__rawgreyimage.shape)
                                nshape[-1] = 1
                                self.__rawgreyimage = np.concatenate(
                                    (self.__rawgreyimage,
                                     np.zeros(
                                         shape=nshape.
                                         shape[:, :, -1],
                                         dtype=self.__rawgreyimage.dtype)),
                                    axis=2)
                        else:
                            zeros = None
                            nshape = list(self.__rawgreyimage.shape)
                            nshape[-1] = 1
                            if -1 in rgbs:
                                zeros = np.zeros(
                                    shape=nshape,
                                    dtype=self.__rawgreyimage.dtype)

                            self.__rawgreyimage = np.concatenate(
                                (self.__rawgreyimage[:, :, rgbs[0]].
                                 reshape(nshape)
                                 if rgbs[0] != -1 else zeros,
                                 self.__rawgreyimage[:, :, rgbs[1]].
                                 reshape(nshape)
                                 if rgbs[1] != -1 else zeros,
                                 self.__rawgreyimage[:, :, rgbs[2]].
                                 reshape(nshape)
                                 if rgbs[2] != -1 else zeros),
                                axis=2)

                    elif self.__filteredimage.shape[0] == 1:
                        if self.rgb():
                            self.setrgb(False)
                            self.__channelwg.showGradient(True)
                            self.__levelswg.showGradient(True)
                        self.__rawgreyimage = self.__filteredimage[:, :, 0]

                except Exception:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.__channelwg.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.__channelwg.colorChannel(),
                        text, str(value))
                    self.__channelwg.setChannel(0)
        elif len(self.__filteredimage.shape) == 2:
            if self.rgb():
                self.setrgb(False)
                self.__channelwg.showGradient(True)
                self.__levelswg.showGradient(True)
            if self.__imagewg.applyMask():
                self.__rawgreyimage = np.array(self.__filteredimage)
            else:
                self.__rawgreyimage = self.__filteredimage
            self.__channelwg.setNumberOfChannels(0)

        elif len(self.__filteredimage.shape) == 1:
            if self.rgb():
                self.setrgb(False)
                self.__channelwg.showGradient(True)
                self.__levelswg.showGradient(True)
            self.__rawgreyimage = np.array(
                self.__filteredimage).reshape(
                    (self.__filteredimage.shape[0], 1))
            self.__channelwg.setNumberOfChannels(0)

        self.__displayimage = self.__rawgreyimage

        if self.__dobkgsubtraction and self.__backgroundimage is not None:
            # simple subtraction
            try:
                if (hasattr(self.__rawgreyimage, "dtype") and
                   self.__rawgreyimage.dtype.name in
                    self.__unsignedmap.keys()) \
                   and (hasattr(self.__backgroundimage, "dtype") and
                   self.__backgroundimage.dtype.name in
                        self.__unsignedmap.keys()):
                    self.__displayimage = np.subtract(
                        self.__rawgreyimage, self.__backgroundimage,
                        dtype=self.__unsignedmap[
                            self.__rawgreyimage.dtype.name])
                else:
                    self.__displayimage = \
                        self.__rawgreyimage - self.__backgroundimage
            except Exception:
                self._checkBkgSubtraction(0)
                self.__backgroundimage = None
                self.__dobkgsubtraction = False
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Background image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Background image does not match "
                    "to the current image",
                    text, str(value))

        if self.__settings.showmask and self.__imagewg.applyMask() and \
           self.__imagewg.maskIndices() is not None:
            # set all masked (non-zero values) to zero by index
            try:
                if not self.__settings.nanmask:
                    self.__displayimage = np.array(self.__displayimage)
                    self.__displayimage[self.__imagewg.maskIndices()] = 0
                else:
                    self.__displayimage = np.array(
                        self.__displayimage,
                        dtype=self.__settings.floattype)
                    self.__displayimage[self.__imagewg.maskIndices()] = np.nan
            except IndexError:
                self.__maskwg.noImage()
                self.__imagewg.setApplyMask(False)
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Mask image does not match "
                    "to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Mask image does not match "
                    "to the current image",
                    text, str(value))

        if self.__settings.showhighvaluemask and \
           self.__imagewg.maskValue() is not None:
            try:
                if self.__settings.nanmask:
                    self.__displayimage = np.array(
                        self.__displayimage,
                        dtype=self.__settings.floattype)
                    with np.warnings.catch_warnings():
                        np.warnings.filterwarnings(
                            'ignore', r'invalid value encountered in greater')
                        self.__imagewg.setMaskValueIndices(
                            self.__displayimage > self.__imagewg.maskValue())
                        self.__displayimage[
                            self.__imagewg.maskValueIndices()] = np.nan
                else:
                    self.__displayimage = np.array(self.__displayimage)
                    self.__imagewg.setMaskValueIndices(
                        self.__displayimage > self.__imagewg.maskValue())
                    self.__displayimage[
                            self.__imagewg.maskValueIndices()] = 0
            except IndexError:
                # self.__highvaluemaskwg.noValue()
                import traceback
                value = traceback.format_exc()
                text = messageBox.MessageBox.getText(
                    "lavue: Cannot apply high value mask to the current image")
                messageBox.MessageBox.warning(
                    self, "lavue: Cannot apply high value mask"
                    " to the current image",
                    text, str(value))

    # @debugmethod
    def __transform(self):
        """ does the image transformation on the given numpy array.

        :returns: crdtranspose, crdleftrightflip, crdupdownflip,
         orgtranspose, orgleftrightflip, orgupdownflip flags
        :rtype: (:obj:`bool`, :obj:`bool`, :obj:`bool`,:obj:`bool`,
                 :obj:`bool`, :obj:`bool`)
        """
        crdupdownflip = False
        crdleftrightflip = False
        crdtranspose = False
        orgupdownflip = False
        orgleftrightflip = False
        orgtranspose = False
        if self.__trafoname == "none":
            pass
        elif self.__trafoname == "flip (up-down)":
            orgupdownflip = True
            if self.__settings.keepcoords:
                crdupdownflip = True
            elif self.__displayimage is not None:
                self.__displayimage = np.fliplr(self.__displayimage)
        elif self.__trafoname == "flip (left-right)":
            orgleftrightflip = True
            if self.__settings.keepcoords:
                crdleftrightflip = True
            elif self.__displayimage is not None:
                self.__displayimage = np.flipud(self.__displayimage)
        elif self.__trafoname == "transpose":
            orgtranspose = True
            if self.__displayimage is not None:
                self.__displayimage = np.swapaxes(
                    self.__displayimage, 0, 1)
                # self.__displayimage = np.transpose(self.__displayimage)
            if self.__settings.keepcoords:
                crdtranspose = True
        elif self.__trafoname == "rot90 (clockwise)":
            orgtranspose = True
            orgupdownflip = True
            if self.__settings.keepcoords:
                crdtranspose = True
                crdupdownflip = True
                if self.__displayimage is not None:
                    self.__displayimage = np.swapaxes(
                        self.__displayimage, 0, 1)
                    # self.__displayimage = np.transpose(self.__displayimage)
            elif self.__displayimage is not None:
                # self.__displayimage = np.transpose(
                #     np.flipud(self.__displayimage))
                self.__displayimage = np.swapaxes(
                    np.flipud(self.__displayimage), 0, 1)
        elif self.__trafoname == "rot180":
            orgupdownflip = True
            orgleftrightflip = True
            if self.__settings.keepcoords:
                crdupdownflip = True
                crdleftrightflip = True
            elif self.__displayimage is not None:
                self.__displayimage = np.flipud(
                    np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot270 (clockwise)":
            orgtranspose = True
            orgleftrightflip = True
            if self.__settings.keepcoords:
                crdtranspose = True
                crdleftrightflip = True
                if self.__displayimage is not None:
                    self.__displayimage = np.swapaxes(
                        self.__displayimage, 0, 1)
                    # self.__displayimage = np.transpose(self.__displayimage)
            elif self.__displayimage is not None:
                self.__displayimage = np.swapaxes(
                    np.fliplr(self.__displayimage), 0, 1)
                # self.__displayimage = np.transpose(
                #     np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot180 + transpose":
            orgtranspose = True
            orgupdownflip = True
            orgleftrightflip = True
            if self.__settings.keepcoords:
                crdtranspose = True
                crdupdownflip = True
                crdleftrightflip = True
                if self.__displayimage is not None:
                    # self.__displayimage = np.transpose(self.__displayimage)
                    self.__displayimage = np.swapaxes(
                        self.__displayimage, 0, 1)
            elif self.__displayimage is not None:
                self.__displayimage = np.swapaxes(
                    np.fliplr(np.flipud(self.__displayimage)), 0, 1)
                # self.__displayimage = np.transpose(
                #     np.fliplr(np.flipud(self.__displayimage)))
        return (crdtranspose, crdleftrightflip, crdupdownflip,
                orgtranspose, orgleftrightflip, orgupdownflip)

    # @debugmethod
    def __applyRange(self):
        """ applies user range
        """
        if self.__settings.showrange and \
           self.__filteredimage is not None:
            x1, y1, x2, y2 = self.__rangewg.rangeWindow()
            position = [None, None]
            if x1 is not None or y1 is not None or \
               x2 is not None or y2 is not None:
                position = self.__setrange(x1, y1, x2, y2)
            scale = [None, None]
            factor = self.__rangewg.factor()
            if factor > 1:
                function = self.__rangewg.function()
                scale = self.__npresize(factor, function)
            if self.__trafoname in ["transpose",
                                    "rot90 (clockwise)",
                                    "rot270 (clockwise)",
                                    "rot180 + transpose"]:
                position = [position[1], position[0]]
                scale = [scale[1], scale[0]]

    # @debugmethod
    def __setrange(self, x1, y1, x2, y2):
        """ sets window range

        :param x1: x1 position
        :type x1: :obj:`int`
        :param y1: y1 position
        :type y1: :obj:`int`
        :param x2: x2 position
        :type x2: :obj:`int`
        :param y2: y2 position
        :type y2: :obj:`int`
        :returns: x,y - start x,y-position
        :rtype: (:obj:`int`, :obj:`int`)
        """
        image = None
        position = [0, 0]
        shape = self.__filteredimage.shape
        if len(shape) == 1 and shape[0]:
            image = self.__filteredimage[x1:x2]
        elif len(shape) == 2:
            image = self.__filteredimage[x1:x2, y1:y2]
        elif len(shape) == 3:
            image = self.__filteredimage[:, x1:x2, y1:y2]
        if image is not None and image.size > 0:
            self.__filteredimage = image
            position = [x1 or 0, y1 or 0]
        return position

    # @debugmethod
    def __npresize(self, factor, function):
        """ resizes image

        :param factor: down-sampling factor
        :type factor: :obj:`int`
        :param function: reduction function
        :type function: :obj:`str`
        :returns: x,y - invert scale
        :rtype: (:obj:`int`, :obj:`int`)
        """
        shape = self.__filteredimage.shape
        scale = [1, 1]
        if len(shape) > 1 and factor > 1:
            w = shape[-2] // factor
            h = shape[-1] // factor
            ww = w * factor
            hh = h * factor
            if ww < factor or hh < factor:
                nfactor = max(min(int(shape[-2]), int(shape[-1])), 1)
                self.__rangewg.setFactor(nfactor)
                factor = 1
                w = shape[-2] // factor
                h = shape[-1] // factor
                ww = w * factor
                hh = h * factor

            if len(shape) == 2 and factor > 1:
                self.__filteredimage = \
                    getattr(
                        self.__filteredimage[:ww, :hh].
                        reshape(w, factor, h, factor),
                        function)((-1, -3))
            elif len(shape) == 3:
                self.__filteredimage = \
                    getattr(
                        self.__filteredimage[:, :ww, :hh].
                        reshape(shape[0], w, factor, h, factor),
                        function)((-1, -3))
            scale = [factor, factor]
        return scale

    @debugmethod
    @QtCore.pyqtSlot()
    def _resizePlot(self, show=True):
        """ resize window and plot
        :param show: enable/disable resizing
        :type show: :obj:`bool`
        """
        x1, y1, x2, y2 = self.__rangewg.rangeWindow()
        factor = self.__rangewg.factor()
        positionscale = [x1, y1, factor, factor]
        if show and (x1 or y1 or factor != 1):
            self.__imagewg.updateMetaData(
                positionscale,
                rescale=True)
        else:
            self.__imagewg.updateMetaData(
                [0, 0, 1, 1],
                rescale=False)
        self.setLavueState({
            "rangewindow": self.__rangewg.rangeWindow(),
            "dsfactor": self.__rangewg.factor(),
            "dsreduction": str(self.__rangewg.function())})
        self._plot()

    # @debugmethod
    def __applyFilters(self):
        """ applies user filters
        """
        # self.__filteredimage = self.__rawimage
        if self.__filterstate:
            for flt in self.__filters:
                try:
                    if self.__filteredimage is not None:
                        image = flt(
                            self.__filteredimage,
                            self.__imagename,
                            self.__metadata,
                            self.__imagewg
                        )
                        fltmdata = None
                        if isinstance(image, tuple):
                            if len(image) >= 2:
                                image, fltmdata = image[:2]
                            if len(image) == 1:
                                image = image
                        if image is not None and (
                                hasattr(image, "size") and image.size > 1):
                            self.__filteredimage = image
                        if isinstance(fltmdata, dict):
                            self.__mdata.update(fltmdata)
                except Exception as e:
                    self.__filterswg.setState(0)
                    import traceback
                    value = traceback.format_exc()
                    messageBox.MessageBox.warning(
                        self, "lavue: problems in applying filters",
                        "%s" % str(e),
                        "%s" % value)
                    # print(str(e))

    # @debugmethod
    def __scale(self, scalingtype):
        """ sets scaletype on the image

        :param scalingtype: scaling type
        :type scalingtype: :obj:`str`
        """
        self.__imagewg.setScalingType(scalingtype)
        if self.__displayimage is None:
            self.__scaledimage = None
        elif scalingtype == "sqrt":
            self.__scaledimage = np.clip(self.__displayimage, 0, np.inf)
            self.__scaledimage = np.sqrt(self.__scaledimage)
        elif scalingtype == "log":
            self.__scaledimage = np.clip(self.__displayimage, 10e-3, np.inf)
            self.__scaledimage = np.log10(self.__scaledimage)
        elif _VMAJOR == '0' and _VMINOR == '9' and int(_VPATCH) > 7:
            # (for 0.9.8 <= version < 0.10.0 i.e. ubuntu 16.04)
            self.__scaledimage = self.__displayimage.astype(
                self.__settings.floattype)
        else:
            self.__scaledimage = self.__displayimage

    # @debugmethod
    def __calcStats(self, flag):
        """ calcualtes scaled limits for intesity levels

        :param flag: (max value, mean value, variance value,
                  min scaled value, max raw value, max scaled value)
                  to calculate
        :type flag: [:obj:`bool`, :obj:`bool`, :obj:`bool`,
                       :obj:`bool`, :obj:`bool`, :obj:`bool`]
        :returns: max value, mean value, variance value,
                  min scaled value, max raw value, max scaled value
        :rtype: [:obj:`str`, :obj:`str`, :obj:`str`, :obj:`str`,
                    :obj:`str`, :obj:`str`]
        """
        if self.__settings.statswoscaling and self.__displayimage is not None \
           and self.__displayimage.size > 0:
            maxval = np.nanmax(self.__displayimage) if flag[0] else 0.0
            meanval = np.nanmean(self.__displayimage) if flag[1] else 0.0
            varval = np.nanvar(self.__displayimage) if flag[2] else 0.0
            maxsval = np.nanmax(self.__scaledimage) if flag[5] else 0.0
        elif (not self.__settings.statswoscaling
              and self.__scaledimage is not None
              and self.__displayimage.size > 0):
            maxval = np.nanmax(self.__scaledimage) \
                     if flag[0] or flag[5] else 0.0
            meanval = np.nanmean(self.__scaledimage) if flag[1] else 0.0
            varval = np.nanvar(self.__scaledimage) if flag[2] else 0.0
            maxsval = maxval
        else:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        maxrawval = np.nanmax(self.__rawgreyimage) if flag[4] else 0.0
        minval = np.nanmin(self.__scaledimage) if flag[3] else 0.0
        return (maxval, meanval, varval, minval, maxrawval,  maxsval)

    @debugmethod
    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(int)
    def _checkHighMasking(self, _=''):
        """ reads the mask image, select non-zero elements and store the indices
        """
        value = self.__highvaluemaskwg.mask()
        try:
            self.__imagewg.setMaskValue(float(value))
        except Exception:
            self.__imagewg.setMaskValue(None)
        maskhighvalue = ""
        if self.__settings.showhighvaluemask:
            maskhighvalue = str(value or "")
        self.setLavueState({"maskhighvalue": maskhighvalue})
        self._plot()

    @debugmethod
    @QtCore.pyqtSlot(int)
    def _checkMasking(self, state):
        """ replots the image with mask if mask exists
        """
        self.__imagewg.setApplyMask(state)
        if self.__imagewg.applyMask() and self.__maskimage is None:
            self.__maskwg.noImage()
        maskfile = ""
        if self.__maskwg.isMaskApplied():
            maskfile = str(self.__settings.maskimagename)
        self.setLavueState({"maskfile": maskfile})
        self._plot()

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _prepareMasking(self, imagename):
        """ reads the mask image, select non-zero elements and store the indices
        """
        imagename = str(imagename)
        if imagename:
            if imagename.endswith(".nxs") or imagename.endswith(".h5") \
               or imagename.endswith(".nx") or imagename.endswith(".ndf"):
                fieldpath = None
                growing = 0
                frame = 0
                handler = imageFileHandler.NexusFieldHandler(
                    str(imagename))
                fields = handler.findImageFields()
                if fields:
                    imgfield = imageField.ImageField(self)
                    imgfield.fields = fields
                    imgfield.frame = 0
                    imgfield.createGUI()
                    if imgfield.exec_():
                        fieldpath = imgfield.field
                        growing = imgfield.growing
                        frame = imgfield.frame
                    else:
                        return
                    currentfield = fields[fieldpath]
                    self.__maskimage = np.transpose(handler.getImage(
                        currentfield["node"],
                        frame, growing, refresh=False))
                else:
                    return
            else:
                self.__maskimage = np.transpose(
                    imageFileHandler.ImageFileHandler(
                        str(imagename)).getImage())
            if self.__settings.zeromask:
                self.__imagewg.setMaskIndices(self.__maskimage == 0)
            else:
                self.__imagewg.setMaskIndices(self.__maskimage != 0)
        else:
            self.__maskimage = None

    # @debugmethod
    def __remasking(self):
        """ recalculates the mask
        """
        if self.__maskimage is not None:
            if self.__settings.zeromask:
                self.__imagewg.setMaskIndices(self.__maskimage == 0)
            else:
                self.__imagewg.setMaskIndices(self.__maskimage != 0)

    @debugmethod
    @QtCore.pyqtSlot(int)
    def _checkBkgSubtraction(self, state):
        """ replots the image with subtranction if background image exists

        :param state: checkbox state
        :type state:  :obj:`int`
        """
        self.__dobkgsubtraction = bool(state)
        if self.__dobkgsubtraction and self.__backgroundimage is None:
            self.__bkgsubwg.setDisplayedName("")
        else:
            self.__bkgsubwg.checkBkgSubtraction(state)
        self.__imagewg.setDoBkgSubtraction(state)
        bkgfile = ""
        if self.__bkgsubwg.isBkgSubApplied():
            bkgfile = str(self.__settings.bkgimagename)
        self.setLavueState({"bkgfile": bkgfile})
        self._plot()

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _prepareBkgSubtraction(self, imagename):
        """ reads the background image

        :param imagename: image name
        :type imagename: :obj:`str`
        """
        imagename = str(imagename)
        if imagename:
            if imagename.endswith(".nxs") or imagename.endswith(".h5") \
               or imagename.endswith(".nx") or imagename.endswith(".ndf"):
                fieldpath = None
                growing = 0
                frame = 0
                handler = imageFileHandler.NexusFieldHandler(
                    str(imagename))
                fields = handler.findImageFields()
                if fields:
                    imgfield = imageField.ImageField(self)
                    imgfield.fields = fields
                    imgfield.frame = 0
                    imgfield.createGUI()
                    if imgfield.exec_():
                        fieldpath = imgfield.field
                        growing = imgfield.growing
                        frame = imgfield.frame
                    else:
                        return
                    currentfield = fields[fieldpath]
                    self.__backgroundimage = np.transpose(
                        handler.getImage(
                            currentfield["node"],
                            frame, growing, refresh=False))
                else:
                    return
            else:
                self.__backgroundimage = np.transpose(
                    imageFileHandler.ImageFileHandler(
                        str(imagename)).getImage())
        else:
            self.__backgroundimage = None

    @debugmethod
    @QtCore.pyqtSlot()
    def _setCurrentImageAsBkg(self):
        """ sets the chrrent image as the background image
        """
        if self.__rawgreyimage is not None:
            self.__backgroundimage = self.__rawgreyimage
            self.__bkgsubwg.setDisplayedName(str(self.__imagename))
        else:
            self.__bkgsubwg.setDisplayedName("")

    @debugmethod
    @QtCore.pyqtSlot(bool)
    def _assessFilters(self, state):
        """ assesses the filter on/off state

        :param state: assess filter status
        :type state:  :obj:`bool`
        """
        if self.__filterstate != state:
            self.__filterstate = state
            for flt in self.__filters:
                try:
                    if state:
                        if hasattr(flt, "initialize"):
                            flt.initialize()
                    else:
                        if hasattr(flt, "terminate"):
                            flt.terminate()
                except Exception as e:
                    self.__filterswg.setState(0)
                    import traceback
                    value = traceback.format_exc()
                    messageBox.MessageBox.warning(
                        self, "lavue: problems in starting or stoping filters",
                        "%s" % str(e),
                        "%s" % value)
                    # print(str(e))

            self.setLavueState({"filters": bool(self.__filterstate)})
            if self.__displayimage is not None:
                self._plot()

    @debugmethod
    @QtCore.pyqtSlot(str)
    def _assessTransformation(self, trafoname):
        """ assesses the transformation and replot it

        :param imagename: transformation name
        :type imagename: :obj:`str`
        """
        self.__trafoname = trafoname
        if trafoname in [
                "transpose", "rot90 (clockwise)",
                "rot270 (clockwise)", "rot180 + transpose"]:
            self.__trafowg.setKeepCoordsLabel(
                self.__settings.keepcoords, True)
        else:
            self.__trafowg.setKeepCoordsLabel(
                self.__settings.keepcoords, False)
        self.setLavueState({"transformation": trafoname})
        self._plot()

    @debugmethod
    def keyPressEvent(self,  event):
        """ skips escape key action

        :param event: close event
        :type event:  :class:`pyqtgraph.QtCore.QEvent`:
        """
        if event.key() != QtCore.Qt.Key_Escape:
            QtGui.QDialog.keyPressEvent(self, event)
        # else:
        #     self.closeEvent(None)

    @debugmethod
    @QtCore.pyqtSlot(bool)
    def setrgb(self, status=True):
        """ sets RGB on/off

        :param status: True for on and False for off
        :type status: :obj:`bool`
        """
        self.__levelswg.setrgb(status)
        self.__imagewg.setrgb(status)
        self._plot()

    @debugmethod
    @QtCore.pyqtSlot(bool)
    def _setRGBState(self, status=True):
        """ sets RGB on/off

        :param status: True for on and False for off
        :type status: :obj:`bool`
        """
        self.__levelswg.setrgb(status)
        self.__imagewg.setrgb(status)
        self.setLavueState({"channel": self.__channelwg.channelLabel()})
        self._plot()

    @debugmethod
    def rgb(self):
        """ gets RGB on/off

        :returns: True for on and False for off
        :rtype: :obj:`bool`
        """
        return self.__imagewg.rgb()
