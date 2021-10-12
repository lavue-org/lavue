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

""" level widget """

from .qtuic import uic
import pyqtgraph as _pg
from pyqtgraph import QtCore, QtGui
from .histogramWidget import HistogramHLUTWidget
from . import messageBox
from . import gradientDialog

# from .histogramWidget import HistogramHLUTItem
import math
import os
import logging


_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".")[:3] \
    if _pg.__version__ else ("0", "9", "0")
try:
    _NPATCH = int(_VPATCH)
except Exception:
    _NPATCH = 0
_PQGVER = int(_VMAJOR) * 1000 + int(_VMINOR) * 100 + _NPATCH


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LevelsGroupBox.ui"))


logger = logging.getLogger("lavue")


class LevelsGroupBox(QtGui.QWidget):

    """
    Set minimum and maximum displayed values and its color.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) minimum level changed signal
    minLevelChanged = QtCore.pyqtSignal(float)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) maximum level changed signal
    maxLevelChanged = QtCore.pyqtSignal(float)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) channel levels changed signal
    channelLevelsChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) automatic levels changed signal
    autoLevelsChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) levels changed signal
    levelsChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) store settings requested
    storeSettingsRequested = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) gradient changed signal
    gradientChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None, settings=None, expertmode=False):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        :param expertmode: expert mode flag
        :type expertmode: :obj:`bool`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj: `bool`) auto levels enabled
        self.__auto = True
        #: (:obj: `bool`) histogram shown
        self.__histo = True
        #: (:obj: `bool`) levels shown
        self.__levels = True
        #: (:obj: `str`) scale label
        self.__scaling = "sqrt"
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings
        #: (:obj:`bool`) expert mode
        self.__expertmode = expertmode
        #: (:obj:`list` <:obj:`int`>) rgb channel indexes
        self.__rgbchannels = (-1, -1, -1)

        #: (:obj:`dict` < :obj:`str`, :obj:`dict` < :obj:`str`,`any`> >
        #                custom gradients
        self.__customgradients = self.__settings.customGradients()
        for name, gradient in self.__customgradients.items():
            _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
            self._addGradientItem(name)

        #: (:obj: `float`) minimum intensity level value
        self.__minval = 0.2
        #: (:obj: `float`) maximum intensity level value
        self.__maxval = 1.1
        #: (:obj: `float`) minimum maximum intensity level value
        #                  for separete channels
        self.__channels = None
        #: (:obj: `int`) channel to display
        self.__dchl = 0
        #: (:obj:`bool`) gradient colors flag
        self.__gradientcolors = False

        self.__ui.minDoubleSpinBox.setMinimum(-10e20)
        self.__ui.minDoubleSpinBox.setMaximum(10e20)
        self.__ui.maxDoubleSpinBox.setMinimum(-10e20)
        self.__ui.maxDoubleSpinBox.setMaximum(10e20)

        #: (:class: `lavuelib.histogramWidget.HistogramHLUTWidget`)
        #:      intensity histogram widget

        for name in _pg.graphicsItems.GradientEditorItem.\
                Gradients.keys():
            self._addGradientItem(name)

        self.__histograms = [
            HistogramHLUTWidget(bins='auto', step='auto',
                                expertmode=expertmode),
            HistogramHLUTWidget(bins='auto', step='auto',
                                expertmode=expertmode),
            HistogramHLUTWidget(bins='auto', step='auto',
                                expertmode=expertmode)
        ]
        self.__histogram = self.__histograms[0]
        self.__histconnect = [False, False, False]

        self.__onLevelsSlots = [
            self._onLevelsChanged,
            self._onLevelsChanged1,
            self._onLevelsChanged2
        ]
        self.__changeGradientSlots = [
            self._changeGradient0,
            self._changeGradient1,
            self._changeGradient2
        ]
        self.__saveGradientSlots = [
            self._saveGradient,
            self._saveGradient1,
            self._saveGradient2
        ]
        self.__removeGradientSlots = [
            self._removeGradient,
            self._removeGradient1,
            self._removeGradient2
        ]
        self.__rgbstatus = False
        self.__ui.histogramLayout.addWidget(self.__histograms[0])
        self.__ui.histogramLayout.addWidget(self.__histograms[1])
        self.__ui.histogramLayout.addWidget(self.__histograms[2])

        self.__ui.gradientComboBox.currentIndexChanged.connect(
            self._updateGradient)
        self.__ui.binsComboBox.currentIndexChanged.connect(self.setBins)

        self.__hideControls()
        self.__ui.autoLevelsCheckBox.stateChanged.connect(
            self._onAutoLevelsChanged)
        self.__ui.stepLineEdit.textChanged.connect(
            self._onStepChanged)
        self.__ui.monoRadioButton.clicked.connect(
            self._monoLevelMode)
        self.__ui.redRadioButton.clicked.connect(
            self._redLevelMode)
        self.__ui.blueRadioButton.clicked.connect(
            self._blueLevelMode)
        self.__ui.greenRadioButton.clicked.connect(
            self._greenLevelMode)
        self.__ui.autofactorLineEdit.textChanged.connect(
            self._onAutoFactorChanged)
        self.__connectHistogram()
        self.__histograms[0].show()
        self.__histograms[1].hide()
        self.__histograms[2].hide()
        # print(self.__histogram.isVisible())
        self.updateLevels(0.1, 1.0)
        self.__connectMinMax()
        self.__levelmode = "mono"

    def _updateLevelLabels(self, dchl=None):
        """ update level labels

        :param dchl: channel id
        :type dchl: :obj:`int`
        """
        if dchl is None:
            dchl = self.__dchl
        if _PQGVER >= 1100:
            if dchl == 1:
                self.__ui.minLabel.setText("Red Min. value:")
                self.__ui.maxLabel.setText("Red Max. value:")
            elif dchl == 2:
                self.__ui.minLabel.setText("Green Min. value:")
                self.__ui.maxLabel.setText("Green Max. value:")
            elif dchl == 3:
                self.__ui.minLabel.setText("Blue Min. value:")
                self.__ui.maxLabel.setText("Blue Max. value:")
            else:
                self.__ui.minLabel.setText("Minimum value:")
                self.__ui.maxLabel.setText("Maximum value:")

    @QtCore.pyqtSlot(bool)
    def _monoLevelMode(self, status):
        """ update to the mono level mode

        :param status: button status
        :type status: :obj:`bool`
        """
        if self.__gradientcolors:
            if status:
                self.__dchl = 0
                self._updateLevelLabels()
                if not self.__histo:
                    self.__histogram.switchLevelMode('mono')
                self.__levelmode = "mono"
                self.updateLevels(self.__minval, self.__maxval)
                if self.__histogram:
                    self.__histogram.switchLevelMode('mono')
        elif _PQGVER >= 1100:
            if status:
                self.__dchl = 0
                if not self.__ui.gradientLabel.isVisible():
                    self._updateLevelLabels()
                    if not self.__histo:
                        self.__histogram.switchLevelMode('mono')
                    self.__levelmode = "mono"
                    self.updateLevels(self.__minval, self.__maxval)
                    if self.__histogram:
                        self.__histogram.switchLevelMode('mono')

    @QtCore.pyqtSlot(bool)
    def _redLevelMode(self, status):
        """ update to the red level mode

        :param status: button status
        :type status: :obj:`bool`
        """
        if self.__gradientcolors:
            if status:
                self.__dchl = 1
                self._updateLevelLabels()
                if not self.__histo:
                    self.__histogram.switchLevelMode('mono')
                self.__levelmode = "rgba"
                if self.__channels is not None:
                    while len(self.__channels) < 1:
                        self.__channels.append(
                            (self.__minval, self.__maxval))
                    self.updateLevels(None, None, self.__channels)
                if self.__histogram:
                    self.__histogram.switchLevelMode('mono')
                self.setGradient(self.__histograms[0].gradient.name, 0)
        elif _PQGVER >= 1100:
            if status:
                self.__dchl = 1
                if self.__ui.gradientLabel.isVisible():
                    self._updateLevelLabels()
                    if not self.__histo:
                        self.__histogram.switchLevelMode('rgba')
                    self.__levelmode = "rgba"
                    if self.__channels is not None:
                        while len(self.__channels) < 1:
                            self.__channels.append(
                                (self.__minval, self.__maxval))
                        self.updateLevels(None, None, self.__channels)
                    if self.__histogram:
                        self.__histogram.switchLevelMode('rgba')

    @QtCore.pyqtSlot(bool)
    def _greenLevelMode(self, status):
        """ update to the green level mode

        :param status: button status
        :type status: :obj:`bool`
        """
        if self.__gradientcolors:
            if status:
                self.__dchl = 2
                self._updateLevelLabels()
                if not self.__histo:
                    self.__histogram.switchLevelMode('mono')
                self.__levelmode = "rgba"
                if self.__channels is not None:
                    while len(self.__channels) < 2:
                        self.__channels.append(
                            (self.__minval, self.__maxval))
                    self.updateLevels(None, None, self.__channels)
                if self.__histogram:
                    self.__histogram.switchLevelMode('mono')
                self.setGradient(self.__histograms[1].gradient.name, 1)
        elif _PQGVER >= 1100:
            if status:
                self.__dchl = 2
                self._updateLevelLabels()
                if self.__ui.gradientLabel.isVisible():
                    if not self.__histo:
                        self.__histogram.switchLevelMode('rgba')
                    self.__levelmode = "rgba"
                    if self.__channels is not None:
                        while len(self.__channels) < 2:
                            self.__channels.append(
                                (self.__minval, self.__maxval))
                        self.updateLevels(None, None, self.__channels)
                    if self.__histogram:
                        self.__histogram.switchLevelMode('rgba')

    @QtCore.pyqtSlot(bool)
    def _blueLevelMode(self, status):
        """ update to the blue level mode

        :param status: button status
        :type status: :obj:`bool`
        """
        if self.__gradientcolors:
            if status:
                self.__dchl = 3
                self._updateLevelLabels()
                if not self.__histo:
                    self.__histogram.switchLevelMode('mono')
                self.__levelmode = "rgba"
                if self.__channels is not None:
                    while len(self.__channels) < 3:
                        self.__channels.append(
                            (self.__minval, self.__maxval))
                    self.updateLevels(None, None, self.__channels)
                if self.__histogram:
                    self.__histogram.switchLevelMode('mono')
                self.setGradient(self.__histograms[2].gradient.name, 2)
        elif _PQGVER >= 1100:
            if status:
                self.__dchl = 3
                if self.__ui.gradientLabel.isVisible():
                    self._updateLevelLabels()
                    if not self.__histo:
                        self.__histogram.switchLevelMode('rgba')
                    self.__levelmode = "rgba"
                    if self.__channels is not None:
                        while len(self.__channels) < 3:
                            self.__channels.append(
                                (self.__minval, self.__maxval))
                        self.updateLevels(None, None, self.__channels)
                    if self.__histogram:
                        self.__histogram.switchLevelMode('rgba')

    def __connectHistogram(self, iid=0):
        """ create histogram object and connect its signals

        :param iid: image id
        :type iid: :obj:`int`
        """
        if not self.__histconnect[iid]:
            self.__histograms[iid].item.sigLevelsChanged.connect(
                self.__onLevelsSlots[iid])
            self.__histograms[iid].sigNameChanged.connect(
                self.__changeGradientSlots[iid])
            self.__histograms[iid].saveGradientRequested.connect(
                self.__saveGradientSlots[iid])
            self.__histograms[iid].removeGradientRequested.connect(
                self.__removeGradientSlots[iid])
            self.__histconnect[iid] = True
        # else:
        #     print("WARN: trying to connect HIS", iid)

    def __disconnectHistogram(self, iid=0):
        """ remove histogram object and disconnect its signals

        :param iid: image id
        :type iid: :obj:`int`
        """
        if self.__histconnect[iid]:
            self.__histograms[iid].item.sigLevelsChanged.disconnect(
                self.__onLevelsSlots[iid])
            self.__histograms[iid].sigNameChanged.disconnect(
                self.__changeGradientSlots[iid])
            self.__histograms[iid].saveGradientRequested.disconnect(
                self.__saveGradientSlots[iid])
            self.__histograms[iid].removeGradientRequested.disconnect(
                self.__removeGradientSlots[iid])
            self.__histconnect[iid] = False
        # else:
        #     print("WARN: trying to disconnect HIS", iid)

    def __connectHistograms(self):
        """ create histogram object and connect its signals
        """
        for iid in range(3):
            if self.__histograms[iid].isVisible():
                self.__connectHistogram(iid)

    def __disconnectHistograms(self):
        """ remove histogram object and disconnect its signals
        """
        for iid in range(3):
            if self.__histograms[iid].isVisible():
                self.__disconnectHistogram(iid)

    def updateCustomGradients(self, gradients):
        self.__customgradients = dict(gradients)
        for name, gradient in self.__customgradients.items():
            _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
            self._addGradientItem(name)
        for iid in range(3):
            self.__histograms[iid].resetGradient()
        self._updateGradient()

    def __connectMinMax(self):
        """ connects mix/max spinboxes
        """
        self.__ui.minDoubleSpinBox.valueChanged.connect(self._onMinMaxChanged)
        self.__ui.maxDoubleSpinBox.valueChanged.connect(self._onMinMaxChanged)

    def __disconnectMinMax(self):
        """ disconnects mix/max spinboxes
        """
        self.__ui.minDoubleSpinBox.valueChanged.disconnect(
            self._onMinMaxChanged)
        self.__ui.maxDoubleSpinBox.valueChanged.disconnect(
            self._onMinMaxChanged)

    @QtCore.pyqtSlot(float)
    def _onMinMaxChanged(self, _):
        """ sets region of the histograms
        """
        if not self.__auto:
            try:
                self.__disconnectMinMax()
                if self.__histo:
                    self.__disconnectHistogram()
                self._checkAndEmit()
                if self.__histo:
                    lowlim = self.__ui.minDoubleSpinBox.value()
                    uplim = self.__ui.maxDoubleSpinBox.value()
                    if self.__gradientcolors and self.__rgbstatus:
                        for iid in range(3):
                            if not self.__dchl or iid + 1 == self.__dchl:
                                self.__histograms[iid].region.setRegion(
                                    [lowlim, uplim])
                    else:
                        if self.__dchl == 0:
                            self.__histogram.region.setRegion([lowlim, uplim])
                        else:
                            if hasattr(self.__histogram, "regions"):
                                self.__histogram.regions[self.__dchl].\
                                    setRegion([lowlim, uplim])
            finally:
                self.__connectMinMax()
                if self.__histo:
                    self.__connectHistogram()
        else:
            lowlim = self.__ui.minDoubleSpinBox.value()
            uplim = self.__ui.maxDoubleSpinBox.value()
            if self.__dchl == 0:
                self.minLevelChanged.emit(lowlim)
                self.maxLevelChanged.emit(uplim)
            else:
                if self.__channels is None:
                    self.__channels = []
                    while len(self.__channels) < self.__dchl:
                        self.__channels.append((lowlim, uplim))
                    self.__channels[self.__dchl - 1] = (lowlim, uplim)
                self.channelLevelsChanged.emit()

    def changeView(self, showhistogram=None, showlevels=None,
                   showadd=None):
        """ shows or hides the histogram widget

        :param showhistogram: if histogram should be shown
        :type showhistogram: :obj:`bool`
        :param showlevels: if levels should be shown
        :type showlevels: :obj:`bool`
        :param showadd: if additional histogram should be shown
        :type showadd: :obj:`bool`
        """
        if showhistogram is True and self.__histo is False:
            if showhistogram is not None:
                self.__histo = showhistogram
            self.showHistograms(True)
        elif showhistogram is False and self.__histo is True:
            if showhistogram is not None:
                self.__histo = showhistogram
            self.showHistograms(False)
        if showadd is True:
            self.__ui.binsComboBox.show()
            self.__ui.binsLabel.show()
            self.__ui.stepLineEdit.show()
            self.__ui.stepLabel.show()
        elif showadd is False:
            self.__ui.binsComboBox.hide()
            self.__ui.binsLabel.hide()
            self.__ui.stepLineEdit.hide()
            self.__ui.stepLabel.hide()
        if showlevels is True and self.__levels is False:
            self.__ui.gradientLabel.show()
            self.__ui.gradientComboBox.show()
            self.__ui.scalingLabel.show()
            self.__ui.autoLevelsCheckBox.show()
            self.__ui.autofactorLineEdit.show()
            self.__ui.autofactorLabel.show()
            self.__ui.maxDoubleSpinBox.show()
            self.__ui.maxLabel.show()
            self.__ui.minDoubleSpinBox.show()
            self.__ui.minLabel.show()
            self.__ui.scalingLabel.show()
        elif showlevels is False and self.__levels is True:
            self.__ui.gradientLabel.hide()
            self.__ui.gradientComboBox.hide()

            self.__ui.scalingLabel.hide()
            self.__ui.autoLevelsCheckBox.hide()
            self.__ui.autofactorLineEdit.hide()
            self.__ui.autofactorLabel.hide()
            self.__ui.maxDoubleSpinBox.hide()
            self.__ui.maxLabel.hide()
            self.__ui.minDoubleSpinBox.hide()
            self.__ui.minLabel.hide()
            self.__ui.scalingLabel.hide()

        if showlevels is not None:
            self.__levels = showlevels

        if not self.__histo and not self.__levels:
            self.hide()
        else:
            self.show()

    def isAutoLevel(self):
        """ returns if automatics levels are enabled

        :returns: if automatics levels are enabled
        :rtype: :obj:`bool`
        """
        return self.__auto

    @QtCore.pyqtSlot(int)
    def setAutoLevels(self, auto):
        """enables or disables automatic levels

        :param auto: if automatics levels to be set
        :type auto: :obj:`bool` or :obj:`int`
        """
        self.__ui.autoLevelsCheckBox.setChecked(
            2 if auto else 0)
        self._onAutoLevelsChanged(auto)

    @QtCore.pyqtSlot(str)
    def _onStepChanged(self, step):
        """sets step for  automatic levels

        :param step: if automatics levels to be set
        :type step: :obj:`str`
        """
        try:
            fstep = float(step)
            if fstep <= 0:
                fstep = None
                self.__ui.stepLineEdit.setText("")
            for histogram in self.__histograms:
                histogram.setStep(fstep)
        except Exception:
            for histogram in self.__histograms:
                histogram.setStep(None)
            self.__ui.stepLineEdit.setText("")
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(str)
    def _onAutoFactorChanged(self, factor):
        """sets factor for  automatic levels

        :param factor: if automatics levels to be set
        :type factor: :obj:`str`
        """
        try:
            ffactor = float(factor)
            if ffactor < 0:
                ffactor = 0
                self.__ui.autofactorLineEdit.setText("0")
            elif ffactor > 100:
                ffactor = 100
                self.__ui.autofactorLineEdit.setText("100")
            for histogram in self.__histograms:
                histogram.setAutoFactor(ffactor)
            self.autoLevelsChanged.emit(1)
        except Exception:
            for histogram in self.__histograms:
                histogram.setAutoFactor(None)
            self.autoLevelsChanged.emit(2 if self.__auto else 0)
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(int)
    def _onAutoLevelsChanged(self, auto):
        """enables or disables automatic levels

        :param auto: if automatics levels to be set
        :type auto: :obj:`bool` or :obj:`int`
        """
        if auto:
            self.__auto = True
            self.__hideControls()
            factor = str(self.__ui.autofactorLineEdit.text())
            try:
                ffactor = float(factor)
                if ffactor < 0:
                    ffactor = 0
                    self.__ui.autofactorLineEdit.setText("0")
                elif ffactor > 100:
                    ffactor = 100
                    self.__ui.autofactorLineEdit.setText("100")
                    for histogram in self.__histograms:
                        histogram.setAutoFactor(ffactor)
            except Exception:
                for histogram in self.__histograms:
                    histogram.setAutoFactor(None)
                self.autoLevelsChanged.emit(2)
        else:
            for histogram in self.__histograms:
                histogram.setAutoFactor(None)
            self.__auto = False
            self.__showControls()
            self.autoLevelsChanged.emit(0)
            self._checkAndEmit()
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(object)
    def _onLevelsChanged1(self, histogram=None):
        """ set min/max level spinboxes according to histogram

        :param histogram: intensity histogram object
        :type histogram: :class: `lavuelib.histogramWidget.HistogramHLUTWidget`
        """
        if histogram is None:
            histogram = self.__histograms[1]
        self._onLevelsChanged(histogram)

    @QtCore.pyqtSlot(object)
    def _onLevelsChanged2(self, histogram=None):
        """ set min/max level spinboxes according to histogram

        :param histogram: intensity histogram object
        :type histogram: :class: `lavuelib.histogramWidget.HistogramHLUTWidget`
        """
        if histogram is None:
            histogram = self.__histograms[2]
        self._onLevelsChanged(histogram)

    @QtCore.pyqtSlot(object)
    def _onLevelsChanged(self, histogram=None):
        """ set min/max level spinboxes according to histogram

        :param histogram: intensity histogram object
        :type histogram: :class: `lavuelib.histogramWidget.HistogramHLUTWidget`

        """
        if histogram is None:
            histogram = self.__histogram
        levels = histogram.region.getRegion()
        lowlim = self.__minval
        uplim = self.__maxval
        changed = False
        try:
            # self.__disconnectMinMax()
            # self.__disconnectHistogram()

            if levels[0] != lowlim or levels[1] != uplim:
                lowlim = levels[0]
                uplim = levels[1]
                # refresh widget
                changed = True
                self.__minval = levels[0]
                self.__maxval = levels[1]
                if self.__dchl == 0:
                    self.__ui.minDoubleSpinBox.setValue(levels[0])
                    self.__ui.maxDoubleSpinBox.setValue(levels[1])
            if hasattr(self.__histogram, "regions") and \
               self.__channels is not None:
                while len(self.__channels) < 3:
                    self.__channels.append((self.__minval, self.__maxval))
                    added = True
                for i in range(1, 4):
                    if self.__gradientcolors and self.__rgbstatus:
                        levels = self.__histograms[i - 1].region.getRegion()
                    else:
                        levels = histogram.regions[i].getRegion()
                    lowlim = self.__channels[i - 1][0]
                    uplim = self.__channels[i - 1][1]
                    added = False
                    if levels[0] != lowlim or levels[1] != uplim or added:
                        lowlim = levels[0]
                        uplim = levels[1]
                        # refresh widget
                        changed = True
                        self.__channels[i - 1] = levels[0], levels[1]
                if self.__dchl > 0:
                    self.__ui.minDoubleSpinBox.setValue(
                        self.__channels[self.__dchl - 1][0])
                    self.__ui.maxDoubleSpinBox.setValue(
                        self.__channels[self.__dchl - 1][1])
        finally:
            # self.__connectMinMax()
            # self.__connectHistogram()
            pass
        if not self.__auto and changed:
            self._checkLevels()
            self._emitLevels()

    @QtCore.pyqtSlot()
    def _checkLevels(self):
        """ checks if the minimum value is actually smaller than the maximum
        """
        minval = self.__ui.minDoubleSpinBox.value()
        maxval = self.__ui.maxDoubleSpinBox.value()
        if maxval >= 10e+20:
            maxval = self.__maxval
        if minval >= 10e+20:
            minval = self.__minval

        if maxval - minval <= 0:
            if minval >= 1.:
                minval = maxval - 1.
            else:
                maxval = minval + 1

        self.__ui.minDoubleSpinBox.setValue(minval)
        self.__ui.maxDoubleSpinBox.setValue(maxval)

    @QtCore.pyqtSlot()
    def _emitLevels(self):
        """ checks if the minimum value is actually smaller than the maximum
        """
        self.minLevelChanged.emit(self.__minval)
        self.maxLevelChanged.emit(self.__maxval)
        self.channelLevelsChanged.emit()

    @QtCore.pyqtSlot()
    def _updateAndEmit(self):
        lowlim = self.__ui.minDoubleSpinBox.value()
        uplim = self.__ui.maxDoubleSpinBox.value()
        if self.__dchl == 0:
            self.__minval = lowlim
            self.__maxval = uplim
            self.minLevelChanged.emit(self.__minval)
            self.maxLevelChanged.emit(self.__maxval)
        else:
            if self.__channels is None:
                self.__channels = []
            while len(self.__channels) < self.__dchl:
                self.__channels.append((lowlim, uplim))
            self.__channels[self.__dchl - 1] = (lowlim, uplim)
            self.channelLevelsChanged.emit()

    @QtCore.pyqtSlot()
    def _checkAndEmit(self):
        """ checks if the minimum value is actually smaller than the maximum
        """
        self._checkLevels()
        self._updateAndEmit()

    def updateLevels(self, lowlim, uplim, channels=None, signals=True,
                     force=False):
        """ set min/max level spinboxes and histogram from the parameters

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        :param signal:  dont disconnect signals
        :type signal: :obj:`bool`
        :param force:  force update histogram
        :type force: :obj:`bool`
        """
        try:
            if not signals:
                self.__disconnectMinMax()

            if lowlim is not None:
                self.__minval = lowlim
                if self.__dchl == 0:
                    self.__ui.minDoubleSpinBox.setValue(lowlim)
            else:
                lowlim = self.__minval
            if uplim is not None:
                self.__maxval = uplim
                if self.__dchl == 0:
                    self.__ui.maxDoubleSpinBox.setValue(uplim)
            else:
                uplim = self.__maxval
            if channels is not None:
                self.__channels = channels
                if self.__dchl != 0 and len(self.__channels) >= self.__dchl:
                    ch = self.__channels[self.__dchl - 1]
                    if ch is not None:
                        chl, chh = ch
                        if chl is not None:
                            self.__ui.minDoubleSpinBox.setValue(chl)
                        if chh is not None:
                            self.__ui.maxDoubleSpinBox.setValue(chh)
        finally:
            if not signals:
                self.__connectMinMax()

        if self.__histo and (self.__auto or force):
            levels = self.__histogram.region.getRegion()
            update = False
            try:
                if self.__histo:
                    if self.__gradientcolors and self.__rgbstatus:
                        self.__disconnectHistograms()
                    else:
                        self.__disconnectHistogram()

                if levels[0] != lowlim or levels[1] != uplim or force:
                    if self.__histo:
                        self.__histogram.region.setRegion([lowlim, uplim])
                if hasattr(self.__histogram, "regions"):
                    if channels is not None and self.__histo:
                        for i, ch in enumerate(self.__channels):
                            if ch is not None:
                                lowlim, uplim = ch
                                if lowlim is not None and uplim is not None:
                                    if self.__gradientcolors and \
                                       self.__rgbstatus:
                                        levels = self.__histograms[i].region\
                                            .getRegion()
                                        if levels[0] != lowlim \
                                           or levels[1] != uplim or force:
                                            self.__histograms[i].region.\
                                                setRegion([lowlim, uplim])
                                    else:
                                        levels = self.__histogram.\
                                            regions[i + 1].getRegion()
                                        if levels[0] != lowlim \
                                           or levels[1] != uplim or force:
                                            self.__histogram.regions[i + 1].\
                                                setRegion([lowlim, uplim])
            finally:
                if self.__histo:
                    if self.__gradientcolors and self.__rgbstatus:
                        self.__connectHistograms()
                    else:
                        self.__connectHistogram()
            if update:
                self._onLevelsChanged()
        self._emitLevels()

    def updateAutoLevels(self, lowlim, uplim, channels=None):
        """ set min/max level spinboxes and histogram from the parameters

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        """
        if channels is not None:
            self.__channels = channels
        try:
            factor = str(self.__ui.autofactorLineEdit.text())
            float(factor)
            channels = None
            llim = None
            ulim = None
            if self.__histo:
                llim, ulim = self.__histogram.getFactorRegion()
                if self.__gradientcolors and self.__rgbstatus:
                    channels = [(llim, ulim)]
                    channels.append(self.__histograms[1].getFactorRegion())
                    channels.append(self.__histograms[2].getFactorRegion())
                else:
                    channels = self.__histogram.getChannelFactorRegion()
            if channels is not None:
                self.__channels = channels
            if llim is not None and ulim is not None:
                self.updateLevels(llim, ulim)
                self.minLevelChanged.emit(llim)
                self.maxLevelChanged.emit(ulim)
            else:
                self.updateLevels(lowlim, uplim, channels)
                if channels is not None:
                    self.channelLevelsChanged.emit()
        except Exception:
            self.updateLevels(lowlim, uplim, channels)

    def __hideControls(self):
        """ disables spinboxes
        """
        self.__ui.minDoubleSpinBox.setEnabled(False)
        self.__ui.maxDoubleSpinBox.setEnabled(False)
        self.__ui.autofactorLineEdit.setEnabled(True)
        self.__ui.autofactorLabel.setEnabled(True)

    def __showControls(self):
        """ enables spinboxes
        """
        self.__ui.minDoubleSpinBox.setEnabled(True)
        self.__ui.maxDoubleSpinBox.setEnabled(True)
        self.__ui.autofactorLineEdit.setEnabled(False)
        self.__ui.autofactorLabel.setEnabled(False)

    def _tologscale(self, lowlim, uplim):
        """ change scaling to log scale

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        :returns: (minimum intensity value, maximum intensity value)
                  in log scale
        :rtype: (:obj:`float`, :obj:`float`)
        """
        if self.__scaling == "linear":
            lowlim = math.log10(
                lowlim or 10e-3) if lowlim > 0 else -2
            uplim = math.log10(
                uplim or 10e-3) if uplim > 0 else -2
        elif self.__scaling == "sqrt":
            lowlim = math.log10(
                lowlim * lowlim or 10e-3) if lowlim > 0 else -2
            uplim = math.log10(
                uplim * uplim or 10e-3) if uplim > 0 else -2
        return lowlim, uplim

    def _tolinearscale(self, lowlim, uplim):
        """ change scaling to linear scale

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        :returns: (minimum intensity value, maximum intensity value)
                  in linear scale
        :rtype: (:obj:`float`, :obj:`float`)
        """
        if self.__scaling == "log":
            lowlim = math.pow(10, lowlim)
            uplim = math.pow(10, uplim)
        elif self.__scaling == "sqrt":
            lowlim = lowlim * lowlim
            uplim = uplim * uplim
        return lowlim, uplim

    def _tosqrtscale(self, lowlim, uplim):
        """ change scaling to sqrt scale

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        :returns: (minimum intensity value, maximum intensity value)
                  in sqrt scale
        :rtype: (:obj:`float`, :obj:`float`)
        """
        if self.__scaling == "linear":
            lowlim = math.sqrt(max(lowlim, 0))
            uplim = math.sqrt(max(uplim, 0))
        elif self.__scaling == "log":
            lowlim = math.sqrt(max(math.pow(10, lowlim), 0))
            uplim = math.sqrt(max(math.pow(10, uplim), 0))
        return lowlim, uplim

    @QtCore.pyqtSlot(str)
    def setRGBChannels(self, rgbchannels):
        """ rgb channel indexes

        :param rgbchannels: rgb channel indexes
        :type rgbchannels: :obj:`tuple` <:obj:`int`>
        """
        if self.__rgbchannels != rgbchannels:
            self.__rgbchannels = rgbchannels
        self.showHistograms(self.__rgbstatus)

    @QtCore.pyqtSlot(str)
    def setScalingLabel(self, scalingtype):
        """ sets scaling label

        :param scalingtype: scaling type, i.e. log, linear, sqrt
        :type scalingtype: :obj:`str`
        """
        lowlim = float(self.__ui.minDoubleSpinBox.value())
        uplim = float(self.__ui.maxDoubleSpinBox.value())
        scalefun = {
            "log": self._tologscale,
            "linear": self._tolinearscale,
            "sqrt": self._tosqrtscale,
        }
        scalelabel = {
            "log": "log scale!",
            "linear": "log linear!",
            "sqrt": "log sqrt!",
        }
        if scalingtype in scalefun.keys():
            sfun = scalefun[scalingtype]
            slabel = scalelabel[scalingtype]
            if scalingtype != self.__scaling:
                self.__ui.scalingLabel.setText(slabel)
                if not self.__auto:
                    lowlim, uplim = sfun(lowlim, uplim)
                    self.__minval, self.__maxval = sfun(
                        self.__minval, self.__maxval)
                    if self.__channels:
                        for i, ch in enumerate(self.__channels):
                            if ch is not None:
                                if ch[0] is not None and ch[1] is not None:
                                    self.__channels[i] = sfun(ch[0], ch[1])

            # self.__ui.minDoubleSpinBox.setValue(lowlim)
            # self.__ui.maxDoubleSpinBox.setValue(uplim)
        if scalingtype != self.__scaling:
            self.__scaling = scalingtype
        if not self.__auto:
            if self.__histo:
                try:
                    self.__disconnectHistogram()
                    self.__histogram.region.setRegion(
                        [self.__minval, self.__maxval])
                    if hasattr(self.__histogram, "regions"):
                        if self.__channels is not None:
                            for i, ch in enumerate(self.__channels):
                                if ch is not None:
                                    lowlim, uplim = ch
                                    if lowlim is not None \
                                       and uplim is not None:
                                        self.__histogram.regions[i + 1].\
                                            setRegion([lowlim, uplim])
                finally:
                    self.__connectHistogram()

                    self.updateLevels(
                        self.__minval, self.__maxval, self.__channels,
                        signals=False)
                    # self._onLevelsChanged()
            else:
                self.__ui.minDoubleSpinBox.setValue(lowlim)
                self.__ui.maxDoubleSpinBox.setValue(uplim)

    @QtCore.pyqtSlot(bool)
    def setrgb(self, status=True):
        """ sets RGB on/off

        :param status: True for on and False for off
        :type status: :obj:`bool`
        """
        self.__histogram.setRGB(status and not self.__gradientcolors)
        if status and self.__dchl and not self.__gradientcolors:
            mode = 'rgba'
            lmode = 'rgba'
            dchl = self.__dchl
        elif status and self.__dchl and self.__gradientcolors:
            mode = 'mono'
            lmode = 'rgba'
            dchl = self.__dchl
        else:
            mode = 'mono'
            lmode = 'mono'
            dchl = 0

        switch = False
        if self.__rgbstatus != status:
            switch = True
            self.__rgbstatus = status
        self.__histogram.switchLevelMode(mode)
        self.__levelmode = lmode
        self._updateLevelLabels(dchl)
        self.showGradient(not status or self.__gradientcolors)
        self.showHistograms(status)
        if _PQGVER >= 1100 or self.__gradientcolors:
            self.showChannels(status)
        if switch:
            self.gradientChanged.emit()

    def showHistograms(self, status=True):
        """ show/hide gradient widget

        :param status: show gradient flag
        :type status: :obj:`bool`
        """
        if self.__gradientcolors and status and self.__histo:
            for iid in range(0, 3):
                if self.__rgbchannels[iid] != -1:
                    if not self.__histograms[iid].isVisible():
                        self.__connectHistogram(iid)
                        self.__histograms[iid].show()
                        self.__histograms[iid].fillHistogram(True)
                else:
                    if self.__histograms[iid].isVisible():
                        self.__histograms[iid].hide()
                        self.__histograms[iid].fillHistogram(False)
                        self.__disconnectHistogram(iid)
        else:
            if self.__histo:
                if not self.__histograms[0].isVisible():
                    self.__connectHistogram()
                    self.__histograms[0].show()
                    self.__histograms[0].fillHistogram(True)
            else:
                if self.__histograms[0].isVisible():
                    self.__histograms[0].hide()
                    self.__histograms[0].fillHistogram(False)
                    self.__disconnectHistogram()
            if self.__histograms[1].isVisible():
                self.__histograms[1].hide()
                self.__histograms[1].fillHistogram(False)
                self.__disconnectHistogram(1)
            if self.__histograms[2].isVisible():
                self.__histograms[2].hide()
                self.__histograms[2].fillHistogram(False)
                self.__disconnectHistogram(2)

    def showGradient(self, status=True):
        """ show/hide gradient widget

        :param status: show gradient flag
        :type status: :obj:`bool`
        """
        if status and not self.__ui.gradientComboBox.isVisible():
            self.__ui.gradientComboBox.show()
            self.__ui.gradientLabel.show()
            self.__histogram.gradient.show()
            # self.setGradient(self.gradient())
            self._updateGradient()
        elif not status and self.__ui.gradientComboBox.isVisible():
            self.__ui.gradientComboBox.hide()
            self.__ui.gradientLabel.hide()
            self.__histogram.gradient.hide()

    def showChannels(self, status=True):
        """ show/hide channel widget

        :param status: show channel flag
        :type status: :obj:`bool`
        """
        if status:
            self.__ui.channelWidget.show()
        else:
            self.__ui.channelWidget.hide()
            # self.__ui.monoRadioButton.setChecked(2)

    @QtCore.pyqtSlot(int)
    def setBins(self, index):
        """ sets bins edges algorithm for histogram

        :param index: bins edges algorithm index for histogram
        :type index: :obj:`int`
        """
        for histogram in self.__histograms:
            histogram.setBins(
                self.__ui.binsComboBox.itemText(index))
        self.levelsChanged.emit()

    def gradient(self):
        """ provides the current color gradient

        :returns:  gradient name
        :rtype: :obj:`str`
        """
        if self.__gradientcolors and self.__rgbstatus:
            return str(";".join(
                [his.gradient.name for his in self.__histograms]))
        else:
            return str(self.__ui.gradientComboBox.currentText())

    @QtCore.pyqtSlot()
    def _saveGradient1(self):
        """ saves the current gradient
        """
        self._saveGradient(1)

    @QtCore.pyqtSlot()
    def _saveGradient2(self):
        """ saves the current gradient
        """
        self._saveGradient(2)

    @QtCore.pyqtSlot()
    def _saveGradient(self, iid=0):
        """ saves the current gradient

        :param iid: image id
        :type iid: :obj:`int`
        """
        graddlg = gradientDialog.GradientDialog()
        graddlg.protectednames = list(
            set(_pg.graphicsItems.GradientEditorItem.Gradients.keys()) -
            set(self.__customgradients.keys())
        )
        graddlg.createGUI()
        if graddlg.exec_():
            if graddlg.name:
                name = graddlg.name
                gradient = self.__histograms[iid].gradient.getCurrentGradient()
                self.__customgradients[name] = gradient
                _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
                self._addGradientItem(name)
                for i, histogram in enumerate(self.__histograms):
                    lname = histogram.gradient.name
                    histogram.resetGradient()
                    if iid == i:
                        lname = name
                    self.setGradient(lname, i)
                self._updateGradient()
                self.__settings.setCustomGradients(self.__customgradients)
                self.storeSettingsRequested.emit()

    @QtCore.pyqtSlot()
    def _removeGradient1(self):
        """ removes the current gradient
        """
        self._removeGradient(1)

    @QtCore.pyqtSlot()
    def _removeGradient2(self):
        """ removes the current gradient
        """
        self._removeGradient(2)

    @QtCore.pyqtSlot()
    def _removeGradient(self, iid=0):
        """ removes the current gradient

        :param iid: image id
        :type iid: :obj:`int`
        """
        name = self.__histograms[iid].gradient.name

        if name in self.__customgradients:
            if QtGui.QMessageBox.question(
                    self, "Removing Label",
                    'Would you like  to remove "%s"" ?' %
                    (name),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Yes) == QtGui.QMessageBox.No:
                return False
            self.__customgradients.pop(name)
            _pg.graphicsItems.GradientEditorItem.Gradients.pop(name)
            self._removeGradientItem(name)
            for i, histogram in enumerate(self.__histograms):
                lname = histogram.gradient.name
                histogram.resetGradient()
                if name != lname:
                    self.setGradient(lname, i)
            self.__settings.setCustomGradients(self.__customgradients)
            self.storeSettingsRequested.emit()
        else:
            messageBox.MessageBox.warning(
                self, "Gradient: '%s' cannot be removed" % str(name),
                None, None)

    def _addGradientItem(self, name):
        """ sets gradient

        :param name  gradient name
        :type name: :obj:`str`
        """
        cid = self.__ui.gradientComboBox.findText(name)
        if cid < 0:
            self.__ui.gradientComboBox.addItem(name)

    def _removeGradientItem(self, name):
        """ removes gradient

        :param name  gradient name
        :type name: :obj:`str`
        """
        cid = self.__ui.gradientComboBox.findText(name)
        if cid > -1:
            self.__ui.gradientComboBox.removeItem(cid)
            self._updateGradient(0)
        else:
            logger.error(
                "_removeGradientItem: "
                "Error in _removeGradientItem for %s" % name)
            # print("Error %s" % name)

    def setGradient(self, name, iid=None):
        """ sets gradient

        :param name  gradient name
        :type name: :obj:`str`
        :param iid: image id
        :type iid: :obj:`int`
        """
        if iid is not None:
            self.__histograms[iid].setGradientByName(name)
            self.__changeGradientSlots[iid](name)
        else:
            names = name.split(";")
            for i, nm in enumerate(names):
                if i > 2:
                    break
                self.__histograms[i].setGradientByName(nm)
                if i + 1 == self.__dchl:
                    self.__changeGradientSlots[i](nm)

    @QtCore.pyqtSlot(int)
    def _updateGradient(self, index=-1):
        """ updates gradient in the intensity histogram

        :param index: gradient index
        :type index: :obj:`int`
        """
        if index == -1:
            name = self.__ui.gradientComboBox.currentText()
            index = self.__ui.gradientComboBox.findText(name)
        # if self.__gradientcolors and self.__rgbstatus:
        if self.__gradientcolors and self.__rgbstatus:
            if not self.__dchl:
                for iid in range(3):
                    self.__histograms[iid].setGradientByName(
                        self.__ui.gradientComboBox.itemText(index))
            else:
                self.__histograms[self.__dchl - 1].setGradientByName(
                    self.__ui.gradientComboBox.itemText(index))
        else:
            self.__histogram.setGradientByName(
                self.__ui.gradientComboBox.itemText(index))
        self.gradientChanged.emit()

    @QtCore.pyqtSlot(str)
    def _changeGradient0(self, name):
        """ updates the gradient combobox

        :param name: gradient name
        :type name: :obj:`str`
        """
        self._changeGradient(name, 0)

    @QtCore.pyqtSlot(str)
    def _changeGradient1(self, name):
        """ updates the gradient combobox

        :param name: gradient name
        :type name: :obj:`str`
        """
        self._changeGradient(name, 1)

    @QtCore.pyqtSlot(str)
    def _changeGradient2(self, name):
        """ updates the gradient combobox

        :param name: gradient name
        :type name: :obj:`str`
        """
        self._changeGradient(name, 2)

    @QtCore.pyqtSlot(str)
    def _changeGradient(self, name, iid=0):
        """ updates the gradient combobox

        :param name: gradient name
        :type name: :obj:`str`
        :param iid: image id
        :type iid: :obj:`int`
        """
        text = self.__ui.gradientComboBox.currentText()
        if text != name:
            cid = self.__ui.gradientComboBox.findText(name)
            if self.__gradientcolors and self.__rgbstatus:
                self.__updateRadio(iid + 1)
            if cid > -1:
                if self.__gradientcolors and self.__rgbstatus or iid == 0:
                    self.__ui.gradientComboBox.setCurrentIndex(cid)
            else:
                logger.error(
                    "LevelsGroupBox.changeGradient: "
                    "Error in _changeGradient for %s" % name)
                # print("Error %s" % name)
        self.gradientChanged.emit()

    def updateHistoImage(self, autoLevel=None):
        """ executes imageChanged of histogram with the givel autoLevel

        :param autoLevel: if automatics levels to be set
        :type autoLevel: :obj:`bool`
        """
        auto = autoLevel if autoLevel is not None else self.__auto
        if self.__gradientcolors and self.__rgbstatus:
            for histogram in self.__histograms:
                histogram.imageChanged(autoLevel=auto)
        else:
            self.__histogram.imageChanged(autoLevel=auto)

    def setImageItem(self, image, iid=0):
        """ sets histogram image

        :param image: histogram image
        :type image: :class:`pyqtgraph.graphicsItems.ImageItem.ImageItem`
        :param iid: image id
        :type iid: :obj:`int`
        """
        self.__histograms[iid].setImageItem(image)

    def levels(self):
        """ provides levels from configuration string

        :returns:  configuration string: lowlim,uplim or
                   lowlim,uplim;c1l,c1u;c2l,c2u;c3l,c3u
        :rtype: :obj:`str`
        """
        lowlim = self.__minval
        uplim = self.__maxval

        main = "%s,%s" % (lowlim, uplim)
        chl = ""
        chw = ""
        if self.__channels:
            chl = ";".join(
                ["%s,%s" % (ch[0], ch[1]) for ch in self.__channels])
            chl = ";%s" % chl
        if self.__dchl in [1, 2, 3]:
            chw = ";%s" % ({1: "red", 2: "green", 3: "blue"}[self.__dchl])
        return "%s%s%s" % (main, chl, chw)

    def channelLevels(self):
        """ provides levels from configuration string

        :returns:  channel levels
        :rtype: :obj:`str`
        """
        if self.__channels is not None:
            return list(self.__channels)

    def setLevels(self, cnflevels):
        """ set levels from configuration string

        :param cnflevels:  configuration string: lowlim,uplim   or
               lowlim,uplim;lowred,upred;lowgreen,upgreen;lowblue,upblue
        :type cnflevels: :obj:`str`
        """
        dchl = 0
        channels = None
        if cnflevels:
            clst = cnflevels.split(";")
            if clst[-1].startswith("r") or clst[-1].startswith("R"):
                dchl = 1
                clst.pop()
            elif clst[-1].startswith("g") or clst[-1].startswith("G"):
                dchl = 2
                clst.pop()
            elif clst[-1].startswith("b") or clst[-1].startswith("B"):
                dchl = 3
                clst.pop()
            channels = []
            if clst:
                self.__ui.autoLevelsCheckBox.setChecked(False)
                self._onAutoLevelsChanged(0)
                for ch in clst[1:]:
                    llst = ch.split(",")
                    lmin = None
                    lmax = None
                    try:
                        smin = llst[0]
                        if smin.startswith("m"):
                            smin = "-" + smin[1:]
                        lmin = float(smin)
                    except Exception as e:
                        logger.warning(str(e))
                        # print(str(e))
                    try:
                        smax = llst[1]
                        if smax.startswith("m"):
                            smax = "-" + smax[1:]
                        lmax = float(smax)
                    except Exception as e:
                        logger.warning(str(e))
                    channels.append((lmin, lmax))

                llst = clst[0].split(",")
                lmin = None
                lmax = None
                try:
                    smin = llst[0]
                    if smin.startswith("m"):
                        smin = "-" + smin[1:]
                    lmin = float(smin)
                except Exception:
                    pass
                try:
                    smax = llst[1]
                    if smax.startswith("m"):
                        smax = "-" + smax[1:]
                    lmax = float(smax)
                except Exception:
                    pass
                self.updateLevels(lmin, lmax, channels, force=True)
        self.__updateRadio(dchl)

    def __updateRadio(self, dchl=None):
        """ update RGB radio button position

        :param dchl: channel id
        :type dchl: :obj:`int`
        """
        if dchl is None:
            dchl = self.__dchl
        if dchl == 0 and not self.__ui.monoRadioButton.isChecked():
            self.__ui.monoRadioButton.click()
        elif dchl == 1 and not self.__ui.redRadioButton.isChecked():
            self.__ui.redRadioButton.click()
        elif dchl == 2 and not self.__ui.greenRadioButton.isChecked():
            self.__ui.greenRadioButton.click()
        elif dchl == 3 and not self.__ui.blueRadioButton.isChecked():
            self.__ui.blueRadioButton.click()

    def autoFactor(self):
        """ provides factor for automatic levels

        :returns: factor for automatic levels
        :rtype: :obj:`str`
        """
        return str(self.__ui.autofactorLineEdit.text())

    def setAutoFactor(self, factor):
        """ sets factor for automatic levels

        :param factor: factor for automatic levels
        :type factor: :obj:`str`
        """
        self.__ui.autofactorLineEdit.setText(factor)
        if factor:
            self.setAutoLevels(2)
        self._onAutoFactorChanged(factor)

    def levelMode(self):
        """ return historgram level mode

        :return: level mode
        :rtype: :obj:`str`
        """
        # if self.__histogram and self.__histo:
        #     return self.__histogram.levelMode
        return self.__levelmode

    def setGradientColors(self, status=True):
        """ sets gradientcolors on/off

        :param status: True for on and False for off
        :type status: :obj:`bool`
        """
        if self.__gradientcolors != status:
            self.__gradientcolors = status
            self.showHistograms(self.__rgbstatus)

    def gradientColors(self):
        """ gets gradientcolors on/off

        :returns: True for on and False for off
        :rtype: :obj:`bool`
        """
        return self.__gradientcolors
