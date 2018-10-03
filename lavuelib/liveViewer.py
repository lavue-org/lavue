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
import json
import numpy as np
import pyqtgraph as _pg
import os
import zmq
import sys

from PyQt4 import QtCore, QtGui, uic

from . import imageSource as isr
from . import messageBox

from . import sourceGroupBox
from . import preparationGroupBox
from . import scalingGroupBox
from . import levelsGroupBox
from . import statisticsGroupBox
from . import imageWidget
from . import imageField
from . import configDialog
from . import release
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


if sys.version_info > (3,):
    basestring = str
    unicode = str


#: ( (:obj:`str`,:obj:`str`,:obj:`str`) )
#:         pg major version, pg minor verion, pg patch version
_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MainWindow.ui"))


class LiveViewer(QtGui.QMainWindow):

    '''The master class for the dialog, contains all other
    widget and handles communication.'''

    #: (:class:`PyQt4.QtCore.pyqtSignal`) state updated signal
    _stateUpdated = QtCore.pyqtSignal(bool)

    def __init__(self, options, parent=None):
        """ constructor

        :param options: commandline options
        :type options: :class:`argparse.Namespace`
        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #: (:obj:`list` < :obj:`str` > ) source class names
        self.__sourcetypes = []
        if isr.HIDRA:
            self.__sourcetypes.append("HidraSourceWidget")
        if isr.REQUESTS:
            self.__sourcetypes.append("HTTPSourceWidget")
        if isr.PYTANGO:
            self.__sourcetypes.append("TangoAttrSourceWidget")
            self.__sourcetypes.append("TangoFileSourceWidget")
        self.__sourcetypes.append("ZMQSourceWidget")
        self.__sourcetypes.append("NXSFileSourceWidget")
        self.__sourcetypes.append("TestSourceWidget")
        # self.__sourcetypes.append("FixTestSourceWidget")

        #: (:obj:`list` < :obj:`str` > ) tool class names
        self.__tooltypes = []
        self.__tooltypes.append("IntensityToolWidget")
        self.__tooltypes.append("ROIToolWidget")
        self.__tooltypes.append("LineCutToolWidget")
        self.__tooltypes.append("AngleQToolWidget")
        if isr.PYTANGO:
            self.__tooltypes.append("MotorsToolWidget")
            self.__tooltypes.append("MeshToolWidget")
        self.__tooltypes.append("OneDToolWidget")
        self.__tooltypes.append("ProjectionToolWidget")
        self.__tooltypes.append("QROIProjToolWidget")

        if options.mode and options.mode.lower() in ["expert"]:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "expert"
        else:
            #: (:obj:`str`) execution mode: expert or user
            self.__umode = "user"
        #: (:obj:`bool`) histogram should be updated
        self.__updatehisto = False
        #: (:obj:`int`) program pid
        self.__apppid = os.getpid()

        #: (:obj:`list` < :obj:`str` > ) allowed source metadata
        self.__allowedmdata = ["datasources"]
        #: (:obj:`list` < :obj:`str` > ) allowed widget metadata
        self.__allowedwgdata = ["axisscales", "axislabels"]

        # (:class:`lavuelib.imageSource.BaseSource`) data source object
        self.__datasource = isr.BaseSource()

        #: (:class:`lavuelib.sardanaUtils.SardanaUtils`)
        #:  sardana utils
        self.__sardana = None

        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings.Settings()

        #: (:class:`lavuelib.controllerClient.ControllerClient`)
        #:   tango controller client
        self.__tangoclient = None

        #: (:obj:`int`) stacking dimension
        self.__growing = None
        #: (:obj:`int`) current frame id
        self.__frame = None
        #: (:obj:`bool`) histogram should be updated
        self.__frameshow = False
        #: (:obj:`str`) nexus field path
        self.__fieldpath = None

        # WIDGET DEFINITIONS
        #: (:class:`lavuelib.sourceGroupBox.SourceGroupBox`) source groupbox
        self.__sourcewg = sourceGroupBox.SourceGroupBox(
            parent=self, sourcetypes=self.__sourcetypes)

        #: (:class:`lavuelib.preparationGroupBox.PreparationGroupBox`)
        #: preparation groupbox
        self.__prepwg = preparationGroupBox.PreparationGroupBox(
            parent=self, settings=self.__settings)
        #: (:class:`lavuelib.scalingGroupBox.ScalingGroupBox`) scaling groupbox
        self.__scalingwg = scalingGroupBox.ScalingGroupBox(parent=self)
        #: (:class:`lavuelib.levelsGroupBox.LevelsGroupBox`) level groupbox
        self.__levelswg = levelsGroupBox.LevelsGroupBox(parent=self)
        #: (:class:`lavuelib.statisticsGroupBox.StatisticsGroupBox`)
        #:     statistic groupbox
        self.__statswg = statisticsGroupBox.StatisticsGroupBox(parent=self)
        #: (:class:`lavuelib.imageWidget.ImageWidget`) image widget
        self.__imagewg = imageWidget.ImageWidget(
            parent=self, tooltypes=self.__tooltypes, settings=self.__settings)

        self.__levelswg.setImageItem(self.__imagewg.image())
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
        #: (:class:`numpy.ndarray`) raw gray image
        self.__rawgreyimage = None
        #: (:obj:`str`) image name
        self.__imagename = None
        #: (:obj:`str`) last image name
        self.__lastimagename = None
        #: (:obj:`str`) metadata JSON dictionary
        self.__metadata = ""
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
        #: (:obj:`float`) file name
        self.__maskvalue = None
        #: (:class:`numpy.ndarray`) mask image indices
        self.__maskindices = None
        #: (:obj:`bool`) apply mask
        self.__applymask = False

        #: (:obj:`str`) source configuration string
        self.__sourceconfiguration = None

        #: (:obj:`str`) transformation name
        self.__trafoname = "None"

        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        # # LAYOUT DEFINITIONS
        self.setWindowTitle(
            "laVue: Live Image Viewer (v%s)" % str(release.__version__))
        self.__ui.confVerticalLayout.addWidget(self.__sourcewg)
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
            self.__levelswg.setScalingLabel)

        # signal from limit setting widget
        self.__levelswg.minLevelChanged.connect(self.__imagewg.setMinLevel)
        self.__levelswg.maxLevelChanged.connect(self.__imagewg.setMaxLevel)
        self.__levelswg.autoLevelsChanged.connect(self.__imagewg.setAutoLevels)
        self.__levelswg.levelsChanged.connect(self._plot)
        self.__ui.cnfPushButton.clicked.connect(self._configuration)
        self.__ui.quitPushButton.clicked.connect(self.close)
        self.__ui.loadPushButton.clicked.connect(self._loadfile)
        if self.__umode in ["user"]:
            self.__ui.cnfPushButton.hide()
        self.__imagewg.roiCoordsChanged.connect(self._calcUpdateStatsSec)
        self.__imagewg.currentToolChanged.connect(
            self._onToolChanged)
        # connecting signals from source widget:
        self.__sourcewg.sourceConnected.connect(self._connectSource)
#        self.__sourcewg.sourceConnected.connect(self._startPlotting)

#        self.__sourcewg.sourceDisconnected.connect(self._stopPlotting)
        self.__sourcewg.sourceDisconnected.connect(self._disconnectSource)

        # gradient selector
        self.__levelswg.channelChanged.connect(self._plot)
        self.__imagewg.aspectLockedToggled.connect(self._setAspectLocked)

        self.__imagewg.replotImage.connect(self._replot)
        # simple mutable caching object for data exchange with thread
        #: (:class:`lavuelib.dataFetchTread.ExchangeList`)
        #:    exchange list
        self.__exchangelist = dataFetchThread.ExchangeList()

        #: (:class:`lavuelib.dataFetchTread.DataFetchThread`)
        #:    data fetch thread
        self.__dataFetcher = dataFetchThread.DataFetchThread(
            self.__datasource, self.__exchangelist)
        self.__dataFetcher.newDataNameFetched.connect(self._getNewData)
        # ugly !!! sent current state to the data fetcher...
        self._stateUpdated.connect(self.__dataFetcher.changeStatus)
        self.__sourcewg.sourceStateChanged.connect(self._updateSource)
        self.__sourcewg.sourceChanged.connect(self._onSourceChanged)

        self.__bkgsubwg.bkgFileSelected.connect(self._prepareBkgSubtraction)
        self.__bkgsubwg.useCurrentImageAsBkg.connect(
            self._setCurrentImageAsBkg)
        self.__bkgsubwg.applyStateChanged.connect(self._checkBkgSubtraction)

        self.__maskwg.maskFileSelected.connect(self._prepareMasking)
        self.__maskwg.applyStateChanged.connect(self._checkMasking)

        self.__highvaluemaskwg.maskHighValueChanged.connect(
            self._checkHighMasking)

        # signals from transformation widget
        self.__trafowg.transformationChanged.connect(
            self._assessTransformation)

        # set the right target name for the source display at initialization

        self.__sourcewg.configurationChanged.connect(
            self._setSourceConfiguration)
        self.__ui.frameSpinBox.valueChanged.connect(self._reloadfile)
        self.__sourcewg.updateLayout()
        self.__sourcewg.emitSourceChanged()
        self.__imagewg.showCurrentTool()

        self.__loadSettings()

        self.__updateframeview()

        start = self.__applyoptions(options)
        self._plot()
        if start:
            self.__sourcewg.start()

        if options.tool:
            QtCore.QTimer.singleShot(10, self.__imagewg.showCurrentTool)

    def __applyoptions(self, options):
        """ apply options

        :param options: commandline options
        :type options: :class:`argparse.Namespace`
        :returns: start flag
        :rtype: :obj:`bool`
        """
        if options.doordevice:
            self.__settings.doorname = options.doordevice

        # load image file
        if options.imagefile:
            oldname = self.__settings.imagename
            oldpath = self.__fieldpath
            oldgrowing = self.__growing
            try:
                self.__settings.imagename = options.imagefile
                if ":/" in self.__settings.imagename:
                    self.__settings.imagename, self.__fieldpath =  \
                        self.__settings.imagename.split(":/", 1)
                else:
                    self.__fieldpath = None
                self.__growing = 0
                self._loadfile(fid=0)
            except Exception:
                self.__settings.imagename = oldname
                self.__fieldpath = oldpath
                self.__growing = oldgrowing

        # set image source
        if options.source:
            msid = None
            for sid, src in enumerate(self.__sourcetypes):
                if src.endswith("SourceWidget"):
                    src = src[:-12]
                    if options.source == src.lower():
                        msid = sid
                        break
            if msid is not None:
                self.__sourcewg.setSourceComboBox(msid)

        if options.configuration:
            self.__sourcewg.configure(options.configuration)

        if options.bkgfile:
            self.__bkgsubwg.setBackground(options.bkgfile)

        if options.maskfile:
            self.__maskwg.setMask(options.maskfile)

        if options.maskhighvalue:
            self.__highvaluemaskwg.setMask(options.maskhighvalue)

        if options.transformation:
            self.__trafowg.setTransformation(options.transformation)

        if options.scaling:
            self.__scalingwg.setScaling(options.scaling)

        if options.levels:
            self.__levelswg.setLevels(options.levels)

        if options.gradient:
            self.__levelswg.setGradient(options.gradient)

        if options.tool:
            self.__imagewg.setTool(options.tool)

        if TANGOCLIENT and options.tangodevice:
            self.__tangoclient = controllerClient.ControllerClient(
                options.tangodevice)
            self.__tangoclient.energyChanged.connect(
                self.__imagewg.updateEnergy)
            self.__tangoclient.detectorDistanceChanged.connect(
                self.__imagewg.updateDetectorDistance)
            self.__tangoclient.beamCenterXChanged.connect(
                self.__imagewg.updateBeamCenterX)
            self.__tangoclient.beamCenterYChanged.connect(
                self.__imagewg.updateBeamCenterY)
            self.__tangoclient.detectorROIsChanged.connect(
                self.__imagewg.updateDetectorROIs)
            self.__imagewg.setTangoClient(self.__tangoclient)
            self.__tangoclient.subscribe()
        else:
            self.__tangoclient = None

        return options.start is True

    @QtCore.pyqtSlot(int)
    def _replotFrame(self, fid):
        """ update ROIs

        :param fid: frame id
        :type fid: :obj:`int`
        """
        self.__ui.frameSpinBox.valueChanged.disconnect(self._replotFrame)
        newimage = None
        if self.__currentfield is not None:
            self.__frame = int(fid)
            try:
                newimage = imageFileHandler.NexusFieldHandler("").getImage(
                    self.__currentfield["node"],
                    self.__frame, self.__growing)
                while newimage is None and self.__frame > 0:
                    self.__frame -= 1
                    self.__updateframeview(True)
                    newimage = imageFileHandler.NexusFieldHandler("").getImage(
                        self.__currentfield["node"],
                        self.__frame, self.__growing)
            except Exception as e:
                import traceback
                value = traceback.format_exc()
                messageBox.MessageBox.warning(
                    self, "lavue: problems in reading the Nexus frame",
                    "%s" % str(e),
                    "%s" % value)
            if newimage is not None:
                self.__rawimage = np.transpose(newimage)
                self._plot()
        self.__ui.frameSpinBox.valueChanged.connect(self._replotFrame)

    def __loadSettings(self):
        """ loads settings from QSettings object
        """
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value(
            "Layout/Geometry", type=QtCore.QByteArray))
        status = self.__settings.load(settings)

        for topic, value in status:
            text = messageBox.MessageBox.getText(topic)
            messageBox.MessageBox.warning(self, topic, text, str(value))

        self.__setSardana(self.__settings.sardana)
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
        self.__imagewg.setAutoDownSample(self.__settings.autodownsample)
        self._assessTransformation(self.__trafoname)
        self.__datasource.setTimeOut(self.__settings.timeout)
        dataFetchThread.GLOBALREFRESHRATE = self.__settings.refreshrate
        self.__imagewg.setStatsWOScaling(self.__settings.statswoscaling)
        self.__imagewg.setROIsColors(self.__settings.roiscolors)

        if self.__settings.detservers:
            serverdict = {"pool": list(self.__settings.detservers)}
        else:
            serverdict = HIDRASERVERLIST
        self.__sourcewg.updateMetaData(
            zmqtopics=self.__settings.zmqtopics,
            dirtrans=self.__settings.dirtrans,
            tangoattrs=self.__settings.tangoattrs,
            tangofileattrs=self.__settings.tangofileattrs,
            tangodirattrs=self.__settings.tangodirattrs,
            zmqservers=self.__settings.zmqservers,
            httpurls=self.__settings.httpurls,
            autozmqtopics=self.__settings.autozmqtopics,
            nxslast=self.__settings.nxslast,
            nxsopen=self.__settings.nxsopen,
            serverdict=serverdict,
            hidraport=self.__settings.hidraport
        )

        self.__statswg.changeView(self.__settings.showstats)
        self.__levelswg.changeView(
            self.__settings.showhisto,
            self.__settings.showlevels)
        self.__prepwg.changeView(
            self.__settings.showmask,
            self.__settings.showsub,
            self.__settings.showtrans,
            self.__settings.showhighvaluemask
        )
        self.__scalingwg.changeView(self.__settings.showscale)
        self.__levelswg.changeView()

    def __storeSettings(self):
        """ stores settings in QSettings object
        """
        settings = QtCore.QSettings()
        settings.setValue(
            "Layout/Geometry",
            QtCore.QByteArray(self.saveGeometry()))

        self.__settings.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        self.__settings.sardana = True if self.__sardana is not None else False
        self.__settings.store(settings)

    @QtCore.pyqtSlot(bool)
    def _setAspectLocked(self, status):
        self.__settings.aspectlocked = status
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)

    @QtCore.pyqtSlot(str)
    def _onToolChanged(self, text):
        if text == "ROI":
            self.__trafoname = "None"
            self.__trafowg.setEnabled(False)
        elif text == "LineCut":
            self.__trafowg.setEnabled(True)
        elif text == "Angle/Q":
            self.__trafowg.setEnabled(True)
        else:
            self.__trafowg.setEnabled(True)

    def closeEvent(self, event):
        """ stores the setting before finishing the application

        :param event: close event
        :type event:  :class:`PyQt4.QtCore.QEvent`:
        """
        if self.__tangoclient:
            self.__tangoclient.unsubscribe()
        self.__storeSettings()
        self.__settings.secstream = False
        try:
            self.__dataFetcher.newDataNameFetched.disconnect(self._getNewData)
        except Exception:
            pass
        # except Exception as e:
        #     print (str(e))

        if self.__sourcewg.isConnected():
            self.__sourcewg.toggleServerConnection()
        self._disconnectSource()
        self.__dataFetcher.stop()
        self.__dataFetcher.wait()
        self.__settings.seccontext.destroy()
        QtGui.QApplication.closeAllWindows()
        event.accept()

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot()
    def _loadfile(self, fid=None):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int`
         """
        self._reloadfile(fid, showmessage=True)

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot()
    def _reloadfile(self, fid=None, showmessage=False):
        """ reloads the image file

        :param fid: frame id
        :type fid: :obj:`int`
        :param showmessage: no image message
        :type showmessage: :obj:`bool`
         """
        newimage = None
        if fid is None:
            fileDialog = QtGui.QFileDialog()
            imagename = str(
                fileDialog.getOpenFileName(
                    self, 'Load file', self.__settings.imagename or '.'))
        else:
            self.__frame = int(fid)
            imagename = self.__settings.imagename
        if imagename:
            if imagename.endswith(".nxs") or imagename.endswith(".h5") \
               or imagename.endswith(".nx") or imagename.endswith(".ndf"):
                self.__settings.imagename = imagename
                handler = imageFileHandler.NexusFieldHandler(
                    str(self.__settings.imagename))
                fields = handler.findImageFields()
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
                    newimage = handler.getImage(
                        currentfield["node"],
                        self.__frame, self.__growing, refresh=False)

                    self.__ui.frameSpinBox.valueChanged.disconnect(
                        self._reloadfile)
                    while newimage is None and self.__frame > 0:
                        self.__frame -= 1
                        self.__updateframeview(True)
                        newimage = handler.getImage(
                            currentfield["node"],
                            self.__frame, self.__growing, refresh=False)
                    self.__ui.frameSpinBox.valueChanged.connect(
                        self._reloadfile)
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
                    self.__updateframeview(True)
            else:
                self.__fieldpath = None
                self.__settings.imagename = imagename
                newimage = imageFileHandler.ImageFileHandler(
                    str(self.__settings.imagename)).getImage()
                self.__updateframeview()
            if newimage is not None:
                self.__imagename = imagename
                self.__rawimage = np.transpose(newimage)
                self._plot()
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

    @QtCore.pyqtSlot()
    def _configuration(self):
        """ launches the configuration dialog
        """
        cnfdlg = configDialog.ConfigDialog(self)
        if not self.__settings.doorname and self.__sardana is not None:
            self.__settings.doorname = self.__sardana.getDeviceName("Door")
        cnfdlg.sardana = True if self.__sardana is not None else False
        cnfdlg.door = self.__settings.doorname
        cnfdlg.addrois = self.__settings.addrois
        cnfdlg.showsub = self.__settings.showsub
        cnfdlg.showtrans = self.__settings.showtrans
        cnfdlg.showscale = self.__settings.showscale
        cnfdlg.showlevels = self.__settings.showlevels
        cnfdlg.showhisto = self.__settings.showhisto
        cnfdlg.showmask = self.__settings.showmask
        cnfdlg.showhighvaluemask = self.__settings.showhighvaluemask
        cnfdlg.showstats = self.__settings.showstats
        cnfdlg.secautoport = self.__settings.secautoport
        cnfdlg.secport = self.__settings.secport
        cnfdlg.hidraport = self.__settings.hidraport
        cnfdlg.secstream = self.__settings.secstream
        cnfdlg.zeromask = self.__settings.zeromask
        cnfdlg.refreshrate = dataFetchThread.GLOBALREFRESHRATE
        cnfdlg.timeout = self.__settings.timeout
        cnfdlg.aspectlocked = self.__settings.aspectlocked
        cnfdlg.autodownsample = self.__settings.autodownsample
        cnfdlg.keepcoords = self.__settings.keepcoords
        cnfdlg.statswoscaling = self.__settings.statswoscaling
        cnfdlg.zmqtopics = self.__settings.zmqtopics
        cnfdlg.detservers = self.__settings.detservers
        cnfdlg.autozmqtopics = self.__settings.autozmqtopics
        cnfdlg.interruptonerror = self.__settings.interruptonerror
        cnfdlg.dirtrans = self.__settings.dirtrans
        cnfdlg.tangoattrs = self.__settings.tangoattrs
        cnfdlg.tangofileattrs = self.__settings.tangofileattrs
        cnfdlg.tangodirattrs = self.__settings.tangodirattrs
        cnfdlg.httpurls = self.__settings.httpurls
        cnfdlg.zmqservers = self.__settings.zmqservers
        cnfdlg.nxslast = self.__settings.nxslast
        cnfdlg.nxsopen = self.__settings.nxsopen
        cnfdlg.sendrois = self.__settings.sendrois
        cnfdlg.showallrois = self.__settings.showallrois
        cnfdlg.storegeometry = self.__settings.storegeometry
        cnfdlg.roiscolors = self.__settings.roiscolors
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__updateConfig(cnfdlg)

    def __updateConfig(self, dialog):
        """ updates the configuration
        """
        self.__settings.doorname = dialog.door
        if dialog.sardana != (True if self.__sardana is not None else False):
            self.__setSardana(dialog.sardana)
            self.__settings.sardana = dialog.sardana
        self.__settings.addrois = dialog.addrois

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

        if self.__settings.showscale != dialog.showscale:
            self.__scalingwg.changeView(dialog.showscale)
            self.__settings.showscale = dialog.showscale

        if self.__settings.showlevels != dialog.showlevels:
            self.__levelswg.changeView(showlevels=dialog.showlevels)
            self.__settings.showlevels = dialog.showlevels

        if self.__settings.showhisto != dialog.showhisto:
            self.__levelswg.changeView(dialog.showhisto)
            self.__settings.showhisto = dialog.showhisto
        if self.__settings.showstats != dialog.showstats:
            self.__statswg.changeView(dialog.showstats)
            self.__settings.showstats = dialog.showstats
        dataFetchThread.GLOBALREFRESHRATE = dialog.refreshrate
        self.__settings.refreshrate = dialog.refreshrate
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
        self.__datasource.setTimeOut(self.__settings.timeout)
        self.__settings.aspectlocked = dialog.aspectlocked
        self.__imagewg.setAspectLocked(self.__settings.aspectlocked)
        self.__settings.autodownsample = dialog.autodownsample
        self.__imagewg.setAutoDownSample(self.__settings.autodownsample)
        replot = False
        remasking = False
        if self.__settings.keepcoords != dialog.keepcoords:
            self.__settings.keepcoords = dialog.keepcoords
            self._assessTransformation(self.__trafoname)
            replot = True

        self.__settings.secstream = dialog.secstream
        self.__settings.storegeometry = dialog.storegeometry
        self.__settings.interruptonerror = dialog.interruptonerror
        setsrc = False
        if self.__settings.hidraport != dialog.hidraport:
            self.__settings.hidraport = dialog.hidraport
            setsrc = True
        if self.__settings.dirtrans != dialog.dirtrans:
            self.__settings.dirtrans = dialog.dirtrans
            setsrc = True
        if self.__settings.tangoattrs != dialog.tangoattrs:
            self.__settings.tangoattrs = dialog.tangoattrs
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
        if self.__settings.detservers != dialog.detservers:
            self.__settings.detservers = dialog.detservers
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
        if self.__settings.showallrois != dialog.showallrois:
            self.__settings.showallrois = dialog.showallrois
        if setsrc:
            if self.__settings.detservers:
                serverdict = {"pool": list(self.__settings.detservers)}
            else:
                serverdict = HIDRASERVERLIST
            self.__sourcewg.updateMetaData(
                zmqtopics=self.__settings.zmqtopics,
                dirtrans=self.__settings.dirtrans,
                tangoattrs=self.__settings.tangoattrs,
                tangofileattrs=self.__settings.tangofileattrs,
                tangodirattrs=self.__settings.tangodirattrs,
                zmqservers=self.__settings.zmqservers,
                httpurls=self.__settings.httpurls,
                autozmqtopics=self.__settings.autozmqtopics,
                nxslast=self.__settings.nxslast,
                nxsopen=self.__settings.nxsopen,
                serverdict=serverdict,
                hidraport=self.__settings.hidraport
            )
            self.__sourcewg.updateLayout()

        self.__settings.statswoscaling = dialog.statswoscaling
        replot = replot or \
            self.__imagewg.setStatsWOScaling(
                self.__settings.statswoscaling)

        if self.__settings.zeromask != dialog.zeromask:
            self.__settings.zeromask = dialog.zeromask
            remasking = True
            replot = True

        if self.__settings.roiscolors != dialog.roiscolors:
            self.__settings.roiscolors = dialog.roiscolors
            self.__imagewg.setROIsColors(self.__settings.roiscolors)

        if remasking:
            self.__remasking()

        if replot:
            self._plot()

    @QtCore.pyqtSlot(str)
    def _setSourceConfiguration(self, sourceConfiguration):
        """ sets the source configuration
        """
        self.__sourceconfiguration = sourceConfiguration
        if self.__sourcewg.currentDataSource() == \
           str(type(self.__datasource).__name__):
            self.__datasource.setConfiguration(self.__sourceconfiguration)

    def __setSardana(self, status):
        """ sets the sardana utils
        """
        if status is False:
            self.__sardana = None
        else:
            self.__sardana = sardanaUtils.SardanaUtils()
        self.__imagewg.setSardanaUtils(self.__sardana)

    @QtCore.pyqtSlot(int)
    def _onSourceChanged(self, status):
        if status:
            self.__datasource = getattr(
                isr, self.__sourcewg.currentDataSource())(
                    self.__settings.timeout)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())

    @QtCore.pyqtSlot(int)
    def _updateSource(self, status):
        """ update the current source

        :param status: current source status id
        :type status: :obj:`int`
        """
        if status:
            self.__datasource.setTimeOut(self.__settings.timeout)
            self.__dataFetcher.setDataSource(self.__datasource)
            if self.__sourceconfiguration:
                self.__datasource.setConfiguration(self.__sourceconfiguration)
            self.__sourcewg.updateMetaData(**self.__datasource.getMetaData())
        self._stateUpdated.emit(bool(status))

    @QtCore.pyqtSlot(bool)
    def _replot(self, autorange):
        """ The main command of the live viewer class:
        draw a numpy array with the given name and autoRange.
        """
        self._plot()
        if autorange:
            self.__imagewg.autoRange()

    @QtCore.pyqtSlot()
    def _plot(self):
        """ The main command of the live viewer class:
        draw a numpy array with the given name.
        """
        # prepare or preprocess the raw image if present:
        self.__prepareImage()

        # perform transformation
        crdtranspose, crdleftrightflip, crdupdownflip = self.__transform()

        # use the internal raw image to create a display image with chosen
        # scaling
        self.__scale(self.__scalingwg.currentScaling())
        # calculate and update the stats for this
        self.__calcUpdateStats()

        # calls internally the plot function of the plot widget
        if self.__imagename is not None and self.__scaledimage is not None:
            self.__ui.fileNameLineEdit.setText(self.__imagename)
        self.__imagewg.setTransformations(
            crdtranspose, crdleftrightflip, crdupdownflip)
        self.__imagewg.plot(
            self.__scaledimage,
            self.__displayimage
            if self.__settings.statswoscaling else self.__scaledimage)
        if self.__settings.showhisto and self.__updatehisto:
            self.__levelswg.updateHistoImage()
            self.__updatehisto = False

    @QtCore.pyqtSlot()
    def _calcUpdateStatsSec(self):
        """ calcuates statistics without  sending security stream
        """
        self.__calcUpdateStats(secstream=False)

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
        maxval, meanval, varval, minval, maxrawval, maxsval = \
            self.__calcStats(
                (stream or display,
                 stream or display,
                 display,
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
            self.__levelswg.updateLevels(minval, maxsval)

    @QtCore.pyqtSlot()
    def _startPlotting(self):
        """ mode changer: start plotting mode.
        It starts plotting if the connection is really established.
        """
        #
        if not self.__sourcewg.isConnected():
            return
        self.__dataFetcher.changeStatus(True)
        if not self.__dataFetcher.isRunning():
            self.__dataFetcher.start()

    @QtCore.pyqtSlot()
    def _stopPlotting(self):
        """ mode changer: stop plotting mode
        """

        if self.__dataFetcher is not None:
            self.__dataFetcher.changeStatus(False)
            pass

    @QtCore.pyqtSlot(int)
    def _connectSource(self, status):
        """  calls the connect function of the source interface

        :param status: current source status id
        :type status: :obj:`int`
        """
        self._updateSource(status)
        if self.__datasource is None:
            messageBox.MessageBox.warning(
                self, "lavue: No data source is defined",
                "No data source is defined",
                "Please select the image source")

        if not self.__datasource.connect():
            self.__sourcewg.connectFailure()
            messageBox.MessageBox.warning(
                self, "lavue: The %s connection could not be established"
                % type(self.__datasource).__name__,
                "The %s connection could not be established"
                % type(self.__datasource).__name__,
                str(self.__datasource.errormessage))
        else:
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
        self._startPlotting()

    @QtCore.pyqtSlot()
    def _disconnectSource(self):
        """ calls the disconnect function of the source interface
        """
        self._stopPlotting()
        self.__datasource.disconnect()
        self.__imagename = None
        self.__imagename = None
        if self.__settings.secstream:
            calctime = time.time()
            messagedata = {
                'command': 'stop', 'calctime': calctime, 'pid': self.__apppid}
            # print(str(messagedata))
            topic = 10001
            self.__settings.secsocket.send_string("%d %s" % (
                topic, str(json.dumps(messagedata)).encode("ascii")))
        self._updateSource(0)
        # self.__datasource = None

    @QtCore.pyqtSlot(str, str)
    def _getNewData(self, name, metadata=None):
        """ checks if data is there at all

        :param name: image name
        :type name: :obj:`str`
        :param metadata: JSON dictionary with metadata
        :type metadata: :obj:`str`
        """

        name, rawimage, metadata = self.__exchangelist.readData()

        if str(self.__imagename).strip() == str(name).strip() and not metadata:
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
            self.__dataFetcher.ready()
            return
        self.__sourcewg.setErrorStatus("")

        if name is None:
            self.__dataFetcher.ready()
            return
        # first time:
        if str(self.__metadata) != str(metadata) and str(metadata).strip():
            imagename, self.__metadata = name, metadata
            if str(imagename).strip() and \
               not isinstance(rawimage, basestring):
                self.__imagename = imagename
                self.__rawimage = rawimage
            try:
                mdata = json.loads(str(metadata))
                if isinstance(mdata, dict):
                    resdata = dict((k, v) for (k, v) in mdata.items()
                                   if k in self.__allowedmdata)
                    wgdata = dict((k, v) for (k, v) in mdata.items()
                                  if k in self.__allowedwgdata)
                    if wgdata:
                        self.__imagewg.updateMetaData(**wgdata)
                    if resdata:
                        self.__sourcewg.updateMetaData(**resdata)
            except Exception as e:
                print(str(e))
        elif str(name).strip():
            if self.__imagename is None or str(self.__imagename) != str(name):
                self.__imagename, self.__metadata \
                    = name, metadata
                if not isinstance(rawimage, basestring):
                    self.__rawimage = rawimage
        self.__updateframeview()
        self._plot()
        QtCore.QCoreApplication.processEvents()
        self.__dataFetcher.ready()

    def __updateframeview(self, status=False):
        if status:
            if self.__frame is not None:
                self.__ui.frameSpinBox.setValue(self.__frame)
            self.__ui.frameSpinBox.show()
        else:
            self.__fieldpath = None
            self.__ui.frameSpinBox.hide()

    def __prepareImage(self):
        """applies: make image gray, substracke the background image and
           apply the mask
        """
        if self.__rawimage is None:
            return

        if len(self.__rawimage.shape) == 3:
            self.__levelswg.setNumberOfChannels(self.__rawimage.shape[0])
            if not self.__levelswg.colorChannel():
                self.__rawgreyimage = np.sum(self.__rawimage, 0)
            else:
                try:
                    if len(self.__rawimage) >= self.__levelswg.colorChannel():
                        self.__rawgreyimage = self.__rawimage[
                            self.__levelswg.colorChannel() - 1]
                    else:
                        self.__rawgreyimage = np.mean(self.__rawimage, 0)
                except Exception:
                    import traceback
                    value = traceback.format_exc()
                    text = messageBox.MessageBox.getText(
                        "lavue: color channel %s does not exist."
                        " Reset to grey scale"
                        % self.__levelswg.colorChannel())
                    messageBox.MessageBox.warning(
                        self,
                        "lavue: color channel %s does not exist. "
                        " Reset to grey scale"
                        % self.__levelswg.colorChannel(),
                        text, str(value))
                    self.__levelswg.setChannel(0)
                    self.__rawgreyimage = np.sum(self.__rawimage, 0)
        elif len(self.__rawimage.shape) == 2:
            if self.__applymask:
                self.__rawgreyimage = np.array(self.__rawimage)
            else:
                self.__rawgreyimage = self.__rawimage
            self.__levelswg.setNumberOfChannels(0)

        elif len(self.__rawimage.shape) == 1:
            self.__rawgreyimage = np.array(
                self.__rawimage).reshape((self.__rawimage.shape[0], 1))
            self.__levelswg.setNumberOfChannels(0)

        self.__displayimage = self.__rawgreyimage

        if self.__dobkgsubtraction and self.__backgroundimage is not None:
            # simple subtraction
            try:
                self.__displayimage = \
                    self.__rawgreyimage - self.__backgroundimage
            except Exception:
                self._checkBkgSubtraction(False)
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

        if self.__settings.showmask and self.__applymask and \
           self.__maskindices is not None:
            # set all masked (non-zero values) to zero by index
            try:
                self.__displayimage = np.array(self.__displayimage)
                self.__displayimage[self.__maskindices] = 0
            except IndexError:
                self.__maskwg.noImage()
                self.__applymask = False
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
           self.__maskvalue is not None:
            try:
                self.__displayimage = np.array(self.__displayimage)
                self.__displayimage[self.__displayimage > self.__maskvalue] = 0
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

    def __transform(self):
        """ does the image transformation on the given numpy array.

        :returns: crdtranspose, crdleftrightflip, crdupdownflip flags
        :rtype: (:obj:`bool`, :obj:`bool`, :obj:`bool`)
        """
        crdupdownflip = False
        crdleftrightflip = False
        crdtranspose = False
        if self.__trafoname is "none":
            pass
        elif self.__trafoname == "flip (up-down)":
            if self.__settings.keepcoords:
                crdupdownflip = True
            elif self.__displayimage is not None:
                    self.__displayimage = np.fliplr(self.__displayimage)
        elif self.__trafoname == "flip (left-right)":
            if self.__settings.keepcoords:
                crdleftrightflip = True
            elif self.__displayimage is not None:
                    self.__displayimage = np.flipud(self.__displayimage)
        elif self.__trafoname == "transpose":
            if self.__displayimage is not None:
                self.__displayimage = np.transpose(self.__displayimage)
            if self.__settings.keepcoords:
                crdtranspose = True
        elif self.__trafoname == "rot90 (clockwise)":
            if self.__settings.keepcoords:
                crdtranspose = True
                crdupdownflip = True
                if self.__displayimage is not None:
                    self.__displayimage = np.transpose(self.__displayimage)
            elif self.__displayimage is not None:
                self.__displayimage = np.transpose(
                    np.flipud(self.__displayimage))
        elif self.__trafoname == "rot180":
            if self.__settings.keepcoords:
                crdupdownflip = True
                crdleftrightflip = True
            elif self.__displayimage is not None:
                self.__displayimage = np.flipud(
                    np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot270 (clockwise)":
            if self.__settings.keepcoords:
                crdtranspose = True
                crdleftrightflip = True
                if self.__displayimage is not None:
                    self.__displayimage = np.transpose(self.__displayimage)
            elif self.__displayimage is not None:
                self.__displayimage = np.transpose(
                    np.fliplr(self.__displayimage))
        elif self.__trafoname == "rot180 + transpose":
            if self.__settings.keepcoords:
                crdtranspose = True
                crdupdownflip = True
                crdleftrightflip = True
                if self.__displayimage is not None:
                    self.__displayimage = np.transpose(self.__displayimage)
            elif self.__displayimage is not None:
                self.__displayimage = np.transpose(
                    np.fliplr(np.flipud(self.__displayimage)))
        return crdtranspose, crdleftrightflip, crdupdownflip

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
            self.__scaledimage = self.__displayimage.astype("float")
        else:
            self.__scaledimage = self.__displayimage

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
        if self.__settings.statswoscaling and self.__displayimage is not None:
            maxval = np.amax(self.__displayimage) if flag[0] else 0.0
            meanval = np.mean(self.__displayimage) if flag[1] else 0.0
            varval = np.var(self.__displayimage) if flag[2] else 0.0
            maxsval = np.amax(self.__scaledimage) if flag[5] else 0.0
        elif (not self.__settings.statswoscaling
              and self.__scaledimage is not None):
            maxval = np.amax(self.__scaledimage) if flag[0] or flag[5] else 0.0
            meanval = np.mean(self.__scaledimage) if flag[1] else 0.0
            varval = np.var(self.__scaledimage) if flag[2] else 0.0
            maxsval = maxval
        else:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        maxrawval = np.amax(self.__rawgreyimage) if flag[4] else 0.0
        minval = np.amin(self.__scaledimage) if flag[3] else 0.0
        return (maxval, meanval, varval, minval, maxrawval,  maxsval)

    @QtCore.pyqtSlot(str)
    def _checkHighMasking(self, value):
        """ reads the mask image, select non-zero elements and store the indices
        """
        try:
            self.__maskvalue = float(value)
        except Exception:
            self.__maskvalue = None
        self._plot()

    @QtCore.pyqtSlot(int)
    def _checkMasking(self, state):
        """ replots the image with mask if mask exists
        """
        self.__applymask = state
        if self.__applymask and self.__maskimage is None:
            self.__maskwg.noImage()
        self._plot()

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
                self.__maskindices = (self.__maskimage == 0)
            else:
                self.__maskindices = (self.__maskimage != 0)
        else:
            self.__maskimage = None
        # self.__maskindices = np.nonzero(self.__maskimage != 0)

    def __remasking(self):
        """ recalculates the mask
        """
        if self.__maskimage is not None:
            if self.__settings.zeromask:
                self.__maskindices = (self.__maskimage == 0)
            else:
                self.__maskindices = (self.__maskimage != 0)

    @QtCore.pyqtSlot(int)
    def _checkBkgSubtraction(self, state):
        """ replots the image with subtranction if background image exists
        """
        self.__dobkgsubtraction = state
        if self.__dobkgsubtraction and self.__backgroundimage is None:
            self.__bkgsubwg.setDisplayedName("")
        else:
            self.__bkgsubwg.checkBkgSubtraction(state)
        self.__imagewg.setDoBkgSubtraction(state)
        self._plot()

    @QtCore.pyqtSlot(str)
    def _prepareBkgSubtraction(self, imagename):
        """ reads the background image
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

    @QtCore.pyqtSlot()
    def _setCurrentImageAsBkg(self):
        """ sets the chrrent image as the background image
        """
        if self.__rawgreyimage is not None:
            self.__backgroundimage = self.__rawgreyimage
            self.__bkgsubwg.setDisplayedName(str(self.__imagename))
        else:
            self.__bkgsubwg.setDisplayedName("")

    @QtCore.pyqtSlot(str)
    def _assessTransformation(self, trafoname):
        """ assesses the transformation and replot it
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
        self._plot()
