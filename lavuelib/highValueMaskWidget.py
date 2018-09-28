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

from PyQt4 import QtCore, QtGui, uic
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HighValueMaskWidget.ui"))


class HighValueMaskWidget(QtGui.QWidget):

    """
    Define and apply masking of the displayed image.
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) mask high value changed signal
    maskHighValueChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtGui.QWidget.__init__(self, parent)

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

    def setMask(self, value):
        """ sets the image mask high value

        :param fname: high pixel value for masking
        :type fname: :obj:`str`
        """
        self.__highValue = self.setDisplayedValue(value)
        self.__ui.highvalueLineEdit.setText(self.__highValue)
        self.maskHighValueChanged.emit(self.__highValue)

    @QtCore.pyqtSlot(str)
    def _applyHighValue(self, value):
        """ shows file dialog and select the file name
        """
        self.__highValue = self.setDisplayedValue(value)

        self.maskHighValueChanged.emit(self.__highValue)

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
        if self.__maskvalue is None:
            self.__ui.highvalueLabel.setEnabled(False)
        else:
            self.__ui.highvalueLabel.setEnabled(True)
        return value

    def noValue(self):
        """ unchecks the apply checkbox and clear the file display
        """
        self.setDisplayedValue("")
        self.__maskvalue = None
        self.__ui.highvalueLabel.setEnabled(False)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = HighValueMaskWidget()
    myapp.show()
    sys.exit(app.exec_())
