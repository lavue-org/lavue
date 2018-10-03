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
                 "ui", "MaskWidget.ui"))


class MaskWidget(QtGui.QWidget):

    """
    Define and apply masking of the displayed image.
    """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) mask file selected signal
    maskFileSelected = QtCore.pyqtSignal(str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) apply state change signal
    applyStateChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:class:`Ui_MaskWidget') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) file name
        self.__fileName = ""
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings

        self.__ui.applyMaskCheckBox.clicked.connect(
            self._emitApplyStateChanged)
        self.__ui.fileSelectPushButton.clicked.connect(self._showFileDialog)

    @QtCore.pyqtSlot(int)
    def _emitApplyStateChanged(self, state):
        """ emits state of apply button

        :param state: apply button state
        :type state: :obj:`int`
        """
        self.applyStateChanged.emit(state)

    def setMask(self, fname):
        """ sets the image mask

        :param fname: file name
        :type fname: :obj:`str`
        """
        self.setDisplayedName(fname)
        self.maskFileSelected.emit(fname)
        self.__ui.applyMaskCheckBox.setChecked(True)
        self.applyStateChanged.emit(2)

    @QtCore.pyqtSlot()
    def _showFileDialog(self):
        """ shows file dialog and select the file name
        """
        fileDialog = QtGui.QFileDialog()
        fileName = str(
            fileDialog.getOpenFileName(
                self, 'Open mask file',
                self.__settings.maskimagename or '/ramdisk/'))
        if fileName:
            self.__fileName = fileName
            self.__settings.maskimagename = fileName
            self.setDisplayedName(self.__fileName)
            self.maskFileSelected.emit(self.__fileName)

    def setDisplayedName(self, name):
        """ sets displayed file name

        :param name: file name
        :type name: :obj:`str`
        """
        if name == "":
            self.__ui.fileNameLabel.setText("no image selected")
            self.__ui.applyMaskCheckBox.setEnabled(False)
        else:
            self.__ui.fileNameLabel.setText("..." + str(name)[-24:])
            self.__ui.applyMaskCheckBox.setEnabled(True)

    def noImage(self):
        """ unchecks the apply checkbox and clear the file display
        """
        self.setDisplayedName("")
        self.__fileName = ""
        self.__ui.applyMaskCheckBox.setChecked(False)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = MaskWidget()
    myapp.show()
    sys.exit(app.exec_())
