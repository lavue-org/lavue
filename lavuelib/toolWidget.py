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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" image widget """


from .qtuic import uic

import os
import re
import math
import sys
import numpy as np
import scipy.interpolate
import pyqtgraph as _pg
import logging
import json
from pyqtgraph import QtCore, QtGui
from enum import Enum

from . import geometryDialog
from . import rangeDialog
from . import diffRangeDialog
from . import takeMotorsDialog
from . import intervalsDialog
from . import motorWatchThread
from . import edDictDialog

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False

try:
    import pyFAI
    #: (:obj:`bool`) pyFAI imported
    PYFAI = True
except ImportError:
    #: (:obj:`bool`) pyFAI imported
    PYFAI = False

if sys.version_info > (3,):
    long = int


_intensityformclass, _intensitybaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "IntensityToolWidget.ui"))

_roiformclass, _roibaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ROIToolWidget.ui"))

_cutformclass, _cutbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LineCutToolWidget.ui"))

_angleqformclass, _angleqbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "AngleQToolWidget.ui"))

_diffractogramformclass, _diffractogrambaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "DiffractogramToolWidget.ui"))

_maximaformclass, _maximabaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MaximaToolWidget.ui"))

_motorsformclass, _motorsbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MotorsToolWidget.ui"))

_meshformclass, _meshbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MeshToolWidget.ui"))

_onedformclass, _onedbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "OneDToolWidget.ui"))

_projectionformclass, _projectionbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ProjectionToolWidget.ui"))

_parametersformclass, _parametersbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ParametersToolWidget.ui"))

_qroiprojformclass, _qroiprojbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "QROIProjToolWidget.ui"))

__all__ = [
    'IntensityToolWidget',
    'ROIToolWidget',
    'LineCutToolWidget',
    'AngleQToolWidget',
    'MotorsToolWidget',
    'MeshToolWidget',
    'OneDToolWidget',
    'ProjectionToolWidget',
    'MaximaToolWidget',
    'ParametersToolWidget',
    'DiffractogramToolWidget',
    'QROIProjToolWidget',
    'twproperties',
]

logger = logging.getLogger("lavue")


class Converters(object):

    """ set of converters
    """

    @classmethod
    def toBool(cls, value):
        """ converts to bool

        :param value: variable to convert
        :type value: any
        :returns: result in bool type
        :rtype: :obj:`bool`
        """
        if type(value).__name__ == 'str' or type(value).__name__ == 'unicode':
            lvalue = value.strip().lower()
            if lvalue == 'false' or lvalue == '0':
                return False
            else:
                return True
        elif value:
            return True
        return False


class ToolParameters(object):
    """ tool parameters
    """
    def __init__(self):
        """ constructor

        """
        #: (:obj:`bool`) lines enabled
        # self.lines = False
        #: (:obj:`bool`) rois enabled
        self.rois = False
        #: (:obj:`bool`) cuts enabled
        self.cuts = False
        #: (:obj:`bool`) mesh enabled
        self.mesh = False
        #: (:obj:`bool`) axes scale enabled
        self.scale = False
        #: (:obj:`bool`) polar axes scale enabled
        self.polarscale = False
        #: (:obj:`bool`) bottom 1d plot enabled
        self.bottomplot = False
        #: (:obj:`bool`) right 1d plot enabled
        self.rightplot = False
        #: (:obj:`bool`) cross hair locker enabled
        self.crosshairlocker = False
        #: (:obj:`bool`) center lines enabled
        self.centerlines = False
        #: (:obj:`bool`) position lines enabled
        self.marklines = False
        #: (:obj:`str`) infolineedit text
        self.infolineedit = None
        #: (:obj:`str`) infolabel text
        self.infolabel = None
        #: (:obj:`str`) infolabel text
        self.infotips = None
        #: (:obj:`str`) show maxima
        self.maxima = False
        #: (:obj:`bool`) vertical and horizontal bounds
        self.vhbounds = False
        #: (:obj:`bool`) angle range enabled
        self.regions = False


class ToolBaseWidget(QtGui.QWidget):
    """ tool widget
    """

    #: (:obj:`str`) tool name
    name = "None"
    #: (:obj:`str`) tool name alias
    alias = "none"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QWidget.__init__(self, parent)
        #: (:class:`pyqtgraph.QtCore.QObject`) mainwidget
        self._mainwidget = parent
        #: (:class:`Ui_ToolBaseWidget')
        #:     ui_toolwidget object from qtdesigner
        self._ui = None
        #: (:class:`ToolParameters`) tool parameters
        self.parameters = ToolParameters()

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = []

    def activate(self):
        """ activates tool widget
        """

    def deactivate(self):
        """ deactivates tool widget
        """

    def afterplot(self):
        """ command after plot
        """

    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """


class IntensityToolWidget(ToolBaseWidget):
    """ intensity tool widget
    """

    #: (:obj:`str`) tool name
    name = "Intensity"
    #: (:obj:`str`) tool name alias
    alias = "intensity"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`Ui_IntensityToolWidget')
        #:        ui_toolwidget object from qtdesigner
        self.__ui = _intensityformclass()
        self.__ui.setupUi(self)

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        self.parameters.scale = True
        self.parameters.crosshairlocker = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"
        self.__ui.crosshairCheckBox.setChecked(self.__settings.crosshairlocker)
        self._updateCrossHairLocker(self.__settings.crosshairlocker)

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.axesPushButton.clicked, self._mainwidget.setTicks],
            [self.__ui.crosshairCheckBox.stateChanged,
             self._updateCrossHairLocker],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    @QtCore.pyqtSlot(int)
    def _updateCrossHairLocker(self, status):
        self.parameters.crosshairlocker = bool(status)
        self._mainwidget.updateinfowidgets(self.parameters)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        txdata, tydata = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        if txdata is not None:
            message = "x = %f%s, y = %f%s, %s = %.2f" % (
                txdata,
                (" %s" % xunits) if xunits else "",
                tydata,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity
            )
        else:
            message = "x = %i%s, y = %i%s, %s = %.2f" % (
                x,
                (" %s" % xunits) if xunits else "",
                y,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity)
        self._mainwidget.setDisplayedText(message)


class RGBIntensityToolWidget(IntensityToolWidget):
    """ intensity tool widget
    """

    #: (:obj:`str`) tool name
    name = "RGB Intensity"
    #: (:obj:`str`) tool name alias
    alias = "rgbintensity"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        IntensityToolWidget.__init__(self, parent)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        ilabel = self._mainwidget.scalingLabel()
        txdata, tydata = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        if isinstance(intensity, np.ndarray) and \
           intensity.size <= 3:
            itn = [0 if (isinstance(it, float) and np.isnan(it))
                   else it for it in intensity]
            if len(itn) >= 3:
                if txdata is not None:
                    message = "x = %f%s, y = %f%s, " \
                              "%s = (%.2f, %.2f, %.2f)" % (
                                  txdata,
                                  (" %s" % xunits) if xunits else "",
                                  tydata,
                                  (" %s" % yunits) if yunits else "",
                                  ilabel,
                                  itn[0], itn[1], itn[2])
                else:
                    message = "x = %i%s, y = %i%s, " \
                              "%s = (%.2f, %.2f, %.2f)" % (
                                  x,
                                  (" %s" % xunits) if xunits else "",
                                  y,
                                  (" %s" % yunits) if yunits else "",
                                  ilabel,
                                  itn[0], itn[1], itn[2])
                self._mainwidget.setDisplayedText(message)


class MotorsToolWidget(ToolBaseWidget):
    """ motors tool widget
    """

    #: (:obj:`str`) tool name
    name = "MoveMotors"
    #: (:obj:`str`) tool name alias
    alias = "movemotors"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYTANGO",)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`str`) x-motor name
        self.__xmotorname = ""
        #: (:obj:`str`) y-motor name
        self.__ymotorname = ""
        #: (:obj:`str`) x final position
        self.__xfinal = None
        #: (:obj:`str`) y final position
        self.__yfinal = None
        #: (:obj:`str`) state of x-motor
        self.__statex = None
        #: (:obj:`str`) state of y-motor
        self.__statey = None
        #: (:class:`PyTango.DeviceProxy`) x-motor device
        self.__xmotordevice = None
        #: (:class:`PyTango.DeviceProxy`) y-motor device
        self.__ymotordevice = None
        #: (:class:`lavuelib.motorWatchThread.motorWatchThread`) motor watcher
        self.__motorWatcher = None
        #: (:obj:`bool`) is moving
        self.__moving = False

        #: (:class:`Ui_MotorsToolWidget')
        #:        ui_toolwidget object from qtdesigner
        self.__ui = _motorsformclass()
        self.__ui.setupUi(self)
        self.__ui.xcurLineEdit.hide()
        self.__ui.ycurLineEdit.hide()

        #: (:obj:`bool`) position lines enabled
        self.parameters.scale = True
        self.parameters.marklines = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.axesPushButton.clicked, self._mainwidget.setTicks],
            [self.__ui.takePushButton.clicked, self._setMotors],
            [self.__ui.movePushButton.clicked, self._moveStopMotors],
            [self._mainwidget.mouseImageDoubleClicked, self._updateFinal],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self.__ui.xLineEdit.textEdited, self._getFinal],
            [self.__ui.yLineEdit.textEdited, self._getFinal],
        ]

    def activate(self):
        """ activates tool widget
        """
        if self.__xfinal is not None and self.__yfinal is not None:
            self._mainwidget.updatePositionMark(
                self.__xfinal, self.__yfinal)

    @QtCore.pyqtSlot(float, float)
    def _updateFinal(self, xdata, ydata):
        """ updates the final motors position

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        if not self.__moving:
            x, y = self._mainwidget.scaledxy(float(xdata), float(ydata))
            if x is not None:
                self.__xfinal = x
                self.__yfinal = y
            else:
                self.__xfinal = float(xdata)
                self.__yfinal = float(ydata)

            self.__ui.xLineEdit.setText(str(self.__xfinal))
            self.__ui.yLineEdit.setText(str(self.__yfinal))
            self.__ui.movePushButton.setToolTip(
                "Move to x- and y-motors to (%s, %s)"
                % (self.__xfinal, self.__yfinal))

    @QtCore.pyqtSlot()
    def _moveStopMotors(self):
        """ move or stop motors depending on movePushButton
        """
        if str(self.__ui.movePushButton.text()) == "Move":
            self.__moveMotors()
        else:
            self.__stopMotors()

    @QtCore.pyqtSlot()
    def _finished(self):
        """ stop motors
        """
        self.__stopMotors()

    def __stopMotors(self):
        """ move motors

        :returns: motors stopped
        :rtype: :obj:`bool`
        """
        try:
            if hasattr(self.__xmotordevice, "stop"):
                self.__xmotordevice.stop()
            elif hasattr(self.__xmotordevice, "StopMove"):
                self.__xmotordevice.StopMove()
            else:
                return False
            if hasattr(self.__ymotordevice, "stop"):
                self.__ymotordevice.stop()
            elif hasattr(self.__ymotordevice, "StopMove"):
                self.__ymotordevice.StopMove()
            else:
                return False
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
        if self.__motorWatcher:
            self.__motorWatcher.motorStatusSignal.disconnect(self._showMotors)
            self.__motorWatcher.watchingFinished.disconnect(self._finished)
            self.__motorWatcher.stop()
            self.__motorWatcher.wait()
            self.__motorWatcher = None
        self._mainwidget.setDoubleClickLock(False)
        self.__ui.movePushButton.setText("Move")
        self.__ui.xcurLineEdit.hide()
        self.__ui.ycurLineEdit.hide()
        self.__ui.takePushButton.show()
        self.__ui.axesPushButton.show()
        self.__moving = False
        self.__ui.xLineEdit.setReadOnly(False)
        self.__ui.yLineEdit.setReadOnly(False)
        self.__ui.xcurLineEdit.setStyleSheet(
            "color: black; background-color: #90EE90;")
        self.__ui.ycurLineEdit.setStyleSheet(
            "color: black; background-color: #90EE90;")
        return True

    @QtCore.pyqtSlot()
    def _getFinal(self):
        """ update final positions
        """
        try:
            self.__xfinal = float(self.__ui.xLineEdit.text())
        except Exception:
            self.__ui.xLineEdit.setFocus()
            return False
        try:
            self.__yfinal = float(self.__ui.yLineEdit.text())
        except Exception:
            self.__ui.yLineEdit.setFocus()
            return False
        self._mainwidget.updatePositionMark(
            self.__xfinal, self.__yfinal)

    def __moveMotors(self):
        """ move motors

        :returns: motors started
        :rtype: :obj:`bool`
        """

        self._getFinal()

        if self.__xmotordevice is None or self.__ymotordevice is None:
            if not self._setMotors():
                return False
        if str(self.__xmotordevice.state) != "ON" \
           and str(self.__ymotordevice.state) != "ON":
            try:
                self.__xmotordevice.position = self.__xfinal
                self.__ymotordevice.position = self.__yfinal
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))
                return False
        else:
            return False
        # print("%s %s" % (self.__xfinal, self.__yfinal))
        self.__motorWatcher = motorWatchThread.MotorWatchThread(
            self.__xmotordevice, self.__ymotordevice)
        self.__motorWatcher.motorStatusSignal.connect(self._showMotors)
        self.__motorWatcher.watchingFinished.connect(self._finished)
        self.__motorWatcher.start()
        self._mainwidget.setDoubleClickLock(True)
        self.__ui.movePushButton.setText("Stop")
        self.__ui.xcurLineEdit.show()
        self.__ui.ycurLineEdit.show()
        self.__ui.takePushButton.hide()
        self.__ui.axesPushButton.hide()
        self.__ui.xLineEdit.setReadOnly(True)
        self.__ui.yLineEdit.setReadOnly(True)
        self.__moving = True
        self.__statex = None
        self.__statey = None
        return True

    @QtCore.pyqtSlot(float, str, float, str)
    def _showMotors(self, positionx, statex, positiony, statey):
        """ shows motors positions and states
        """
        # print("%s %s %s %s" % (positionx, statex, positiony, statey))
        self.__ui.xcurLineEdit.setText(str(positionx))
        self.__ui.ycurLineEdit.setText(str(positiony))
        if self.__statex != statex:
            self.__statex = statex
            if statex == "MOVING":
                self.__ui.xcurLineEdit.setStyleSheet(
                    "color: black; background-color: #ADD8E6;")
            else:
                self.__ui.xcurLineEdit.setStyleSheet(
                    "color: black; background-color: #90EE90;")
        if self.__statey != statey:
            self.__statey = statey
            if statey == "MOVING":
                self.__ui.ycurLineEdit.setStyleSheet(
                    "color: black; background-color: #ADD8E6;")
            else:
                self.__ui.ycurLineEdit.setStyleSheet(
                    "color: black; background-color: #90EE90;")

    @QtCore.pyqtSlot()
    def _setMotors(self):
        """ launches motors widget

        :returns: apply status
        :rtype: :obj:`bool`
        """

        motors = self._mainwidget.getElementNames("MotorList")
        cnfdlg = takeMotorsDialog.TakeMotorsDialog()
        if motors is not None:
            cnfdlg.motortips = motors
        cnfdlg.xmotorname = self.__xmotorname
        cnfdlg.ymotorname = self.__ymotorname
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__xmotorname = cnfdlg.xmotorname
            self.__ymotorname = cnfdlg.ymotorname
            self.__xmotordevice = cnfdlg.xmotordevice
            self.__ymotordevice = cnfdlg.ymotordevice
            self.__ui.takePushButton.setToolTip(
                "x-motor: %s\ny-motor: %s" % (
                    self.__xmotorname, self.__ymotorname))
            self.__ui.xLabel.setToolTip(
                "x-motor position (%s)" % self.__xmotorname)
            self.__ui.xLineEdit.setToolTip(
                "final x-motor position (%s)" % self.__xmotorname)
            self.__ui.xcurLineEdit.setToolTip(
                "current x-motor position (%s)" % self.__xmotorname)
            self.__ui.yLabel.setToolTip(
                "y-motor position (%s)" % self.__ymotorname)
            self.__ui.yLineEdit.setToolTip(
                "final y-motor position (%s)" % self.__ymotorname)
            self.__ui.ycurLineEdit.setToolTip(
                "current y-motor position (%s)" % self.__ymotorname)
            return True
        return False

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        txdata, tydata = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        if txdata is not None:
            message = "x = %f%s, y = %f%s, %s = %.2f" % (
                txdata,
                (" %s" % xunits) if xunits else "",
                tydata,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity
            )
        else:
            message = "x = %f%s, y = %f%s, %s = %.2f" % (
                x,
                (" %s" % xunits) if xunits else "",
                y,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity)
        self._mainwidget.setDisplayedText(message)


class WD(Enum):
    """ Enum with Parameter Widget positions
    """
    label = 0
    read = 1
    write = 2
    button = 3


class ParametersToolWidget(ToolBaseWidget):
    """ motors tool widget
    """
    #: (:obj:`str`) tool name
    name = "Parameters"
    #: (:obj:`str`) tool name alias
    alias = "parameters"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYTANGO",)

    #: (:obj:`dict` <:obj:`str` , :obj:`type` or :obj:`types.MethodType` >) \
    #:      map of type : converting function
    convert = {"float16": float, "float32": float, "float64": float,
               "float": float, "int64": long, "int32": int,
               "int16": int, "int8": int, "int": int, "uint64": long,
               "uint32": long, "uint16": int,
               "uint8": int, "uint": int, "string": str, "str": str,
               "bool": Converters.toBool}

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        # #: (:obj:`list` <str, str, str>)
        #        detector parameters (label, devicename, type)
        self.__detparams = []
        #: (:obj:`list` <:class:`PyTango.DeviceProxy`>)  attribute proxies
        self.__aproxies = []
        #: (:obj:`list` <:list:`any`>)  attribute values
        self.__avalues = []
        #: (:class:`lavuelib.motorWatchThread.attributeWatchThread`)
        #               attribute watcher
        self.__attrWatcher = None
        #: (:obj:`bool`) is watching
        self.__watching = False
        #: (:obj:`list` <:obj:`list` <:class:`pyqtgraph.QtCore.QObject`> >)
        # widgets
        self.__widgets = []

        #: (:class:`Ui_ParametersToolWidget')
        #:        ui_toolwidget object from qtdesigner
        self.__ui = _parametersformclass()
        self.__ui.setupUi(self)

        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.setupPushButton.clicked, self._setParameters],
            [self._mainwidget.mouseImagePositionChanged, self._message],
         ]

        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) apply mapper
        self.__applymapper = QtCore.QSignalMapper(self)
        self.__applymapper.mapped.connect(self._applypars)

    def _applypars(self, wid):
        """ apply the parameter with the given widget id

        :param wid: widget id
        :type wid: :obj:`int`
        """
        txt = str(self.__widgets[wid][WD.write.value].text() or "")
        tp = self.__detparams[wid][2]
        frm = self.__detparams[wid][4]
        ap = self.__aproxies[wid]
        if frm == "SPECTRUM":
            try:
                vl = json.loads(txt)
            except Exception as e:
                try:
                    vl = txt.split()
                    if tp and tp in self.convert.keys():
                        vl = [self.convert[tp](v) for v in vl]
                except Exception as e2:
                    logger.warning(str(e))
                    logger.warning(str(e2))
                    vl = txt
        elif frm == "IMAGE":
            try:
                vl = json.loads(txt)
            except Exception as e:
                logger.warning(str(e))
                vl = txt
        else:
            try:
                if tp and tp in self.convert.keys():
                    vl = self.convert[tp](txt)
                else:
                    vl = txt
            except Exception as e:
                logger.warning(str(e))
                vl = txt
        try:
            ap.write(vl)
        except Exception as e:
            logger.warning(str(e))

    def activate(self):
        """ activates tool widget
        """
        record = json.loads(str(self.__settings.tangodetattrs or "{}").strip())
        if not isinstance(record, dict):
            record = {}
        self.__aproxies = []
        self.__detparams = []
        self.__avalues = []
        for lb in sorted(record.keys()):
            try:
                dv = record[lb]
                ap = PyTango.AttributeProxy(dv)
                unit = ""
                frm = ""
                try:
                    cap = ap.get_config()
                    unit = cap.unit or ""
                    vl = ap.read().value
                    tp = type(vl).__name__
                    if tp == "ndarray":
                        tp = str(vl.dtype)
                    frm = str(cap.data_format)
                except Exception as e:
                    logger.warning(str(e))
                    vl = None
                    tp = ""
            except Exception as e:
                logger.warning(str(e))
                dv = None
            if dv is not None:
                self.__aproxies.append(ap)
                self.__detparams.append([lb, dv, tp, unit, frm])
                self.__avalues.append(vl)
        self.__updateWidgets()
        self.__attrWatcher = motorWatchThread.AttributeWatchThread(
            self.__aproxies, self.__settings.toolpollinginterval)
        self.__attrWatcher.attrValuesSignal.connect(self._showValues)
        self.__attrWatcher.start()

    def __updateWidgets(self):
        """ add widgets
        """
        layout = self.__ui.parGridLayout

        while len(self.__detparams) > len(self.__widgets):
            self.__widgets.append(
                [
                    QtGui.QLabel(parent=self._mainwidget),
                    QtGui.QLineEdit(parent=self._mainwidget),
                    QtGui.QLineEdit(parent=self._mainwidget),
                    QtGui.QPushButton("Apply", parent=self._mainwidget),
                ]
            )
            last = len(self.__widgets)
            self.__widgets[-1][WD.read.value].setReadOnly(True)
            self.__widgets[-1][WD.read.value].setStyleSheet(
                "color: black; background-color: #90EE90;")
            self.__widgets[-1][WD.read.value].setAlignment(
                QtCore.Qt.AlignCenter)
            self.__widgets[-1][WD.write.value].setAlignment(
                QtCore.Qt.AlignRight)
            for i, w in enumerate(self.__widgets[-1]):
                layout.addWidget(w, last, i)
            self.__widgets[-1][WD.button.value].clicked.connect(
                self.__applymapper.map)
            self.__applymapper.setMapping(
                self.__widgets[-1][WD.button.value], last - 1)
            # self.__widgets[-1][WD.read.value].setMaximumWidth(200)
        while len(self.__detparams) < len(self.__widgets):
            wds = self.__widgets.pop()
            self.__applymapper.removeMappings(wds[WD.button.value])
            for w in wds:
                w.hide()
                layout.removeWidget(w)
        for i, pars in enumerate(self.__detparams):
            self.__widgets[i][WD.label.value].setText("%s:" % pars[0])
            self.__widgets[i][WD.label.value].setToolTip("%s" % pars[1])
            self.__widgets[i][WD.write.value].setText("")
            self.__widgets[i][WD.write.value].setToolTip("%s" % pars[1])
            self.__widgets[i][WD.write.button.value].setToolTip(
                "Write the new value of %s" % pars[0])
            if self.__avalues[i] is None:
                vl = ""
            else:
                vl = str(self.__avalues[i])
            if pars[3]:
                vl = "%s %s" % (vl, pars[3])
            self.__widgets[i][WD.read.value].setToolTip(vl)
            self.__widgets[i][WD.read.value].setText(vl)

    def deactivate(self):
        """ activates tool widget
        """
        if self.__attrWatcher:
            self.__attrWatcher.attrValuesSignal.disconnect(self._showValues)
            # self.__attrWatcher.watchingFinished.disconnect(self._finished)
            self.__attrWatcher.stop()
            self.__attrWatcher.wait()
            self.__attrWatcher = None
        self.__aproxies = []
        self.__detparams = []
        self.__avalues = []

    @QtCore.pyqtSlot(str)
    def _showValues(self, values):
        """ show values
        """
        vls = json.loads(values)
        # print(vls)
        # print([type(vl).__name__ for vl in vls])
        for i, pars in enumerate(self.__widgets):
            if i < len(vls):
                vl = str(vls[i])
                if self.__detparams[i][3]:
                    vl = "%s %s" % (vl, self.__detparams[i][3])
                self.__widgets[i][WD.read.value].setText(vl)
                self.__widgets[i][WD.read.value].setToolTip(vl)

    @QtCore.pyqtSlot()
    def _setParameters(self):
        """ launches parameters widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        record = json.loads(str(self.__settings.tangodetattrs or "{}").strip())
        if not isinstance(record, dict):
            record = {}
        dform = edDictDialog.EdDictDialog(self)
        dform.record = record
        dform.title = "Tango Detector Attributes"
        dform.createGUI()
        dform.exec_()
        if dform.dirty:
            for key in list(record.keys()):
                if not str(key).strip():
                    record.pop(key)
            if self.__settings.tangodetattrs != str(json.dumps(record)):
                self.__settings.tangodetattrs = str(json.dumps(record))
                self.__updateParams()

    def __updateParams(self):
        """ update parameters
        """
        self.deactivate()
        self.activate()

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        txdata, tydata = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        if txdata is not None:
            message = "x = %f%s, y = %f%s, %s = %.2f" % (
                txdata,
                (" %s" % xunits) if xunits else "",
                tydata,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity
            )
        else:
            message = "x = %f%s, y = %f%s, %s = %.2f" % (
                x,
                (" %s" % xunits) if xunits else "",
                y,
                (" %s" % yunits) if yunits else "",
                ilabel,
                intensity)
        self._mainwidget.setDisplayedText(message)


class MeshToolWidget(ToolBaseWidget):
    """ mesh tool widget
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) roi info Changed signal
    roiInfoChanged = QtCore.pyqtSignal(str)

    #: (:obj:`str`) tool name
    name = "MeshScan"
    #: (:obj:`str`) tool name alias
    alias = "meshscan"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYTANGO",)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`str`) x-motor name
        self.__xmotorname = ""
        #: (:obj:`str`) y-motor name
        self.__ymotorname = ""
        #: (:obj:`str`) state of x-motor
        self.__statex = None
        #: (:obj:`str`) state of y-motor
        self.__statey = None
        #: (:class:`PyTango.DeviceProxy`) x-motor device
        self.__xmotordevice = None
        #: (:class:`PyTango.DeviceProxy`) y-motor device
        self.__ymotordevice = None
        #: (:class:`PyTango.DeviceProxy`) door server
        self.__door = None
        #: (:class:`lavuelib.motorWatchThread.motorWatchThread`) motor watcher
        self.__motorWatcher = None
        #: (:obj:`bool`) is moving
        self.__moving = False

        #: (:obj:`int`) number of x intervals
        self.__xintervals = 2
        #: (:obj:`int`) number of y intervals
        self.__yintervals = 3
        #: (:obj:`float`) integration time in seconds
        self.__itime = 0.1

        #: (:class:`Ui_MeshToolWidget')
        #:        ui_toolwidget object from qtdesigner
        self.__ui = _meshformclass()
        self.__ui.setupUi(self)
        self.__showLabels()

        self.parameters.scale = True
        self.parameters.rois = False
        self.parameters.mesh = True
        self.parameters.infolineedit = ""
        self.parameters.infolabel = "[x1, y1, x2, y2]: "
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.axesPushButton.clicked, self._mainwidget.setTicks],
            [self.__ui.takePushButton.clicked, self._setMotors],
            [self.__ui.intervalsPushButton.clicked, self._setIntervals],
            [self.__ui.scanPushButton.clicked, self._scanStopMotors],
            [self.roiInfoChanged, self._mainwidget.updateDisplayedText],
            [self._mainwidget.roiValueChanged, self.updateROIDisplayText],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def activate(self):
        """ activates tool widget
        """
        self._mainwidget.changeMeshRegion()
        # self._mainwidget.updateROIs(1)

    def deactivate(self):
        """ deactivates tool widget
        """
        self._mainwidget.meshCoordsChanged.emit()

    @QtCore.pyqtSlot(str, int, str)
    def updateROIDisplayText(self, text, currentroi, roiVal):
        """ updates ROI display text

        :param text: standard display text
        :type text: :obj:`str`
        :param currentroi: current roi label
        :type currentroi: :obj:`str`
        :param text: roi sum value
        :type text: :obj:`str`
        """

        if "/" in roiVal:
            sroiv = " / ".split(roiVal)
            roiVal = sroiv[currentroi] if len(sroiv) > currentroi else ""
        roilabel = "roi [%s]" % (currentroi + 1)

        self.roiInfoChanged.emit("%s, %s = %s" % (text, roilabel, roiVal))

    @QtCore.pyqtSlot()
    def _scanStopMotors(self):
        """ starts or stops scan
        """
        if str(self.__ui.scanPushButton.text()) == "Scan":
            self.__startScan()
        else:
            self.__stopScan()

    @QtCore.pyqtSlot()
    def _finished(self):
        """ stops mesh scan without stopping the macro
        """
        self.__stopScan(stopmacro=False)

    def __stopScan(self, stopmacro=True):
        """ stops mesh scan
        :param stopmacro: call stopmacro
        :type stopmacro: :obj:`bool`
        :returns: motors stopped
        :rtype: :obj:`bool`
        """

        if stopmacro:
            try:
                self.__door.StopMacro()
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))

        if self.__motorWatcher:
            self.__motorWatcher.motorStatusSignal.disconnect(self._showMotors)
            self.__motorWatcher.watchingFinished.disconnect(self._finished)
            self.__motorWatcher.stop()
            self.__motorWatcher.wait()
            self.__motorWatcher = None
        self.__showLabels()
        self.__moving = False
        self.__ui.xcurLineEdit.setStyleSheet(
            "color: black; background-color: #90EE90;")
        self.__ui.ycurLineEdit.setStyleSheet(
            "color: black; background-color: #90EE90;")
        self._mainwidget.showDoorError()
        return True

    def __showLabels(self):
        """ shows GUI labels
        """
        self.__ui.scanPushButton.setText("Scan")
        self.__ui.xcurLineEdit.hide()
        self.__ui.ycurLineEdit.hide()
        self.__ui.takePushButton.show()
        self.__ui.axesPushButton.show()
        self.__ui.intervalsPushButton.show()
        self.__ui.xLabel.setText("X: %s" % (self.__xintervals))
        self.__ui.yLabel.setText("Y: %s" % (self.__yintervals))
        self.__ui.timeLabel.setText("dT: %ss" % str(self.__itime))
        self.__ui.timeLabel.show()

    def __hideLabels(self):
        """ hides GUI labels
        """
        self.__ui.scanPushButton.setText("Stop")
        self.__ui.xcurLineEdit.show()
        self.__ui.ycurLineEdit.show()
        self.__ui.takePushButton.hide()
        self.__ui.axesPushButton.hide()
        self.__ui.intervalsPushButton.hide()
        self.__ui.xLabel.setText("X: %s" % (self.__xintervals))
        self.__ui.yLabel.setText("Y: %s" % (self.__yintervals))
        self.__ui.timeLabel.setText("dT: %ss" % str(self.__itime))
        self.__ui.timeLabel.show()

    def __startScan(self):
        """ start scan

        :returns: motors started
        :rtype: :obj:`bool`
        """
        coords = self._mainwidget.meshCoords()
        if 0 < len(coords):
            curcoords = coords[0]
        else:
            return False

        if self.__xmotordevice is None or self.__ymotordevice is None:
            if not self._setMotors():
                return False

        macrocommand = []
        macrocommand.append("mesh")
        macrocommand.append(str(self.__xmotorname))
        macrocommand.append(str(float(curcoords[0])))
        macrocommand.append(str(float(curcoords[2])))
        macrocommand.append(str(self.__xintervals))
        macrocommand.append(str(self.__ymotorname))
        macrocommand.append(str(float(curcoords[1])))
        macrocommand.append(str(float(curcoords[3])))
        macrocommand.append(str(self.__yintervals))
        macrocommand.append(str(self.__itime))
        macrocommand.append("True")
        self.__door = self._mainwidget.getDoor()
        if self.__door is None:
            logger.error(
                "MeshToolWidget.__startScan: Cannot access Door device")
            return False

        if not self._mainwidget.runMacro(macrocommand):
            logger.error(
                "MeshToolWidget.__startScan: Cannot in running %s"
                % macrocommand)
            return False

        self.__motorWatcher = motorWatchThread.MotorWatchThread(
            self.__xmotordevice, self.__ymotordevice, self.__door)
        self.__motorWatcher.motorStatusSignal.connect(self._showMotors)
        self.__motorWatcher.watchingFinished.connect(self._finished)
        self.__motorWatcher.start()
        self.__hideLabels()
        self.__moving = True
        self.__statex = None
        self.__statey = None
        return True

    @QtCore.pyqtSlot(float, str, float, str)
    def _showMotors(self, positionx, statex, positiony, statey):
        """ shows motors positions and states
        """
        # print("%s %s %s %s" % (positionx, statex, positiony, statey))
        self.__ui.xcurLineEdit.setText(str(positionx))
        self.__ui.ycurLineEdit.setText(str(positiony))
        if self.__statex != statex:
            self.__statex = statex
            if statex == "MOVING":
                self.__ui.xcurLineEdit.setStyleSheet(
                    "color: black; background-color: #ADD8E6;")
            else:
                self.__ui.xcurLineEdit.setStyleSheet(
                    "color: black; background-color: #90EE90;")
        if self.__statey != statey:
            self.__statey = statey
            if statey == "MOVING":
                self.__ui.ycurLineEdit.setStyleSheet(
                    "color: black; background-color: #ADD8E6;")
            else:
                self.__ui.ycurLineEdit.setStyleSheet(
                    "color: black; background-color: #90EE90;")

    @QtCore.pyqtSlot()
    def _setMotors(self):
        """ launches motors widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        motors = self._mainwidget.getElementNames("MotorList")
        cnfdlg = takeMotorsDialog.TakeMotorsDialog()
        if motors is not None:
            cnfdlg.motortips = motors
        cnfdlg.title = "Motor aliases"
        cnfdlg.xmotorname = self.__xmotorname
        cnfdlg.ymotorname = self.__ymotorname
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__xmotorname = cnfdlg.xmotorname
            self.__ymotorname = cnfdlg.ymotorname
            self.__xmotordevice = cnfdlg.xmotordevice
            self.__ymotordevice = cnfdlg.ymotordevice
            self.__ui.takePushButton.setToolTip(
                "x-motor: %s\ny-motor: %s" % (
                    self.__xmotorname, self.__ymotorname))
            self.__ui.xLabel.setToolTip(
                "x-motor interval number (%s)" % self.__xmotorname)
            self.__ui.xcurLineEdit.setToolTip(
                "current x-motor position (%s)" % self.__xmotorname)
            self.__ui.yLabel.setToolTip(
                "y-motor interval number (%s)" % self.__ymotorname)
            self.__ui.ycurLineEdit.setToolTip(
                "current y-motor position (%s)" % self.__ymotorname)
            self.__showLabels()
            return True
        return False

    @QtCore.pyqtSlot()
    def _setIntervals(self):
        """ launches motors widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = intervalsDialog.IntervalsDialog()
        cnfdlg.xintervals = self.__xintervals
        cnfdlg.yintervals = self.__yintervals
        cnfdlg.itime = self.__itime
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__xintervals = cnfdlg.xintervals
            self.__yintervals = cnfdlg.yintervals
            self.__itime = cnfdlg.itime
            self.__ui.intervalsPushButton.setToolTip(
                "x-intervals:%s\ny-intervals:%s\nintegration time:%s" % (
                    self.__xintervals, self.__yintervals, self.__itime))
            self.__showLabels()
            return True
        return False

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides mesh message
        """
        message = ""
        coords = self._mainwidget.meshCoords()
        if 0 < len(coords):
            message = "%s" % coords[0]
        self._mainwidget.setDisplayedText(message)


class ROIToolWidget(ToolBaseWidget):
    """ roi tool widget
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply ROI pressed signal
    applyROIPressed = QtCore.pyqtSignal(str, int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) fetch ROI pressed signal
    fetchROIPressed = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) roi info Changed signal
    roiInfoChanged = QtCore.pyqtSignal(str)

    #: (:obj:`str`) tool name
    name = "ROI"
    #: (:obj:`str`) tool name alias
    alias = "roi"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _roiformclass()
        self.__ui.setupUi(self)

        #: (:obj:`list`< :obj:`str`>) sardana aliases
        self.__aliases = []
        #: (:obj:`int`) ROI label length
        self.__textlength = 0

        self.parameters.rois = True
        self.parameters.infolineedit = ""
        self.parameters.infolabel = "[x1, y1, x2, y2], sum: "
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        self._updateApplyButton()
        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.applyROIPushButton.clicked, self._emitApplyROIPressed],
            [self.__ui.fetchROIPushButton.clicked, self._emitFetchROIPressed],
            [self.applyROIPressed, self._mainwidget.applyROIs],
            [self.fetchROIPressed, self._mainwidget.fetchROIs],
            [self.roiInfoChanged, self._mainwidget.updateDisplayedText],
            [self.__ui.labelROILineEdit.textChanged,
             self._updateApplyButton],
            [self.__ui.roiSpinBox.valueChanged, self._mainwidget.updateROIs],
            [self.__ui.roiSpinBox.valueChanged,
             self._mainwidget.writeDetectorROIsAttribute],
            [self.__ui.labelROILineEdit.textEdited, self._writeDetectorROIs],
            [self._mainwidget.roiLineEditChanged, self._updateApplyButton],
            [self._mainwidget.roiAliasesChanged, self.updateROILineEdit],
            [self._mainwidget.roiValueChanged, self.updateROIDisplayText],
            [self._mainwidget.roiNumberChanged, self.setROIsNumber],
            [self._mainwidget.sardanaEnabled, self.updateROIButton],
            [self._mainwidget.mouseImagePositionChanged, self._message],
        ]

    def activate(self):
        """ activates tool widget
        """
        self._mainwidget.changeROIRegion()
        self.setROIsNumber(len(self._mainwidget.roiCoords()))
        self.__aliases = self._mainwidget.getElementNames("ExpChannelList")
        self.updateROILineEdit(self._mainwidget.roilabels)
        self.__updateCompleter()
        self.updateROIButton(self.__settings.sardana)

    def __updateCompleter(self):
        """ updates the labelROI help
        """
        text = str(self.__ui.labelROILineEdit.text())
        sttext = text.strip()
        sptext = sttext.split()
        stext = ""
        if text.endswith(" "):
            stext = sttext
        elif len(sptext) > 1:
            stext = " ".join(sptext[:-1])

        if stext:
            if self.__aliases:
                hints = ["%s %s" % (stext, al) for al in self.__aliases]
            else:
                hints = [stext]
        else:
            hints = self.__aliases or []
        completer = QtGui.QCompleter(hints, self)
        self.__ui.labelROILineEdit.setCompleter(completer)

    def deactivate(self):
        """ deactivates tool widget
        """
        self._mainwidget.roiCoordsChanged.emit()

    @QtCore.pyqtSlot()
    def _writeDetectorROIs(self):
        """ writes Detector rois and updates roi labels
        """
        self._mainwidget.roilabels = str(self.__ui.labelROILineEdit.text())
        self._mainwidget.writeDetectorROIsAttribute()

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides roi message
        """
        message = ""
        current = self._mainwidget.currentROI()
        coords = self._mainwidget.roiCoords()
        if current > -1 and current < len(coords):
            message = "%s" % coords[current]
        self._mainwidget.setDisplayedText(message)

    @QtCore.pyqtSlot()
    def _emitApplyROIPressed(self):
        """ emits applyROIPressed signal"""

        text = str(self.__ui.labelROILineEdit.text()).strip()
        if not text:
            self.__ui.labelROILineEdit.setText("rois")
            self._updateApplyButton()
            text = str(self.__ui.labelROILineEdit.text()).strip()
        roispin = int(self.__ui.roiSpinBox.value())
        self.applyROIPressed.emit(text, roispin)

    @QtCore.pyqtSlot()
    def _emitFetchROIPressed(self):
        """ emits fetchROIPressed signal"""
        text = str(self.__ui.labelROILineEdit.text())
        self.fetchROIPressed.emit(text)

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateApplyButton(self):
        """ updates applied button"""
        stext = str(self.__ui.labelROILineEdit.text())
        self._mainwidget.roilabels = stext
        currentlength = len(stext)
        # if not stext.strip():
        # self.__ui.applyROIPushButton.setEnabled(False)
        self.__updateCompleter()
        # else:
        #    # self.__ui.applyROIPushButton.setEnabled(True)
        if stext.endswith(" ") or currentlength < self.__textlength:
            self.__updateCompleter()
        self.__textlength = currentlength

    @QtCore.pyqtSlot(str)
    def updateROILineEdit(self, text):
        """ updates ROI line edit text

        :param text: text to update
        :type text: :obj:`str`
        """

        if not self.__ui.labelROILineEdit.hasFocus():
            self.__ui.labelROILineEdit.setText(text)
            self._updateApplyButton()

    @QtCore.pyqtSlot(bool)
    def updateROIButton(self, enabled):
        """ enables/disables ROI buttons

        :param enable: buttons enabled
        :type enable: :obj:`bool`
        """
        # self.__ui.applyROIPushButton.setEnabled(enabled)
        self.__ui.fetchROIPushButton.setEnabled(enabled)

    @QtCore.pyqtSlot(int)
    def updateApplyTips(self, rid):
        """ updates apply tips

        :param rid: current roi id
        :type rid: :obj:`int`
        """
        if rid < 0:
            self.__ui.applyROIPushButton.setToolTip(
                "remove ROI aliases from the Door environment"
                " as well as from Active MntGrp")
        else:
            self.__ui.applyROIPushButton.setToolTip(
                "add ROI aliases to the Door environment "
                "as well as to Active MntGrp")

    @QtCore.pyqtSlot(str, int, str)
    def updateROIDisplayText(self, text, currentroi, roiVal):
        """ updates ROI display text

        :param text: standard display text
        :type text: :obj:`str`
        :param currentroi: current roi label
        :type currentroi: :obj:`str`
        :param text: roi sum value
        :type text: :obj:`str`
        """

        roilabel = "roi [%s]" % (currentroi + 1)
        slabel = []

        rlabel = str(self.__ui.labelROILineEdit.text())
        if rlabel:
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in slabel if lb]
        if slabel:
            roilabel = "%s [%s]" % (
                slabel[currentroi]
                if currentroi < len(slabel) else slabel[-1],
                (currentroi + 1)
            )
        if "/" in roiVal:
            self.roiInfoChanged.emit(
                "%s, %s; values = %s" % (text, roilabel, roiVal))
        else:
            self.roiInfoChanged.emit("%s, %s = %s" % (text, roilabel, roiVal))

    @QtCore.pyqtSlot(int)
    def setROIsNumber(self, rid):
        """sets a number of rois

        :param rid: number of rois
        :type rid: :obj:`int`
        """
        self.__ui.roiSpinBox.setValue(rid)


class LineCutToolWidget(ToolBaseWidget):
    """ line-cut tool widget
    """

    #: (:obj:`str`) tool name
    name = "LineCut"
    #: (:obj:`str`) tool name alias
    alias = "linecut"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`Ui_LineCutToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _cutformclass()
        self.__ui.setupUi(self)

        self.parameters.cuts = True
        self.parameters.bottomplot = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`int`) 1d x-coorindate index,
        #:          i.e. {0:Points, 1:"X-Pixels", 2:"Y-Pixels"}
        self.__xindex = 0
        #: (:obj:`bool`) plot cuts
        self.__allcuts = False
        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot freezed
        self.__freezed = []

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot
        self.__curves = []
        #: (:obj:`int`) current plot number
        self.__nrplots = 0

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.cutSpinBox.valueChanged, self._updateCuts],
            [self._mainwidget.cutNumberChanged, self._setCutsNumber],
            [self._mainwidget.cutCoordsChanged, self._plotCuts],
            [self.__ui.xcoordsComboBox.currentIndexChanged,
             self._setXCoords],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self.__ui.allcutsCheckBox.stateChanged, self._updateAllCuts],
            [self._mainwidget.freezeBottomPlotClicked, self._freezeplot],
            [self._mainwidget.clearBottomPlotClicked, self._clearplot],
        ]

    @QtCore.pyqtSlot()
    def _freezeplot(self):
        """ freeze plot
        """
        self._clearplot()
        nrplots = self.__nrplots
        while nrplots > len(self.__freezed):
            cr = self._mainwidget.onedbottomplot()
            cr.setPen(_pg.mkColor(0.5))
            self.__freezed.append(cr)

        for i in range(nrplots):
            self.__freezed[i].setData(*self.__curves[i].getData())
            self.__freezed[i].show()
            self.__freezed[i].setVisible(True)
        for i in range(nrplots, len(self.__freezed)):
            self.__freezed[i].hide()
            self.__freezed[i].setVisible(True)
            # print(type(cr))

    @QtCore.pyqtSlot()
    def _clearplot(self):
        """ clear plot
        """
        for cr in self.__freezed:
            cr.setVisible(False)

    @QtCore.pyqtSlot(int)
    def _updateCuts(self, cid):
        """ update Cuts

        :param cid: cut id
        :type cid: :obj:`int`
        """
        if self.__allcuts:
            self.__allcuts = True
        else:
            self.__allcuts = False

        self._mainwidget.updateCuts(cid)

    def afterplot(self):
        """ command after plot
        """
        self._plotCuts()

    def activate(self):
        """ activates tool widget
        """
        if not self.__curves:
            self.__curves.append(self._mainwidget.onedbottomplot(True))
            self.__nrplots = 1
        for curve in self.__curves:
            curve.show()
            curve.setVisible(True)
        self._updateAllCuts(self.__allcuts)
        self._plotCuts()
        self._mainwidget.bottomplotShowMenu(True, True)

    def deactivate(self):
        """ activates tool widget
        """
        self._mainwidget.bottomplotShowMenu()
        for curve in self.__curves:
            curve.hide()
            curve.setVisible(False)
            self._mainwidget.removebottomplot(curve)
        self.__curves = []
        for freezed in self.__freezed:
            freezed.hide()
            freezed.setVisible(False)
            self._mainwidget.removebottomplot(freezed)
        self.__freezed = []

    @QtCore.pyqtSlot(int)
    def _updateAllCuts(self, value):
        """ updates X row status

        :param value: if True or not 0 x-cooridnates taken from the first row
        :param value: :obj:`int` or  :obj:`bool`
        """
        self.__allcuts = value
        self._updateCuts(self.__ui.cutSpinBox.value())

    @QtCore.pyqtSlot(int)
    def _setXCoords(self, xindex):
        """ sets x-coodinates for 1d plot

        :param xindex: 1d x-coorindate index,
        :type xindex: :obj:`int`
        """
        self.__xindex = xindex
        self._plotCuts()

    @QtCore.pyqtSlot()
    def _plotCuts(self):
        """ plots the current 1d Cut
        """
        if self.__allcuts:
            self._plotAllCuts()
        else:
            self._plotCut()

    def _plotAllCuts(self):
        """ plot all 1d Cuts
        """

        if self._mainwidget.currentTool() == self.name:
            nrplots = self.__ui.cutSpinBox.value()
            if self.__nrplots != nrplots:
                while nrplots > len(self.__curves):
                    self.__curves.append(self._mainwidget.onedbottomplot())
                for i in range(nrplots):
                    self.__curves[i].show()
                for i in range(nrplots, len(self.__curves)):
                    self.__curves[i].hide()
                self.__nrplots = nrplots
                if nrplots:
                    for i, cr in enumerate(self.__curves):
                        if i < nrplots:
                            cr.setPen(_pg.hsvColor(i/float(nrplots)))
            coords = self._mainwidget.cutCoords()
            rws = self._mainwidget.rangeWindowScale()
            for i in range(nrplots):
                dt = self._mainwidget.cutData(i)
                if dt is not None:
                    if self.__settings.nanmask:
                        if dt.dtype.kind == 'f' and np.isnan(dt.min()):
                            dt = np.nan_to_num(dt)
                    if self.__xindex:
                        if i < len(coords):
                            crds = coords[i]
                        else:
                            crds = [0, 0, 1, 1, 0.00001]
                        if self.__xindex == 2:
                            dx = np.linspace(crds[1], crds[3], len(dt))
                        else:
                            dx = np.linspace(crds[0], crds[2], len(dt))
                        self.__curves[i].setData(x=dx, y=dt)
                    else:
                        if rws > 1.0:
                            dx = np.linspace(0, len(dt - 1) * rws, len(dt))
                            self.__curves[i].setData(x=dx, y=dt)
                        else:
                            self.__curves[i].setData(y=dt)
                    self.__curves[i].setVisible(True)
                else:
                    self.__curves[i].setVisible(False)

    def _plotCut(self):
        """ plot the current 1d Cut
        """
        if self.__nrplots > 1:
            for i in range(1, len(self.__curves)):
                self.__curves[i].setVisible(False)
                self.__curves[i].hide()
            self.__nrplots = 1
        if self._mainwidget.currentTool() == self.name:
            dt = self._mainwidget.cutData()
            self.__curves[0].setPen(_pg.mkColor('r'))
            if dt is not None:
                if self.__settings.nanmask:
                    if dt.dtype.kind == 'f' and np.isnan(dt.min()):
                        dt = np.nan_to_num(dt)
                if self.__xindex:
                    crds = [0, 0, 1, 1, 0.00001]
                    if self._mainwidget.currentCut() > -1:
                        crds = self._mainwidget.cutCoords()[
                            self._mainwidget.currentCut()]
                    if self.__xindex == 2:
                        dx = np.linspace(crds[1], crds[3], len(dt))
                    else:
                        dx = np.linspace(crds[0], crds[2], len(dt))
                    self.__curves[0].setData(x=dx, y=dt)
                else:
                    rws = self._mainwidget.rangeWindowScale()
                    if rws > 1.0:
                        dx = np.linspace(0, len(dt - 1) * rws, len(dt))
                        self.__curves[0].setData(x=dx, y=dt)
                    else:
                        self.__curves[0].setData(y=dt)
                self.__curves[0].setVisible(True)
            else:
                self.__curves[0].setVisible(False)

    @QtCore.pyqtSlot(int)
    def _setCutsNumber(self, cid):
        """sets a number of cuts

        :param cid: number of cuts
        :type cid: :obj:`int`
        """
        self.__ui.cutSpinBox.setValue(cid)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides cut message
        """
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        if self._mainwidget.currentCut() > -1:
            crds = self._mainwidget.cutCoords()[
                self._mainwidget.currentCut()]
            crds = "[[%.2f, %.2f], [%.2f, %.2f], width=%.2f]" % tuple(crds)
        else:
            crds = "[[0, 0], [0, 0], width=0]"
        message = "%s, x = %.2f, y = %.2f, %s = %.2f" % (
            crds, x, y, ilabel, intensity)
        self._mainwidget.setDisplayedText(message)


class ProjectionToolWidget(ToolBaseWidget):
    """ Projections tool widget
    """

    #: (:obj:`str`) tool name
    name = "Projections"
    #: (:obj:`str`) tool name alias
    alias = "projections"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`Ui_ProjectionToolWidget')
        #:      ui_toolwidget object from qtdesigner
        self.__ui = _projectionformclass()
        self.__ui.setupUi(self)

        #: (:class:`pyqtgraph.PlotDataItem`) 1D bottom plot
        self.__bottomplot = None
        #: (:class:`pyqtgraph.PlotDataItem`) 1D bottom plot
        self.__rightplot = None
        #: (:obj:`int`) function index
        self.__funindex = 0

        #: (:obj:`slice`) selected rows
        self.__rows = None
        #: (:obj:`slice`) selected columns
        self.__columns = None
        #: (:obj:`slice`) selected rows
        self.__dsrows = None
        #: (:obj:`slice`) selected columns
        self.__dscolumns = None

        self.parameters.bottomplot = True
        self.parameters.rightplot = True
        self.parameters.vhbounds = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.funComboBox.currentIndexChanged,
             self._setFunction],
            [self.__ui.rowsliceLineEdit.textChanged, self._updateRows],
            [self.__ui.columnsliceLineEdit.textChanged, self._updateColumns],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self._mainwidget.scalesChanged, self._updateColumns],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def __updateslice(self, text, dx=None, ds=None):
        """ create slices from the text
        """
        rows = "ERROR"
        dsrows = "ERROR"
        if text:
            try:
                if ":" in text:
                    slices = text.split(":")
                    s0 = int(slices[0]) if slices[0].strip() else 0
                    s1 = int(slices[1]) if slices[1].strip() else None
                    if len(slices) > 2:
                        s2 = int(slices[2]) if slices[2].strip() else None
                        rows = slice(s0, s1, s2)
                        if dx is not None:
                            dsrows = slice((s0-dx)/ds, (s1-dx)/ds, s2/ds)
                        else:
                            dsrows = rows
                    else:
                        rows = slice(s0, s1)
                        if dx is not None:
                            dsrows = slice((s0-dx)/ds, (s1-dx)/ds)
                        else:
                            dsrows = rows
                else:
                    rows = int(text)
                    if dx is not None:
                        dsrows = int((rows - dx)/ds)
                    else:
                        dsrows = rows
            except Exception:
                pass
        else:
            rows = None
            dsrows = None
        return rows, dsrows

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateSlices(self):
        """ updates applied button"""
        rtext = str(self.__ui.rowsliceLineEdit.text()).strip()
        ctext = str(self.__ui.columnsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
            self.__rows, self.__dsrows = self.__updateslice(
                rtext, int(dy), int(ds2))
            self.__columns, self.__dscolumns = self.__updateslice(
                ctext, int(dx), int(ds1))
        else:
            self.__rows, self.__dsrows = self.__updateslice(rtext)
            self.__columns, self.__dscolumns = self.__updateslice(ctext)
        if self.__rows is None:
            self._mainwidget.updateHBounds(None, None)
        elif isinstance(self.__rows, int):
            self._mainwidget.updateHBounds(self.__rows, self.__rows + 1)
        elif isinstance(self.__rows, slice):
            self._mainwidget.updateHBounds(self.__rows.start, self.__rows.stop)
        if self.__columns is None:
            self._mainwidget.updateVBounds(None, None)
        elif isinstance(self.__columns, int):
            self._mainwidget.updateVBounds(self.__columns, self.__columns + 1)
        elif isinstance(self.__columns, slice):
            self._mainwidget.updateVBounds(
                self.__columns.start, self.__columns.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateRows(self):
        """ updates applied button"""
        rtext = str(self.__ui.rowsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
            self.__rows, self.__dsrows = self.__updateslice(
                rtext, int(dy), int(ds2))
        else:
            self.__rows, self.__dsrows = self.__updateslice(rtext)
        if self.__rows is None:
            self._mainwidget.updateHBounds(None, None)
        elif isinstance(self.__rows, int):
            self._mainwidget.updateHBounds(self.__rows, self.__rows + 1)
        elif isinstance(self.__rows, slice):
            self._mainwidget.updateHBounds(self.__rows.start, self.__rows.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateColumns(self):
        """ updates applied button"""
        text = str(self.__ui.columnsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
        if rwe:
            self.__columns, self.__dscolumns = self.__updateslice(
                text, int(dx), int(ds1))
        else:
            self.__columns, self.__dscolumns = self.__updateslice(text)
        if self.__columns is None:
            self._mainwidget.updateVBounds(None, None)
        elif isinstance(self.__columns, int):
            self._mainwidget.updateVBounds(self.__columns, self.__columns + 1)
        elif isinstance(self.__columns, slice):
            self._mainwidget.updateVBounds(
                self.__columns.start, self.__columns.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(int)
    def _setFunction(self, findex):
        """ set sum or mean function

        :param findex: function index, i.e. 0:mean, 1:sum
        :type findex: :obj:`int`
        """
        self.__funindex = findex
        self._plotCurves()

    def afterplot(self):
        """ command after plot
        """
        self._plotCurves()

    def activate(self):
        """ activates tool widget
        """
        if self.__bottomplot is None:
            self.__bottomplot = self._mainwidget.onedbarbottomplot()

        if self.__rightplot is None:
            self.__rightplot = self._mainwidget.onedbarrightplot()

        self.__bottomplot.show()
        self.__rightplot.show()
        self.__bottomplot.setVisible(True)
        self.__rightplot.setVisible(True)
        self._updateSlices()
        self._plotCurves()

    def deactivate(self):
        """ activates tool widget
        """
        if self.__bottomplot is not None:
            self.__bottomplot.hide()
            self.__bottomplot.setVisible(False)
            self._mainwidget.removebottomplot(self.__bottomplot)
            self.__bottomplot = None
        if self.__rightplot is not None:
            self.__rightplot.hide()
            self.__rightplot.setVisible(False)
            self._mainwidget.removerightplot(self.__rightplot)
            self.__rightplot = None

    @QtCore.pyqtSlot()
    def _plotCurves(self):
        """ plots the current image in 1d plots
        """
        if self._mainwidget.currentTool() == self.name:
            dts = self._mainwidget.rawData()
            if dts is not None:
                if self.__funindex:
                    npfun = np.nansum
                else:
                    npfun = np.nanmean

                if self.__dsrows == "ERROR":
                    sx = []
                elif self.__dsrows is not None:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            if isinstance(self.__dsrows, slice):
                                sx = npfun(dts[:, self.__dsrows], axis=1)
                            else:
                                sx = dts[:, self.__dsrows]
                    except Exception:
                        sx = []

                else:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            sx = npfun(dts, axis=1)
                    except Exception:
                        sx = []

                if self.__dscolumns == "ERROR":
                    sy = []
                if self.__dscolumns is not None:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            if isinstance(self.__dscolumns, slice):
                                sy = npfun(dts[self.__dscolumns, :], axis=0)
                            else:
                                sy = dts[self.__dscolumns, :]
                    except Exception:
                        sy = []
                else:
                    with np.warnings.catch_warnings():
                        np.warnings.filterwarnings(
                            "ignore", r'Mean of empty slice')
                        sy = npfun(dts, axis=0)

                rwe = self._mainwidget.rangeWindowEnabled()
                if rwe:
                    x, y, s1, s2 = self._mainwidget.scale(
                        useraxes=False, noNone=True)
                    if self._mainwidget.transformations()[3]:
                        x, y = y, x
                        s1, s2 = s2, s1
                    xx = list(
                        range(int(x), len(sx) * int(s1) + int(x), int(s1)))
                    yy = list(
                        range(int(y), len(sy) * int(s2) + int(y), int(s2)))
                    width = [s1] * len(sx)
                    height = [s1] * len(sy)
                else:
                    xx = list(range(len(sx)))
                    yy = list(range(len(sy)))
                    width = [1.0] * len(sx)
                    height = [1.0] * len(sy)
                self.__bottomplot.setOpts(
                    y0=[0]*len(sx), y1=sx, x=xx,
                    width=width)
                self.__bottomplot.drawPicture()
                self.__rightplot.setOpts(
                    x0=[0]*len(sy), x1=sy, y=yy,
                    height=height)
                self.__rightplot.drawPicture()

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        message = "x = %i, y = %i, %s = %.2f" % (
            x, y, ilabel, intensity)
        self._mainwidget.setDisplayedText(message)


class OneDToolWidget(ToolBaseWidget):
    """ 1d plot tool widget
    """

    #: (:obj:`str`) tool name
    name = "1d-Plot"
    #: (:obj:`str`) tool name alias
    alias = "1d-plot"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:class:`Ui_OneDToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _onedformclass()
        self.__ui.setupUi(self)

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot
        self.__curves = []
        #: (:obj:`int`) current plot number
        self.__nrplots = 0

        #: ((:obj:`list`<:obj:`int`>) selected rows
        self.__rows = [0]
        #: ((:obj:`list`<:obj:`int`>) selected rows
        self.__dsrows = [0]
        #: ((:obj:`bool`) x in first row
        self.__xinfirstrow = False
        #: ((:obj:`bool`) accumalate status
        self.__accumulate = False
        #: ((:obj:`int`) buffer size
        self.__buffersize = 1024
        #: ((:class:`ndarray`) buffer
        self.__buffer = None

        self.__ui.rowsLineEdit.setText("0")
        self.parameters.bottomplot = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.rowsLineEdit.textChanged, self._updateRows],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self.__ui.sizeLineEdit.textChanged, self._setBufferSize],
            [self.__ui.xCheckBox.stateChanged, self._updateXRow],
            [self.__ui.accuPushButton.clicked, self._startStopAccu],
            [self.__ui.resetPushButton.clicked, self._resetAccu],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def afterplot(self):
        """ command after plot
        """
        self._plotCurves()

    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """

        if self.__accumulate:
            dts = rawarray
            newrow = np.sum(dts[:, self.__dsrows], axis=1)
            if self.__buffer is not None and \
               self.__buffer.shape[1] == newrow.shape[0]:
                if self.__buffer.shape[0] >= self.__buffersize:
                    self.__buffer = np.vstack(
                        [self.__buffer[
                            self.__buffer.shape[0] - self.__buffersize + 1:,
                            :],
                         newrow]
                    )
                else:
                    self.__buffer = np.vstack([self.__buffer, newrow])
            else:
                self.__buffer = np.array([newrow])
            return np.transpose(self.__buffer), rawarray

    def activate(self):
        """ activates tool widget
        """
        self.__ui.sizeLineEdit.setText(str(self.__buffersize))
        self._updateRows()

    def deactivate(self):
        """ activates tool widget
        """
        for cr in self.__curves:
            cr.hide()
            cr.setVisible(False)
            self._mainwidget.removebottomplot(cr)
        self.__curves = []
        self.__nrplots = 0

    @QtCore.pyqtSlot()
    def _resetAccu(self):
        """ reset accumulation buffer
        """
        self.__buffer = None

    @QtCore.pyqtSlot()
    def _startStopAccu(self):
        """ start/stop accumulation buffer
        """
        if not self.__accumulate:
            self.__accumulate = True
            self.__ui.accuPushButton.setText("Stop")
        else:
            self.__accumulate = False
            self.__ui.accuPushButton.setText("Collect")

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _setBufferSize(self):
        """ start/stop accumulation buffer

        """
        try:
            self.__buffersize = int(self.__ui.sizeLineEdit.text())
        except Exception as e:
            # print(str(e))
            logger.warning(str(e))
            self.__buffersize = 1024

    @QtCore.pyqtSlot(int)
    def _updateXRow(self, value):
        """ updates X row status

        :param value: if True or not 0 x-cooridnates taken from the first row
        :param value: :obj:`int` or  :obj:`bool`
        """
        self.__xinfirstrow = True if value else False
        self._updateRows()

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateRows(self):
        """ updates applied button"""
        text = str(self.__ui.rowsLineEdit.text()).strip()
        rows = []
        dsrows = []
        rwe = None
        if text:
            if text == "ALL":
                rows = [None]
            else:
                try:
                    rwe = self._mainwidget.rangeWindowEnabled()
                    if rwe:
                        dx, dy, ds1, ds2 = self._mainwidget.scale(
                            useraxes=False, noNone=True)
                        if self._mainwidget.transformations()[3]:
                            dx, dy = dy, dx
                            ds1, ds2 = ds2, ds1
                    stext = [rw for rw in re.split(",| ", text) if rw]
                    for rw in stext:
                        if ":" in rw:
                            slices = rw.split(":")
                            s0 = int(slices[0]) if slices[0].strip() else 0
                            s1 = int(slices[1]) if slices[1].strip() else 0
                            if len(slices) > 2:
                                s2 = int(slices[2]) if slices[2].strip() else 1
                                rows.extend(list(range(s0, s1, s2)))
                                if rwe:
                                    dsrows.extend(
                                        list(range(int((s0-dy)/ds2),
                                                   int((s1-dy)/ds2),
                                                   int(s2/ds2))))
                            else:
                                rows.extend(list(range(s0, s1)))
                                if rwe:
                                    dsrows.extend(
                                        list(range(int((s0-dy)/ds2),
                                                   int((s1-dy)/ds2))))
                        else:
                            rows.append(int(rw))
                            if rwe:
                                dsrows.append(int((int(rw)-dy)/ds2))
                except Exception:
                    rows = []
        self.__rows = rows
        if not rwe:
            self.__dsrows = rows
        else:
            self.__dsrows = dsrows
        self._plotCurves()

    @QtCore.pyqtSlot()
    def _plotCurves(self):
        """ plots the current image in 1d plots
        """
        if self._mainwidget.currentTool() == self.name:
            dts = self._mainwidget.rawData()
            if dts is not None:
                dtnrpts = dts.shape[1]
                if self.__dsrows:
                    if self.__dsrows[0] is None:
                        if self.__xinfirstrow:
                            nrplots = dtnrpts - 1
                        else:
                            nrplots = dtnrpts

                    else:
                        nrplots = len(self.__dsrows)
                else:
                    nrplots = 0
                if self.__nrplots != nrplots:
                    while nrplots > len(self.__curves):
                        self.__curves.append(self._mainwidget.onedbottomplot())
                    for i in range(nrplots):
                        self.__curves[i].show()
                    for i in range(nrplots, len(self.__curves)):
                        self.__curves[i].hide()
                    self.__nrplots = nrplots
                    if nrplots:
                        for i, cr in enumerate(self.__curves):
                            if i < nrplots:
                                cr.setPen(_pg.hsvColor(i/float(nrplots)))
                rwe = self._mainwidget.rangeWindowEnabled()
                if rwe:
                    dx, dy, ds1, ds2 = self._mainwidget.scale(
                        useraxes=False, noNone=True)
                    if self._mainwidget.transformations()[3]:
                        dx, dy = dy, dx
                        ds1, ds2 = ds2, ds1
                for i in range(nrplots):
                    if self.__dsrows:
                        if self.__dsrows[0] is None:
                            if self.__xinfirstrow and i:
                                self.__curves[i].setData(
                                    x=dts[:, 0], y=dts[:, i])
                            elif rwe:
                                y = dts[:, i]
                                x = np.linspace(
                                    dx, len(y - 1) * ds1 + dx, len(y))
                                self.__curves[i].setData(x=x, y=y)
                            else:
                                self.__curves[i].setData(dts[:, i])
                            self.__curves[i].setVisible(True)
                        elif (self.__dsrows[i] >= 0 and
                              self.__dsrows[i] < dtnrpts):
                            if self.__xinfirstrow:
                                self.__curves[i].setData(
                                    x=dts[:, 0], y=dts[:, self.__dsrows[i]])
                            elif rwe:
                                y = dts[:, self.__dsrows[i]]
                                x = np.linspace(
                                    dx, len(y - 1) * ds1 + dx, len(y))
                                self.__curves[i].setData(x=x, y=y)
                            else:
                                self.__curves[i].setData(
                                    dts[:, self.__dsrows[i]])
                            self.__curves[i].setVisible(True)
                        else:
                            self.__curves[i].setVisible(False)
                    else:
                        self.__curves[i].setVisible(False)
            else:
                for cr in self.__curves:
                    cr.setVisible(False)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides intensity message
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        ilabel = self._mainwidget.scalingLabel()
        message = "x = %i, y = %i, %s = %.2f" % (
            x, y, ilabel, intensity)
        self._mainwidget.setDisplayedText(message)


class AngleQToolWidget(ToolBaseWidget):
    """ angle/q tool widget
    """

    #: (:obj:`str`) tool name
    name = "Angle/Q"
    #: (:obj:`str`) tool name alias
    alias = "angle/q"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`int`) geometry space index -> 0: angle, 1 q-space
        self.__gspaceindex = 0

        #: (:obj:`int`) plot index -> 0: Cartesian, 1 polar-th, 2 polar-q
        self.__plotindex = 0

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _angleqformclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) old lock value
        self.__oldlocked = None

        #: (:class:`numpy.array`) radial array cache
        self.__lastradial = None
        #: (:class:`numpy.array`) angle array cache
        self.__lastangle = None
        #: (:obj:`float`) energy cache
        self.__lastenergy = None
        #: (:obj:`float`) radmax cache
        self.__lastradmax = None
        #: (:obj:`float`) plotindex cache
        self.__lastpindex = None
        #: (:obj:`float`) detdistance cache
        self.__lastdistance = None
        #: (:obj:`float`) center x cache
        self.__lastcenterx = None
        #: (:obj:`float`) center y cache
        self.__lastcentery = None
        #: (:obj:`float`) pixelsizeycache
        self.__lastpsizex = None
        #: (:obj:`float`) pixelsizey cache
        self.__lastpsizey = None
        #: (:class:`numpy.array`) x array cache
        self.__lastx = None
        #: (:class:`numpy.array`) y array cache
        self.__lasty = None
        #: (:obj:`float`) maxdim cache
        self.__lastmaxdim = None

        #: (:obj:`float`) start position of radial q coordinate
        self.__radqstart = None
        #: (:obj:`float`) end position of radial q coordinate
        self.__radqend = None
        #: (:obj:`int`) grid size of radial q coordinate
        self.__radqsize = None
        #: (:obj:`float`) start position of radial theta coordinate
        self.__radthstart = None
        #: (:obj:`float`) end position of radial theta coordinate
        self.__radthend = None
        #: (:obj:`int`) grid size of radial theta coordinate
        self.__radthsize = None
        #: (:obj:`float`) start position of polar angle
        self.__polstart = None
        #: (:obj:`float`) end position of polar angle
        self.__polend = None
        #: (:obj:`int`) grid size of polar angle
        self.__polsize = None

        #: (:obj:`float`) range changed flag
        self.__rangechanged = True

        # self.parameters.lines = True
        #: (:obj:`str`) infolineedit text
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""
        self.parameters.centerlines = True
        self.parameters.polarscale = False
        # self.parameters.rightplot = True

        #: (`lavuelib.imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`float`) radial coordinate factor
        self.__radmax = 1.

        #: (:obj:`float`) polar coordinate factor
        self.__polmax = 1.

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.angleqPushButton.clicked, self._setGeometry],
            [self.__ui.rangePushButton.clicked, self._setPolarRange],
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._setGSpaceIndex],
            [self.__ui.plotComboBox.currentIndexChanged,
             self._setPlotIndex],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def activate(self):
        """ activates tool widget
        """
        self.__oldlocked = None
        self.updateGeometryTip()
        self.updateRangeTip()
        self._mainwidget.updateCenter(
            self.__settings.centerx, self.__settings.centery)

    def deactivate(self):
        """ deactivates tool widget
        """
        self._setPlotIndex(0)

    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """
        if self.__plotindex != 0:
            if self._mainwidget.transformations()[0]:
                tdata = self.__plotPolarImage(np.transpose(array))
            else:
                tdata = self.__plotPolarImage(array)
            return tdata, tdata

    def __havexychanged(self, radial, angle):
        """ if xy changed

        :param radial: radial coordinate
        :type radial: :obj:`float` or :class:`numpy.array`
        :param angle: polar angle coordinate
        :type angle: :obj:`float` or :class:`numpy.array`
        :returns: flag if (x, y) have changed
        :rtype: :obj:`bool`
        """
        recalc = False
        if self.__lastradial is None or self.__lastangle is None or \
           self.__lastenergy is None or self.__lastradmax is None or \
           self.__lastpindex is None or self.__lastdistance is None or \
           self.__lastcenterx is None or self.__lastcentery is None or \
           self.__lastpsizex is None or self.__lastpsizey is None or \
           self.__lastx is None or self.__lasty is None:
            recalc = True
        elif self.__lastenergy != self.__settings.energy:
            recalc = True
        elif self.__lastradmax != self.__radmax:
            recalc = True
        elif self.__lastpindex != self.__plotindex:
            recalc = True
        elif self.__lastdistance != self.__settings.detdistance:
            recalc = True
        elif self.__lastcenterx != self.__settings.centerx:
            recalc = True
        elif self.__lastcentery != self.__settings.centery:
            recalc = True
        elif self.__lastpsizex != self.__settings.pixelsizex:
            recalc = True
        elif self.__lastpsizey != self.__settings.pixelsizey:
            recalc = True
        elif (isinstance(radial, np.ndarray) and
              not np.array_equal(self.__lastradial, radial)):
            recalc = True
        elif (not isinstance(radial, np.ndarray)
              and self.__lastradial != radial):
            recalc = True
        elif (isinstance(angle, np.ndarray)
              and not np.array_equal(self.__lastangle, angle)):
            recalc = True
        elif not isinstance(angle, np.ndarray) and self.__lastangle != angle:
            recalc = True
        return recalc

    def __intintensity(self, radial, angle):
        """ intensity interpolation function

        :param radial: radial coordinate
        :type radial: :obj:`float` or :class:`numpy.array`
        :param angle: polar angle coordinate
        :type angle: :obj:`float` or :class:`numpy.array`
        :return: interpolated intensity
        :rtype: :obj:`float` or :class:`numpy.array`
        """
        if self.__rangechanged or self.__havexychanged(radial, angle):
            if self.__plotindex == 1:
                rstart = self.__radthstart \
                    if self.__radthstart is not None else 0
                theta = radial * self.__radmax + rstart * math.pi / 180
            else:
                wavelength = 12398.4193/self.__settings.energy
                rstart = self.__radqstart \
                    if self.__radqstart is not None else 0
                theta = 2. * np.arcsin(
                    (radial * self.__radmax + rstart) * wavelength
                    / (4. * math.pi))
            if self.__polsize is not None or \
               self.__polstart is not None or self.__polend is not None:
                pstart = self.__polstart if self.__polstart is not None else 0
                angle = angle * self.__polmax + pstart
            fac = 1000. * self.__settings.detdistance * np.tan(theta)
            self.__lastx = self.__settings.centerx + \
                fac * np.sin(angle * math.pi / 180) \
                / self.__settings.pixelsizex
            self.__lasty = self.__settings.centery + \
                fac * np.cos(angle * math.pi / 180) \
                / self.__settings.pixelsizey
            self.__lastenergy = self.__settings.energy
            self.__lastradmax = self.__radmax
            self.__lastpindex = self.__plotindex
            self.__lastdistance = self.__settings.detdistance
            self.__lastcenterx = self.__settings.centerx
            self.__lastcentery = self.__settings.centery
            self.__lastpsizex = self.__settings.pixelsizex
            self.__lastpsizey = self.__settings.pixelsizey
            self.__lastradial = radial
            self.__lastangle = angle
            self.__rangechanged = False

        if hasattr(self.__inter, "ev"):
            return self.__inter.ev(self.__lastx, self.__lasty)
        else:
            return self.__inter(np.transpose(
                [self.__lastx, self.__lasty], axes=[1, 2, 0]))

    def __calculateRadMax(self, pindex, rdata=None):
        """ recalculates radmax

        :param rarray: 2d image array
        :type rarray: :class:`numpy.ndarray`
        """
        if rdata is None:
            rdata = self._mainwidget.currentData()
        if rdata is not None:

            if pindex == 1:
                if self.__lastmaxdim is not None \
                   and self.__radthsize is not None:
                    maxdim = self.__lastmaxdim
                else:
                    maxdim = max(rdata.shape[0], rdata.shape[1])
                rstart = self.__radthstart \
                    if self.__radthstart is not None else 0
                if self.__radthend is None:
                    _, _, th0 = self.__pixel2theta(0, 0, False)
                    _, _, th1 = self.__pixel2theta(0, rdata.shape[1], False)
                    _, _, th2 = self.__pixel2theta(rdata.shape[0], 0, False)
                    _, _, th3 = self.__pixel2theta(
                        rdata.shape[0], rdata.shape[1], False)
                    try:
                        rmax = max(th0, th1, th2, th3)
                    except TypeError:
                        rmax = None
                else:
                    rmax = (self.__radthend - rstart) * math.pi / 180.
                if self.__radthsize is not None:
                    maxdim = self.__radthsize
                if rmax is None:
                    self._setGeometry()
                    return False
                self.__radmax = rmax/float(maxdim)

            elif pindex == 2:
                if self.__lastmaxdim is not None \
                   and self.__radqsize is not None:
                    maxdim = self.__lastmaxdim
                else:
                    maxdim = max(rdata.shape[0], rdata.shape[1])
                rstart = self.__radqstart \
                    if self.__radqstart is not None else 0
                if self.__radqend is None:
                    _, _, q0 = self.__pixel2q(0, 0, False)
                    _, _, q1 = self.__pixel2q(0, rdata.shape[1], False)
                    _, _, q2 = self.__pixel2q(rdata.shape[0], 0, False)
                    _, _, q3 = self.__pixel2q(
                        rdata.shape[0], rdata.shape[1], False)
                    try:
                        rmax = max(q0, q1, q2, q3)
                    except TypeError:
                        rmax = None
                else:
                    rmax = (self.__radqend - rstart)
                if self.__radqsize is not None:
                    maxdim = self.__radqsize
                if rmax is None:
                    self._setGeometry()
                    return False
                self.__radmax = rmax/float(maxdim)
            if pindex:
                psize = self.__polsize if self.__polsize is not None else 360
                pstart = self.__polstart if self.__polstart is not None else 0
                pend = self.__polend if self.__polend is not None else 360
                self.__polmax = float(pend - pstart) / psize
        return True

    def __plotPolarImage(self, rdata=None):
        """ intensity interpolation function

        :param rarray: 2d image array
        :type rarray: :class:`numpy.ndarray`
        :return: 2d image array
        :rtype: :class:`numpy.ndarray`
        """
        if self.__settings.energy > 0 and self.__settings.detdistance > 0 and \
           self.__settings.pixelsizex > 0 and self.__settings.pixelsizey > 0:
            if rdata is None:
                rdata = self._mainwidget.currentData()
            rwe = self._mainwidget.rangeWindowEnabled()
            if rwe:
                dx, dy, ds1, ds2 = self._mainwidget.scale(
                    useraxes=False, noNone=True)
                xx = np.array(range(int(dx),
                                    int((rdata.shape[0])*ds1 + dx),
                                    int(ds1)))

                yy = np.array(range(int(dy),
                                    int((rdata.shape[1])*ds2 + dy),
                                    int(ds2)))
            else:
                xx = np.array(range(rdata.shape[0]))
                yy = np.array(range(rdata.shape[1]))

            self.__inter = scipy.interpolate.RegularGridInterpolator(
                (xx, yy), rdata,
                fill_value=(0 if self._mainwidget.scaling() != 'log'
                            else -2),
                bounds_error=False)

            maxpolar = self.__polsize if self.__polsize is not None else 360
            if self.__plotindex == 1:
                if self.__radthsize is not None:
                    self.__lastmaxdim = self.__radthsize
                else:
                    self.__lastmaxdim = max(rdata.shape[0], rdata.shape[1])
            else:
                if self.__radqsize is not None:
                    self.__lastmaxdim = self.__radqsize
                else:
                    self.__lastmaxdim = max(rdata.shape[0], rdata.shape[1])

            while not self.__calculateRadMax(self.__plotindex, rdata):
                pass
            tdata = np.fromfunction(
                lambda x, y: self.__intintensity(x, y),
                (self.__lastmaxdim, maxpolar),
                dtype=float)
            # else:
            #     self.__inter = scipy.interpolate.RectBivariateSpline(
            #         xx, yy, rdata)
            #     tdata = np.fromfunction(
            #         lambda x, y: self.__intintensity(x, y),
            #         (self.__lastmaxdim, maxpolar),
            #         dtype=float)
            return tdata

    @QtCore.pyqtSlot(float, float)
    def _updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        if self.__plotindex == 0:
            txdata = None
            if self._mainwidget.rangeWindowEnabled():
                txdata, tydata = self._mainwidget.scaledxy(
                    xdata, ydata, useraxes=False)
                if txdata is not None:
                    xdata = txdata
                    ydata = tydata
            self.__settings.centerx = float(xdata)
            self.__settings.centery = float(ydata)
            self._mainwidget.writeAttribute("BeamCenterX", float(xdata))
            self._mainwidget.writeAttribute("BeamCenterY", float(ydata))
            self._message()
            self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides geometry message
        """
        message = ""
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                x, y, useraxes=False)
            if txdata is not None:
                x = txdata
                y = tydata
        ilabel = self._mainwidget.scalingLabel()
        if self.__plotindex == 0:
            if self.__gspaceindex == 0:
                thetax, thetay, thetatotal = self.__pixel2theta(x, y)
                if thetax is not None:
                    message = "th_x = %f deg, th_y = %f deg," \
                              " th_tot = %f deg, %s = %.2f" \
                              % (thetax * 180 / math.pi,
                                 thetay * 180 / math.pi,
                                 thetatotal * 180 / math.pi,
                                 ilabel, intensity)
            else:
                qx, qy, q = self.__pixel2q(x, y)
                if qx is not None:
                    message = u"q_x = %f 1/\u212B, q_y = %f 1/\u212B, " \
                              u"q = %f 1/\u212B, %s = %.2f" \
                              % (qx, qy, q, ilabel, intensity)
        elif self.__plotindex == 1:
            rstart = self.__radthstart \
                if self.__radthstart is not None else 0
            pstart = self.__polstart if self.__polstart is not None else 0
            iscaling = self._mainwidget.scaling()
            if iscaling != "linear" and not ilabel.startswith(iscaling):
                if ilabel[0] == "(":
                    ilabel = "%s%s" % (iscaling, ilabel)
                else:
                    ilabel = "%s(%s)" % (iscaling, ilabel)

            message = u"th_tot = %f deg, polar = %f deg, " \
                      u" %s = %.2f" % (
                          x * 180 / math.pi * self.__radmax + rstart,
                          y * self.__polmax + pstart,
                          ilabel, intensity)
        elif self.__plotindex == 2:
            iscaling = self._mainwidget.scaling()
            pstart = self.__polstart if self.__polstart is not None else 0
            rstart = self.__radqstart \
                if self.__radqstart is not None else 0
            if iscaling != "linear" and not ilabel.startswith(iscaling):
                if ilabel[0] == "(":
                    ilabel = "%s%s" % (iscaling, ilabel)
                else:
                    ilabel = "%s(%s)" % (iscaling, ilabel)

            message = u"q = %f 1/\u212B, polar = %f deg, " \
                      u" %s = %.2f" % (
                          x * self.__radmax + rstart,
                          y * self.__polmax + pstart,
                          ilabel, intensity)

        self._mainwidget.setDisplayedText(message)

    def __pixel2theta(self, xdata, ydata, xy=True):
        """ converts coordinates from pixel positions to theta angles

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :param xy: flag
        :type xy: :obj:`bool`
        :returns: x-theta, y-theta, total-theta
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        thetax = None
        thetay = None
        thetatotal = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            xcentered = xdata - self.__settings.centerx
            ycentered = ydata - self.__settings.centery
            if xy:
                thetax = math.atan(
                    xcentered * self.__settings.pixelsizex / 1000.
                    / self.__settings.detdistance)
                thetay = math.atan(
                    ycentered * self.__settings.pixelsizey / 1000.
                    / self.__settings.detdistance)
            r = math.sqrt(
                (xcentered * self.__settings.pixelsizex / 1000.) ** 2
                + (ycentered * self.__settings.pixelsizey / 1000.) ** 2)
            thetatotal = math.atan(
                r / self.__settings.detdistance)
        return thetax, thetay, thetatotal

    def __pixel2q(self, xdata, ydata, xy=True):
        """ converts coordinates from pixel positions to q-space coordinates

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :param xy: flag
        :type xy: :obj:`bool`
        :returns: q_x, q_y, q_total
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        qx = None
        qy = None
        q = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            thetax, thetay, thetatotal = self.__pixel2theta(
                xdata, ydata, xy)
            wavelength = 12398.4193/self.__settings.energy
            if xy:
                qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
                qy = 4 * math.pi / wavelength * math.sin(thetay/2.)
            q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qy, q

    def __tipmessage(self):
        """ provides geometry messate

        :returns: geometry text
        :rtype: :obj:`unicode`
        """

        return u"geometry:\n" \
            u"  center = (%s, %s) pixels\n" \
            u"  pixel_size = (%s, %s) \u00B5m\n" \
            u"  detector_distance = %s mm\n" \
            u"  energy = %s eV" % (
                self.__settings.centerx,
                self.__settings.centery,
                self.__settings.pixelsizex,
                self.__settings.pixelsizey,
                self.__settings.detdistance,
                self.__settings.energy
            )

    @QtCore.pyqtSlot()
    def _setPolarRange(self):
        """ launches range widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = rangeDialog.RangeDialog()
        cnfdlg.polstart = self.__polstart
        cnfdlg.polend = self.__polend
        cnfdlg.polsize = self.__polsize
        cnfdlg.radqstart = self.__radqstart
        cnfdlg.radqend = self.__radqend
        cnfdlg.radqsize = self.__radqsize
        cnfdlg.radthstart = self.__radthstart
        cnfdlg.radthend = self.__radthend
        cnfdlg.radthsize = self.__radthsize
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__polstart = cnfdlg.polstart
            self.__polend = cnfdlg.polend
            self.__polsize = cnfdlg.polsize
            self.__radthstart = cnfdlg.radthstart
            self.__radthend = cnfdlg.radthend
            self.__radthsize = cnfdlg.radthsize
            self.__radqstart = cnfdlg.radqstart
            self.__radqend = cnfdlg.radqend
            self.__radqsize = cnfdlg.radqsize
            self.__rangechanged = True
            self.updateRangeTip()
            self._setPlotIndex(self.__plotindex)
            if self.__plotindex:
                self._mainwidget.emitReplotImage()

    @QtCore.pyqtSlot()
    def _setGeometry(self):
        """ launches geometry widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = geometryDialog.GeometryDialog()
        cnfdlg.centerx = self.__settings.centerx
        cnfdlg.centery = self.__settings.centery
        cnfdlg.energy = self.__settings.energy
        cnfdlg.pixelsizex = self.__settings.pixelsizex
        cnfdlg.pixelsizey = self.__settings.pixelsizey
        cnfdlg.detdistance = self.__settings.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__settings.centerx = cnfdlg.centerx
            self.__settings.centery = cnfdlg.centery
            self.__settings.energy = cnfdlg.energy
            self.__settings.pixelsizex = cnfdlg.pixelsizex
            self.__settings.pixelsizey = cnfdlg.pixelsizey
            self.__settings.detdistance = cnfdlg.detdistance
            self._mainwidget.writeAttribute(
                "BeamCenterX", float(self.__settings.centerx))
            self._mainwidget.writeAttribute(
                "BeamCenterY", float(self.__settings.centery))
            self._mainwidget.writeAttribute(
                "Energy", float(self.__settings.energy))
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)
            if self.__plotindex:
                self._mainwidget.emitReplotImage()

    @QtCore.pyqtSlot(int)
    def _setGSpaceIndex(self, gindex):
        """ set gspace index

        :param gspace: g-space index, i.e. angle or q-space
        :type gspace: :obj:`int`
        """
        self.__gspaceindex = gindex

    @QtCore.pyqtSlot(int)
    def _setPlotIndex(self, pindex=None):
        """ set gspace index

        :param gspace: g-space index,
        :         i.e. 0: Cartesian, 1: polar-th, 2: polar-q
        :type gspace: :obj:`int`
        """
        if pindex:
            while not self.__calculateRadMax(pindex):
                pass
            self.parameters.centerlines = False
            self.parameters.polarscale = True
            if pindex == 1:
                rscale = 180. / math.pi * self.__radmax
                rstart = self.__radthstart \
                    if self.__radthstart is not None else 0
            else:
                rscale = self.__radmax
                rstart = self.__radqstart \
                    if self.__radqstart is not None else 0
            pstart = self.__polstart if self.__polstart is not None else 0
            pscale = self.__polmax
            self._mainwidget.setPolarScale([rstart, pstart], [rscale, pscale])
            if not self.__plotindex:
                self.__oldlocked = self._mainwidget.setAspectLocked(False)
        else:
            if self.__oldlocked is not None:
                self._mainwidget.setAspectLocked(self.__oldlocked)
            self.parameters.centerlines = True
            self.parameters.polarscale = False
        if pindex is not None:
            self.__plotindex = pindex
            if self.__ui.plotComboBox.currentIndex != pindex:
                self.__ui.plotComboBox.setCurrentIndex(pindex)
        self._mainwidget.updateinfowidgets(self.parameters)

        self._mainwidget.emitReplotImage()

    @QtCore.pyqtSlot()
    def updateGeometryTip(self):
        """ update geometry tips
        """
        message = self.__tipmessage()
        self._mainwidget.updateDisplayedTextTip(
            "coordinate info display for the mouse pointer\n%s"
            % message)
        self.__ui.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.__ui.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)
        self.__ui.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)

    @QtCore.pyqtSlot()
    def updateRangeTip(self):
        """ update geometry tips
        """
        self.__ui.rangePushButton.setToolTip(
            u"Polar: [%s, %s] deg, size=%s\n"
            u"th_tot: [%s, %s] deg, size=%s\n"
            u"q: [%s, %s] 1/\u212B, size=%s" % (
                self.__polstart if self.__polstart is not None else "0",
                self.__polend if self.__polend is not None else "360",
                self.__polsize if self.__polsize is not None else "max",
                self.__radthstart if self.__radthstart is not None else "0",
                self.__radthend if self.__radthend is not None else "thmax",
                self.__radthsize if self.__radthsize is not None else "max",
                self.__radqstart if self.__radqstart is not None else "0",
                self.__radqend if self.__radqend is not None else "qmax",
                self.__radqsize if self.__radqsize is not None else "max")
        )


class DiffractogramToolWidget(ToolBaseWidget):
    """ diffractogram tool widget
    """

    #: (:obj:`str`) tool name
    name = "Diffractogram"
    #: (:obj:`str`) tool name alias
    alias = "diffractogram"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYFAI",)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`int`) unit index
        #               ->  0: q_nm^-1, 1: q_A-1, 2: 2th_deg, 3: 2th_rad
        self.__unitindex = 0
        self.__units = ["q_nm^-1", "q_A^-1", "2th_deg", "2th_rad", "r_mm"]

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _diffractogramformclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) old lock value
        self.__oldlocked = None

        #: ((:obj:`bool`) show diffractogram status
        self.__showdiff = False

        #: ([:obj:`float`, :obj:`float`] )
        #          range positions of radial in current units
        self.__radrange = None
        #: (:obj:`float`) start position of radial in deg
        self.__radstart = None
        #: (:obj:`float`) end position of radial in deg
        self.__radend = None
        #: (:obj:`int`) start position of azimuth angle in deg
        self.__azstart = None
        #: (:obj:`float`) end position of azimuth angle in deg
        self.__azend = None
        #: ([:obj:`float`, :obj:`float`] ) range positions of azimuth in deg
        self.__azrange = None

        #: (:obj:`float`) range changed flag
        self.__rangechanged = True

        #: (:class:`pyFAI.azimuthalIntegrator.AzimuthalIntegrator`)
        #       azimuthal integrator
        self.__ai = None

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot freezed
        self.__freezed = []

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot
        self.__curves = []
        #: (:obj:`int`) current plot number
        self.__nrplots = 0

        # self.parameters.lines = True
        #: (:obj:`str`) infolineedit text
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""
        self.parameters.bottomplot = True
        self.parameters.centerlines = True
        self.parameters.polarscale = False
        self.parameters.regions = True
        # self.parameters.rightplot = True

        #: (`lavuelib.imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            # [self.__ui.angleqPushButton.clicked, self._setGeometry],
            [self.__ui.rangePushButton.clicked, self._setPolarRange],
            [self.__ui.showPushButton.clicked, self._showhideDiff],
            [self.__ui.nextPushButton.clicked, self._plotDiff],
            [self.__ui.calibrationPushButton.clicked, self._loadCalibration],
            [self.__ui.unitComboBox.currentIndexChanged,
             self._setUnitIndex],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            # [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def afterplot(self):
        """ command after plot
        """
        if self.__showdiff:
            self._plotDiff()

    def activate(self):
        """ activates tool widget
        """
        self.__oldlocked = None
        # self.updateGeometryTip()
        self.updateRangeTip()
        self._mainwidget.updateCenter(
            self.__settings.centerx, self.__settings.centery)
        self.__updateButtons()
        if not self.__curves:
            self.__curves.append(self._mainwidget.onedbottomplot(True))
            self.__nrplots = 1
        for curve in self.__curves:
            curve.show()
            curve.setVisible(True)
        # self._updateAllCuts(self.__allcuts)

        # if self.__settings.calibrationfilename:
        #     self._loadCalibration(
        #         self.__settings.calibrationfilename)
        if self.__ai:
            self._plotDiff()
        self._mainwidget.bottomplotShowMenu(True, True)

    def deactivate(self):
        """ deactivates tool widget
        """
        self._mainwidget.bottomplotShowMenu()
        for curve in self.__curves:
            curve.hide()
            curve.setVisible(False)
            self._mainwidget.removebottomplot(curve)
        self.__curves = []
        # for freezed in self.__freezed:
        #     freezed.hide()
        #     freezed.setVisible(False)
        #     self._mainwidget.removebottomplot(freezed)
        # self.__freezed = []

    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """

    @QtCore.pyqtSlot(float, float)
    def _updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        txdata = None
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                xdata, ydata, useraxes=False)
            if txdata is not None:
                xdata = txdata
                ydata = tydata
        self.__settings.centerx = float(xdata)
        self.__settings.centery = float(ydata)
        if self.__ai is not None:
            # print("center: %s %s" % (xdata, ydata))
            # self.__ai.set_poni1(
            #     self.__settings.centery * self.__settings.pixelsizex
            # / 1000000.)
            # self.__ai.set_poni2(
            #     self.__settings.centerx * self.__settings.pixelsizey
            # / 1000000.)
            # aic = self.__ai.get_config()
            aif = self.__ai.getFit2D()
            # print(self.__ai)
            self.__ai.setFit2D(aif["directDist"],
                               self.__settings.centerx,
                               self.__settings.centery,
                               aif["tilt"],
                               aif["tiltPlanRotation"])
            # print(self.__ai)
        self._mainwidget.writeAttribute("BeamCenterX", float(xdata))
        self._mainwidget.writeAttribute("BeamCenterY", float(ydata))
        self._message()
        self._plotDiff()
        self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def _loadCalibration(self, fileName=None):
        """ load calibration file
        """
        if fileName is None:
            fileDialog = QtGui.QFileDialog()
            fileout = fileDialog.getOpenFileName(
                self._mainwidget, 'Open calibration file',
                self.__settings.calibrationfilename or '/ramdisk/',
                "PONI (*.poni);;All files (*)"
            )
            if isinstance(fileout, tuple):
                fileName = str(fileout[0])
            else:
                fileName = str(fileout)
        if fileName:
            try:
                self.__ai = pyFAI.load(fileName)
                # print(str(self.__ai))
                self.__settings.calibrationfilename = fileName
                self.__writedetsettings()
                self._mainwidget.updateCenter(
                    self.__settings.centerx, self.__settings.centery)
            except Exception as e:
                # print(str(e))
                logger.warning(str(e))
                self.__ai = None
            self.__updateButtons(self.__ai is not None)

    def __writedetsettings(self):
        """ write detector settings from ai object
        """
        aic = self.__ai.get_config()
        self.__settings.detponi1 = aic["poni1"]
        self.__settings.detponi2 = aic["poni2"]
        self.__settings.detrot1 = aic["rot1"]
        self.__settings.detrot2 = aic["rot2"]
        self.__settings.detrot3 = aic["rot3"]
        self.__settings.pixelsizex = self.__settings.distance2um(
            (self.__ai.get_pixel2(), "m"))
        self.__settings.pixelsizey = self.__settings.distance2um(
            (self.__ai.get_pixel1(), "m"))
        self.__settings.detdistance = self.__settings.distance2mm(
            (aic["dist"], "m"))
        self.__settings.energy = self.__settings.length2ev(
            (float(aic["wavelength"]), "m"))
        aif = self.__ai.getFit2D()
        self.__settings.centerx = float(aif["centerX"])
        self.__settings.centery = float(aif["centerY"])
        self._mainwidget.writeAttribute("BeamCenterX",
                                        float(self.__settings.centerx))
        self._mainwidget.writeAttribute("BeamCenterY",
                                        float(self.__settings.centery))
        self._mainwidget.writeAttribute(
            "Energy", float(self.__settings.energy))
        self._mainwidget.writeAttribute(
            "DetectorDistance",
            float(self.__settings.detdistance))

    def __updateButtons(self, status=None):
        """ update buttons

        :param status: show button flag
        :type status: :obj:`bool`
        """
        if status is None:
            status = self.__ai is not None
        self.__ui.showPushButton.setEnabled(status)
        self.__ui.nextPushButton.setEnabled(status)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides geometry message
        """
        message = ""
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                x, y, useraxes=False)
            if txdata is not None:
                x = txdata
                y = tydata
        ilabel = self._mainwidget.scalingLabel()
        chi = None
        if self.__ai is not None:
            chi = self.__ai.chi(
                np.array([y - 0.5]), np.array([x - 0.5]))
            if len(chi):
                chi = chi[0]
        if self.__unitindex in [2, 3]:
            tth = None
            if self.__ai is not None:
                tth = self.__ai.tth(
                    np.array([y - 0.5]), np.array([x - 0.5])),
                if len(tth):
                    tth = tth[0]
            if tth is not None and chi is not None:
                unit = "rad"
                if self.__unitindex == 2:
                    unit = "deg"
                    chi = chi * 180./math.pi
                    tth = tth * 180./math.pi
                message = "x, y = [%s, %s], tth = %f %s, chi = %f %s," \
                          " %s = %.2f" \
                          % (x, y, tth, unit,
                             chi, unit,
                             ilabel, intensity)
            else:
                message = "x, y = [%s, %s], %s = %.2f" % (
                    x, y, ilabel, intensity)
        elif self.__unitindex in [0, 1]:
            qa = None
            if self.__ai is not None:
                qa = self.__ai.qFunction(
                    np.array([y - 0.5]), np.array([x - 0.5])),
                if len(qa):
                    qa = qa[0]
            if qa is not None and chi is not None:
                unit = u"1/\u212B"
                chi = chi * 180./math.pi
                if self.__unitindex == 0:
                    unit = "1/nm"
                if self.__unitindex == 1:
                    qa = qa / 10.
                message = "x, y = [%s, %s], q = %f %s, chi = %f %s," \
                          " %s = %.2f" \
                          % (x, y, qa, unit,
                             chi, "deg",
                             ilabel, intensity)
            else:
                message = "x, y = [%s, %s], %s = %.2f" % (
                    x, y, ilabel, intensity)
        elif self.__unitindex in [4]:
            ra = None
            if self.__ai is not None:
                ra = self.__ai.rFunction(
                    np.array([y - 0.5]), np.array([x - 0.5])),
                if len(ra):
                    ra = ra[0] * 1000.
            if ra is not None and chi is not None:
                chi = chi * 180./math.pi
                message = "x, y = [%s, %s], r = %f %s, chi = %f %s," \
                          " %s = %.2f" \
                          % (x, y, ra, "mm",
                             chi, "deg",
                             ilabel, intensity)
            else:
                message = "x, y = [%s, %s], %s = %.2f" % (
                    x, y, ilabel, intensity)
        self._mainwidget.setDisplayedText(message)

    # def __tipmessage(self):
    #     """ provides geometry messate

    #     :returns: geometry text
    #     :rtype: :obj:`unicode`
    #     """

    #     return u"geometry:\n" \
    #         u"  center = (%s, %s) pixels\n" \
    #         u"  pixel_size = (%s, %s) \u00B5m\n" \
    #         u"  detector_distance = %s mm\n" \
    #         u"  energy = %s eV" % (
    #             self.__settings.centerx,
    #             self.__settings.centery,
    #             self.__settings.pixelsizex,
    #             self.__settings.pixelsizey,
    #             self.__settings.detdistance,
    #             self.__settings.energy
    #         )

    @QtCore.pyqtSlot()
    def _showhideDiff(self):
        """ show or hide diffractogram
        """
        if not self.__showdiff:
            self.__showdiff = True
            self.__ui.showPushButton.setText("Stop")
            self._plotDiff()
        else:
            self.__showdiff = False
            self.__ui.showPushButton.setText("Show")

    @QtCore.pyqtSlot()
    def _plotDiff(self):
        """ plot diffractogram
        """
        if self.__ai is not None:
            if self.__nrplots > 1:
                for i in range(1, len(self.__curves)):
                    self.__curves[i].setVisible(False)
                    self.__curves[i].hide()
                self.__nrplots = 1
            if self._mainwidget.currentTool() == self.name:
                dts = self._mainwidget.rawData()
                # print(dts)
                # self.__curves[0].setPen(_pg.mkColor('r'))
                if dts is not None:
                    try:
                        trans = self._mainwidget.transformations()[0]
                        csa = self.__settings.correctsolidangle
                        unit = self.__units[self.__unitindex]
                        dts = dts if trans else dts.T
                        mask = None
                        if dts.dtype.kind == 'f' and np.isnan(dts.min()):
                            mask = np.isnan(dts)
                            dts = np.array(dts)
                            dts[mask] = 0.
                            if mask is not None:
                                mask = mask.astype("int")
                        if self.__settings.showhighvaluemask and \
                           self._mainwidget.maskValue() is not None and \
                           self._mainwidget.maskValueIndices() is not None:
                            if mask is None:
                                mask = np.zeros(dts.shape)
                            mask[self._mainwidget.maskValueIndices().T] = 1
                        if self.__settings.showmask and \
                           self._mainwidget.applyMask() and \
                           self._mainwidget.maskIndices() is not None:
                            if mask is None:
                                mask = np.zeros(dts.shape)
                            mask[self._mainwidget.maskIndices().T] = 1
                        res = self.__ai.integrate1d(
                            dts,
                            self.__settings.diffnpt,
                            correctSolidAngle=csa,
                            radial_range=self.__radrange,
                            azimuth_range=self.__azrange,
                            unit=unit, mask=mask)
                        # print(res)
                        x = res[0]
                        y = res[1]
                        self.__curves[0].setData(x=x, y=y)
                    except Exception as e:
                        # print(str(e))
                        logger.warning(str(e))
                        x = []
                        y = []
                        self.__curves[0].setData(x=x, y=y)
                    self.__curves[0].setVisible(True)
                else:
                    self.__curves[0].setVisible(False)

    @QtCore.pyqtSlot()
    def _setPolarRange(self):
        """ launches range widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = diffRangeDialog.DiffRangeDialog()
        cnfdlg.azstart = self.__azstart
        cnfdlg.azend = self.__azend
        cnfdlg.radstart = self.__radstart
        cnfdlg.radend = self.__radend
        cnfdlg.radunitindex = 2
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__azstart = cnfdlg.azstart
            self.__azend = cnfdlg.azend
            if self.__azend is None and self.__azstart is None:
                self.__azrange = None
            elif self.__azend is not None or self.__azstart is not None:
                if self.__azstart is None:
                    self.__azstart = 0
                if self.__azend is None:
                    self.__azend = 360
                self.__azrange = [self.__azstart, self.__azend]
            self.__radstart = cnfdlg.radstart
            self.__radend = cnfdlg.radend
            if self.__radend is not None or self.__radstart is not None:
                if self.__radstart is None:
                    self.__radstart = 0
                if self.__radend is None:
                    self.__radend = 90
            self.__updaterad()
            self.__rangechanged = True
            self.updateRangeTip()
            if self.__azrange and self.__radrange:
                self._mainwidget.updateRegions(
                    1, [[self.__radstart, self.__azstart,
                         self.__radstart, self.__azend,
                         self.__radend, self.__azend,
                         self.__radend, self.__azstart]])
            else:
                self._mainwidget.updateRegions(
                    1, [[0, 0]])
            self._plotDiff()

    def __updaterad(self):
        """update radial range in deg
        """

        if self.__radend is None or self.__radstart is None:
            self.__radrange = None
        else:
            if self.__unitindex == 2:
                self.__radrange = [self.__radstart, self.__radend]
            else:
                rs = self.__radstart * math.pi / 180.
                re = self.__radend * math.pi / 180.
                if self.__unitindex < 2:
                    wavelength = 12398.4193/self.__settings.energy
                    fac = 4 * math.pi / wavelength
                    qs = fac * math.sin(rs/2.)
                    qe = fac * math.sin(re/2.)
                    if self.__unitindex == 0:
                        qs = qs * 10.
                        qe = qe * 10.
                    self.__radrange = [qs, qe]
                elif self.__unitindex == 3:
                    self.__radrange = [rs, re]
                elif self.__unitindex == 4:
                    rs = math.tan(rs) * self.__settings.detdistance
                    re = math.tan(re) * self.__settings.detdistance
                    self.__radrange = [rs, re]

    @QtCore.pyqtSlot(int)
    def _setUnitIndex(self, uindex):
        """ set unit index

        :param gspace: unit index, i.e. q_nm^-1, q_A^-1, 2th_deg, 2th_rad
        :type gspace: :obj:`int`
        """
        self.__unitindex = uindex
        self.__updaterad()
        self._plotDiff()

    @QtCore.pyqtSlot()
    def updateRangeTip(self):
        """ update geometry tips
        """
        self.__ui.rangePushButton.setToolTip(
            u"radial range: [%s, %s] deg \n"
            u"azimuth range: [%s, %s] deg\n" % (
                self.__radstart if self.__radstart is not None else "0",
                self.__radend if self.__radend is not None else "90",
                self.__azstart if self.__azstart is not None else "0",
                self.__azend if self.__azend is not None else "360")
        )


class MaximaToolWidget(ToolBaseWidget):
    """ angle/q tool widget
    """

    #: (:obj:`str`) tool name
    name = "Maxima"
    #: (:obj:`str`) tool name alias
    alias = "maxima"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`int`) geometry space index -> 0: angle, 1 q-space
        self.__gspaceindex = 0

        #: (:obj:`int`) plot index -> 0: Cartesian, 1 polar-th, 2 polar-q
        self.__plotindex = 0

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _maximaformclass()
        self.__ui.setupUi(self)

        # self.parameters.lines = True
        #: (:obj:`str`) infolineedit text
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""
        self.parameters.centerlines = True
        self.parameters.polarscale = False
        self.parameters.maxima = True
        # self.parameters.rightplot = True

        #: (`lavuelib..imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`float`) radial coordinate factor
        self.__radmax = 1.

        #: (:obj:`float`) polar coordinate factor
        self.__polmax = 1.

        #: (:obj:`bool`) reploting flag
        self.__reploting = False

        #: (:obj:`bool`) reploting flag
        self.__updating = False

        #: (:obj:`list`) last combo items
        self.__lastcomboitems = []

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.angleqPushButton.clicked, self._setGeometry],
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._setGSpaceIndex],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self.__ui.maximaComboBox.currentIndexChanged, self._replot],
            [self.__ui.numberSpinBox.valueChanged, self._replot],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def activate(self):
        """ activates tool widget
        """
        self.updateGeometryTip()
        self._mainwidget.updateCenter(
            self.__settings.centerx, self.__settings.centery)

    def deactivate(self):
        """ deactivates tool widget
        """

    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """
        if rawarray is not None and rawarray.any():
            nr = self.__ui.numberSpinBox.value()
            nr = min(nr, rawarray.size)
            if nr > 0:
                offset = [0.5, 0.5]
                if self.__settings.nanmask:
                    if rawarray.dtype.kind == 'f' and \
                       np.isnan(rawarray.min()):
                        rawarray = np.nan_to_num(rawarray)
                fidxs = np.argsort(rawarray, axis=None)[-nr:]
                aidxs = [np.unravel_index(idx, rawarray.shape)
                         for idx in fidxs]
                naidxs = aidxs
                rwe = self._mainwidget.rangeWindowEnabled()
                if rwe:
                    x, y, s1, s2 = self._mainwidget.scale(
                        useraxes=False, noNone=True)
                    naidxs = [(int(i * s1 + x), int(j * s2 + y))
                              for i, j in aidxs]
                    offset = [offset[0] * s1, offset[1] * s2]
                maxidxs = [[naidxs[n][0], naidxs[n][1], rawarray[i, j]]
                           for n, (i, j) in enumerate(aidxs)]
                current = self.__updatemaxima(maxidxs)
                if current >= 0:
                    aidxs.append(aidxs.pop(len(naidxs) - current - 1))
                self._mainwidget.setMaximaPos(naidxs, offset)
            else:
                self.__updatemaxima([])
                self._mainwidget.setMaximaPos([])
        self.__reploting = False

    def __updatemaxima(self, maxidxs):
        """ updates maxima in the combobox

        :param maxidxs: list with [[xn,yn, maxn], ... [x1,y1, max1]]
        :type maxidxs:
        """
        self.__updating = True
        combo = self.__ui.maximaComboBox
        idx = combo.currentIndex()
        if len(maxidxs) < idx:
            idx = len(maxidxs)
        if len(maxidxs) and idx < 0:
            idx = 0

        trans = self._mainwidget.transformations()[0]
        if trans:
            comboitems = ["%s: %s at (%s, %s)" % (i + 1, vl[2], vl[1], vl[0])
                          for i, vl in enumerate(reversed(maxidxs))]
        else:
            comboitems = ["%s: %s at (%s, %s)" % (i + 1, vl[2], vl[0], vl[1])
                          for i, vl in enumerate(reversed(maxidxs))]
        if self.__lastcomboitems != comboitems:
            self.__lastcomboitems != comboitems
            combo.clear()
            # self.__reploting = True
            combo.addItems(comboitems)
            combo.setCurrentIndex(idx)
        self.__updating = False
        return idx

    @QtCore.pyqtSlot(float, float)
    def _updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        txdata = None
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                xdata, ydata, useraxes=False)
            if txdata is not None:
                xdata = txdata
                ydata = tydata
        self.__settings.centerx = float(xdata)
        self.__settings.centery = float(ydata)
        self._mainwidget.writeAttribute("BeamCenterX", float(xdata))
        self._mainwidget.writeAttribute("BeamCenterY", float(ydata))
        self._message()
        self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def _replot(self):
        if not self.__reploting and not self.__updating:
            self.__reploting = True
            self._mainwidget.emitReplotImage(False)

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides geometry message
        """
        message = ""
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        txdata = None
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                x, y, useraxes=False)
        if txdata is not None:
            x, y = txdata, tydata
        ilabel = self._mainwidget.scalingLabel()
        if self.__gspaceindex == 0:
            thetax, thetay, thetatotal = self.__pixel2theta(x, y)
            if thetax is not None:
                message = "th_x = %f deg, th_y = %f deg," \
                          " th_tot = %f deg, %s = %.2f" \
                          % (thetax * 180 / math.pi,
                             thetay * 180 / math.pi,
                             thetatotal * 180 / math.pi,
                             ilabel, intensity)
        elif self.__gspaceindex == 1:
            qx, qy, q = self.__pixel2q(x, y)
            if qx is not None:
                message = u"q_x = %f 1/\u212B, q_y = %f 1/\u212B, " \
                          u"q = %f 1/\u212B, %s = %.2f" \
                          % (qx, qy, q, ilabel, intensity)
        else:
            message = "x = %.2f, y = %.2f, %s = %.2f" % (
                x, y, ilabel, intensity)
        self._mainwidget.setDisplayedText(message)

    def __pixel2theta(self, xdata, ydata, xy=True):
        """ converts coordinates from pixel positions to theta angles

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :param xy: flag
        :type xy: :obj:`bool`
        :returns: x-theta, y-theta, total-theta
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        thetax = None
        thetay = None
        thetatotal = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            xcentered = xdata - self.__settings.centerx
            ycentered = ydata - self.__settings.centery
            if xy:
                thetax = math.atan(
                    xcentered * self.__settings.pixelsizex / 1000.
                    / self.__settings.detdistance)
                thetay = math.atan(
                    ycentered * self.__settings.pixelsizey / 1000.
                    / self.__settings.detdistance)
            r = math.sqrt(
                (xcentered * self.__settings.pixelsizex / 1000.) ** 2
                + (ycentered * self.__settings.pixelsizey / 1000.) ** 2)
            thetatotal = math.atan(
                r / self.__settings.detdistance)
        return thetax, thetay, thetatotal

    def __pixel2q(self, xdata, ydata, xy=True):
        """ converts coordinates from pixel positions to q-space coordinates

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :param xy: flag
        :type xy: :obj:`bool`
        :returns: q_x, q_y, q_total
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        qx = None
        qy = None
        q = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            thetax, thetay, thetatotal = self.__pixel2theta(
                xdata, ydata, xy)
            wavelength = 12398.4193/self.__settings.energy
            if xy:
                qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
                qy = 4 * math.pi / wavelength * math.sin(thetay/2.)
            q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qy, q

    def __tipmessage(self):
        """ provides geometry messate

        :returns: geometry text
        :rtype: :obj:`unicode`
        """

        return u"geometry:\n" \
            u"  center = (%s, %s) pixels\n" \
            u"  pixel_size = (%s, %s) \u00B5m\n" \
            u"  detector_distance = %s mm\n" \
            u"  energy = %s eV" % (
                self.__settings.centerx,
                self.__settings.centery,
                self.__settings.pixelsizex,
                self.__settings.pixelsizey,
                self.__settings.detdistance,
                self.__settings.energy
            )

    @QtCore.pyqtSlot()
    def _setGeometry(self):
        """ launches geometry widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = geometryDialog.GeometryDialog()
        cnfdlg.centerx = self.__settings.centerx
        cnfdlg.centery = self.__settings.centery
        cnfdlg.energy = self.__settings.energy
        cnfdlg.pixelsizex = self.__settings.pixelsizex
        cnfdlg.pixelsizey = self.__settings.pixelsizey
        cnfdlg.detdistance = self.__settings.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__settings.centerx = cnfdlg.centerx
            self.__settings.centery = cnfdlg.centery
            self.__settings.energy = cnfdlg.energy
            self.__settings.pixelsizex = cnfdlg.pixelsizex
            self.__settings.pixelsizey = cnfdlg.pixelsizey
            self.__settings.detdistance = cnfdlg.detdistance
            self._mainwidget.writeAttribute(
                "BeamCenterX", float(self.__settings.centerx))
            self._mainwidget.writeAttribute(
                "BeamCenterY", float(self.__settings.centery))
            self._mainwidget.writeAttribute(
                "Energy", float(self.__settings.energy))
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)
            if self.__plotindex:
                self._mainwidget.emitReplotImage()

    @QtCore.pyqtSlot(int)
    def _setGSpaceIndex(self, gindex):
        """ set gspace index

        :param gspace: g-space index, i.e. angle or q-space
        :type gspace: :obj:`int`
        """
        self.__gspaceindex = gindex

    @QtCore.pyqtSlot()
    def updateGeometryTip(self):
        """ update geometry tips
        """
        message = self.__tipmessage()
        self._mainwidget.updateDisplayedTextTip(
            "coordinate info display for the mouse pointer\n%s"
            % message)
        self.__ui.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.__ui.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)


class QROIProjToolWidget(ToolBaseWidget):
    """ angle/q +roi + projections tool widget
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply ROI pressed signal
    applyROIPressed = QtCore.pyqtSignal(str, int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) fetch ROI pressed signal
    fetchROIPressed = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) roi info Changed signal
    roiInfoChanged = QtCore.pyqtSignal(str)

    #: (:obj:`str`) tool name
    name = "Q+ROI+Proj"
    #: (:obj:`str`) tool name alias
    alias = "q+roi+proj"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        ToolBaseWidget.__init__(self, parent)

        #: (:obj:`int`) geometry space index -> 0: angle, 1 q-space
        self.__gspaceindex = 0

        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _qroiprojformclass()
        self.__ui.setupUi(self)

        #: (:class:`pyqtgraph.PlotDataItem`) 1D bottom plot
        self.__bottomplot = None
        #: (:class:`pyqtgraph.PlotDataItem`) 1D bottom plot
        self.__rightplot = None
        #: (:obj:`int`) function index
        self.__funindex = 0

        #: (:obj:`slice`) selected rows
        self.__rows = None
        #: (:obj:`slice`) selected columns
        self.__columns = None
        #: (:obj:`slice`) selected rows
        self.__dsrows = None
        #: (:obj:`slice`) selected columns
        self.__dscolumns = None

        #: (:obj:`list`< :obj:`str`>) sardana aliases
        self.__aliases = []
        #: (:obj:`int`) ROI label length
        self.__textlength = 0

        self.parameters.bottomplot = True
        self.parameters.rightplot = True
        self.parameters.rois = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""
        self.parameters.centerlines = True

        #: (:class:`lavuelib.settings.Settings`:) configuration settings
        self.__settings = self._mainwidget.settings()

        self._updateApplyButton()
        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.applyROIPushButton.clicked, self._emitApplyROIPressed],
            [self.__ui.fetchROIPushButton.clicked, self._emitFetchROIPressed],
            [self.__ui.angleqPushButton.clicked, self._setGeometry],
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._setGSpaceIndex],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],

            [self.applyROIPressed, self._mainwidget.applyROIs],
            [self.fetchROIPressed, self._mainwidget.fetchROIs],
            [self.roiInfoChanged, self._mainwidget.updateDisplayedText],
            [self.__ui.labelROILineEdit.textChanged,
             self._updateApplyButton],
            [self.__ui.roiSpinBox.valueChanged, self._mainwidget.updateROIs],
            [self.__ui.roiSpinBox.valueChanged,
             self._mainwidget.writeDetectorROIsAttribute],
            [self.__ui.labelROILineEdit.textEdited,
             self._writeDetectorROIs],
            [self._mainwidget.roiLineEditChanged, self._updateApplyButton],
            [self._mainwidget.roiAliasesChanged, self.updateROILineEdit],
            [self._mainwidget.roiValueChanged, self.updateROIDisplayText],
            [self._mainwidget.roiNumberChanged, self.setROIsNumber],
            [self._mainwidget.sardanaEnabled, self.updateROIButton],
            [self._mainwidget.mouseImagePositionChanged, self._roimessage],

            [self.__ui.funComboBox.currentIndexChanged,
             self._setFunction],
            [self.__ui.rowsliceLineEdit.textChanged, self._updateRows],
            [self.__ui.columnsliceLineEdit.textChanged, self._updateColumns],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self._mainwidget.scalesChanged, self._updateColumns],
        ]

    def activate(self):
        """ activates tool widget
        """
        self.updateGeometryTip()
        self._mainwidget.updateCenter(
            self.__settings.centerx, self.__settings.centery)
        self._mainwidget.changeROIRegion()
        self.setROIsNumber(len(self._mainwidget.roiCoords()))
        self.__aliases = self._mainwidget.getElementNames("ExpChannelList")
        self.updateROILineEdit(self._mainwidget.roilabels)
        self.__updateCompleter()
        self.updateROIButton(self.__settings.sardana)

        if self.__bottomplot is None:
            self.__bottomplot = self._mainwidget.onedbarbottomplot()

        if self.__rightplot is None:
            self.__rightplot = self._mainwidget.onedbarrightplot()

        self.__bottomplot.show()
        self.__rightplot.show()
        self.__bottomplot.setVisible(True)
        self.__rightplot.setVisible(True)
        self._updateSlices()
        self._plotCurves()

    def deactivate(self):
        """ deactivates tool widget
        """
        self._mainwidget.roiCoordsChanged.emit()

        if self.__bottomplot is not None:
            self.__bottomplot.hide()
            self.__bottomplot.setVisible(False)
            self._mainwidget.removebottomplot(self.__bottomplot)
            self.__bottomplot = None
        if self.__rightplot is not None:
            self.__rightplot.hide()
            self.__rightplot.setVisible(False)
            self._mainwidget.removerightplot(self.__rightplot)
            self.__rightplot = None

    @QtCore.pyqtSlot()
    def _writeDetectorROIs(self):
        """ writes Detector rois and updates roi labels
        """
        self._mainwidget.roilabels = str(self.__ui.labelROILineEdit.text())
        self._mainwidget.writeDetectorROIsAttribute()

    def __updateslice(self, text, dx=None, ds=None):
        """ create slices from the text
        """
        rows = "ERROR"
        dsrows = "ERROR"
        if text:
            try:
                if ":" in text:
                    slices = text.split(":")
                    s0 = int(slices[0]) if slices[0].strip() else 0
                    s1 = int(slices[1]) if slices[1].strip() else None
                    if len(slices) > 2:
                        s2 = int(slices[2]) if slices[2].strip() else None
                        rows = slice(s0, s1, s2)
                        if dx is not None:
                            dsrows = slice((s0-dx)/ds, (s1-dx)/ds, s2/ds)
                        else:
                            dsrows = rows
                    else:
                        rows = slice(s0, s1)
                        if dx is not None:
                            dsrows = slice((s0-dx)/ds, (s1-dx)/ds)
                        else:
                            dsrows = rows
                else:
                    rows = int(text)
                    if dx is not None:
                        dsrows = int((rows - dx)/ds)
                    else:
                        dsrows = rows
            except Exception:
                pass
        else:
            rows = None
            dsrows = None
        return rows, dsrows

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateSlices(self):
        """ updates applied button"""
        rtext = str(self.__ui.rowsliceLineEdit.text()).strip()
        ctext = str(self.__ui.columnsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
            self.__rows, self.__dsrows = self.__updateslice(
                rtext, int(dy), int(ds2))
            self.__columns, self.__dscolumns = self.__updateslice(
                ctext, int(dx), int(ds1))
        else:
            self.__rows, self.__dsrows = self.__updateslice(rtext)
            self.__columns, self.__dscolumns = self.__updateslice(ctext)
        if self.__rows is None:
            self._mainwidget.updateHBounds(None, None)
        elif isinstance(self.__rows, int):
            self._mainwidget.updateHBounds(self.__rows, self.__rows + 1)
        elif isinstance(self.__rows, slice):
            self._mainwidget.updateHBounds(self.__rows.start, self.__rows.stop)
        if self.__columns is None:
            self._mainwidget.updateVBounds(None, None)
        elif isinstance(self.__columns, int):
            self._mainwidget.updateVBounds(self.__columns, self.__columns + 1)
        elif isinstance(self.__columns, slice):
            self._mainwidget.updateVBounds(
                self.__columns.start, self.__columns.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateRows(self):
        """ updates applied button"""
        rtext = str(self.__ui.rowsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
            self.__rows, self.__dsrows = self.__updateslice(
                rtext, int(dy), int(ds2))
        else:
            self.__rows, self.__dsrows = self.__updateslice(rtext)
        if self.__rows is None:
            self._mainwidget.updateHBounds(None, None)
        elif isinstance(self.__rows, int):
            self._mainwidget.updateHBounds(self.__rows, self.__rows + 1)
        elif isinstance(self.__rows, slice):
            self._mainwidget.updateHBounds(self.__rows.start, self.__rows.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateColumns(self):
        """ updates applied button"""
        text = str(self.__ui.columnsliceLineEdit.text()).strip()
        rwe = self._mainwidget.rangeWindowEnabled()
        if rwe:
            dx, dy, ds1, ds2 = self._mainwidget.scale(
                useraxes=False, noNone=True)
        if rwe:
            self.__columns, self.__dscolumns = self.__updateslice(
                text, int(dx), int(ds1))
        else:
            self.__columns, self.__dscolumns = self.__updateslice(text)
        if self.__columns is None:
            self._mainwidget.updateVBounds(None, None)
        elif isinstance(self.__columns, int):
            self._mainwidget.updateVBounds(self.__columns, self.__columns + 1)
        elif isinstance(self.__columns, slice):
            self._mainwidget.updateVBounds(
                self.__columns.start, self.__columns.stop)
        self._plotCurves()

    @QtCore.pyqtSlot(int)
    def _setFunction(self, findex):
        """ set sum or mean function

        :param findex: function index, i.e. 0:mean, 1:sum
        :type findex: :obj:`int`
        """
        self.__funindex = findex
        self._plotCurves()

    def afterplot(self):
        """ command after plot
        """
        self._plotCurves()

    @QtCore.pyqtSlot()
    def _plotCurves(self):
        """ plots the current image in 1d plots
        """
        if self._mainwidget.currentTool() == self.name:
            dts = self._mainwidget.rawData()
            if dts is not None:
                if self.__funindex:
                    npfun = np.nansum
                else:
                    npfun = np.nanmean

                if self.__dsrows == "ERROR":
                    sx = []
                elif self.__dsrows is not None:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            if isinstance(self.__dsrows, slice):
                                sx = npfun(dts[:, self.__dsrows], axis=1)
                            else:
                                sx = dts[:, self.__dsrows]
                    except Exception:
                        sx = []

                else:
                    with np.warnings.catch_warnings():
                        np.warnings.filterwarnings(
                            "ignore", r'Mean of empty slice')
                        sx = npfun(dts, axis=1)

                if self.__dscolumns == "ERROR":
                    sy = []
                if self.__dscolumns is not None:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            if isinstance(self.__dscolumns, slice):
                                sy = npfun(dts[self.__dscolumns, :], axis=0)
                            else:
                                sy = dts[self.__dscolumns, :]
                    except Exception:
                        sy = []
                else:
                    try:
                        with np.warnings.catch_warnings():
                            np.warnings.filterwarnings(
                                "ignore", r'Mean of empty slice')
                            sy = npfun(dts, axis=0)
                    except Exception:
                        sy = []

                rwe = self._mainwidget.rangeWindowEnabled()
                if rwe:
                    x, y, s1, s2 = self._mainwidget.scale(
                        useraxes=False, noNone=True)
                    if self._mainwidget.transformations()[3]:
                        x, y = y, x
                        s1, s2 = s2, s1
                    xx = list(
                        range(int(x), len(sx) * int(s1) + int(x), int(s1)))
                    yy = list(
                        range(int(y), len(sy) * int(s2) + int(y), int(s2)))
                    width = [s1] * len(sx)
                    height = [s1] * len(sy)
                else:
                    xx = list(range(len(sx)))
                    yy = list(range(len(sy)))
                    width = [1.0] * len(sx)
                    height = [1.0] * len(sy)
                self.__bottomplot.setOpts(
                    y0=[0]*len(sx), y1=sx, x=xx,
                    width=width)
                self.__bottomplot.drawPicture()
                self.__rightplot.setOpts(
                    x0=[0]*len(sy), x1=sy, y=yy,
                    height=height)
                self.__rightplot.drawPicture()

    def __updateCompleter(self):
        """ updates the labelROI help
        """
        text = str(self.__ui.labelROILineEdit.text())
        sttext = text.strip()
        sptext = sttext.split()
        stext = ""
        if text.endswith(" "):
            stext = sttext
        elif len(sptext) > 1:
            stext = " ".join(sptext[:-1])

        if stext:
            if self.__aliases:
                hints = ["%s %s" % (stext, al) for al in self.__aliases]
            else:
                hints = [stext]
        else:
            hints = self.__aliases or []
        completer = QtGui.QCompleter(hints, self)
        self.__ui.labelROILineEdit.setCompleter(completer)

    @QtCore.pyqtSlot()
    def _roimessage(self):
        """ provides roi message
        """
        message = ""
        current = self._mainwidget.currentROI()
        coords = self._mainwidget.roiCoords()
        if current > -1 and current < len(coords):
            message = "%s" % coords[current]
        self.__setDisplayedText(message)

    def __setDisplayedText(self, text=None):
        """ sets displayed info text and recalculates the current roi sum

        :param text: text to display
        :type text: :obj:`str`
        """
        sroiVal = ""
        if text is not None:
            self.__lasttext = text
        else:
            text = self.__lasttext
        if self.__settings.showallrois:
            currentroi = self._mainwidget.currentROI()
            roiVals = self._mainwidget.calcROIsums()
            if roiVals is not None:
                sroiVal = " / ".join(
                    [(("%g" % roiv) if roiv is not None else "?")
                     for roiv in roiVals])
        else:
            roiVal, currentroi = self._mainwidget.calcROIsum()
            if roiVal is not None:
                sroiVal = "%.4f" % roiVal
        if currentroi is not None:
            self.updateROIDisplayText(text, currentroi, sroiVal)
        else:
            self.__ui.roiinfoLineEdit.setText(text)

    @QtCore.pyqtSlot()
    def _emitApplyROIPressed(self):
        """ emits applyROIPressed signal"""

        text = str(self.__ui.labelROILineEdit.text())
        roispin = int(self.__ui.roiSpinBox.value())
        self.applyROIPressed.emit(text, roispin)

    @QtCore.pyqtSlot()
    def _emitFetchROIPressed(self):
        """ emits fetchROIPressed signal"""
        text = str(self.__ui.labelROILineEdit.text())
        self.fetchROIPressed.emit(text)

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot()
    def _updateApplyButton(self):
        """ updates applied button"""
        stext = str(self.__ui.labelROILineEdit.text())
        self._mainwidget.roilabels = stext
        currentlength = len(stext)
        if not stext.strip():
            self.__ui.applyROIPushButton.setEnabled(False)
            self.__updateCompleter()
        else:
            self.__ui.applyROIPushButton.setEnabled(True)
        if stext.endswith(" ") or currentlength < self.__textlength:
            self.__updateCompleter()
        self.__textlength = currentlength

    @QtCore.pyqtSlot(str)
    def updateROILineEdit(self, text):
        """ updates ROI line edit text

        :param text: text to update
        :type text: :obj:`str`
        """
        if not self.__ui.labelROILineEdit.hasFocus():
            self.__ui.labelROILineEdit.setText(text)
            self._updateApplyButton()

    @QtCore.pyqtSlot(bool)
    def updateROIButton(self, enabled):
        """ enables/disables ROI buttons

        :param enable: buttons enabled
        :type enable: :obj:`bool`
        """
        # self.__ui.applyROIPushButton.setEnabled(enabled)
        self.__ui.fetchROIPushButton.setEnabled(enabled)

    @QtCore.pyqtSlot(int)
    def updateApplyTips(self, rid):
        """ updates apply tips

        :param rid: current roi id
        :type rid: :obj:`int`
        """
        if rid < 0:
            self.__ui.applyROIPushButton.setToolTip(
                "remove ROI aliases from the Door environment"
                " as well as from Active MntGrp")
        else:
            self.__ui.applyROIPushButton.setToolTip(
                "add ROI aliases to the Door environment "
                "as well as to Active MntGrp")

    @QtCore.pyqtSlot(str, int, str)
    def updateROIDisplayText(self, text, currentroi, roiVal):
        """ updates ROI display text

        :param text: standard display text
        :type text: :obj:`str`
        :param currentroi: current roi label
        :type currentroi: :obj:`str`
        :param text: roi sum value
        :type text: :obj:`str`
        """

        roilabel = "roi [%s]" % (currentroi + 1)
        slabel = []

        rlabel = str(self.__ui.labelROILineEdit.text())
        if rlabel:
            slabel = re.split(';|,| |\n', rlabel)
            slabel = [lb for lb in slabel if lb]
        if slabel:
            roilabel = "%s [%s]" % (
                slabel[currentroi]
                if currentroi < len(slabel) else slabel[-1],
                (currentroi + 1)
            )
        if "/" in roiVal:
            self.__ui.roiinfoLineEdit.setText(
                "%s, %s; values = %s" % (text, roilabel, roiVal))
        else:
            self.__ui.roiinfoLineEdit.setText(
                "%s, %s = %s" % (text, roilabel, roiVal))

    @QtCore.pyqtSlot(int)
    def setROIsNumber(self, rid):
        """sets a number of rois

        :param rid: number of rois
        :type rid: :obj:`int`
        """
        self.__ui.roiSpinBox.setValue(rid)
        # self._mainwidget.writeDetectorROIsAttribute()

    @QtCore.pyqtSlot(float, float)
    def _updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        txdata = None
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                xdata, ydata, useraxes=False)
            if txdata is not None:
                xdata = txdata
                ydata = tydata
        self.__settings.centerx = float(xdata)
        self.__settings.centery = float(ydata)
        self._mainwidget.writeAttribute("BeamCenterX", float(xdata))
        self._mainwidget.writeAttribute("BeamCenterY", float(ydata))
        self._message()
        self.updateGeometryTip()

    @QtCore.pyqtSlot()
    def _message(self):
        """ provides geometry message
        """
        message = ""
        _, _, intensity, x, y = self._mainwidget.currentIntensity()
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        if self._mainwidget.rangeWindowEnabled():
            txdata, tydata = self._mainwidget.scaledxy(
                x, y, useraxes=False)
            if txdata is not None:
                x = txdata
                y = tydata
        ilabel = self._mainwidget.scalingLabel()
        if self.__gspaceindex == 0:
            thetax, thetay, thetatotal = self.__pixel2theta(x, y)
            if thetax is not None:
                message = "th_x = %f deg, th_y = %f deg," \
                          " th_tot = %f deg, %s = %.2f" \
                          % (thetax * 180 / math.pi,
                             thetay * 180 / math.pi,
                             thetatotal * 180 / math.pi,
                             ilabel, intensity)
        else:
            qx, qy, q = self.__pixel2q(x, y)
            if qx is not None:
                message = u"q_x = %f 1/\u212B, q_y = %f 1/\u212B, " \
                          u"q = %f 1/\u212B, %s = %.2f" \
                          % (qx, qy, q, ilabel, intensity)

        self._mainwidget.updateDisplayedText(message)

    def __pixel2theta(self, xdata, ydata):
        """ converts coordinates from pixel positions to theta angles

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :returns: x-theta, y-theta, total-theta
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        thetax = None
        thetay = None
        thetatotal = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            xcentered = xdata - self.__settings.centerx
            ycentered = ydata - self.__settings.centery
            thetax = math.atan(
                xcentered * self.__settings.pixelsizex / 1000.
                / self.__settings.detdistance)
            thetay = math.atan(
                ycentered * self.__settings.pixelsizey / 1000.
                / self.__settings.detdistance)
            r = math.sqrt(
                (xcentered * self.__settings.pixelsizex / 1000.) ** 2
                + (ycentered * self.__settings.pixelsizey / 1000.) ** 2)
            thetatotal = math.atan(
                r / self.__settings.detdistance)
        return thetax, thetay, thetatotal

    def __pixel2q(self, xdata, ydata):
        """ converts coordinates from pixel positions to q-space coordinates

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :returns: q_x, q_y, q_total
        :rtype: (:obj:`float`, :obj:`float`, :obj:`float`)
        """
        qx = None
        qy = None
        q = None
        if self.__settings.energy > 0 and self.__settings.detdistance > 0:
            thetax, thetay, thetatotal = self.__pixel2theta(
                xdata, ydata)
            wavelength = 12398.4193/self.__settings.energy
            qx = 4 * math.pi / wavelength * math.sin(thetax/2.)
            qy = 4 * math.pi / wavelength * math.sin(thetay/2.)
            q = 4 * math.pi / wavelength * math.sin(thetatotal/2.)
        return qx, qy, q

    def __tipmessage(self):
        """ provides geometry messate

        :returns: geometry text
        :rtype: :obj:`unicode`
        """

        return u"geometry:\n" \
            u"  center = (%s, %s) pixels\n" \
            u"  pixel_size = (%s, %s) \u00B5m\n" \
            u"  detector_distance = %s mm\n" \
            u"  energy = %s eV" % (
                self.__settings.centerx,
                self.__settings.centery,
                self.__settings.pixelsizex,
                self.__settings.pixelsizey,
                self.__settings.detdistance,
                self.__settings.energy
            )

    @QtCore.pyqtSlot()
    def _setGeometry(self):
        """ launches geometry widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = geometryDialog.GeometryDialog()
        cnfdlg.centerx = self.__settings.centerx
        cnfdlg.centery = self.__settings.centery
        cnfdlg.energy = self.__settings.energy
        cnfdlg.pixelsizex = self.__settings.pixelsizex
        cnfdlg.pixelsizey = self.__settings.pixelsizey
        cnfdlg.detdistance = self.__settings.detdistance
        cnfdlg.createGUI()
        if cnfdlg.exec_():
            self.__settings.centerx = cnfdlg.centerx
            self.__settings.centery = cnfdlg.centery
            self.__settings.energy = cnfdlg.energy
            self.__settings.pixelsizex = cnfdlg.pixelsizex
            self.__settings.pixelsizey = cnfdlg.pixelsizey
            self.__settings.detdistance = cnfdlg.detdistance
            self._mainwidget.writeAttribute(
                "BeamCenterX", float(self.__settings.centerx))
            self._mainwidget.writeAttribute(
                "BeamCenterY", float(self.__settings.centery))
            self._mainwidget.writeAttribute(
                "Energy", float(self.__settings.energy))
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)

    @QtCore.pyqtSlot(int)
    def _setGSpaceIndex(self, gindex):
        """ set gspace index

        :param gspace: g-space index, i.e. angle or q-space
        :type gspace: :obj:`int`
        """
        self.__gspaceindex = gindex

    @QtCore.pyqtSlot()
    def updateGeometryTip(self):
        """ update geometry tips
        """
        message = self.__tipmessage()
        self._mainwidget.updateDisplayedTextTip(
            "coordinate info display for the mouse pointer\n%s"
            % message)
        self.__ui.angleqPushButton.setToolTip(
            "Input physical parameters\n%s" % message)
        self.__ui.angleqComboBox.setToolTip(
            "Select the display space\n%s" % message)
        self.__ui.toolLabel.setToolTip(
            "coordinate info display for the mouse pointer\n%s" % message)


#: ( :obj:`dict` < :obj:`str`, any > ) tool widget properties
twproperties = []
for nm in __all__:
    if nm.endswith("ToolWidget"):
        cl = globals()[nm]
        twproperties.append(
            {
                'alias': cl.alias,
                'name': cl.name,
                'widget': nm,
                'requires': cl.requires,
            })
