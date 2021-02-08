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
        self.__scaling = ""
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings
        #: (:obj:`bool`) expert mode
        self.__expertmode = expertmode

        #: (:obj:`dict` < :obj:`str`, :obj:`dict` < :obj:`str`,`any`> >
        #                custom gradients
        self.__customgradients = self.__settings.customGradients()
        for name, gradient in self.__customgradients.items():
            _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
            self._addGradientItem(name)

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

        for name in _pg.graphicsItems.GradientEditorItem.\
                Gradients.keys():
            self._addGradientItem(name)

        self.__histogram = HistogramHLUTWidget(
            bins='auto', step='auto',
            expertmode=expertmode)
        self.__ui.histogramLayout.addWidget(self.__histogram)

        self.__ui.gradientComboBox.currentIndexChanged.connect(
            self._updateGradient)
        self.__ui.binsComboBox.currentIndexChanged.connect(self.setBins)

        self.__hideControls()
        self.__ui.autoLevelsCheckBox.stateChanged.connect(
            self._onAutoLevelsChanged)
        self.__ui.stepLineEdit.textChanged.connect(
            self._onStepChanged)
        self.__ui.autofactorLineEdit.textChanged.connect(
            self._onAutoFactorChanged)
        self.__connectHistogram()
        self.updateLevels(self.__minval, self.__maxval)
        self.__connectMinMax()

    def __connectHistogram(self):
        """ create histogram object and connect its signals
        """
        self.__histogram.item.sigLevelsChanged.connect(self._onLevelsChanged)
        self.__histogram.sigNameChanged.connect(self._changeGradient)
        self.__histogram.saveGradientRequested.connect(self._saveGradient)
        self.__histogram.removeGradientRequested.connect(self._removeGradient)

    def __disconnectHistogram(self):
        """ remove histogram object and disconnect its signals
        """
        self.__histogram.item.sigLevelsChanged.disconnect(
            self._onLevelsChanged)
        self.__histogram.sigNameChanged.disconnect(
            self._changeGradient)
        self.__histogram.saveGradientRequested.disconnect(
            self._saveGradient)
        self.__histogram.removeGradientRequested.disconnect(
            self._removeGradient)

    def updateCustomGradients(self, gradients):
        self.__customgradients = dict(gradients)
        for name, gradient in self.__customgradients.items():
            _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
            self._addGradientItem(name)
        self.__histogram.resetGradient()
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
                self._checkAndEmit()
                if self.__histo:
                    lowlim = self.__ui.minDoubleSpinBox.value()
                    uplim = self.__ui.maxDoubleSpinBox.value()
                    self.__histogram.region.setRegion([lowlim, uplim])
            finally:
                self.__connectMinMax()
        else:
            lowlim = self.__ui.minDoubleSpinBox.value()
            uplim = self.__ui.maxDoubleSpinBox.value()
            self.minLevelChanged.emit(lowlim)
            self.maxLevelChanged.emit(uplim)

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
            self.__connectHistogram()
            self.__histogram.show()
            self.__histogram.fillHistogram(True)
        elif showhistogram is False and self.__histo is True:
            self.__histogram.hide()
            self.__histogram.fillHistogram(False)
            self.__disconnectHistogram()
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
            self.__histogram.setStep(fstep)
        except Exception:
            self.__histogram.setStep(None)
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
            self.__histogram.setAutoFactor(ffactor)
            self.autoLevelsChanged.emit(1)
        except Exception:
            self.__histogram.setAutoFactor(None)
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
                self.__histogram.setAutoFactor(ffactor)
            except Exception:
                self.__histogram.setAutoFactor(None)
                self.autoLevelsChanged.emit(2)
        else:
            self.__histogram.setAutoFactor(None)
            self.__auto = False
            self.__showControls()
            self.autoLevelsChanged.emit(0)
            self._checkAndEmit()
        self.levelsChanged.emit()

    @QtCore.pyqtSlot(object)
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
        if lowlim is not None:
            self.__ui.minDoubleSpinBox.setValue(lowlim)
        else:
            lowlim = self.__ui.minDoubleSpinBox.value()
        if uplim is not None:
            self.__ui.maxDoubleSpinBox.setValue(uplim)
        else:
            uplim = self.__ui.maxDoubleSpinBox.value()
        if self.__histo and self.__auto:
            levels = self.__histogram.region.getRegion()
            if levels[0] != lowlim or levels[1] != uplim:
                self.__histogram.region.setRegion([lowlim, uplim])

    def updateAutoLevels(self, lowlim, uplim):
        """ set min/max level spinboxes and histogram from the parameters

        :param lowlim: minimum intensity value
        :type lowlim: :obj:`float`
        :param uplim:  maximum intensity value
        :type uplim: :obj:`float`
        """
        try:
            factor = str(self.__ui.autofactorLineEdit.text())
            float(factor)
            llim, ulim = self.__histogram.getFactorRegion()
            if llim is not None and ulim is not None:
                self.updateLevels(llim, ulim)
                self.minLevelChanged.emit(llim)
                self.maxLevelChanged.emit(ulim)
            else:
                self.updateLevels(lowlim, uplim)
        except Exception:
            self.updateLevels(lowlim, uplim)

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

    @QtCore.pyqtSlot(bool)
    def setrgb(self, status=True):
        """ sets RGB on/off

        :param status: True for on and False for off
        :type status: :obj:`bool`
        """
        self.__histogram.setRGB(status)
        self.showGradient(not status)

    def showGradient(self, status=True):
        """ resets color channel

        :param status: show gradient flag
        :type status: :obj:`bool`
        """
        if status:
            self.__ui.gradientComboBox.show()
            self.__ui.gradientLabel.show()
            self.__histogram.gradient.show()
            self._updateGradient()
        else:
            self.__ui.gradientComboBox.hide()
            self.__ui.gradientLabel.hide()
            self.__histogram.gradient.hide()

    @QtCore.pyqtSlot(int)
    def setBins(self, index):
        """ sets bins edges algorithm for histogram

        :param index: bins edges algorithm index for histogram
        :type index: :obj:`int`
        """
        self.__histogram.setBins(
            self.__ui.binsComboBox.itemText(index))
        self.levelsChanged.emit()

    def gradient(self):
        """ provides the current color gradient

        :returns:  gradient name
        :rtype: :obj:`str`
        """
        return str(self.__ui.gradientComboBox.currentText())

    @QtCore.pyqtSlot()
    def _saveGradient(self):
        """ saves the current gradient
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
                gradient = self.__histogram.gradient.getCurrentGradient()
                self.__customgradients[name] = gradient
                _pg.graphicsItems.GradientEditorItem.Gradients[name] = gradient
                self._addGradientItem(name)
                self.__histogram.resetGradient()
                self.setGradient(name)
                self._updateGradient()
                self.__settings.setCustomGradients(self.__customgradients)
                self.storeSettingsRequested.emit()

    @QtCore.pyqtSlot()
    def _removeGradient(self):
        """ removes the current gradient
        """
        name = str(self.gradient())

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
            self.__histogram.resetGradient()
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

    def setGradient(self, name):
        """ sets gradient

        :param name  gradient name
        :type name: :obj:`str`
        """
        self._changeGradient(name)

    @QtCore.pyqtSlot(int)
    def _updateGradient(self, index=-1):
        """ updates gradient in the intensity histogram

        :param index: gradient index
        :type index: :obj:`int`
        """
        if index == -1:
            name = self.__ui.gradientComboBox.currentText()
            index = self.__ui.gradientComboBox.findText(name)
        self.__histogram.setGradientByName(
            self.__ui.gradientComboBox.itemText(index))
        self.gradientChanged.emit()

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
        self.__histogram.imageChanged(autoLevel=auto)

    def setImageItem(self, image):
        """ sets histogram image

        :param image: histogram image
        :type image: :class:`pyqtgraph.graphicsItems.ImageItem.ImageItem`
        """
        self.__histogram.setImageItem(image)

    def levels(self):
        """ provides levels from configuration string

        :returns:  configuration string: lowlim,uplim
        :rtype: :obj:`str`
        """
        lowlim = self.__ui.minDoubleSpinBox.value()
        uplim = self.__ui.maxDoubleSpinBox.value()
        return "%s,%s" % (lowlim, uplim)

    def setLevels(self, cnflevels):
        """ set levels from configuration string

        :param cnflevels:  configuration string: lowlim,uplim
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
