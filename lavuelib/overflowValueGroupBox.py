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
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" overflow value groupbox """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "OverflowValueGroupBox.ui"))


class OverflowValueGroupBox(QtWidgets.QGroupBox):

    """
    Define and apply overflow value of the displayed image.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) overflow value changed signal
    overflowValueChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply state change signal
    applyStateChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtWidgets.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_OverflowValueGroupBox') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) file name
        self.__overflowvalue = None
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings

        self.noValue()
        self.__ui.overflowvalueLineEdit.textChanged.connect(
            self._applyOverflowValue)
        self.__ui.overflowvalueCheckBox.clicked.connect(
            self._emitApplyStateChanged)

    @QtCore.pyqtSlot(bool)
    def _emitApplyStateChanged(self, state):
        """ emits state of apply button

        :param state: apply button state
        :type state: :obj:`bool`
        """
        self.applyStateChanged.emit(int(state))

    def setOverflowValue(self, value):
        """ sets the image overflow value

        :param fname: high pixel overflow value
        :type fname: :obj:`str`
        """
        self.__overflowvalue = self.setDisplayedValue(value)
        self.__ui.overflowvalueLineEdit.setText(self.__overflowvalue)
        self.overflowValueChanged.emit(self.__overflowvalue)
        self.__ui.overflowvalueCheckBox.setChecked(True)

    def overflowValue(self):
        """ provides the image overflow value

        :returns: high pixel overflow value
        :rtype: :obj:`str`
        """
        if self.__ui.overflowvalueCheckBox.isChecked():
            return self.__overflowvalue
        else:
            return ""

    @QtCore.pyqtSlot(str)
    def _applyOverflowValue(self, value):
        """ shows file dialog and select the file name
        """
        self.__overflowvalue = self.setDisplayedValue(value)

        self.overflowValueChanged.emit(self.__overflowvalue)

    def setDisplayedValue(self, value):
        """ sets displayed high pixel value

        :param name: high pixel value
        :type name: :obj:`str`
        """
        try:
            self.__overflowvalue = float(value)
        except Exception:
            self.__overflowvalue = None
            value = ""
        return value

    def noValue(self):
        """ unchecks the apply checkbox and clear the file display
        """
        self.setDisplayedValue("")
        self.__overflowvalue = None
        self.__ui.overflowvalueCheckBox.setChecked(False)

    def changeView(self, showoverflow=False):
        """ shows or hides the overflow widget

        :param showoverflow: if overflow widget should be shown
        :type showoverflow: :obj:`bool`
        """
        if showoverflow:
            self.show()
        else:
            self.hide()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    myapp = OverflowValueGroupBox()
    myapp.show()
    sys.exit(app.exec_())
