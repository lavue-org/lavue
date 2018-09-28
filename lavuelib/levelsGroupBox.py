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

from PyQt4 import QtCore, QtGui, uic
from .histogramWidget import HistogramHLUTWidget, HistogramHLUTItem
import math
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "LevelsGroupBox.ui"))


class LevelsGroupBox(QtGui.QGroupBox):

    """
    Set minimum and maximum displayed values and its color.
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) minimum level changed signal
    minLevelChanged = QtCore.pyqtSignal(float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) maximum level changed signal
    maxLevelChanged = QtCore.pyqtSignal(float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) automatic levels changed signal
    autoLevelsChanged = QtCore.pyqtSignal(int)  # bool does not work...
    #: (:class:`PyQt4.QtCore.pyqtSignal`) levels changed signal
    levelsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) color channel changed signal
    channelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_LevelsGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj: `bool`) colors to be shown
        self.__colors = True
        #: (:obj: `bool`) auto levels enebled
        self.__auto = True
        #: (:obj: `bool`) histogram shown
        self.__histo = True
        #: (:obj: `bool`) levels shown
        self.__levels = True
        #: (:obj: `str`) scale label
        self.__scaling = ""
        #: (:obj: `int`) current color channel
        self.__colorchannel = 0
        #: (:obj: `int`) number of color channels
        self.__numberofchannels = 0

        #: (:obj: `float`) minimum intensity level value
        self.__minval = 0.1
        #: (:obj: `float`) maximum intensity level value
        self.__maxval = 1.

        self.__ui.minDoubleSpinBox.setMinimum(-10e20)
        self.__ui.minDoubleSpinBox.setMaximum(10e20)
        self.__ui.maxDoubleSpinBox.setMinimum(-10e20)
        self.__ui.maxDoubleSpinBox.setMaximum(10e20)

        #: (:class: `lavuelib.histogramWidget.HistogramHLUTWidget`)
        #:      intensity histogram widget
        self.__histogram = HistogramHLUTWidget()
        self.__ui.histogramLayout.addWidget(self.__histogram)

        self.__ui.gradientComboBox.currentIndexChanged.connect(
            self._updateGradient)
        self.setNumberOfChannels(-1)
        self.__ui.channelComboBox.currentIndexChanged.connect(self.setChannel)

        self.__hideControls()
        self.__ui.autoLevelsCheckBox.stateChanged.connect(
            self._onAutoLevelsChanged)
        self.__connectHistogram()
        self.updateLevels(self.__minval, self.__maxval)
        self.__connectMinMax()

    def __connectHistogram(self):
        """ create histogram object and connect its signals
        """
        self.__histogram.item.sigLevelsChanged.connect(self._onLevelsChanged)
        self.__histogram.gradient.sigNameChanged.connect(self._changeGradient)

    def __disconnectHistogram(self):
        """ remove histogram object and disconnect its signals
        """
        self.__histogram.item.sigLevelsChanged.disconnect(
            self._onLevelsChanged)
        self.__histogram.gradient.sigNameChanged.disconnect(
            self._changeGradient)

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
                self._checkAndEmit()
                if self.__histo:
                    lowlim = self.__ui.minDoubleSpinBox.value()
                    uplim = self.__ui.maxDoubleSpinBox.value()
                    self.__histogram.region.setRegion([lowlim, uplim])
            finally:
                self.__connectMinMax()

    def changeView(self, showhistogram=None, showlevels=None):
        """ shows or hides the histogram widget

        :param showhistogram: if histogram should be shown
        :type showhistogram: :obj:`bool`
        :param showlevels: if levels should be shown
        :type showlevels: :obj:`bool`
        """

        if showhistogram is True and self.__histo is False:
            self.__connectHistogram()
            self.__histogram.show()
            self.__histogram.fillHistogram(True)
        elif showhistogram is False and self.__histo is True:
            self.__histogram.hide()
            self.__histogram.fillHistogram(False)
            self.__disconnectHistogram()

        if showlevels is True and self.__levels is False:
            if self.__colors:
                self.__ui.channelLabel.show()
                self.__ui.channelComboBox.show()
            else:
                self.__ui.channelLabel.hide()
                self.__ui.channelComboBox.hide()
            self.__ui.gradientLabel.show()
            self.__ui.gradientComboBox.show()
            self.__ui.scalingLabel.show()
            self.__ui.autoLevelsCheckBox.show()
            self.__ui.maxDoubleSpinBox.show()
            self.__ui.maxLabel.show()
            self.__ui.minDoubleSpinBox.show()
            self.__ui.minLabel.show()
            self.__ui.scalingLabel.show()
        elif showlevels is False and self.__levels is True:
            self.__ui.channelLabel.hide()
            self.__ui.channelComboBox.hide()
            self.__ui.gradientLabel.hide()
            self.__ui.gradientComboBox.hide()

            self.__ui.scalingLabel.hide()
            self.__ui.autoLevelsCheckBox.hide()
            self.__ui.maxDoubleSpinBox.hide()
            self.__ui.maxLabel.hide()
            self.__ui.minDoubleSpinBox.hide()
            self.__ui.minLabel.hide()
            self.__ui.scalingLabel.hide()

        if showhistogram is not None:
            self.__histo = showhistogram
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
    def _onAutoLevelsChanged(self, auto):
        """enables or disables automatic levels

        :param auto: if automatics levels to be set
        :type auto: :obj:`bool`
        """
        if auto == 2:
            self.__auto = True
            self.__hideControls()
            self.autoLevelsChanged.emit(1)
        else:
            self.__auto = False
            self.__showControls()
            self.autoLevelsChanged.emit(0)
            self._checkAndEmit()
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(HistogramHLUTItem)
    def _onLevelsChanged(self, histogram):
        """ set min/max level spinboxes according to histogram

        :param histogram: intensity histogram object
        :type histogram: :class: `lavuelib.histogramWidget.HistogramHLUTWidget`

        """
        levels = histogram.region.getRegion()
        lowlim = self.__ui.minDoubleSpinBox.value()
        uplim = self.__ui.maxDoubleSpinBox.value()
        if levels[0] != lowlim or levels[1] != uplim:
            self.__ui.minDoubleSpinBox.setValue(levels[0])
            self.__ui.maxDoubleSpinBox.setValue(levels[1])
            if not self.__auto:
                self._checkAndEmit()

    @QtCore.pyqtSlot()
    def _checkAndEmit(self):
        """ checks if the minimum value is actually smaller than the maximum
        """
        self.__minval = self.__ui.minDoubleSpinBox.value()
        self.__maxval = self.__ui.maxDoubleSpinBox.value()
        if self.__maxval - self.__minval <= 0:
            if self.__minval >= 1.:
                self.__minval = self.__maxval - 1.
            else:
                self.__maxval = self.__minval + 1

        self.__ui.minDoubleSpinBox.setValue(self.__minval)
        self.__ui.maxDoubleSpinBox.setValue(self.__maxval)

        self.minLevelChanged.emit(self.__minval)
        self.maxLevelChanged.emit(self.__maxval)
        self.levelsChanged.emit()

    def updateLevels(self, lowlim, uplim):
        """ set min/max level spinboxes and histogram from the parameters

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        """
        self.__ui.minDoubleSpinBox.setValue(lowlim)
        self.__ui.maxDoubleSpinBox.setValue(uplim)
        if self.__histo and self.__auto:
            levels = self.__histogram.region.getRegion()
            if levels[0] != lowlim or levels[1] != uplim:
                self.__histogram.region.setRegion([lowlim, uplim])

    def __hideControls(self):
        """ disables spinboxes
        """
        self.__ui.minDoubleSpinBox.setEnabled(False)
        self.__ui.maxDoubleSpinBox.setEnabled(False)

    def __showControls(self):
        """ enables spinboxes
        """
        self.__ui.minDoubleSpinBox.setEnabled(True)
        self.__ui.maxDoubleSpinBox.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def setScalingLabel(self, scalingtype):
        """ sets scaling label

        :param scalingtype: scaling type, i.e. log, linear, sqrt
        :type scalingtype: :obj:`str`
        """
        lowlim = float(self.__ui.minDoubleSpinBox.value())
        uplim = float(self.__ui.maxDoubleSpinBox.value())
        if scalingtype == "log":
            if scalingtype != self.__scaling:
                self.__ui.scalingLabel.setText("log scale!")
                if not self.__auto:
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
        elif scalingtype == "linear":
            if scalingtype != self.__scaling:
                self.__ui.scalingLabel.setText("linear scale!")
                if not self.__auto:
                    if self.__scaling == "log":
                        lowlim = math.pow(10, lowlim)
                        uplim = math.pow(10, uplim)
                    elif self.__scaling == "sqrt":
                        lowlim = lowlim * lowlim
                        uplim = uplim * uplim
        elif scalingtype == "sqrt":
            if scalingtype != self.__scaling:
                self.__ui.scalingLabel.setText("sqrt scale!")
                if not self.__auto:
                    if self.__scaling == "linear":
                        lowlim = math.sqrt(max(lowlim, 0))
                        uplim = math.sqrt(max(uplim, 0))
                    elif self.__scaling == "log":
                        lowlim = math.sqrt(max(math.pow(10, lowlim), 0))
                        uplim = math.sqrt(max(math.pow(10, uplim), 0))
        if scalingtype != self.__scaling:
            self.__scaling = scalingtype
        if not self.__auto:
            if self.__histo:
                self.__histogram.region.setRegion([lowlim, uplim])
            else:
                self.__ui.minDoubleSpinBox.setValue(lowlim)
                self.__ui.maxDoubleSpinBox.setValue(uplim)

    @QtCore.pyqtSlot(int)
    def setChannel(self, channel):
        """ sets color channel

        :param channel: color channel
        :type channel: :obj:`int`
        """
        if self.__colorchannel != channel:
            if channel >= 0 and channel <= self.__numberofchannels + 1:
                self.__colorchannel = channel
                self.channelChanged.emit()

    def colorChannel(self):
        """ provides color channel

        :returns: color channel
        :rtype: :obj:`int`
        """
        return self.__colorchannel

    def setNumberOfChannels(self, number):
        """ sets maximum number of color channel

        :param number:  number of color channel
        :type number: :obj:`int`
        """
        if number != self.__numberofchannels:
            self.__numberofchannels = int(max(number, 0))
            if self.__numberofchannels > 0:
                for i in reversed(
                        range(0, self.__ui.channelComboBox.count())):
                    self.__ui.channelComboBox.removeItem(i)
                self.__ui.channelComboBox.addItem("sum")

                self.__ui.channelComboBox.addItems(
                    ["channel %s" % (ch + 1)
                     for ch in range(self.__numberofchannels)])

                self.__ui.channelComboBox.addItem("mean")
                self.__ui.channelLabel.show()
                self.__ui.channelComboBox.show()
                self.__colors = True
            else:
                self.__ui.channelLabel.hide()
                self.__ui.channelComboBox.hide()
                self.__colors = False

    def setGradient(self, name):
        """ set gradient

        :param cnflevels:  configuration string
        :type cnflevels: :obj:`str`
        """
        self._changeGradient(name)

    @QtCore.pyqtSlot(int)
    def _updateGradient(self, index):
        """ updates gradient in the intensity histogram

        :param index: gradient index
        :type index: :obj:`int`
        """
        self.__histogram.setGradientByName(
            self.__ui.gradientComboBox.itemText(index))

    @QtCore.pyqtSlot(str)
    def _changeGradient(self, name):
        """ updates the gradient combobox

        :param name: gradient name
        :type name: :obj:`str`
        """
        text = self.__ui.gradientComboBox.currentText()
        if text != name:
            cid = self.__ui.gradientComboBox.findText(name)
            if cid > -1:
                self.__ui.gradientComboBox.setCurrentIndex(cid)
            else:
                print("Error %s" % name)

    def updateHistoImage(self, autoLevel=None):
        """ executes imageChanged of histogram with the givel autoLevel

        :param autoLevel: if automatics levels to be set
        :type autoLevel: :obj:`bool`
        """
        auto = autoLevel if autoLevel is not None else self.__auto
        self.__histogram.imageChanged(autoLevel=auto)

    def setImageItem(self, image):
        """ sets histogram image

        :param image: histogram image
        :type image: :class:`pyqtgraph.graphicsItems.ImageItem.ImageItem`
        """
        self.__histogram.setImageItem(image)

    def setLevels(self, cnflevels):
        """ set levels from configuration string

        :param cnflevels:  configuration string
        :type cnflevels: :obj:`str`
        """
        self.__ui.autoLevelsCheckBox.setChecked(False)
        self._onAutoLevelsChanged(0)
        llst = cnflevels.split(",")
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
        self.updateLevels(lmin, lmax)
