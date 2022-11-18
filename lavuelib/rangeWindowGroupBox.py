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
#

""" range window widget """


from .qtuic import uic
from pyqtgraph import QtCore

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

import os
import logging

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "RangeWindowGroupBox.ui"))

logger = logging.getLogger("lavue")


class RangeWindowGroupBox(QtWidgets.QWidget):
    """
    Select how an image should be transformed.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) factor changed signal
    factorChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) function changed signal
    functionChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) range window changed signal
    rangeWindowChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QWidget.__init__(self, parent)

        #: (:class:`Ui_RangeWindowGroupBox') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)
        self.__ui.factorSpinBox.valueChanged.connect(
            self._emitFactorChanged)
        self.__ui.functionComboBox.currentIndexChanged.connect(
            self._emitFunctionChanged)
        self.__ui.x1LineEdit.textChanged.connect(self._emitRangeWindowChanged)
        self.__ui.y1LineEdit.textChanged.connect(self._emitRangeWindowChanged)
        self.__ui.x2LineEdit.textChanged.connect(self._emitRangeWindowChanged)
        self.__ui.y2LineEdit.textChanged.connect(self._emitRangeWindowChanged)

    @QtCore.pyqtSlot()
    def _emitRangeWindowChanged(self):
        """emits rangeWindowChanged
        """
        self.rangeWindowChanged.emit()

    @QtCore.pyqtSlot()
    def _emitFunctionChanged(self):
        """emits functionChanged
        """
        self.functionChanged.emit()

    @QtCore.pyqtSlot()
    def _emitFactorChanged(self):
        """emits factorChanged
        """
        self.factorChanged.emit()

    def function(self):
        """ provides the reduction function name, i.e. max, min, mean, sum

        :returns:  function name
        :rtype: :obj:`str`
        """
        return str(self.__ui.functionComboBox.currentText())

    def setFunction(self, name):
        """ sets the reduction function

        :param name:  function name, i.e. max, min, mean, sum
        :type name: :obj:`str`
        """
        text = self.__ui.functionComboBox.currentText()
        if text != name:
            cid = self.__ui.functionComboBox.findText(name)
            if cid > -1:
                self.__ui.functionComboBox.setCurrentIndex(cid)
            else:
                # print("Error %s" % name)
                logger.warning(
                    "RangeWindowGroupBox.setFunction: "
                    "Error in setFunction for %s" % name)

    def factor(self):
        """ provides the current resize factor

        :returns: resize factor
        :rtype: :obj:`int`
        """
        return int(self.__ui.factorSpinBox.value())

    def setFactor(self, factor):
        """ provides the current resize factor

        :param factor: resize factor
        :type factor: :obj:`int`
        """
        try:
            self.__ui.factorSpinBox.setValue(int(factor))
        except Exception:
            self.__ui.factorSpinBox.setValue(1)

    def rangeWindow(self):
        """ provides the range window

        :returns: x1, y1, x2, y2 of range window bounds
        :rtype: :obj:`list` <:obj:`int`>
        """
        try:
            x1 = int(self.__ui.x1LineEdit.text())
        except Exception:
            x1 = None
        try:
            x2 = int(self.__ui.x2LineEdit.text())
        except Exception:
            x2 = None
        try:
            y1 = int(self.__ui.y1LineEdit.text())
        except Exception:
            y1 = None
        try:
            y2 = int(self.__ui.y2LineEdit.text())
        except Exception:
            y2 = None

        return [x1, y1, x2, y2]

    def setRangeWindow(self, bounds):
        """ provides the range window

        :param bounds: range window bounds: x1:x2,y1:y2
        :type: :obj:`str`
        """
        lims = bounds.replace(":", ",").split(",")
        if len(lims) == 4:
            try:
                int(lims[0].replace("m", "-"))
                self.__ui.x1LineEdit.setText(
                    lims[0].replace("m", "-"))
            except Exception:
                self.__ui.x1LineEdit.setText("")
            try:
                int(lims[1].replace("m", "-"))
                self.__ui.x2LineEdit.setText(
                    lims[1].replace("m", "-"))
            except Exception:
                self.__ui.x2LineEdit.setText("")
            try:
                int(lims[2].replace("m", "-"))
                self.__ui.y1LineEdit.setText(
                    lims[2].replace("m", "-"))
            except Exception:
                self.__ui.y1LineEdit.setText("")
            try:
                int(lims[3].replace("m", "-"))
                self.__ui.y2LineEdit.setText(
                    lims[3].replace("m", "-"))
            except Exception:
                self.__ui.y2LineEdit.setText("")

    def changeView(self, showrangeWindow=None):
        """ show or hide widgets

        :param showrangeWindow: widget shown
        :type showrangeWindow: :obj:`bool`
        """
        if showrangeWindow is not None:
            if showrangeWindow:
                self.show()
            else:
                self.hide()
