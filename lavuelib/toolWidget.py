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
import time
import numpy as np
import scipy.optimize
import scipy.interpolate
import pyqtgraph as _pg
import logging
import random
import json
from pyqtgraph import QtCore, QtGui, functions
from enum import Enum

from . import geometryDialog
from . import rangeDialog
from . import diffRangeDialog
from . import takeMotorsDialog
from . import intervalsDialog
from . import motorWatchThread
from . import edDictDialog
from . import edListDialog
from . import commandThread
from .sardanaUtils import debugmethod

try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    #: (:obj:`bool`) tango imported
    TANGO = True
except ImportError:
    #: (:obj:`bool`) tango imported
    TANGO = False

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
        #: (:obj:`bool`) tool axes scale enabled
        self.toolscale = False
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

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return ""


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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
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
             self._mainwidget.emitTCC],
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

    def afterplot(self):
        """ command after plot
        """
        if self.__settings.sendresults:
            self.__sendresults()

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "crosshair_locker" in cnf.keys():
                crosshairlocker = cnf["crosshair_locker"]
                self.__ui.crosshairCheckBox.setChecked(crosshairlocker)
            pars = ["position", "scale",
                    "xtext", "ytext", "xunits", "yunits"]
            if any(par in cnf.keys() for par in pars):
                self._mainwidget.updateTicks(cnf)

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["crosshair_locker"] = self.__ui.crosshairCheckBox.isChecked()
        xpos, ypos, xsc, ysc = self._mainwidget.scale()
        cnf["xunits"], cnf["yunits"] = self._mainwidget.axesunits()
        cnf["xtext"], cnf["ytext"] = self._mainwidget.axestext()
        cnf["position"] = [xpos, ypos]
        cnf["scale"] = [xsc, ysc]
        return json.dumps(cnf)

    def __sendresults(self):
        """ send results to LavueController
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        scaling = self._mainwidget.scalingLabel()
        sx, sy = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        results = {"tool": self.alias}
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["pixel"] = [float(x), float(y)]
        results["intensity"] = float(intensity)
        results["scaled_coordiantes"] = [float(sx), float(sy)]
        results["coordiantes_units"] = [xunits, yunits]
        results["intensity_scaling"] = scaling
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))


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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

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

    def afterplot(self):
        """ command after plot
        """
        if self.__settings.sendresults:
            self.__sendresults()

    def __sendresults(self):
        """ send results to LavueController
        """
        x, y, intensity = self._mainwidget.currentIntensity()[:3]
        if isinstance(intensity, float) and np.isnan(intensity):
            intensity = 0
        scaling = self._mainwidget.scalingLabel()
        sx, sy = self._mainwidget.scaledxy(x, y)
        xunits, yunits = self._mainwidget.axesunits()
        if isinstance(intensity, np.ndarray):
            intensity = [0 if (isinstance(it, float) and np.isnan(it))
                         else float(it) for it in intensity]
        results = {"tool": self.alias}
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["pixel"] = [float(x), float(y)]
        results["intensity"] = intensity
        results["scaled_coordiantes"] = [float(sx), float(sy)]
        results["coordiantes_units"] = [xunits, yunits]
        results["intensity_scaling"] = scaling
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))


class MotorsToolWidget(ToolBaseWidget):
    """ motors tool widget
    """

    #: (:obj:`str`) tool name
    name = "MoveMotors"
    #: (:obj:`str`) tool name alias
    alias = "movemotors"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("TANGO",)

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
        #: (:class:`tango.DeviceProxy`) x-motor device
        self.__xmotordevice = None
        #: (:class:`tango.DeviceProxy`) y-motor device
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
            [self.__ui.xLineEdit.textChanged, self._mainwidget.emitTCC],
            [self.__ui.yLineEdit.textEdited, self._getFinal],
            [self.__ui.yLineEdit.textChanged, self._mainwidget.emitTCC],
        ]

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            pars = ["position", "scale",
                    "xtext", "ytext", "xunits", "yunits"]
            if any(par in cnf.keys() for par in pars):
                self._mainwidget.updateTicks(cnf)
            if "motors" in cnf.keys():
                try:
                    motorname = cnf["motors"][0]
                    motordevice = tango.DeviceProxy(motorname)
                    for attr in ["state", "position"]:
                        if not hasattr(motordevice, attr):
                            raise Exception("Missing %s" % attr)
                    self.__xmotorname = motorname
                    self.__xmotordevice = motordevice
                except Exception as e:
                    logger.warning(str(e))
                try:
                    motorname = cnf["motors"][1]
                    motordevice = tango.DeviceProxy(motorname)
                    for attr in ["state", "position"]:
                        if not hasattr(motordevice, attr):
                            raise Exception("Missing %s" % attr)
                    self.__ymotorname = motorname
                    self.__ymotordevice = motordevice
                except Exception as e:
                    logger.warning(str(e))
            if "x_position" in cnf.keys():
                try:
                    self.__ui.xLineEdit.setText(str(cnf["x_position"]))
                except Exception:
                    pass
            if "y_position" in cnf.keys():
                try:
                    self.__ui.yLineEdit.setText(str(cnf["y_position"]))
                except Exception:
                    pass
            if "move" in cnf.keys():
                if cnf["move"]:
                    if str(self.__ui.movePushButton.text()) == "Move":
                        self._moveStopMotors()
            if "stop" in cnf.keys():
                if cnf["stop"]:
                    if str(self.__ui.movePushButton.text()) == "Stop":
                        self._moveStopMotors()

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        xpos, ypos, xsc, ysc = self._mainwidget.scale()
        cnf["xunits"], cnf["yunits"] = self._mainwidget.axesunits()
        cnf["xtext"], cnf["ytext"] = self._mainwidget.axestext()
        cnf["position"] = [xpos, ypos]
        cnf["scale"] = [xsc, ysc]
        try:
            cnf["x_position"] = float(self.__ui.xLineEdit.text())
        except Exception:
            cnf["x_position"] = self.__ui.xLineEdit.text()
        try:
            cnf["y_position"] = float(self.__ui.yLineEdit.text())
        except Exception:
            cnf["y_position"] = self.__ui.yLineEdit.text()
        cnf["motors"] = [self.__xmotorname, self.__ymotorname]
        if str(self.__ui.movePushButton.text()) == "Move":
            cnf["motor_state"] = "ON"
        else:
            cnf["motor_state"] = "MOVING"

        return json.dumps(cnf)

    def activate(self):
        """ activates tool widget
        """
        if self.__xfinal is not None and self.__yfinal is not None:
            self._mainwidget.updatePositionMark(
                self.__xfinal, self.__yfinal, True)

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
        self._mainwidget.emitTCC()

    @QtCore.pyqtSlot()
    def _finished(self):
        """ stop motors
        """
        self.__stopMotors()
        self._mainwidget.emitTCC()

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
            self.__xfinal, self.__yfinal, True)

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
            self._mainwidget.emitTCC()
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
    requires = ("TANGO",)

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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

        # #: (:obj:`list` <str, str, str>)
        #        detector parameters (label, devicename, type)
        self.__detparams = []
        #: (:obj:`list` <:class:`tango.DeviceProxy`>)  attribute proxies
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

    @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "tango_det_attrs" in cnf.keys():
                record = cnf["tango_det_attrs"]
                if self.__settings.tangodetattrs != str(json.dumps(record)):
                    self.__settings.tangodetattrs = str(json.dumps(record))
                self.__updateParams()

    @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        try:
            cnf["tango_det_attrs"] = json.loads(self.__settings.tangodetattrs)
        except Exception as e:
            logger.warning(str(e))
        return json.dumps(cnf)

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

    @debugmethod
    def activate(self):
        """ activates tool widget
        """
        record = json.loads(str(self.__settings.tangodetattrs or "{}").strip())
        if not isinstance(record, dict):
            record = {}
        self.deactivate()
        for lb in sorted(record.keys()):
            try:
                dv = record[lb]
                ap = tango.AttributeProxy(dv)
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
        while not self.__attrWatcher.isWatching():
            QtCore.QCoreApplication.processEvents()
            time.sleep(0.1)

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

    @debugmethod
    def deactivate(self):
        """ activates tool widget
        """
        if self.__attrWatcher:
            self.__attrWatcher.attrValuesSignal.disconnect(self._showValues)
            # self.__attrWatcher.watchingFinished.disconnect(self._finished)
            logger.debug("STOPING %s" % str(self.__attrWatcher))
            self.__attrWatcher.stop()
            logger.debug("WAITING  for %s" % str(self.__attrWatcher))
            self.__attrWatcher.wait()
            logger.debug("REMOVING  for %s" % str(self.__attrWatcher))
            self.__attrWatcher = None
        self.__aproxies = []
        self.__detparams = []
        self.__avalues = []

    @QtCore.pyqtSlot(str)
    def _showValues(self, values):
        """ show values
        """
        vls = json.loads(values)
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
        self._mainwidget.emitTCC()

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
    requires = ("TANGO",)

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
        #: (:class:`tango.DeviceProxy`) x-motor device
        self.__xmotordevice = None
        #: (:class:`tango.DeviceProxy`) y-motor device
        self.__ymotordevice = None
        #: (:class:`tango.DeviceProxy`) door server
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

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            pars = ["position", "scale",
                    "xtext", "ytext", "xunits", "yunits"]
            if any(par in cnf.keys() for par in pars):
                self._mainwidget.updateTicks(cnf)
            if "motors" in cnf.keys():
                try:
                    motorname = cnf["motors"][0]
                    motordevice = tango.DeviceProxy(motorname)
                    for attr in ["state", "position"]:
                        if not hasattr(motordevice, attr):
                            raise Exception("Missing %s" % attr)
                    self.__xmotorname = motorname
                    self.__xmotordevice = motordevice
                except Exception as e:
                    logger.warning(str(e))
                try:
                    motorname = cnf["motors"][1]
                    motordevice = tango.DeviceProxy(motorname)
                    for attr in ["state", "position"]:
                        if not hasattr(motordevice, attr):
                            raise Exception("Missing %s" % attr)
                    self.__ymotorname = motorname
                    self.__ymotordevice = motordevice
                except Exception as e:
                    logger.warning(str(e))
            pars = ["x_intervals", "y_intervals", "interval_time"]
            if any(par in cnf.keys() for par in pars):
                if "x_intervals" in cnf.keys():
                    try:
                        self.__xintervals = int(cnf["x_intervals"])
                    except Exception:
                        pass
                if "y_intervals" in cnf.keys():
                    try:
                        self.__yintervals = int(cnf["y_intervals"])
                    except Exception:
                        pass
                if "interval_time" in cnf.keys():
                    try:
                        self.__itime = float(cnf["interval_time"])
                    except Exception:
                        pass
                self._updateIntervals()
            if "scan" in cnf.keys():
                if cnf["scan"]:
                    if str(self.__ui.scanPushButton.text()) == "Scan":
                        self._scanStopMotors()
            if "stop" in cnf.keys():
                if cnf["stop"]:
                    if str(self.__ui.scanPushButton.text()) == "Stop":
                        self._scanStopMotors()

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        xpos, ypos, xsc, ysc = self._mainwidget.scale()
        cnf["xunits"], cnf["yunits"] = self._mainwidget.axesunits()
        cnf["xtext"], cnf["ytext"] = self._mainwidget.axestext()
        cnf["position"] = [xpos, ypos]
        cnf["scale"] = [xsc, ysc]
        cnf["x_intervals"] = self.__xintervals
        cnf["y_intervals"] = self.__yintervals
        cnf["interval_time"] = self.__itime
        cnf["motors"] = [self.__xmotorname, self.__ymotorname]
        if str(self.__ui.scanPushButton.text()) == "Scan":
            cnf["motor_state"] = "ON"
        else:
            cnf["motor_state"] = "MOVING"

        return json.dumps(cnf)

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
        self._mainwidget.emitTCC()

    @QtCore.pyqtSlot()
    def _finished(self):
        """ stops mesh scan without stopping the macro
        """
        self.__stopScan(stopmacro=False)
        self._mainwidget.emitTCC()

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
            self._mainwidget.emitTCC()
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
            self._updateIntervals()
            return True
        return False

    def _updateIntervals(self):
        """ update interval informations
        """
        self.__ui.intervalsPushButton.setToolTip(
            "x-intervals:%s\ny-intervals:%s\nintegration time:%s" % (
                self.__xintervals, self.__yintervals, self.__itime))
        self.__showLabels()
        self._mainwidget.emitTCC()

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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
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
            [self.__ui.roiSpinBox.valueChanged, self._mainwidget.emitTCC],
            [self.__ui.roiSpinBox.valueChanged,
             self._mainwidget.writeDetectorROIsAttribute],
            [self.__ui.labelROILineEdit.textEdited, self._writeDetectorROIs],
            [self.__ui.labelROILineEdit.textEdited, self._mainwidget.emitTCC],
            [self._mainwidget.roiLineEditChanged, self._updateApplyButton],
            [self._mainwidget.roiAliasesChanged, self.updateROILineEdit],
            [self._mainwidget.roiValueChanged, self.updateROIDisplayText],
            [self._mainwidget.roiNumberChanged, self.setROIsNumber],
            [self._mainwidget.sardanaEnabled, self.updateROIButton],
            [self._mainwidget.mouseImagePositionChanged, self._message],
        ]

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "aliases" in cnf.keys():
                aliases = cnf["aliases"]
                if isinstance(aliases, list):
                    aliases = " ".join(aliases)
                self.__ui.labelROILineEdit.setText(aliases)
            if "rois_number" in cnf.keys():
                try:
                    self.__ui.roiSpinBox.setValue(int(cnf["rois_number"]))
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if "apply" in cnf.keys():
                if cnf["apply"]:
                    self._emitApplyROIPressed()
            if "fetch" in cnf.keys():
                if cnf["fetch"]:
                    self._emitFetchROIPressed()

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["aliases"] = str(self.__ui.labelROILineEdit.text()).split(" ")
        cnf["rois_number"] = self.__ui.roiSpinBox.value()
        return json.dumps(cnf)

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
        if self.__settings.singlerois:
            slabel = re.split(';|,| |\n', str(text))
            slabel = [lb for lb in slabel if lb]
            lsl = len(slabel)
            while lsl < len(self._mainwidget.roiCoords()):
                lsl += 1
                slabel.append("roi%s" % lsl)

            self.__ui.labelROILineEdit.setText(" ".join(slabel))
            self._updateApplyButton()
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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.cutSpinBox.valueChanged, self._updateCuts],
            [self.__ui.cutSpinBox.valueChanged, self._mainwidget.emitTCC],
            [self._mainwidget.cutNumberChanged, self._setCutsNumber],
            [self._mainwidget.cutCoordsChanged, self._plotCuts],
            [self.__ui.xcoordsComboBox.currentIndexChanged,
             self._setXCoords],
            [self.__ui.xcoordsComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self.__ui.allcutsCheckBox.stateChanged, self._updateAllCuts],
            [self.__ui.allcutsCheckBox.stateChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.freezeBottomPlotClicked, self._freezeplot],
            [self._mainwidget.clearBottomPlotClicked, self._clearplot],
        ]

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "cuts_number" in cnf.keys():
                try:
                    self.__ui.cutSpinBox.setValue(int(cnf["cuts_number"]))
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if "all_cuts" in cnf.keys():
                self.__ui.allcutsCheckBox.setChecked(bool(cnf["all_cuts"]))
            if "x_coordinates" in cnf.keys():
                idxs = ["points", "x-pixels", "y-pixels"]
                xcrd = str(cnf["x_coordinates"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.xcoordsComboBox.setCurrentIndex(idx)

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["x_coordinates"] = str(
            self.__ui.xcoordsComboBox.currentText()).lower()
        cnf["all_cuts"] = self.__ui.allcutsCheckBox.isChecked()
        cnf["cuts_number"] = self.__ui.cutSpinBox.value()
        return json.dumps(cnf)

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
            dt = self.__curves[i].xData, self.__curves[i].yData
            self.__freezed[i].setData(*dt)
            self.__freezed[i].show()
            self.__freezed[i].setVisible(True)
        for i in range(nrplots, len(self.__freezed)):
            self.__freezed[i].hide()
            self.__freezed[i].setVisible(True)

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
            if self.__settings.sendresults:
                xl = []
                yl = []
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
                        if self.__settings.sendresults:
                            xl.append([float(e) for e in dx])
                            yl.append([float(e) for e in dt])
                    else:
                        if rws > 1.0:
                            dx = np.linspace(0, len(dt - 1) * rws, len(dt))
                            self.__curves[i].setData(x=dx, y=dt)
                            if self.__settings.sendresults:
                                xl.append([float(e) for e in dx])
                                yl.append([float(e) for e in dt])
                        else:
                            self.__curves[i].setData(y=dt)
                            if self.__settings.sendresults:
                                xl.append(list(range(len(dt))))
                                yl.append([float(e) for e in dt])

                    self.__curves[i].setVisible(True)
                else:
                    self.__curves[i].setVisible(False)
            if self.__settings.sendresults:
                self.__sendresults(xl, yl)

    def _plotCut(self):
        """ plot the current 1d Cut
        """
        if self.__nrplots > 1:
            for i in range(1, len(self.__curves)):
                self.__curves[i].setVisible(False)
                self.__curves[i].hide()
            self.__nrplots = 1
        if self._mainwidget.currentTool() == self.name:
            if self.__settings.sendresults:
                xl = []
                yl = []
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
                    if self.__settings.sendresults:
                        xl.append([float(e) for e in dx])
                        yl.append([float(e) for e in dt])
                else:
                    rws = self._mainwidget.rangeWindowScale()
                    if rws > 1.0:
                        dx = np.linspace(0, len(dt - 1) * rws, len(dt))
                        self.__curves[0].setData(x=dx, y=dt)
                        if self.__settings.sendresults:
                            xl.append([float(e) for e in dx])
                            yl.append([float(e) for e in dt])
                    else:
                        self.__curves[0].setData(y=dt)
                        if self.__settings.sendresults:
                            xl.append(list(range(len(dt))))
                            yl.append([float(e) for e in dt])
                self.__curves[0].setVisible(True)
            else:
                self.__curves[0].setVisible(False)
            if self.__settings.sendresults:
                self.__sendresults(xl, yl)

    def __sendresults(self, xl, yl):
        """ send results to LavueController

        :param xl:  list of x's for each diffractogram
        :type xl: :obj:`list` < :obj:`list` <float>>
        :param yl:  list of values for each diffractogram
        :type yl: :obj:`list` < :obj:`list` <float>>
        """
        results = {"tool": self.alias}
        npl = len(xl)
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["nrlinecuts"] = len(xl)
        for i in range(npl):
            results["linecut_%s" % (i + 1)] = [xl[i], yl[i]]
        results["unit"] = ["point", "x-pixel", "y-pixel"][self.__xindex]
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

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
            [self.__ui.funComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self.__ui.rowsliceLineEdit.textChanged, self._updateRows],
            [self.__ui.rowsliceLineEdit.textChanged, self._mainwidget.emitTCC],
            [self.__ui.columnsliceLineEdit.textChanged, self._updateColumns],
            [self.__ui.columnsliceLineEdit.textChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self._mainwidget.scalesChanged, self._updateColumns],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "mapping" in cnf.keys():
                idxs = ["mean", "sum"]
                xcrd = str(cnf["mapping"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.funComboBox.setCurrentIndex(idx)
            if "rows" in cnf.keys():
                self.__ui.rowsliceLineEdit.setText(cnf["rows"])
            if "columns" in cnf.keys():
                self.__ui.columnsliceLineEdit.setText(cnf["columns"])

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["mapping"] = str(
            self.__ui.funComboBox.currentText()).lower()
        cnf["rows"] = self.__ui.rowsliceLineEdit.text()
        cnf["columns"] = self.__ui.columnsliceLineEdit.text()
        return json.dumps(cnf)

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
                else:
                    s1 = 1.0
                    s2 = 1.0
                    xx = list(range(len(sx)))
                    yy = list(range(len(sy)))
                width = [s1] * len(sx)
                height = [s2] * len(sy)
                self.__bottomplot.setOpts(
                    y0=[0]*len(sx), y1=sx, x=xx,
                    width=width)
                self.__bottomplot.drawPicture()
                self.__rightplot.setOpts(
                    x0=[0]*len(sy), x1=sy, y=yy,
                    height=height)
                self.__rightplot.drawPicture()
                if self.__settings.sendresults:
                    xslice = self.__dsrows
                    yslice = self.__dscolumns
                    if hasattr(xslice, "start"):
                        xslice = [xslice.start, xslice.stop, xslice.step]
                    if hasattr(yslice, "start"):
                        yslice = [yslice.start, yslice.stop, yslice.step]
                    self.__sendresults(
                        xx,
                        [float(e) for e in sx],
                        s1, xslice,
                        yy,
                        [float(e) for e in sy],
                        s2, yslice,
                        "sum" if self.__funindex else "mean"
                    )

    def __sendresults(self, xx, sx, xscale, xslice,
                      yy, sy, yscale, yslice, fun):
        """ send results to LavueController

        :param xx:  x's coordinates
        :type xx:  :obj:`list` <float>
        :param sx:  projection to x coordinate
        :type sx:  :obj:`list` <float>
        :param xscale:  x scale
        :type xscale:  :obj:`float`
        :param xslice:  x slice
        :type xslice:  :obj:`list` <float>
        :param yy:  y's coordinates
        :type yy:  :obj:`list` <float>
        :param sy:  projection to y coordinate
        :type sy:  :obj:`list` <float>
        :param yscale:  y scale
        :type yscale:  :obj:`float`
        :param yslice:  y slice
        :type yslice:  :obj:`list` <float>
        :param fun:  projection function name
        :type fun:  :obj:`str`
        """
        results = {"tool": self.alias}
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["xx"] = xx
        results["sx"] = sx
        results["xscale"] = xscale
        results["xslice"] = xslice
        results["yy"] = yy
        results["sy"] = sy
        results["yscale"] = yscale
        results["yslice"] = yslice
        results["function"] = fun
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

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
        #: ((:obj:`list`<:obj:`str`>) legend labels
        self.__labels = []
        #: ((:obj:`bool`) x in first row
        self.__xinfirstrow = False
        #: ((:obj:`bool`) accumalate status
        self.__accumulate = False
        #: ((:obj:`int`) buffer size
        self.__buffersize = 1024
        #: ((:class:`ndarray`) buffer
        self.__buffer = None

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

        self.__ui.rowsLineEdit.setText("0")
        self.parameters.bottomplot = True
        self.parameters.infolineedit = ""
        self.parameters.infotips = \
            "coordinate info display for the mouse pointer"

        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.rowsLineEdit.textChanged, self._updateRows],
            [self.__ui.rowsLineEdit.textChanged, self._mainwidget.emitTCC],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self.__ui.sizeLineEdit.textChanged, self._setBufferSize],
            [self.__ui.sizeLineEdit.textChanged, self._mainwidget.emitTCC],
            [self.__ui.xCheckBox.stateChanged, self._updateXRow],
            [self.__ui.xCheckBox.stateChanged, self._mainwidget.emitTCC],
            [self.__ui.accuPushButton.clicked, self._startStopAccu],
            [self.__ui.resetPushButton.clicked, self._resetAccu],
            [self.__ui.labelsPushButton.clicked, self._setLabels],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "rows_to_plot" in cnf.keys():
                self.__ui.rowsLineEdit.setText(cnf["rows_to_plot"])
            if "buffer_size" in cnf.keys():
                self.__ui.sizeLineEdit.setText(str(cnf["buffer_size"]))
            if "collect" in cnf.keys():
                self._startStopAccu()
            if "xrow" in cnf.keys():
                self.__ui.xCheckBox.setChecked(bool(cnf["xrow"]))
            if "reset" in cnf.keys():
                if cnf["reset"]:
                    self._resetAccu()
            if "labels" in cnf.keys():
                self.__labels = cnf["labels"]
                self.deactivate()
                self.activate()

            if "1d_stretch" in cnf.keys():
                try:
                    val = int(cnf["1d_stretch"])
                    self._mainwidget.bottomplotStretch(val)
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["rows_to_plot"] = self.__ui.rowsLineEdit.text()
        try:
            cnf["buffer_size"] = int(self.__ui.sizeLineEdit.text())
        except Exception:
            cnf["buffer_size"] = self.__ui.sizeLineEdit.text()
        cnf["collect"] = self.__accumulate
        cnf["xrow"] = self.__ui.xCheckBox.isChecked()
        cnf["labels"] = self.__labels
        return json.dumps(cnf)

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
        self._mainwidget.onedshowlegend(True)

    def deactivate(self):
        """ activates tool widget
        """
        for cr in self.__curves:
            cr.hide()
            cr.setVisible(False)
            self._mainwidget.removebottomplot(cr)
        self.__curves = []
        self.__nrplots = 0
        self._mainwidget.onedshowlegend(False)

    @QtCore.pyqtSlot()
    def _setLabels(self):
        """ launches label widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        dform = edListDialog.EdListDialog(self)
        dform.record = list(self.__labels or [])
        dform.title = "Tango Detector Attributes"
        dform.createGUI()
        dform.exec_()
        if dform.dirty:
            self.__labels = dform.record
            self.deactivate()
            self.activate()
            self._mainwidget.emitTCC()

    @QtCore.pyqtSlot()
    def _resetAccu(self):
        """ reset accumulation buffer
        """
        self.__buffer = None
        self._mainwidget.emitTCC()

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
        self._mainwidget.emitTCC()

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
            reset = False
            if self.__settings.sendresults:
                xl = []
                yl = []
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
                        ii = len(self.__curves)
                        lb = str(ii + 1)
                        if self.__labels and len(self.__labels) > ii:
                            if self.__labels[ii] is not None:
                                lb = self.__labels[ii]
                            else:
                                lb = str(ii + 1)
                        self.__curves.append(
                            self._mainwidget.onedbottomplot(name=lb))
                    for i in range(nrplots):
                        self.__curves[i].show()
                    for i in range(nrplots, len(self.__curves)):
                        self.__curves[i].hide()
                    if nrplots < self.__nrplots:
                        reset = True
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
                                if self.__settings.sendresults:
                                    xl.append([float(e) for e in dts[:, 0]])
                                    yl.append([float(e) for e in dts[:, i]])
                            elif rwe:
                                y = dts[:, i]
                                x = np.linspace(
                                    dx, len(y - 1) * ds1 + dx, len(y))
                                self.__curves[i].setData(x=x, y=y)
                                if self.__settings.sendresults:
                                    xl.append([float(e) for e in x])
                                    yl.append([float(e) for e in y])
                            else:
                                self.__curves[i].setData(dts[:, i])
                                if self.__settings.sendresults:
                                    dt = dts[:, i]
                                    xl.append(list(range(len(dt))))
                                    yl.append([float(e) for e in dt])
                            self.__curves[i].setVisible(True)
                        elif (self.__dsrows[i] >= 0 and
                              self.__dsrows[i] < dtnrpts):
                            if self.__xinfirstrow:
                                self.__curves[i].setData(
                                    x=dts[:, 0], y=dts[:, self.__dsrows[i]])
                                if self.__settings.sendresults:
                                    xl.append([float(e) for e in dts[:, 0]])
                                    yl.append([float(e) for e in
                                               dts[:, self.__dsrows[i]]])
                            elif rwe:
                                y = dts[:, self.__dsrows[i]]
                                x = np.linspace(
                                    dx, len(y - 1) * ds1 + dx, len(y))
                                self.__curves[i].setData(x=x, y=y)
                                if self.__settings.sendresults:
                                    xl.append([float(e) for e in x])
                                    yl.append([float(e) for e in y])
                            else:
                                self.__curves[i].setData(
                                    dts[:, self.__dsrows[i]])
                                if self.__settings.sendresults:
                                    dt = dts[:, self.__dsrows[i]]
                                    xl.append(list(range(len(dt))))
                                    yl.append([float(e) for e in dt])
                            self.__curves[i].setVisible(True)
                        else:
                            self.__curves[i].setVisible(False)
                    else:
                        self.__curves[i].setVisible(False)
                if self.__settings.sendresults:
                    self.__sendresults(xl, yl)
            else:
                for cr in self.__curves:
                    cr.setVisible(False)
            if reset:
                self.deactivate()
                self.activate()

    def __sendresults(self, xl, yl):
        """ send results to LavueController

        :param xl:  list of x's for each diffractogram
        :type xl: :obj:`list` < :obj:`list` <float>>
        :param yl:  list of values for each diffractogram
        :type yl: :obj:`list` < :obj:`list` <float>>
        """
        results = {"tool": self.alias}
        npl = len(xl)
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["nrplots"] = len(xl)
        for i in range(npl):
            results["onedplot_%s" % (i + 1)] = [xl[i], yl[i]]
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

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
        self.parameters.toolscale = False
        # self.parameters.rightplot = True

        #: (`lavuelib.imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`) configuration settings
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
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self.__ui.plotComboBox.currentIndexChanged,
             self._setPlotIndex],
            [self.__ui.plotComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.geometryChanged, self._mainwidget.emitTCC],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "geometry" in cnf.keys():
                try:
                    self._updateGeometry(cnf["geometry"])
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))
            if "plot_type" in cnf.keys():
                idxs = ["pixels", "polar-th", "polar-q"]
                xcrd = str(cnf["plot_type"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.plotComboBox.setCurrentIndex(idx)
            if "units" in cnf.keys():
                idxs = ["angles", "q-space"]
                xcrd = str(cnf["units"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.angleqComboBox.setCurrentIndex(idx)
            if "plot_range" in cnf.keys():
                try:
                    self._updatePolarRange(cnf["plot_range"])
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["plot_type"] = str(
            self.__ui.plotComboBox.currentText()).lower()
        cnf["units"] = str(
            self.__ui.angleqComboBox.currentText()).lower()

        cnf["plot_range"] = [
            [self.__polstart, self.__polend, self.__polsize],
            [self.__radthstart, self.__radthend, self.__radthsize],
            [self.__radqstart, self.__radqend, self.__radqsize]
        ]
        cnf["geometry"] = {
            "centerx": self.__settings.centerx,
            "centery": self.__settings.centery,
            "energy": self.__settings.energy,
            "pixelsizex": self.__settings.pixelsizex,
            "pixelsizey": self.__settings.pixelsizey,
            "detdistance": self.__settings.detdistance,
        }
        return json.dumps(cnf)

    # @debugmethod
    def activate(self):
        """ activates tool widget
        """
        self.__oldlocked = None
        self.updateGeometryTip()
        self.updateRangeTip()
        self._mainwidget.updateCenter(
            self.__settings.centerx, self.__settings.centery)

    # @debugmethod
    def deactivate(self):
        """ deactivates tool widget
        """
        self._setPlotIndex(0)

    # @debugmethod
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
                wavelength = 12398.4193 / self.__settings.energy
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
                    # self._setGeometry()
                    logger.warning(
                        "Please set the detector geometry to continue")
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
                    # self._setGeometry()
                    logger.warning(
                        "Please set the detector geometry to continue")
                    return False
                self.__radmax = rmax/float(maxdim)
            if pindex:
                psize = self.__polsize if self.__polsize is not None else 360
                pstart = self.__polstart if self.__polstart is not None else 0
                pend = self.__polend if self.__polend is not None else 360
                self.__polmax = float(pend - pstart) / psize
        return True

    # @debugmethod
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
                (int(self.__lastmaxdim), int(maxpolar)),
                dtype=float)
            # else:
            #     self.__inter = scipy.interpolate.RectBivariateSpline(
            #         xx, yy, rdata)
            #     tdata = np.fromfunction(
            #         lambda x, y: self.__intintensity(x, y),
            #         (int(self.__lastmaxdim), int(maxpolar)),
            #         dtype=float)
            return tdata

    # @debugmethod
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
            self._mainwidget.emitTCC()

    # @debugmethod
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
            wavelength = 12398.4193 / self.__settings.energy
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

    # @debugmethod
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

    # @debugmethod
    def _updatePolarRange(self, plotrange):
        """ update polar range

        :returns: (start, end, size) for polar, theta and q coordinates
        :rtype: :obj:`list`< [:obj:`float` ,:obj:`float` ,:obj:`float`] >
        """
        try:
            self.__polstart = float(plotrange[0][0])
        except Exception:
            self.__polstart = None
        try:
            self.__polend = float(plotrange[0][1])
        except Exception:
            self.__polend = None
        try:
            self.__polsize = float(plotrange[0][2])
        except Exception:
            self.__polsize = None
        try:
            self.__radthstart = float(plotrange[1][0])
        except Exception:
            self.__radthstart = None
        try:
            self.__radthend = float(plotrange[1][1])
        except Exception:
            self.__radthend = None
        try:
            self.__radthsize = float(plotrange[1][2])
        except Exception:
            self.__radthsize = None
        try:
            self.__radqstart = float(plotrange[2][0])
        except Exception:
            self.__radqstart = None
        try:
            self.__radqend = float(plotrange[2][1])
        except Exception:
            self.__radqend = None
        try:
            self.__radqsize = float(plotrange[2][2])
        except Exception:
            self.__radqsize = None
        self.__rangechanged = True
        self.updateRangeTip()
        # self._setPlotIndex(self.__plotindex)
        if self.__plotindex:
            self._mainwidget.emitReplotImage()
        self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot()
    def _updateGeometry(self, geometry):
        """ update geometry widget

        :param geometry: geometry dictionary
        :type geometry: :obj:`dict` < :obj:`str`, :obj:`list`>
        """
        try:
            if "centerx" in geometry.keys():
                self.__settings.centerx = float(geometry["centerx"])
                self._mainwidget.writeAttribute(
                    "BeamCenterX", float(self.__settings.centerx))
        except Exception:
            pass
        try:
            if "centery" in geometry.keys():
                self.__settings.centery = float(geometry["centery"])
                self._mainwidget.writeAttribute(
                    "BeamCenterY", float(self.__settings.centery))
        except Exception:
            pass
        try:
            if "energy" in geometry.keys():
                self.__settings.energy = float(geometry["energy"])
                self._mainwidget.writeAttribute(
                    "Energy", float(self.__settings.energy))
        except Exception:
            pass
        try:
            if "pixelsizex" in geometry.keys():
                self.__settings.pixelsizex = float(geometry["pixelsizex"])
        except Exception:
            pass
        try:
            if "pixelsizey" in geometry.keys():
                self.__settings.pixelsizey = float(geometry["pixelsizey"])
        except Exception:
            pass
        try:
            if "detdistance" in geometry.keys():
                self.__settings.detdistance = float(geometry["detdistance"])
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
        except Exception:
            pass
        if geometry:
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)
            if self.__plotindex:
                self._mainwidget.emitReplotImage()
            self._mainwidget.emitTCC()

    # @debugmethod
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
            self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot(int)
    def _setGSpaceIndex(self, gindex):
        """ set gspace index

        :param gspace: g-space index, i.e. angle or q-space
        :type gspace: :obj:`int`
        """
        self.__gspaceindex = gindex

    # @debugmethod
    @QtCore.pyqtSlot(int)
    def _setPlotIndex(self, pindex=None):
        """ set gspace index

        :param gspace: g-space index,
        :         i.e. 0: Cartesian, 1: polar-th, 2: polar-q
        :type gspace: :obj:`int`
        """
        if pindex:
            if not self.__calculateRadMax(pindex):
                self.__ui.plotComboBox.setCurrentIndex(0)
                return
            self.parameters.centerlines = False
            self.parameters.toolscale = True
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
            self._mainwidget.setToolScale([rstart, pstart], [rscale, pscale])
            if not self.__plotindex:
                self.__oldlocked = self._mainwidget.setAspectLocked(False)
        else:
            if self.__oldlocked is not None:
                self._mainwidget.setAspectLocked(self.__oldlocked)
            self.parameters.centerlines = True
            self.parameters.toolscale = False
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
        #: (:obj:`list` <:obj:`str`>) list of units
        self.__units = ["q_nm^-1", "q_A^-1", "2th_deg",
                        "2th_rad", "r_mm", "r_pixel"]

        #: (:obj:`int`) plot index
        #               ->  0: Image, <i>: Buffer <i>
        self.__plotindex = 0
        #: (:obj:`bool`) old lock value
        self.__oldlocked = None
        #: (:class:`Ui_ROIToolWidget') ui_toolwidget object from qtdesigner
        self.__ui = _diffractogramformclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) old lock value
        self.__oldlocked = None

        #: (:obj:`bool`) reset scale flag
        self.__resetscale = True

        #: ((:obj:`bool`) show diffractogram status
        self.__showdiff = False

        #: (:obj:`list` < [:obj:`float`, :obj:`float`] >)
        #          range positions of radial in current units
        self.__radrange = [None]
        #: (:obj:`list` < :obj:`float`>) start position of radial in deg
        self.__radstart = [None]
        #: (:obj:`list` < :obj:`float >) end position of radial in deg
        self.__radend = [None]
        #: (:obj:`list` < :obj:`float`>) start position of azimuth angle in deg
        self.__azstart = [None]
        #: (:obj:`list` < :obj:`float`>) end position of azimuth angle in deg
        self.__azend = [None]
        #: (:obj:`list` < [:obj:`float`, :obj:`float`] > )
        #          range positions of azimuth in deg
        self.__azrange = [None]

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot freezed
        self.__freezed = []

        #: (:obj:`list`<:class:`pyqtgraph.PlotDataItem`>) 1D plot
        self.__curves = []
        #: (:obj:`int`) current plot number
        self.__nrplots = 0

        #: (:obj:`bool`) progressbar is running
        self.__progressFlag = False
        #: (:class:`pyqtgraph.QtGui.QProgressDialog`) progress bar
        self.__progress = None
        #: (:obj:`list` <:class:`lavuelib.commandThread.CommandThread`>) \
        #:     command thread
        self.__commandthread = None

        #: ( :obj:`list` <  :obj:`list` <  :obj:`list` < (float, float) > > >)
        #    list of region lines
        self.__regions = []

        #: (:obj:`list` < (int, int, int) > ) list with region colors
        self.__colors = []
        #: ( (:obj:`int`, :obj:`int', :obj:`int`)) default pen color
        self.__defpen = (0, 255, 127)

        #: (:obj:`bool`) accumalate status
        self.__accumulate = False
        #: (:obj:`bool`) show buffer status
        self.__showbuffer = False
        #: (:obj:`int`) buffer size
        self.__buffersize = 1024
        #: ([:class:`ndarray`,:class:`ndarray` :class:`ndarray`,
        #     :class:`ndarray`]) y-buffers for diffractogram
        self.__buffers = [None, None, None, None]
        #: (:obj:`list` < [:obj:`int`, :obj:`int`] > )
        #      x-buffers of (position, scale) for diffractogram
        self.__xbuffers = [None, None, None, None]
        #: (:obj:`list` < `list` < :obj:`int` > > ) time stamps
        self.__timestamps = [[], [], [], []]

        # self.parameters.lines = True
        #: (:obj:`str`) infolineedit text
        self.parameters.infolineedit = ""
        self.parameters.infotips = ""
        self.parameters.bottomplot = True
        self.parameters.centerlines = True
        self.parameters.toolscale = False
        self.parameters.regions = True
        # self.parameters.rightplot = True

        #: (`lavuelib.imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()
        self.setColors(self.__settings.roiscolors)
        #: (:obj:`list` < [:class:`pyqtgraph.QtCore.pyqtSignal`, :obj:`str`] >)
        #: list of [signal, slot] object to connect
        self.signal2slot = [
            [self.__ui.diffSpinBox.valueChanged, self._updateDiffNumber],
            [self.__ui.diffSpinBox.valueChanged, self._mainwidget.emitTCC],
            [self.__ui.rangePushButton.clicked, self._setPolarRange],
            [self.__ui.showPushButton.clicked, self._showhideDiff],
            [self.__ui.nextPushButton.clicked, self._nextPlotDiff],
            [self.__ui.calibrationPushButton.clicked, self._loadCalibration],
            [self.__ui.unitComboBox.currentIndexChanged,
             self._setUnitIndex],
            [self.__ui.unitComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self.__ui.mainplotComboBox.currentIndexChanged,
             self._setPlotIndex],
            [self.__ui.mainplotComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self.__ui.sizeLineEdit.textChanged, self._setBufferSize],
            [self.__ui.sizeLineEdit.textChanged, self._mainwidget.emitTCC],
            [self.__ui.accuPushButton.clicked, self._startStopAccu],
            [self.__ui.bufferPushButton.clicked, self._showBuffer],
            [self.__ui.resetPushButton.clicked, self._resetAccu],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.geometryChanged, self._mainwidget.emitTCC],
            [self._mainwidget.geometryChanged, self._updateSetCenter],
            [self._mainwidget.freezeBottomPlotClicked, self._freezeplot],
            [self._mainwidget.clearBottomPlotClicked, self._clearplot],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self._mainwidget.colorsChanged, self.setColors]
        ]
        # self.__ui.showPushButton.hide()
        # self.__ui.nextPushButton.hide()
        self._showBuffer(False)

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "calibration" in cnf.keys():
                calib = cnf["calibration"]
                try:
                    self._loadCalibration(calib)
                except Exception as e:
                    logger.warning(str(e))
            if "diff_number" in cnf.keys():
                try:
                    self.__ui.diffSpinBox.setValue(int(cnf["diff_number"]))
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if "diff_ranges" in cnf.keys():
                try:
                    self._updatePolarRange(cnf["diff_ranges"])
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))
            if "diff_units" in cnf.keys():
                idxs = ["q [1/nm]", "q [1/A]", "2th [deg]", "2th [rad]",
                        "r [mm]", "r [pixel]"]
                xcrd = str(cnf["diff_units"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.unitComboBox.setCurrentIndex(idx)
            if "show_diff" in cnf.keys():
                if cnf["show_diff"]:
                    if str(self.__ui.showPushButton.text()) == "Show":
                        self._showhideDiff()
                else:
                    if str(self.__ui.showPushButton.text()) == "Stop":
                        self._showhideDiff()
            if "stop_diff" in cnf.keys():
                if cnf["stop_diff"]:
                    if str(self.__ui.showPushButton.text()) == "Stop":
                        self._showhideDiff()
            if "next" in cnf.keys():
                if cnf["next"]:
                    if str(self.__ui.nextPushButton.text()) == "Next":
                        self._nextPlotDiff()
            if "main_plot" in cnf.keys():
                idxs = [
                    "image", "buffer 1", "buffer 2", "buffer 3", "buffer 4"]
                xcrd = str(cnf["main_plot"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception as e:
                    print(str(e))
                    idx = 0
                self.__ui.mainplotComboBox.setCurrentIndex(idx)
            if "buffering" in cnf.keys():
                self._showBuffer()
            if "buffer_size" in cnf.keys():
                self.__ui.sizeLineEdit.setText(str(cnf["buffer_size"]))
            if "reset" in cnf.keys():
                if cnf["reset"]:
                    self._resetAccu()
            if "collect" in cnf.keys():
                if cnf["collect"] and not self.__accumulate:
                    self._startStopAccu()
                elif not cnf["collect"] and self.__accumulate:
                    self._startStopAccu()

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["calibration"] = self.__settings.calibrationfilename
        cnf["diff_number"] = self.__ui.diffSpinBox.value()
        ranges = []
        for nip in range(cnf["diff_number"]):
            azs = self.__azstart[nip] if len(self.__azstart) > nip else None
            aze = self.__azend[nip] if len(self.__azend) > nip else None
            rds = self.__radstart[nip] if len(self.__radstart) > nip else None
            rde = self.__radend[nip] if len(self.__radend) > nip else None
            ranges.append([azs, aze, rds, rde])
        cnf["diff_ranges"] = ranges
        units = ["q [1/nm]", "q [1/A]", "2th [deg]", "2th [rad]",
                 "r [mm]", "r [pixel]"]
        idx = self.__ui.unitComboBox.currentIndex()
        cnf["diff_units"] = units[idx]
        try:
            cnf["buffer_size"] = int(self.__ui.sizeLineEdit.text())
        except Exception:
            cnf["buffer_size"] = self.__ui.sizeLineEdit.text()
        cnf["buffering"] = self.__showbuffer
        cnf["collect"] = self.__accumulate
        cnf["show_diff"] = self.__showdiff
        cnf["main_plot"] = str(
            self.__ui.mainplotComboBox.currentText()).lower()
        return json.dumps(cnf)

    # @debugmethod
    @QtCore.pyqtSlot()
    def _setBufferSize(self):
        """ start/stop accumulation buffer

        """
        try:
            self.__buffersize = int(self.__ui.sizeLineEdit.text())
            self._resetAccu()
        except Exception as e:
            # print(str(e))
            logger.warning(str(e))
            self.__buffersize = 1024

    # @debugmethod
    @QtCore.pyqtSlot()
    def _resetAccu(self):
        """ reset accumulation buffer
        """
        self.__buffers = [None, None, None, None]
        self.__xbuffers = [None, None, None, None]
        self.__timestamps = [[], [], [], []]
        # np.empty(shape=(int(self.__settings.diffnpt), 0))
        # diffdata = None
        self.__resetscale = True
        if self.__plotindex != 0:
            diffdata = np.zeros(shape=(1, 1))
            self._mainwidget.updateImage(diffdata, diffdata)
        self._mainwidget.emitTCC()

    # @debugmethod
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
        self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot()
    def _showBuffer(self, status=None):
        """ show/hide buffer widgets
        """
        if status is not None:
            self.__showbuffer = not status
        if not self.__showbuffer:
            self.__showbuffer = True
            if QtGui.QIcon.hasThemeIcon("go-up"):
                icon = QtGui.QIcon.fromTheme("go-up")
                self.__ui.bufferPushButton.setIcon(icon)
            else:
                # self.__ui.bufferPushButton.setText(u" \u25B2 Buffering")
                self.__ui.bufferPushButton.setText(u" \u25B4 Buffering ")
            self.__ui.bufferFrame.show()
        else:
            self.__showbuffer = False
            if QtGui.QIcon.hasThemeIcon("go-down"):
                icon = QtGui.QIcon.fromTheme("go-down")
                self.__ui.bufferPushButton.setIcon(icon)
            else:
                # self.__ui.bufferPushButton.setText(u" \u25BC Buffering")
                self.__ui.bufferPushButton.setText(u" \u25BE Buffering ")
            self.__ui.bufferFrame.hide()
            self.adjustSize()
        self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot(str)
    def setColors(self, colors=None, force=False):
        """ sets colors

        :param colors: json list of roi colors
        :type colors: :obj:`str`
        :returns: change status
        :rtype: :obj:`bool`
        """
        if colors is not None:
            colors = json.loads(colors)
            if not isinstance(colors, list):
                return False
            for cl in colors:
                if not isinstance(cl, list):
                    return False
                if len(cl) != 3:
                    return False
                for clit in cl:
                    if not isinstance(clit, int):
                        return False
        else:
            colors = self.__colors
            force = True
        if self.__colors != colors or force:
            self.__colors = colors
            for i, cr in enumerate(self.__curves):
                clr = tuple(colors[i % len(colors)]) if colors \
                    else self.__defpen
                cr.setPen(_pg.mkPen(clr))

    # @debugmethod
    def runProgress(self, commands, onclose="_closeReset",
                    text="Updating diffractogram ranges ..."):
        """ starts progress thread with the given commands

        :param commands: list of commands
        :type commands: :obj:`list` <:obj:`str`>
        :param onclose: close command name
        :type onclose: :obj:`str`
        :param text: text to display
        :type text: :obj:`str`
        """
        if self.__progress:
            return
        if self.__commandthread:
            self.__commandthread.setParent(None)
            self.__commandthread = None
        self.__commandthread = commandThread.CommandThread(
            self, commands, self._mainwidget)
        oncloseaction = getattr(self, onclose)
        self.__commandthread.finished.connect(
            oncloseaction, QtCore.Qt.QueuedConnection)
        self.__progress = None
        self.__progress = QtGui.QProgressDialog(
            text, "Cancel", 0, 0, self)
        self.__progress.setWindowModality(QtCore.Qt.WindowModal)
        self.__progress.setCancelButton(None)
        self.__progress.rejected.connect(
            self.waitForThread, QtCore.Qt.QueuedConnection)
        self.__commandthread.start()
        self.__progress.show()

    # @debugmethod
    def waitForThread(self):
        """ waits for running thread
        """
        logger.debug("waiting for Thread")
        if self.__commandthread:
            try:
                self.__commandthread.wait()
            except Exception as e:
                logger.warning(str(e))
        logger.debug("waiting for Thread ENDED")

    # @debugmethod
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
            dt = self.__curves[i].xData, self.__curves[i].yData
            self.__freezed[i].setData(*dt)
            self.__freezed[i].show()
            self.__freezed[i].setVisible(True)
        for i in range(nrplots, len(self.__freezed)):
            self.__freezed[i].hide()
            self.__freezed[i].setVisible(True)
            # print(type(cr))

    # @debugmethod
    @QtCore.pyqtSlot()
    def _clearplot(self):
        """ clear freezed plot
        """
        for cr in self.__freezed:
            cr.setVisible(False)

    # @debugmethod
    @QtCore.pyqtSlot(int)
    def _updateDiffNumber(self, did):
        """ update diffractorgram number

        :param did: diffractogram id
        :type did: :obj:`int`
        """
        QtCore.QCoreApplication.processEvents()
        self.updateRangeTip()
        self.__updateBufferCombobox(did)
        # self.__nrplots = self.__ui.diffSpinBox.value()
        #
        self._plotDiff()
        self.setColors(self.__settings.roiscolors, True)
        # self.__updateregion()
        QtCore.QCoreApplication.processEvents()
        while len(self.__regions) > self.__nrplots:
            self.regions.pop()
        QtCore.QCoreApplication.processEvents()
        self._updateRegionsAndPlot()

    # @debugmethod
    def __updateBufferCombobox(self, did):
        """ update buffer combobox

        :param did: diffractogram id
        :type did: :obj:`int`
        """
        combo = self.__ui.mainplotComboBox
        # idx = combo.currentIndex()
        cnt = combo.count()
        while did >= cnt:
            if cnt:
                combo.addItem("Buffer %s" % (cnt))
            else:
                combo.addItem("Image")
            cnt = combo.count()
        while did + 1 < cnt:
            combo.removeItem(cnt - 1)
            cnt = combo.count()
        # if idx >= cnt:
        #     changed = True

    # @debugmethod
    def afterplot(self):
        """ command after plot
        """

    # @debugmethod
    def activate(self):
        """ activates tool widget
        """
        self.__oldlocked = None
        self.__ui.sizeLineEdit.setText(str(self.__buffersize))
        self.updateGeometryTip()
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
        self.setColors(self.__settings.roiscolors, True)
        # if self.__settings.calibrationfilename:
        #     self._loadCalibration(
        #         self.__settings.calibrationfilename)
        # self.__ui.diffSpinBox.setEnabled(False)
        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        if aistat:
            self._plotDiff()
        self._mainwidget.bottomplotShowMenu(True, True)
        self.__ui.mainplotComboBox.setCurrentIndex(0)
        self._setPlotIndex(0)

    # @debugmethod
    @QtCore.pyqtSlot()
    def _nextPlotDiff(self):
        """ plot all diffractograms and update
        """
        self._plotDiffWithBuffering()
        if self.__plotindex > 0 and \
           self.__plotindex <= len(self.__buffers):
            if self.__buffers[self.__plotindex - 1] is not None:
                diffdata = np.transpose(self.__buffers[self.__plotindex - 1])
            else:
                diffdata = None
                diffdata = np.zeros(shape=(1, 1))
                self.__resetscale = True
                # np.empty(shape=(int(self.__settings.diffnpt), 0))
            self._mainwidget.updateImage(diffdata, diffdata)
        self._mainwidget.emitTCC()

    # @debugmethod
    def deactivate(self):
        """ deactivates tool widget
        """
        self.waitForThread()
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

    # @debugmethod
    def _plotDiffWithBuffering(self):
        """ plot diffractogram with buffering
        """
        xl, yl, ts = self._plotDiff()
        # print(yl)
        if self.__accumulate:
            for i, yy in enumerate(yl):
                newrow = np.array(yy)
                if self.__buffers[i] is not None and \
                   self.__buffers[i].shape[1] == newrow.shape[0]:
                    if self.__buffers[i].shape[0] >= self.__buffersize:
                        self.__buffers[i] = np.vstack(
                            [self.__buffers[i][
                                self.__buffers[i].shape[0]
                                - self.__buffersize + 1:,
                                :],
                             newrow]
                        )
                        if self.__timestamps[i]:
                            self.__timestamps[i].pop(0)
                    else:
                        self.__buffers[i] = np.vstack(
                            [self.__buffers[i], newrow])
                    self.__timestamps[i].append(ts)
                else:
                    self.__buffers[i] = np.array([yy])
                    self.__timestamps[i] = [ts]
                if self.__xbuffers[i] is None or self.__resetscale:
                    xbuf = np.array(xl[i])
                    pos = 0.0
                    sc = 1.0
                    if len(xbuf) > 0:
                        pos = xbuf[0]
                    if len(xbuf) > 1:
                        sc = (xbuf[-1] - xbuf[0])/(len(xbuf) - 1)
                    self.__xbuffers[i] = [pos, sc]
                    if (self.__ui.mainplotComboBox.currentIndex() -
                       1 == i):
                        self._mainwidget.setToolScale(
                            [pos, 0], [sc, 1])
                        # self._mainwidget.setToolScale(
                        #    [0, 0], [1, 1])
            self.__resetscale = False

    # @debugmethod
    def beforeplot(self, array, rawarray):
        """ command  before plot

        :param array: 2d image array
        :type array: :class:`numpy.ndarray`
        :param rawarray: 2d raw image array
        :type rawarray: :class:`numpy.ndarray`
        :return: 2d image array and raw image
        :rtype: (:class:`numpy.ndarray`, :class:`numpy.ndarray`)
        """
        if self.__showdiff:
            self._plotDiffWithBuffering()
        if self.__plotindex > 0 and \
           self.__plotindex <= len(self.__buffers):
            if self.__buffers[self.__plotindex - 1] is not None:
                diffdata = np.transpose(self.__buffers[self.__plotindex - 1])
            else:
                diffdata = None
                diffdata = np.zeros(shape=(1, 1))
                self.__resetscale = True
                # np.empty(shape=(int(self.__settings.diffnpt), 0))
            return (diffdata, diffdata)

    # @debugmethod
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
            with QtCore.QMutexLocker(self.__settings.aimutex):
                if self.__settings.ai is not None:
                    aif = self.__settings.ai.getFit2D()
                    self.__settings.ai.setFit2D(aif["directDist"],
                                                self.__settings.centerx,
                                                self.__settings.centery,
                                                aif["tilt"],
                                                aif["tiltPlanRotation"])
                self._mainwidget.writeAttribute("BeamCenterX", float(xdata))
                self._mainwidget.writeAttribute("BeamCenterY", float(ydata))
            self._message()
            self.__updateregion()
            self._plotDiff()
            self.updateGeometryTip()
            self._resetAccu()
            self._mainwidget.emitTCC()
            # self.__resetscale = True

    # @debugmethod
    @QtCore.pyqtSlot()
    def _updateSetCenter(self):
        """ updates the image center

        """
        # return
        with QtCore.QMutexLocker(self.__settings.aimutex):
            if self.__settings.ai is not None:
                aif = self.__settings.ai.getFit2D()
                self.__settings.ai.setFit2D(aif["directDist"],
                                            self.__settings.centerx,
                                            self.__settings.centery,
                                            aif["tilt"],
                                            aif["tiltPlanRotation"])
        self._resetAccu()
        self.__updateregion()
        self._plotDiff()
        # self.__resetscale = True

    # @debugmethod
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
                with QtCore.QMutexLocker(self.__settings.aimutex):
                    self.__settings.ai = pyFAI.load(fileName)
                # self.__settings.ai.rot1 = 0
                # self.__settings.ai.rot1 = math.pi/4 * 0.5
                # self.__settings.ai.rot1 = math.pi/4 * 0.75
                # self.__settings.ai.rot1 = math.pi/4.
                # self.__settings.ai.rot2 = math.pi/4.
                # self.__settings.ai.rot3 = math.pi/2.
                # print(str(self.__settings.ai))
                self.__settings.calibrationfilename = fileName
                self.__writedetsettings()
                self._mainwidget.updateCenter(
                    self.__settings.centerx, self.__settings.centery)
            except Exception as e:
                # print(str(e))
                logger.warning(str(e))
                with QtCore.QMutexLocker(self.__settings.aimutex):
                    self.__settings.ai = None
            with QtCore.QMutexLocker(self.__settings.aimutex):
                self.__updateButtons(self.__settings.ai is not None)
            self.__updateregion()
            self.updateGeometryTip()
            self._resetAccu()
        self._mainwidget.emitTCC()
        self.__resetscale = True

    # @debugmethod
    def __writedetsettings(self):
        """ write detector settings from ai object
        """
        self.__settings.updateDetectorParameters()
        self._mainwidget.writeDetectorAttributes()

    # @debugmethod
    def __updateButtons(self, status=None):
        """ update buttons

        :param status: show button flag
        :type status: :obj:`bool`
        """
        if status is None:
            status = self.__settings.ai is not None
        self.__ui.showPushButton.setEnabled(status)
        self.__ui.nextPushButton.setEnabled(status)
        self.__ui.diffSpinBox.setEnabled(status)

    # @debugmethod
    @QtCore.pyqtSlot()
    def _message(self):
        """ provides geometry message
        """
        message = ""
        if self.__plotindex == 0:
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
            with QtCore.QMutexLocker(self.__settings.aimutex):
                if self.__settings.ai is not None:
                    chi = self.__settings.ai.chi(
                        np.array([y - 0.5]), np.array([x - 0.5]))
                    if len(chi):
                        chi = chi[0]
            if self.__unitindex in [2, 3]:
                tth = None
                with QtCore.QMutexLocker(self.__settings.aimutex):
                    if self.__settings.ai is not None:
                        tth = self.__settings.ai.tth(
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
                    if self.__unitindex == 3:
                        ap = self.__approxpoint(tth, chi)
                        message += " $%s$" % str(ap)
                else:
                    message = "x, y = [%s, %s], %s = %.2f" % (
                        x, y, ilabel, intensity)
            elif self.__unitindex in [0, 1]:
                qa = None
                with QtCore.QMutexLocker(self.__settings.aimutex):
                    if self.__settings.ai is not None:
                        qa = self.__settings.ai.qFunction(
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
                with QtCore.QMutexLocker(self.__settings.aimutex):
                    if self.__settings.ai is not None:
                        ra = self.__settings.ai.rFunction(
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
            elif self.__unitindex in [5]:
                cx = self.__settings.centerx
                cy = self.__settings.centery
                ra = math.sqrt((cx - x)**2 + (cy - y)**2)
                if ra is not None and chi is not None:
                    chi = chi * 180./math.pi
                    message = "x, y = [%s, %s], r = %f %s, chi = %f %s," \
                              " %s = %.2f" \
                              % (x, y, ra, "pixel",
                                 chi, "deg",
                                 ilabel, intensity)
                else:
                    message = "x, y = [%s, %s], %s = %.2f" % (
                        x, y, ilabel, intensity)
        elif self.__plotindex > 0:
            ix, iy, intensity, x, y = self._mainwidget.currentIntensity()
            ilabel = self._mainwidget.scalingLabel()
            pindex = self.__ui.mainplotComboBox.currentIndex()
            pos = 0.0
            sc = 1.0
            tst = []
            ts = ""
            if len(self.__xbuffers) >= pindex and \
               self.__xbuffers[pindex - 1]:
                pos, sc = self.__xbuffers[pindex - 1]
            xc = pos + x * sc
            if len(self.__timestamps) >= pindex and \
               self.__timestamps[pindex - 1]:
                tst = self.__timestamps[pindex - 1]
            it = int(iy)
            # itx = int(ix)
            if it < len(tst) and it >= 0:
                ts = tst[it]
                # store first tst[0]
                # ts = tst[it] - tst[0]
            units = self.__units[self.__unitindex]
            xlabel = self.__ui.unitComboBox.currentText()
            if "[" in xlabel:
                xlabel, units = xlabel.split("[", 1)
                units = units.replace("]", "")
            message = "no: %s, %s = %s %s, %s = %.2f (time = %s s)" % (
                        it, xlabel, xc, units,  ilabel, intensity, ts)
        self._mainwidget.setDisplayedText(message)

    # @debugmethod
    def __tipmessage(self):
        """ provides geometry messate

        :returns: geometry text
        :rtype: :obj:`unicode`
        """
        tips = ""
        with QtCore.QMutexLocker(self.__settings.aimutex):
            if self.__settings.ai:
                tips = str(self.__settings.ai)
        return tips

    # @debugmethod
    @QtCore.pyqtSlot()
    def updateGeometryTip(self):
        """ update geometry tips
        """
        message = self.__tipmessage()
        self.__ui.calibrationPushButton.setToolTip(
            "Input physical parameters\n%s" % message)

    # @debugmethod
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
        self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot()
    def _plotDiff(self):
        """ plot all diffractograms

        :returns: (list of x's for each diffractogram,
                   list of y's for each diffractogram,
                   integer timestamp)

        :rtype: (:obj:`list` < :obj:`list` <float>>,
                 :obj:`list` < :obj:`list` <float>>,
                 int)
        """
        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        xl = []
        yl = []
        timestamp = time.time()
        if aistat:
            if self._mainwidget.currentTool() == self.name:
                if self.__settings.sendresults:
                    xl = []
                    yl = []
                    pxl = []
                    pyl = []
                    pel = []
                nrplots = self.__ui.diffSpinBox.value()
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
                                colors = self.__colors
                                clr = tuple(colors[i % len(colors)]) \
                                    if colors else self.__defpen
                                cr.setPen(_pg.mkPen(clr))
                dts = self._mainwidget.rawData()
                if dts is not None:
                    trans = self._mainwidget.transformations()[0]
                    csa = self.__settings.correctsolidangle
                    unit = self.__units[self.__unitindex]
                    if self.__unitindex in [5]:
                        unit = "r_mm"
                    else:
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
                    for i in range(nrplots):
                        try:
                            with QtCore.QMutexLocker(self.__settings.aimutex):
                                res = self.__settings.ai.integrate1d(
                                    dts,
                                    self.__settings.diffnpt,
                                    correctSolidAngle=csa,
                                    radial_range=(
                                        self.__radrange[i]
                                        if len(self.__radrange) > i else None),
                                    azimuth_range=(
                                        self.__azrange[i]
                                        if len(self.__azrange) > i else None),
                                    unit=unit, mask=mask)
                            # print(res)
                            x = res[0]
                            y = res[1]
                            if self.__unitindex in [5]:
                                with QtCore.QMutexLocker(
                                        self.__settings.aimutex):
                                    aif = self.__settings.ai.getFit2D()
                                if aif["pixelX"] and aif["pixelY"]:
                                    if self.__azrange[i] is None:
                                        azs, aze = 0, math.pi/2
                                    else:
                                        azs, aze = self.__azrange[i]
                                        azs *= math.pi / 180.
                                        aze *= math.pi / 180.
                                    facx = 1000./aif["pixelX"]
                                    facy = 1000./aif["pixelY"]
                                    with QtCore.QMutexLocker(
                                            self.__settings.aimutex):
                                        cs1 = math.cos(
                                            azs + self.__settings.ai.rot3)
                                        cs2 = math.cos(
                                            aze + self.__settings.ai.rot3)
                                        sn1 = math.sin(
                                            azs + self.__settings.ai.rot3)
                                        sn2 = math.sin(
                                            aze + self.__settings.ai.rot3)
                                        fc1 = facx * cs1 / math.cos(
                                            self.__settings.ai.rot1)
                                        fc2 = facx * cs2 / math.cos(
                                            self.__settings.ai.rot1)
                                        fs1 = facy * sn1 / math.cos(
                                            self.__settings.ai.rot2)
                                        fs2 = facy * sn2 / math.cos(
                                            self.__settings.ai.rot2)
                                    x = [
                                        (math.sqrt(
                                            (fc1 * r)**2 + (fs1 * r)**2)
                                         + math.sqrt(
                                             (fc2 * r)**2 + (fs2 * r)**2))
                                        / 2
                                        for r in x]
                            self.__curves[i].setData(x=x, y=y)
                            if self.__settings.sendresults or \
                               self.__accumulate:
                                xl.append([float(e) for e in x])
                                yl.append([float(e) for e in y])
                            if self.__settings.sendresults:
                                px, py, pe = self.__findpeaks2(x, y)
                                pxl.append([float(e) for e in px])
                                pyl.append([float(e) for e in py])
                                pel.append(float(pe))
                        except Exception as e:
                            # print(str(e))
                            logger.warning(str(e))
                            x = []
                            y = []
                            self.__curves[i].setData(x=x, y=y)
                        self.__curves[i].setVisible(True)
                else:
                    for i in range(nrplots):
                        self.__curves[i].setVisible(False)
                if self.__settings.sendresults:
                    self.__sendresults(xl, yl, pxl, pyl, pel, timestamp)
        return xl, yl, timestamp

    def __sendresults(self, xl, yl, pxl=None, pyl=None, pel=None,
                      timestamp=None):
        """ send results to LavueController

        :param xl:  list of x's for each diffractogram
        :type xl: :obj:`list` < :obj:`list` <float>>
        :param yl:  list of values for each diffractogram
        :type yl: :obj:`list` < :obj:`list` <float>>
        :param pxl:  list of peak x's for each diffractogram
        :type pxl: :obj:`list` < :obj:`list` <float>>
        :param pyl:  list of peak values for each diffractogram
        :type pyl: :obj:`list` < :obj:`list` <float>>
        :param pel:  peak x's errors for each diffractogram
        :type pel:  :obj:`list` <float>
        :param timestamp:  timestamp
        :type timestamp:  :obj:`int`
        """
        results = {"tool": self.alias}
        npl = len(xl)
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = timestamp
        results["nrdiffs"] = len(xl)
        results["calibration"] = self.__settings.calibrationfilename
        for i in range(npl):
            results["radial_range_%s" % (i + 1)] = self.__radrange[i] \
                if len(self.__radrange) > i else None
            results["azimuth_range_%s" % (i + 1)] = self.__azrange[i] \
                if len(self.__azrange) > i else None
            results["diff_%s" % (i + 1)] = [xl[i], yl[i]]
            if pxl is not None and pyl is not None:
                results["peaks_%s" % (i + 1)] = [pxl[i], pyl[i]]
                if pel is not None:
                    results["peaks_%s_error" % (i + 1)] = pel[i]
        results["unit"] = self.__units[self.__unitindex]
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

    def __findpeaks(self, x, y, nr=20):
        """ find peaks from diffractogram

        :param x:  x of diffractogram
        :type x:  :obj:`list` <float>>
        :param y:  values of diffractogram
        :type y:  :obj:`list` <float>>
        :param nr:  list of peak x's for each diffractogram
        :type nr: :obj:`int`
        :returns: (peak_xs, peak_values, x_error)
        :rtype: (:obj:`list` <float>, :obj:`list` <float>, :obj:`float`)
        """
        t = np.array(y)
        xml = []
        yml = []
        iml = []
        eml = []

        it = 0
        while (t > 0).any() and it < nr:
            im = np.argmax(t)
            tm = t[im]
            iml.append(im)
            xml.append(x[im])
            yml.append(tm)
            er = max(x[im] - x[max(im - 1, 0)],
                     x[min(im + 1, len(x) - 1)] - x[im])
            eml.append(er)
            it += 1
            # print("%s. found %s (%s +- %s, %s)" % (it, im, x[im], er, tm))

            i1 = im
            while i1 and t[i1 - 1] < t[i1]:
                i1 -= 1
            ib = i1

            i1 = im
            while i1 + 1 < len(t) and t[i1 + 1] < t[i1]:
                i1 += 1
            ie = i1
            # print(t)
            # print("cut: [%s: %s]" %  (ib, ie))
            t[ib:(ie + 1)] = 0
            # print(t)
        return ([float(e) for e in xml],
                [float(e) for e in yml],
                max(eml))

    def __findpeaks2(self, x, y, nr=20):
        """ find peaks from diffractogram with scipy

        :param x:  x of diffractogram
        :type x:  :obj:`list` <float>>
        :param y:  values of diffractogram
        :type y:  :obj:`list` <float>>
        :param nr:  list of peak x's for each diffractogram
        :type nr: :obj:`int`
        :returns: (peak_xs, peak_values, x_error)
        :rtype: (:obj:`list` <float>, :obj:`list` <float>, :obj:`float`)
        """
        f = scipy.interpolate.InterpolatedUnivariateSpline(x, y, k=4)
        xml = f.derivative().roots()
        yml = f(xml)
        er = max([(x[i+1] - x[i]) for i in range(len(x) - 1)])
        iml = np.argpartition(yml, -nr)[-nr:]
        iml = iml[np.argsort(-yml[iml])]
        iml = iml[:nr]
        return ([float(e) for e in xml[iml]],
                [float(e) for e in yml[iml]],
                er)

    # @debugmethod
    @QtCore.pyqtSlot()
    def _setPolarRange(self):
        """ launches range widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        nrplots = self.__ui.diffSpinBox.value()
        if nrplots:
            cnfdlg = diffRangeDialog.DiffRangeTabDialog(nrplots)
            cnfdlg.azstart = self.__azstart
            cnfdlg.azend = self.__azend
            cnfdlg.radstart = self.__radstart
            cnfdlg.radend = self.__radend
            cnfdlg.radunitindex = 2
            cnfdlg.createGUI()
            if cnfdlg.exec_():
                self.__azstart = cnfdlg.azstart
                self.__azend = cnfdlg.azend
                self.__radstart = cnfdlg.radstart
                self.__radend = cnfdlg.radend
                self.__updateregion()
                self._resetAccu()
                self._mainwidget.emitTCC()

    # @debugmethod
    def _updatePolarRange(self, ranges):
        """ update diffractogram ranges

        :param ranges: list of [azimuth_start, azimuth_end,
                                radial_start, radial_end]
                       elements for each diffractograms
        :type ranges: :obj:`list` < [
                           :obj:`float`, :obj:`float`,
                           :obj:`float`, :obj:`float` ]>
        """
        nrplots = self.__ui.diffSpinBox.value()
        if nrplots:
            azstart = []
            azend = []
            radstart = []
            radend = []
            for rn in ranges:
                azstart.append(rn[0])
                azend.append(rn[1])
                radstart.append(rn[2])
                radend.append(rn[3])
            self.__azstart = azstart
            self.__azend = azend
            self.__radstart = radstart
            self.__radend = radend
            self.__updateregion()
            self._resetAccu()
            self._mainwidget.emitTCC()

    def __updateaz(self):
        """ update azimuth range in deg
        """
        nrplots = self.__ui.diffSpinBox.value()
        self.__azrange = []
        for _ in range(len(self.__azend), nrplots):
            self.__azend.append(None)
        for _ in range(len(self.__azstart), nrplots):
            self.__azstart.append(None)
        for i in range(nrplots):
            if self.__azend[i] is None and self.__azstart[i] is None:
                self.__azrange.append(None)
            elif (self.__azend[i] is not None
                  or self.__azstart[i] is not None):
                if self.__azstart[i] is None:
                    self.__azstart[i] = 0
                if self.__azend[i] is None:
                    self.__azend[i] = 360
                self.__azrange.append([self.__azstart[i], self.__azend[i]])

    def __updaterad(self):
        """update radial range in deg
        """
        nrplots = self.__ui.diffSpinBox.value()
        self.__radrange = []
        for _ in range(len(self.__radend), nrplots):
            self.__radend.append(None)
        for _ in range(len(self.__radstart), nrplots):
            self.__radstart.append(None)
        for i in range(nrplots):
            if self.__radend[i] is not None or \
               self.__radstart[i] is not None:
                if self.__radstart[i] is None:
                    self.__radstart[i] = 0
                if self.__radend[i] is None:
                    self.__radend[i] = 90
            if self.__radend[i] is None or self.__radstart[i] is None:
                self.__radrange.append(None)
            else:
                if self.__unitindex == 2:
                    self.__radrange.append(
                        [self.__radstart[i], self.__radend[i]])
                else:
                    rs = self.__radstart[i] * math.pi / 180.
                    re = self.__radend[i] * math.pi / 180.
                    if self.__unitindex < 2:
                        oneoverlength = self.__settings.energy / 12398.4193
                        fac = 4 * math.pi * oneoverlength
                        qs = fac * math.sin(rs/2.)
                        qe = fac * math.sin(re/2.)
                        if self.__unitindex == 0:
                            qs = qs * 10.
                            qe = qe * 10.
                        self.__radrange.append([qs, qe])
                    elif self.__unitindex == 3:
                        self.__radrange.append([rs, re])
                    elif self.__unitindex in [4, 5]:
                        try:
                            [rbb, rbe, reb, ree, _, _, _, _] = \
                                self.__getcorners(
                                    self.__radstart[i],
                                    self.__radend[i],
                                    self.__azstart[i],
                                    self.__azend[i])
                            logger.debug(
                                "RESULT %s %s %s" % (
                                    str(rbb.x), rbb.success, rbb.fun))
                            logger.debug(
                                "RESULT %s %s %s" % (
                                    str(rbe.x), rbe.success, rbe.fun))
                            logger.debug(
                                "RESULT %s %s %s" % (
                                    str(reb.x), reb.success, reb.fun))
                            logger.debug(
                                "RESULT %s %s %s" % (
                                    str(ree.x), ree.success, ree.fun))
                            rsl = []
                            rel = []
                            if rbb.success:
                                with QtCore.QMutexLocker(
                                        self.__settings.aimutex):
                                    ra = self.__settings.ai.rFunction(
                                        np.array([rbb.x[1] - 0.5]),
                                        np.array([rbb.x[0] - 0.5]))
                                    if len(ra):
                                        rsl.append(ra[0] * 1000.)
                            if rbe.success:
                                with QtCore.QMutexLocker(
                                        self.__settings.aimutex):
                                    ra = self.__settings.ai.rFunction(
                                        np.array([rbe.x[1] - 0.5]),
                                        np.array([rbe.x[0] - 0.5]))
                                    if len(ra):
                                        rsl.append(ra[0] * 1000.)

                            if reb.success:
                                with QtCore.QMutexLocker(
                                        self.__settings.aimutex):
                                    ra = self.__settings.ai.rFunction(
                                        np.array([reb.x[1] - 0.5]),
                                        np.array([reb.x[0] - 0.5]))
                                    if len(ra):
                                        rel.append(ra[0] * 1000.)
                            if ree.success:
                                with QtCore.QMutexLocker(
                                        self.__settings.aimutex):
                                    ra = self.__settings.ai.rFunction(
                                        np.array([ree.x[1] - 0.5]),
                                        np.array([ree.x[0] - 0.5]))
                                    if len(ra):
                                        rel.append(ra[0] * 1000.)
                            if rsl:
                                rs = np.mean(rsl)
                            else:
                                rs = math.tan(rs) * self.__settings.detdistance
                            if rel:
                                re = np.mean(rel)
                            else:
                                re = math.tan(re) * self.__settings.detdistance
                        except Exception as e:
                            logger.debug(str(e))
                            rs = math.tan(rs) * self.__settings.detdistance
                            re = math.tan(re) * self.__settings.detdistance
                        self.__radrange.append([rs, re])

    def __updateregion(self):
        """ update diffractogram region
        """
        self.__updateaz()
        self.__updaterad()
        self.updateRangeTip()
        self.runProgress(["findregions"], "_updateRegionsAndPlot")

    # @debugmethod
    def findregions(self):
        """ find regions lists
        """
        nrplots = self.__ui.diffSpinBox.value()
        regions = []
        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        for i in range(nrplots):
            if ((self.__azrange and self.__azrange[i]) or
               (self.__radrange and self.__radrange[i])) and aistat:
                azstart = self.__azstart[i] \
                    if self.__azstart[i] is not None else 0
                azend = self.__azend[i] \
                    if self.__azend[i] is not None else 360
                radstart = self.__radstart[i] \
                    if self.__radstart[i] is not None else 0
                radend = self.__radend[i] \
                    if self.__radend[i] is not None else 70
                try:
                    regions.append(
                        self.__findregion(radstart, radend, azstart, azend))
                except Exception as e:
                    try:
                        logger.warning(str(e))
                        # print(str(e))
                        regions.append(
                            self.__findregion2(
                                radstart, radend, azstart, azend))
                    except Exception as e2:
                        logger.warning(str(e2))
                        # print(str(e2))
                        # regions.append([])
        self.__regions = regions

    # @debugmethod
    def _updateRegionsAndPlot(self, regions=None):
        """ update regions and plots

        :param regions: list of region lines
        :type regions: :obj:`list` <  :obj:`list` <  :obj:`list`
                  < (:obj:`float`, :obj:`float`) > > >
        """
        regions = regions if regions is not None else self.__regions
        self._mainwidget.updateRegions(regions)
        self._resetAccu()
        self._plotDiff()
        self._closeReset()

    # @debugmethod
    def _closeReset(self):
        """ close reset method for progressbar

        :returns: progress status
        :rtype: :obj:`bool`
        """
        status = True
        logger.debug("closing Progress")
        if self.__progress:
            self.__progress.reset()
        if self.__commandthread and self.__commandthread.error:
            logger.error(
                "Problems in updating Channels %s" %
                str(self.__commandthread.error))
            self.__commandthread.error = None
            status = False
        if self.__progress:
            self.__progress.setParent(None)
            self.__progress = None
        self.waitForThread()
        logger.debug("closing Progress ENDED")
        return status

    def __findregion2(self, radstart, radend, azstart, azend):
        """ find region defined by angle range using image masking method

        :param radstart: start of radial region
        :type radstart: :obj:`float`
        :param radend: end of radial region
        :type radend: :obj:`float`
        :param azstart: start of azimuth region
        :type azstart: :obj:`float`
        :param azend: end of azimuth region
        :type azend: :obj:`float`
        :returns: list of region lines
        :rtype:  :obj:`list` < :obj:`list` < (float, float) > >
        """
        if azend - azstart >= 360:
            azstart = 0
            azend = 360
        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        if aistat:
            dts = self._mainwidget.rawData()

            if dts is not None and dts.shape and len(dts.shape) == 2:
                shape = dts.T.shape
            else:
                shape = [1000., 1000.]
            with QtCore.QMutexLocker(self.__settings.aimutex):
                tta = self.__settings.ai.twoThetaArray(shape)
                cha = self.__settings.ai.chiArray(shape)
            rb = self.__degtrim(radstart, 0, 360) * math.pi / 180.
            re = self.__degtrim(radend, 0, 360) * math.pi / 180.

            ab = self.__degtrim(azstart, -180, 180) * math.pi / 180.
            ae = self.__degtrim(azend, -180, 180) * math.pi / 180.

            lines = []

            if azend - azstart < 360:
                chmask = (cha < ab) | (cha > ae)
                ttaa = (tta - rb) * (tta - re)
                ttaa[chmask] = 6
                rblines = functions.isocurve(
                    ttaa, 0, connected=True)
                logger.debug("RUN1 %s " % len(rblines))

                thmask = (tta < rb) | (tta > re)
                chaa = (cha - ab) * (cha - ae)
                chaa[thmask] = 6
                ablines = functions.isocurve(
                    chaa, 0, connected=True)
                logger.debug("RUN2 %s " % len(ablines))
            else:
                ttaa = (tta - rb) * (tta - re)
                rblines = functions.isocurve(
                    ttaa, 0, connected=True)
                logger.debug("RUN4 %s " % len(rblines))

            for line in rblines:
                lines.append([(p[1], p[0]) for p in line])
            if azend - azstart < 360:
                for line in ablines:
                    lines.append([(p[1], p[0]) for p in line])
            # for line in relines:
            #     lines.append([(p[1], p[0]) for p in line])

            # print(lines)
            return lines
            # self._mainwidget.updateRegions(lines)

        else:
            return []
            # self._mainwidget.updateRegions([[(0, 0)]])

    def __findregion(self, radstart, radend, azstart, azend):
        """ find region defined by angle range using Newton method

        :param radstart: start of radial region
        :type radstart: :obj:`float`
        :param radend: end of radial region
        :type radend: :obj:`float`
        :param azstart: start of azimuth region
        :type azstart: :obj:`float`
        :param azend: end of azimuth region
        :type azend: :obj:`float`
        :returns: list of region lines
        :rtype:  :obj:`list` < :obj:`list` < (float, float) > >
        """
        if azend - azstart >= 360:
            azstart = 0
            azend = 360
        [rbb, rbe, reb, ree, rb, re, ab, ae] = self.__getcorners(
            radstart, radend, azstart, azend)
        azb = azstart * math.pi / 180.
        aze = azend * math.pi / 180.
        logger.debug("RESULT %s %s %s" % (str(rbb.x), rbb.success, rbb.fun))
        logger.debug("RESULT %s %s %s" % (str(rbe.x), rbe.success, rbe.fun))
        logger.debug("RESULT %s %s %s" % (str(reb.x), reb.success, reb.fun))
        logger.debug("RESULT %s %s %s" % (str(ree.x), ree.success, ree.fun))
        # print("RESULT %s %s %s" % (str(rbb.x), rbb.success, rbb.fun))
        # print("RESULT %s %s %s" % (str(rbe.x), rbe.success, rbe.fun))
        # print("RESULT %s %s %s" % (str(reb.x), reb.success, reb.fun))
        # print("RESULT %s %s %s" % (str(ree.x), ree.success, ree.fun))
        lines = []
        if azend - azstart < 360:
            pbbeb = self.__findfixchipath(rbb.x, reb.x, ab, rb, re)
            lines.append(pbbeb)
            pbeee = self.__findfixchipath(rbe.x, ree.x, ae, rb, re)
            lines.append(pbeee)
        if self.__radstart[0] > 0:
            pbbbe = self.__findfixradpath(
                rbb.x, rbe.x, rb, azb, aze,
                full=(azend - azstart >= 360))
            lines.append(pbbbe)
        if self.__radend[0] < 60:
            pebee = self.__findfixradpath(
                reb.x, ree.x, re, azb, aze,
                full=(azend - azstart >= 360))
            lines.append(pebee)
        return lines

    @classmethod
    def __degtrim(cls, vl, lowbound, upbound):
        """ trim angle value to bounds in deg

        :param vl: value to trim
        :type vl: :obj:`float`
        :param lowbound: lower bound of value
        :type lowbound: :obj:`float`
        :param upbound: upper blund of value
        :type upbound: :obj:`float`
        :returns: trimmed value
        :rtype: :obj:`float`
        """
        while vl >= upbound:
            vl -= 360
        while vl < lowbound:
            vl += 360
        return vl

    @classmethod
    def __radtrim(cls, vl, lowbound, upbound):
        """ trim angle value to bounds in rad

        :param vl: value to trim
        :type vl: :obj:`float`
        :param lowbound: lower bound of value
        :type lowbound: :obj:`float`
        :param upbound: upper blund of value
        :type upbound: :obj:`float`
        :returns: trimmed value
        :rtype: :obj:`float`
        """
        while vl >= upbound:
            vl -= 2 * math.pi
        while vl < lowbound:
            vl += 2 * math.pi
        return vl

    def __findfixchipath(self, xstart, xend, chi, radstart, radend,
                         step=4, fmax=1.e-10):
        """ find a path for fix azimuth angle

        :param xstart: start point
        :type xstart: :obj:`float`
        :param xend: end point
        :type xend: :obj:`float`
        :param chi: chi angle value
        :type chi: :obj:`float`
        :param radstart: radial angle start value
        :type radstart: :obj:`float`
        :param radend: radial angle end value
        :type radend: :obj:`float`
        :param fmax: maximal allowed value for the test function
        :type fmax: :obj:`float`
        :returns: list of points
        :rtype: :obj:`list` < (float, float) >
        """
        points = [tuple(xstart)]

        if self.__dist2(xstart, xend) < step * step:
            points.append(tuple(xend))
            return points

        alphas = []
        cut = None
        tchi = self.__radtrim(chi, -math.pi, math.pi)
        if tchi < -math.pi/2 or tchi > math.pi/2:
            cut = 0
        cchi = self.__chi(xstart, cut)
        x = xstart

        def rsfun(alpha, x, step, cut, chi):
            y = [x[0] + step * math.cos(alpha),
                 x[1] + step * math.sin(alpha)]
            return [self.__chi(y, cut) - chi]

        res = scipy.optimize.root(rsfun, cchi, (x, step, cut, cchi))
        y = [x[0] + step * math.cos(res.x[0]),
             x[1] + step * math.sin(res.x[0])]
        if self.__tth(x) - self.__tth(y) > 0 or \
           (not res.success and abs(res.fun) > fmax):
            res = scipy.optimize.root(rsfun, - cchi, (x, step, cut, cchi))
            y = [x[0] + step * math.cos(res.x[0]),
                 x[1] + step * math.sin(res.x[0])]
            if self.__tth(x) - self.__tth(y) > 0 or \
               (not res.success and abs(res.fun) > fmax):
                raise Exception("__findfixchipath: Cannot find the next point")

        points.append(tuple(y))
        if self.__dist2(y, xend) < step * step:
            points.append(tuple(xend))
            return points
        alphas.append(res.x[0])

        waking = True
        maxit = 10000
        it = 0
        istep = step
        while waking and maxit > it:
            it += 1
            alp = self.__fitnext(alphas[-5:])
            x = y
            res = scipy.optimize.root(rsfun, alp, (x, istep, cut, cchi))
            y = [x[0] + istep * math.cos(res.x[0]),
                 x[1] + istep * math.sin(res.x[0])]
            if self.__tth(x) - self.__tth(y) > 0 or \
               (not res.success and abs(res.fun) > fmax):
                istep = step / 2.
                continue

            points.append(tuple(y))
            if self.__dist2(y, xend) < istep * istep:
                waking = False
            alphas.append(res.x[0])
            istep = step
        points.append(tuple(xend))
        return points

    def __findfixradpath(self, xstart, xend, rad, azstart, azend,
                         step=4, fmax=1.e-10, full=False):
        """ find a path for fixed radial angle

        :param xstart: start point
        :type xstart: :obj:`float`
        :param xend: end point
        :type xend: :obj:`float`
        :param rad: radial angle value
        :type rad: :obj:`float`
        :param azstart: azimuth angle start value
        :type azstart: :obj:`float`
        :param azend: azimuth angle end value
        :type azend: :obj:`float`
        :param fmax: maximal allowed value for the test function
        :type fmax: :obj:`float`
        :param full: full angle flag
        :type full: :obj:`bool`
        :returns: list of points
        :rtype: :obj:`list` < (float, float) >
        """
        aze = azend
        points = [tuple(xstart)]
        while azstart > aze:
            aze += 2 * math.pi

        alphas = []
        cut = None
        tth1 = self.__tth(xstart)
        tth2 = self.__tth([xstart[0] + 1, xstart[1]])
        tth3 = self.__tth([xstart[0], xstart[1] + 1])
        dth = max(abs(tth1 - tth2), abs(tth1 - tth3))
        if (rad/dth) < 10. * step:
            step = (rad / dth) / 10.
        elif (rad/dth) > 10000. * step:
            step = (rad / dth) / 10000.
        if ((self.__dist2(xstart, xend) < step * step
             and abs(azstart - aze) < math.pi) or step < 1.e-6):
            points.append(tuple(xend))
            return points

        # tth = self.__tth(xstart)
        tchi = self.__chi(xstart)

        if tchi < -math.pi/2 or tchi > math.pi/2:
            cut = 0
        cchi = self.__chi(xstart, cut)
        x = xstart
        logger.debug("CUT %s %s " % (cut, cchi))

        def rsfun(alpha, x, step, cut, tth):
            y = [x[0] + step * math.cos(alpha),
                 x[1] + step * math.sin(alpha)]
            return [self.__tth(y) - tth]

        itm = 10
        it = 0
        istep = step
        while it < itm:
            it += 1
            res = scipy.optimize.root(rsfun, cchi + math.pi/2,
                                      (x, istep, cut, rad))
            y = [x[0] + istep * math.cos(res.x[0]),
                 x[1] + istep * math.sin(res.x[0])]
            if self.__chi(x, cut) - self.__chi(y, cut) > 0 or \
               (not res.success and abs(res.fun) > fmax):
                res = scipy.optimize.root(rsfun, -cchi - math.pi/2,
                                          (x, istep, cut, rad))
                y = [x[0] + istep * math.cos(res.x[0]),
                     x[1] + istep * math.sin(res.x[0])]
                if self.__chi(x, cut) - self.__chi(y, cut) > 0 or \
                   (not res.success and abs(res.fun) > fmax):
                    istep = istep / 2.
                else:
                    break
            else:
                break
        if it == itm:
            raise Exception("__findfixradpath: Cannot find the next point")

        points.append(tuple(y))
        if self.__dist2(y, xend) < step * step and not full:
            points.append(tuple(xend))
            return points
        alphas.append(res.x[0])

        waking = True
        maxit = 10000
        it = 0
        istep = step
        while waking and maxit > it:
            it += 1
            alp = self.__fitnext(alphas[-5:])
            x = y
            tchi = self.__chi(x, cut)
            if tchi < -math.pi/2 or tchi > math.pi/2:
                cut = 0
            else:
                cut = None

            res = scipy.optimize.root(rsfun, alp, (x, istep, cut, rad))
            y = [x[0] + istep * math.cos(res.x[0]),
                 x[1] + istep * math.sin(res.x[0])]
            if self.__chi(x, cut) - self.__chi(y, cut) > 0 or \
               (not res.success and abs(res.fun) > fmax):
                istep = step / 2.
                continue

            points.append(tuple(y))
            if self.__dist2(y, xend) < istep * istep:
                waking = False
            alphas.append(res.x[0])
            istep = step
        points.append(tuple(xend))
        return points

    def __fitnext(self, y, x=None, x0=None):
        """ fits next y value

        :param y: list of y values
        :type y: :obj:`list` <:obj:`float`>
        :param x: list of x values
        :type x: :obj:`list` <:obj:`float`>
        :param x0: next x value
        :type x0: :obj:`float`
        :returns: next y value
        :rtype: :obj:`float`
        """
        n = len(y)
        if x is None:
            x = range(n)
            x0 = n
        return np.poly1d(np.polyfit(x, y, n - 1))(x0)

    def __dist2(self, x, y):
        """ distance square of x and y

        :param x: 2d point x
        :type x: :obj:`list` <:obj:`float`>
        :param y: 2d point y
        :type y: :obj:`list` <:obj:`float`>
        :returns: distance square
        :rtype: :obj:`float`
        """
        d0 = x[0] - y[0]
        d1 = x[1] - y[1]
        return d0 * d0 + d1 * d1

    def __chi(self, x, cut=None):
        """ chi of left bottom pixel corner in rad

        :param x: 2d point x
        :type x: :obj:`list` <:obj:`float`>
        :param cut: cut position in rad
        :type cut: :obj:`float`
        :returns: chi value
        :rtype: :obj:`float`
        """
        with QtCore.QMutexLocker(self.__settings.aimutex):
            chi = float(self.__settings.ai.chi(
                np.array([x[1] - 0.5]), np.array([x[0] - 0.5]))[0])
        if cut is not None and chi > cut and cut > -math.pi:
            chi += 2 * math.pi
        return chi

    def __tth(self, x, path=None):
        """ tth of left bottom pixel corner in rad

        :param x: 2d point x
        :type x: :obj:`list` <:obj:`float`>
        :param path: path method
        :type path: :obj:`str`
        :returns: chi value
        :rtype: :obj:`float`
        """
        with QtCore.QMutexLocker(self.__settings.aimutex):
            tth = self.__settings.ai.tth(
                np.array([x[1] - 0.5]), np.array([x[0] - 0.5]), path=path)[0]
        return float(tth)

    def __findpoint(self, rd, az, shape, start=None, itmax=20, fmax=1e-9):
        """ find a point in pixels

        :param rd: radial coordinate
        :type rd: :obj:`float`
        :param az: azimuth coordinate
        :type az: :obj:`float`
        :param shape: shape of the image
        :type shape: [:obj:`float`, :obj:`float`]
        :param start: start coordinate
        :type start: [:obj:`float`, :obj:`float`]
        :param itmaxstart: maximal number of tries
        :type start: :obj:`int`
        :param fmax: maximal allowed value for the test function
        :type fmax: :obj:`float`
        """
        def rafun(x, f1, f2):
            return [self.__tth(x) - f1, self.__chi(x) - f2]
        found = False
        it = 0
        if start is None:
            start = self.__approxpoint(rd, az)
        while not found and it < itmax:
            res = scipy.optimize.root(rafun, start, (rd, az))
            f = res.fun
            f2 = f[0] * f[0] + f[1] * f[1]
            found = res.success and f2 < fmax
            it += 1
            start = [random.randint(0, shape[0]),
                     random.randint(0, shape[1])]
        logger.debug("Tries: %s" % it)
        logger.debug(res)
        return res

    def __getcorners(self, radstart, radend, azstart, azend):
        """ find region corners

        :param radstart: start of radial region in deg
        :type radstart: :obj:`float`
        :param radend: end of radial region in deg
        :type radend: :obj:`float`
        :param azstart: start of azimuth region in deg
        :type azstart: :obj:`float`
        :param azend: end of azimuth region in deg
        :type azend: :obj:`float`
        :returns: [rbb, rbe, reb, ree, rb, re, ab, ae]
                  where rbb, rbe, reb, ree
                   are result objects of found region corners
                  while rb, re, ab, ae
                   are input angles in radians
        :rtype:  :obj:`list` <:obj:`float`>
        """

        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        if aistat:
            dts = self._mainwidget.rawData()
            if dts is not None and dts.shape and len(dts.shape) == 2:
                shape = dts.shape
            else:
                shape = [1000., 1000.]

            rb = self.__degtrim(radstart, 0, 360) * math.pi / 180.
            re = self.__degtrim(radend, 0, 360) * math.pi / 180.
            ab = self.__degtrim(azstart, -180, 180) * math.pi / 180.
            ae = self.__degtrim(azend, -180, 180) * math.pi / 180.

            rbb = self.__findpoint(rb, ab, shape)
            rbe = self.__findpoint(rb, ae, shape)
            ree = self.__findpoint(re, ae, shape)
            reb = self.__findpoint(re, ab, shape)

            return [rbb, rbe, reb, ree, rb, re, ab, ae]

    def __approxpoint(self, rad, az):
        """ find approximate x,y coorinates from angles

        :param rad: radial angle in rad
        :type rad: :obj:`float`
        :param az: azimuth angle in rad
        :type az: :obj:`float`
        :returns: [x, y] coordinates
        :rtype:  [:obj:`float`, :obj:`float`]
        """
        with QtCore.QMutexLocker(self.__settings.aimutex):
            aistat = self.__settings.ai is not None
        if aistat:
            tnr = math.tan(rad)
            csa = math.cos(az)
            sna = math.sin(az)
            dst = self.__settings.detdistance
            xc = self.__settings.centerx
            yc = self.__settings.centery
            px = self.__settings.pixelsizex / 1000.
            py = self.__settings.pixelsizey / 1000.
            y = (dst * sna * tnr + yc * py)/py
            x = (dst * csa * tnr + xc * px)/px
            return [x, y]

    # @debugmethod
    @QtCore.pyqtSlot(int)
    def _setUnitIndex(self, uindex):
        """ set unit index

        :param uindex: unit index, i.e. q_nm^-1, q_A^-1, 2th_deg, 2th_rad
        :type uindex: :obj:`int`
        """
        if self.__unitindex != uindex:
            self._resetAccu()
            self.__unitindex = uindex
        self.__updaterad()
        self._plotDiff()

    # @debugmethod
    @QtCore.pyqtSlot(int)
    def _setPlotIndex(self, pindex):
        """ set plot index

        :param pindex: plot index -> 0: Image, <i>: Buffer <i>
        :type pindex: :obj:`int`
        """
        if pindex and pindex > 0:
            self.parameters.centerlines = False
            self.parameters.toolscale = True
            self.parameters.regions = False
            if len(self.__xbuffers) >= pindex and \
               self.__xbuffers[pindex - 1]:
                pos, sc = self.__xbuffers[pindex - 1]
                self._mainwidget.setToolScale([pos, 0], [sc, 1])
            else:
                self._mainwidget.setToolScale([0, 0], [1, 1])
            # self._mainwidget.setToolScale([0, 0], [1, 1])
            if not self.__plotindex:
                self.__oldlocked = self._mainwidget.setAspectLocked(False)
        else:
            if self.__oldlocked is not None:
                self._mainwidget.setAspectLocked(self.__oldlocked)
            self.parameters.centerlines = True
            self.parameters.toolscale = False
            self.parameters.regions = True
        if pindex is not None:
            self.__plotindex = pindex
        self._mainwidget.updateinfowidgets(self.parameters)
        self._mainwidget.emitReplotImage()

    # @debugmethod
    @QtCore.pyqtSlot()
    def updateRangeTip(self):
        """ update geometry tips
        """
        text = u""
        nrplots = self.__ui.diffSpinBox.value()
        for i in range(nrplots):
            if nrplots > 1:
                text += "%s. " % (i + 1)
            text += \
                u"Radial range: [%s, %s] deg; Azimuth range: [%s, %s] deg" % (
                    self.__radstart[i]
                    if (len(self.__radstart) > i and
                        self.__radstart[i] is not None)
                    else "0",
                    self.__radend[i]
                    if (len(self.__radend) > i and
                        self.__radend[i] is not None)
                    else "90",
                    self.__azstart[i]
                    if (len(self.__azstart) > i and
                        self.__azstart[i] is not None)
                    else "0",
                    self.__azend[i]
                    if (len(self.__azend) > i and
                        self.__azend[i] is not None)
                    else "360")
            if i < nrplots - 1:
                text += "\n"
        self.__ui.rangePushButton.setToolTip(text)


class MaximaToolWidget(ToolBaseWidget):
    """ maxima tool widget
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
        self.parameters.toolscale = False
        self.parameters.maxima = True
        # self.parameters.rightplot = True

        #: (`lavuelib..imageDisplayWidget.AxesParameters`) axes backup
        self.__axes = None

        #: (:class:`lavuelib.settings.Settings`) configuration settings
        self.__settings = self._mainwidget.settings()

        #: (:obj:`float`) radail coordinate factor
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
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self.__ui.maximaComboBox.currentIndexChanged, self._replot],
            [self.__ui.maximaComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self.__ui.numberSpinBox.valueChanged, self._replot],
            [self.__ui.numberSpinBox.valueChanged, self._mainwidget.emitTCC],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.geometryChanged, self._mainwidget.emitTCC],
            [self._mainwidget.mouseImagePositionChanged, self._message]
        ]

    # @debugmethod
    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "geometry" in cnf.keys():
                try:
                    self._updateGeometry(cnf["geometry"])
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))
            if "maxima_number" in cnf.keys():
                try:
                    self.__ui.numberSpinBox.setValue(int(cnf["maxima_number"]))
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if "units" in cnf.keys():
                idxs = ["angles", "q-space", "xy-space"]
                xcrd = str(cnf["units"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.angleqComboBox.setCurrentIndex(idx)
            if "current_maximum" in cnf.keys():
                try:
                    cmx = int(cnf["current_maximum"]) - 1
                    self.__ui.maximaComboBox.setCurrentIndex(cmx)
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))
                    cmx = 0

    # @debugmethod
    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["units"] = str(
            self.__ui.angleqComboBox.currentText()).lower()
        cnf["maxima_number"] = self.__ui.numberSpinBox.value()
        cnf["current_maximum"] = self.__ui.maximaComboBox.currentIndex() + 1
        cnf["geometry"] = {
            "centerx": self.__settings.centerx,
            "centery": self.__settings.centery,
            "energy": self.__settings.energy,
            "pixelsizex": self.__settings.pixelsizex,
            "pixelsizey": self.__settings.pixelsizey,
            "detdistance": self.__settings.detdistance,
        }
        return json.dumps(cnf)

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

    # @debugmethod
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

        QtCore.QCoreApplication.processEvents()
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
        if self.__settings.sendresults:
            self.__sendresults(maxidxs)
        return idx

    def __sendresults(self, maxidxs):
        """ send results to LavueController

        :param maxidxs: list with [[xn,yn, maxn], ... [x1,y1, max1]]
        :type maxidxs:
        """
        results = {"tool": self.alias}
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["maxima"] = maxidxs
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

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
            wavelength = 12398.4193 / self.__settings.energy
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

    # @debugmethod
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
            self._mainwidget.emitTCC()

    # @debugmethod
    @QtCore.pyqtSlot()
    def _updateGeometry(self, geometry):
        """ update geometry widget

        :param geometry: geometry dictionary
        :type geometry: :obj:`dict` < :obj:`str`, :obj:`list`>
        """
        try:
            if "centerx" in geometry.keys():
                self.__settings.centerx = float(geometry["centerx"])
                self._mainwidget.writeAttribute(
                    "BeamCenterX", float(self.__settings.centerx))
        except Exception:
            pass
        try:
            if "centery" in geometry.keys():
                self.__settings.centery = float(geometry["centery"])
                self._mainwidget.writeAttribute(
                    "BeamCenterY", float(self.__settings.centery))
        except Exception:
            pass
        try:
            if "energy" in geometry.keys():
                self.__settings.energy = float(geometry["energy"])
                self._mainwidget.writeAttribute(
                    "Energy", float(self.__settings.energy))
        except Exception:
            pass
        try:
            if "pixelsizex" in geometry.keys():
                self.__settings.pixelsizex = float(geometry["pixelsizex"])
        except Exception:
            pass
        try:
            if "pixelsizey" in geometry.keys():
                self.__settings.pixelsizey = float(geometry["pixelsizey"])
        except Exception:
            pass
        try:
            if "detdistance" in geometry.keys():
                self.__settings.detdistance = float(geometry["detdistance"])
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
        except Exception:
            pass
        if geometry:
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)
            if self.__plotindex:
                self._mainwidget.emitReplotImage()
            self._mainwidget.emitTCC()

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

        #: (:class:`lavuelib.settings.Settings`) configuration settings
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
            [self.__ui.angleqComboBox.currentIndexChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.mouseImageDoubleClicked,
             self._updateCenter],
            [self._mainwidget.mouseImagePositionChanged, self._message],
            [self._mainwidget.geometryChanged, self.updateGeometryTip],
            [self._mainwidget.geometryChanged, self._mainwidget.emitTCC],

            [self.applyROIPressed, self._mainwidget.applyROIs],
            [self.fetchROIPressed, self._mainwidget.fetchROIs],
            [self.roiInfoChanged, self._mainwidget.updateDisplayedText],
            [self.__ui.labelROILineEdit.textChanged,
             self._updateApplyButton],
            [self.__ui.roiSpinBox.valueChanged, self._mainwidget.updateROIs],
            [self.__ui.roiSpinBox.valueChanged, self._mainwidget.emitTCC],
            [self.__ui.roiSpinBox.valueChanged,
             self._mainwidget.writeDetectorROIsAttribute],
            [self.__ui.labelROILineEdit.textEdited,
             self._writeDetectorROIs],
            [self.__ui.labelROILineEdit.textEdited, self._mainwidget.emitTCC],
            [self._mainwidget.roiLineEditChanged, self._updateApplyButton],
            [self._mainwidget.roiAliasesChanged, self.updateROILineEdit],
            [self._mainwidget.roiValueChanged, self.updateROIDisplayText],
            [self._mainwidget.roiNumberChanged, self.setROIsNumber],
            [self._mainwidget.sardanaEnabled, self.updateROIButton],
            [self._mainwidget.mouseImagePositionChanged, self._roimessage],

            [self.__ui.funComboBox.currentIndexChanged,
             self._setFunction],
            [self.__ui.rowsliceLineEdit.textChanged, self._updateRows],
            [self.__ui.rowsliceLineEdit.textChanged, self._mainwidget.emitTCC],
            [self.__ui.columnsliceLineEdit.textChanged, self._updateColumns],
            [self.__ui.columnsliceLineEdit.textChanged,
             self._mainwidget.emitTCC],
            [self._mainwidget.scalesChanged, self._updateRows],
            [self._mainwidget.scalesChanged, self._updateColumns],
        ]

    def configure(self, configuration):
        """ set configuration for the current tool

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        if configuration:
            cnf = json.loads(configuration)
            if "geometry" in cnf.keys():
                try:
                    self._updateGeometry(cnf["geometry"])
                except Exception as e:
                    # print(str(e))
                    logger.warning(str(e))
            if "rois_number" in cnf.keys():
                try:
                    self.__ui.roiSpinBox.setValue(int(cnf["rois_number"]))
                except Exception as e:
                    logger.warning(str(e))
                    # print(str(e))
            if "aliases" in cnf.keys():
                aliases = cnf["aliases"]
                if isinstance(aliases, list):
                    aliases = " ".join(aliases)
                self.__ui.labelROILineEdit.setText(aliases)
            if "units" in cnf.keys():
                idxs = ["angles", "q-space"]
                xcrd = str(cnf["units"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.angleqComboBox.setCurrentIndex(idx)
            if "apply" in cnf.keys():
                if cnf["apply"]:
                    self._emitApplyROIPressed()
            if "fetch" in cnf.keys():
                if cnf["fetch"]:
                    self._emitFetchROIPressed()
            if "mapping" in cnf.keys():
                idxs = ["mean", "sum"]
                xcrd = str(cnf["mapping"]).lower()
                try:
                    idx = idxs.index(xcrd)
                except Exception:
                    idx = 0
                self.__ui.funComboBox.setCurrentIndex(idx)
            if "rows" in cnf.keys():
                self.__ui.rowsliceLineEdit.setText(cnf["rows"])
            if "columns" in cnf.keys():
                self.__ui.columnsliceLineEdit.setText(cnf["columns"])

    def configuration(self):
        """ provides configuration for the current tool

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        cnf = {}
        cnf["aliases"] = str(self.__ui.labelROILineEdit.text()).split(" ")
        cnf["rois_number"] = self.__ui.roiSpinBox.value()
        cnf["mapping"] = str(
            self.__ui.funComboBox.currentText()).lower()
        cnf["rows"] = self.__ui.rowsliceLineEdit.text()
        cnf["columns"] = self.__ui.columnsliceLineEdit.text()
        cnf["units"] = str(
            self.__ui.angleqComboBox.currentText()).lower()
        cnf["geometry"] = {
            "centerx": self.__settings.centerx,
            "centery": self.__settings.centery,
            "energy": self.__settings.energy,
            "pixelsizex": self.__settings.pixelsizex,
            "pixelsizey": self.__settings.pixelsizey,
            "detdistance": self.__settings.detdistance,
        }
        return json.dumps(cnf)

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
                else:
                    s1 = 1.0
                    s2 = 1.0
                    xx = list(range(len(sx)))
                    yy = list(range(len(sy)))
                width = [s1] * len(sx)
                height = [s2] * len(sy)
                self.__bottomplot.setOpts(
                    y0=[0]*len(sx), y1=sx, x=xx,
                    width=width)
                self.__bottomplot.drawPicture()
                self.__rightplot.setOpts(
                    x0=[0]*len(sy), x1=sy, y=yy,
                    height=height)
                self.__rightplot.drawPicture()
                if self.__settings.sendresults:
                    xslice = self.__dsrows
                    yslice = self.__dscolumns
                    if hasattr(xslice, "start"):
                        xslice = [xslice.start, xslice.stop, xslice.step]
                    if hasattr(yslice, "start"):
                        yslice = [yslice.start, yslice.stop, yslice.step]
                    self.__sendresults(
                        xx,
                        [float(e) for e in sx],
                        s1, xslice,
                        yy,
                        [float(e) for e in sy],
                        s2, yslice,
                        "sum" if self.__funindex else "mean"
                    )

    def __sendresults(self, xx, sx, xscale, xslice,
                      yy, sy, yscale, yslice, fun):
        """ send results to LavueController

        :param xx:  x's coordinates
        :type xx:  :obj:`list` <float>
        :param sx:  projection to x coordinate
        :type sx:  :obj:`list` <float>
        :param xscale:  x scale
        :type xscale:  :obj:`float`
        :param xslice:  x slice
        :type xslice:  :obj:`list` <float>
        :param yy:  y's coordinates
        :type yy:  :obj:`list` <float>
        :param sy:  projection to y coordinate
        :type sy:  :obj:`list` <float>
        :param yscale:  y scale
        :type yscale:  :obj:`float`
        :param yslice:  y slice
        :type yslice:  :obj:`list` <float>
        :param fun:  projection function name
        :type fun:  :obj:`str`
        """
        results = {"tool": self.alias}
        results["imagename"] = self._mainwidget.imageName()
        results["timestamp"] = time.time()
        results["xx"] = xx
        results["sx"] = sx
        results["xscale"] = xscale
        results["xslice"] = xslice
        results["yy"] = yy
        results["sy"] = sy
        results["yscale"] = yscale
        results["yslice"] = yslice
        results["function"] = fun
        self._mainwidget.writeAttribute(
            "ToolResults", json.dumps(results))

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
        self._mainwidget.emitTCC()

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
            wavelength = 12398.4193 / self.__settings.energy
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
            self.__settings.updateAISettings()
            self._mainwidget.writeDetectorAttributes()
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)

    # @debugmethod
    @QtCore.pyqtSlot()
    def _updateGeometry(self, geometry):
        """ update geometry widget

        :param geometry: geometry dictionary
        :type geometry: :obj:`dict` < :obj:`str`, :obj:`list`>
        """
        try:
            if "centerx" in geometry.keys():
                self.__settings.centerx = float(geometry["centerx"])
                self._mainwidget.writeAttribute(
                    "BeamCenterX", float(self.__settings.centerx))
        except Exception:
            pass
        try:
            if "centery" in geometry.keys():
                self.__settings.centery = float(geometry["centery"])
                self._mainwidget.writeAttribute(
                    "BeamCenterY", float(self.__settings.centery))
        except Exception:
            pass
        try:
            if "energy" in geometry.keys():
                self.__settings.energy = float(geometry["energy"])
                self._mainwidget.writeAttribute(
                    "Energy", float(self.__settings.energy))
        except Exception:
            pass
        try:
            if "pixelsizex" in geometry.keys():
                self.__settings.pixelsizex = float(geometry["pixelsizex"])
        except Exception:
            pass
        try:
            if "pixelsizey" in geometry.keys():
                self.__settings.pixelsizey = float(geometry["pixelsizey"])
        except Exception:
            pass
        try:
            if "detdistance" in geometry.keys():
                self.__settings.detdistance = float(geometry["detdistance"])
            self._mainwidget.writeAttribute(
                "DetectorDistance",
                float(self.__settings.detdistance))
        except Exception:
            pass
        if geometry:
            self.updateGeometryTip()
            self._mainwidget.updateCenter(
                self.__settings.centerx, self.__settings.centery)
            self._mainwidget.emitTCC()

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
