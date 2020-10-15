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

""" background subtreaction widget """


from .qtuic import uic
from pyqtgraph import QtCore, QtGui

import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "BkgSubtractionWidget.ui"))


class BkgSubtractionWidget(QtGui.QWidget):

    """
    Define bkg image and subtract from displayed image.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) bkg file selected signal
    bkgFileSelected = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) use current image signal
    useCurrentImageAsBkg = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply state change signal
    applyStateChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) bkg file selected signal
    bfFileSelected = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) use current image signal
    useCurrentImageAsBF = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply state change signal
    applyBFStateChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:class:`Ui_BkgSubtractionkWidget') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) file name
        self.__fileName = ""
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings

        self.__ui.selectPushButton.clicked.connect(self._showImageSelection)
        self.__ui.selectCurrentPushButton.hide()
        self.__ui.selectCurrentPushButton.clicked.connect(self._useCurrent)

        self.__ui.selectFilePushButton.hide()
        self.__ui.selectFilePushButton.clicked.connect(self._showFileDialog)
        self.__ui.applyBkgCheckBox.clicked.connect(
            self._emitApplyStateChanged)
        if QtGui.QIcon.hasThemeIcon("document-open"):
            icon = QtGui.QIcon.fromTheme("document-open")
            self.__ui.selectPushButton.setIcon(icon)

        self.__ui.selectBFPushButton.clicked.connect(
            self._showBFImageSelection)
        self.__ui.selectCurrentBFPushButton.hide()
        self.__ui.selectCurrentBFPushButton.clicked.connect(self._useCurrentBF)

        self.__ui.selectBFFilePushButton.hide()
        self.__ui.selectBFFilePushButton.clicked.connect(
            self._showBFFileDialog)
        self.__ui.applyBFCheckBox.clicked.connect(
            self._emitApplyBFStateChanged)
        if QtGui.QIcon.hasThemeIcon("document-open"):
            icon = QtGui.QIcon.fromTheme("document-open")
            self.__ui.selectBFPushButton.setIcon(icon)

    @QtCore.pyqtSlot(bool)
    def _emitApplyStateChanged(self, state):
        """ emits state of apply button

        :param state: apply button state
        :type state: :obj:`bool`
        """
        self.applyStateChanged.emit(int(state))

    @QtCore.pyqtSlot(bool)
    def _emitApplyBFStateChanged(self, state):
        """ emits state of apply brightfield button

        :param state: apply button state
        :type state: :obj:`bool`
        """
        self.applyBFStateChanged.emit(int(state))

    @QtCore.pyqtSlot()
    def _showFileDialog(self):
        """ shows file dialog and select the file name
        """
        fileDialog = QtGui.QFileDialog()

        fileout = fileDialog.getOpenFileName(
            self, 'Open file', self.__settings.bkgimagename or '.')
        if isinstance(fileout, tuple):
            fileName = str(fileout[0])
        else:
            fileName = str(fileout)
        if fileName:
            self.__settings.bkgimagename = fileName
            self.setDisplayedName(self.__settings.bkgimagename)
            self.bkgFileSelected.emit(self.__settings.bkgimagename)
            self.__hideImageSelection()

    @QtCore.pyqtSlot()
    def _showBFFileDialog(self):
        """ shows file dialog and select the file name
        """
        fileDialog = QtGui.QFileDialog()

        fileout = fileDialog.getOpenFileName(
            self, 'Open file', self.__settings.bfimagename or '.')
        if isinstance(fileout, tuple):
            fileName = str(fileout[0])
        else:
            fileName = str(fileout)
        if fileName:
            self.__settings.bfimagename = fileName
            self.setDisplayedBFName(self.__settings.bfimagename)
            self.bfFileSelected.emit(self.__settings.bfimagename)
            self.__hideBFImageSelection()

    def setBackground(self, fname):
        """ sets the image background

        :param fname: file name
        :type fname: :obj:`str`
        """
        self.__settings.bkgimagename = fname
        self.setDisplayedName(fname)
        self.bkgFileSelected.emit(fname)
        self.__ui.applyBkgCheckBox.setChecked(True)
        self.applyStateChanged.emit(2)

    def setBrightField(self, fname):
        """ sets the image background

        :param fname: file name
        :type fname: :obj:`str`
        """
        self.__settings.bfimagename = fname
        self.setDisplayedBFName(fname)
        self.bfFileSelected.emit(fname)
        self.__ui.applyBFCheckBox.setChecked(True)
        self.applyBFStateChanged.emit(2)

    @QtCore.pyqtSlot()
    def _useCurrent(self):
        """ emits useCurrentImageAsBkg and hides image selection
        """
        self.useCurrentImageAsBkg.emit()
        self.__hideImageSelection()

    @QtCore.pyqtSlot()
    def _useCurrentBF(self):
        """ emits useCurrentImageAsBF and hides image selection
        """
        self.useCurrentImageAsBF.emit()
        self.__hideBFImageSelection()

    def setDisplayedName(self, name):
        """ sets displayed file name

        :param name: file name
        :type name: :obj:`str`
        """
        if name == "":
            self.__ui.fileLabel.setText("no Image selected")
            self.__ui.applyBkgCheckBox.setEnabled(False)
        else:
            self.__ui.fileLabel.setText("..." + str(name)[-24:])
            self.__ui.applyBkgCheckBox.setEnabled(True)

    def setDisplayedBFName(self, name):
        """ sets displayed file name

        :param name: file name
        :type name: :obj:`str`
        """
        if name == "":
            self.__ui.bfFileLabel.setText("no Image selected")
            self.__ui.applyBFCheckBox.setEnabled(False)
        else:
            self.__ui.bfFileLabel.setText("..." + str(name)[-24:])
            self.__ui.applyBFCheckBox.setEnabled(True)

    @QtCore.pyqtSlot()
    def _showImageSelection(self):
        """ shows image selection
        """
        self.__ui.selectCurrentPushButton.show()
        self.__ui.selectFilePushButton.show()
        self.__ui.selectPushButton.hide()

    @QtCore.pyqtSlot()
    def _showBFImageSelection(self):
        """ shows image selection
        """
        self.__ui.selectCurrentBFPushButton.show()
        self.__ui.selectBFFilePushButton.show()
        self.__ui.selectBFPushButton.hide()

    def __hideImageSelection(self):
        """ hides image selection
        """
        self.__ui.selectCurrentPushButton.hide()
        self.__ui.selectFilePushButton.hide()
        self.__ui.selectPushButton.show()

    def __hideBFImageSelection(self):
        """ hides image selection
        """
        self.__ui.selectCurrentBFPushButton.hide()
        self.__ui.selectBFFilePushButton.hide()
        self.__ui.selectBFPushButton.show()

    def checkBFSubtraction(self, state):
        """ unchecks apply CheckBox if state is 1 and it is checked
        and reset the display

        :param state: checkbox state
        :type state:  :obj:`int`
        """
        if not state and self.__ui.applyBFCheckBox.isChecked():
            self.__ui.applyBFCheckBox.setChecked(False)
            self.setDisplayedBFName("")

    def checkBkgSubtraction(self, state):
        """ unchecks apply CheckBox if state is 1 and it is checked
        and reset the display

        :param state: checkbox state
        :type state:  :obj:`int`
        """
        if not state and self.__ui.applyBkgCheckBox.isChecked():
            self.__ui.applyBkgCheckBox.setChecked(False)
            self.setDisplayedName("")

    def isBkgSubApplied(self):
        """ if background subtraction applied
        :returns: apply status
        :rtype: :obj:`bool`
        """
        return self.__ui.applyBkgCheckBox.isChecked()

    def isBFSubApplied(self):
        """ if brightfield correction applied
        :returns: apply status
        :rtype: :obj:`bool`
        """
        return self.__ui.applyBFCheckBox.isChecked()


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    myapp = BkgSubtractionWidget()
    myapp.show()
    sys.exit(app.exec_())
