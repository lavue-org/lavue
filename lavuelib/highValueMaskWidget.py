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

""" mask widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HighValueMaskWidget.ui"))


class HighValueMaskWidget(QtWidgets.QWidget):

    """
    Define and apply masking of the displayed image.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) mask high value changed signal
    maskHighValueChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply state change signal
    applyStateChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtWidgets.QWidget.__init__(self, parent)

        #: (:class:`Ui_HighValueMaskWidget') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) file name
        self.__maskvalue = None
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings

        self.noValue()
        self.__ui.highvalueLineEdit.textChanged.connect(
            self._applyHighValue)
        self.__ui.highvalueCheckBox.clicked.connect(
            self._emitApplyStateChanged)

    @QtCore.pyqtSlot(bool)
    def _emitApplyStateChanged(self, state):
        """ emits state of apply button

        :param state: apply button state
        :type state: :obj:`bool`
        """
        self.applyStateChanged.emit(int(state))

    def setMask(self, value):
        """ sets the image mask high value

        :param fname: high pixel value for masking
        :type fname: :obj:`str`
        """
        self.__maskvalue = self.setDisplayedValue(value)
        self.__ui.highvalueLineEdit.setText(self.__maskvalue)
        self.maskHighValueChanged.emit(self.__maskvalue)
        self.__ui.highvalueCheckBox.setChecked(True)

    def mask(self):
        """ provides the image mask high value

        :returns: high pixel value for masking
        :rtype: :obj:`str`
        """
        if self.__ui.highvalueCheckBox.isChecked():
            return self.__maskvalue
        else:
            return ""

    @QtCore.pyqtSlot(str)
    def _applyHighValue(self, value):
        """ shows file dialog and select the file name
        """
        self.__maskvalue = self.setDisplayedValue(value)

        self.maskHighValueChanged.emit(self.__maskvalue)

    def setDisplayedValue(self, value):
        """ sets displayed high pixel value

        :param name: high pixel value
        :type name: :obj:`str`
        """
        try:
            self.__maskvalue = float(value)
        except Exception:
            self.__maskvalue = None
            value = ""
        return value

    def noValue(self):
        """ unchecks the apply checkbox and clear the file display
        """
        self.setDisplayedValue("")
        self.__maskvalue = None
        self.__ui.highvalueCheckBox.setChecked(False)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    myapp = HighValueMaskWidget()
    myapp.show()
    sys.exit(app.exec_())
