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

""" normalization widget """


from .qtuic import uic
from pyqtgraph import QtCore, QtGui

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "NormalizationWidget.ui"))


class NormalizationWidget(QtWidgets.QWidget):

    """
    Define bkg image and subtract from displayed image.
    """

    bfFileSelected = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) use current image signal
    useCurrentImageAsBF = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) apply state change signal
    applyBFStateChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) BF scaling factor change signal
    bfScalingFactorChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtWidgets.QWidget.__init__(self, parent)

        #: (:class:`Ui_NormalizationkWidget') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings

        self.__ui.selectBFPushButton.clicked.connect(
            self._showBFImageSelection)
        self.__ui.selectCurrentBFPushButton.hide()
        self.__ui.selectCurrentBFPushButton.clicked.connect(self._useCurrentBF)

        self.__ui.selectBFFilePushButton.hide()
        self.__ui.selectBFFilePushButton.clicked.connect(
            self._showBFFileDialog)
        self.__ui.applyBFCheckBox.clicked.connect(
            self._emitApplyBFStateChanged)
        self.__ui.bfsfLineEdit.textChanged.connect(
            self._emitBFScalingFactorChanged)
        if QtGui.QIcon.hasThemeIcon("document-open"):
            icon = QtGui.QIcon.fromTheme("document-open")
            self.__ui.selectBFPushButton.setIcon(icon)

    def setBFScalingFactor(self, scale):
        """ sets the bright field scaling factor

        :param scale: bright field scaling factor
        :type scale: :obj:`float` or :obj:`str`
        """
        self.__ui.bfsfLineEdit.setText(str(scale if scale is not None else ""))

    def bfScalingFactor(self):
        """ provides bright field scaling factor

        :returns: bright field scaling factor
        :rtype: :obj:`float`
        """
        try:
            scale = float(self.__ui.bfsfLineEdit.text())
        except Exception:
            scale = None
        return scale

    @QtCore.pyqtSlot()
    def _emitBFScalingFactorChanged(self):
        """ emits BF scaling factor chnaged
        """
        self.bfScalingFactorChanged.emit()

    @QtCore.pyqtSlot(bool)
    def _emitApplyBFStateChanged(self, state):
        """ emits state of apply brightfield button

        :param state: apply button state
        :type state: :obj:`bool`
        """
        self.applyBFStateChanged.emit(int(state))

    @QtCore.pyqtSlot()
    def _showBFFileDialog(self):
        """ shows file dialog and select the file name
        """
        fileDialog = QtWidgets.QFileDialog()

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
    def _useCurrentBF(self):
        """ emits useCurrentImageAsBF and hides image selection
        """
        self.useCurrentImageAsBF.emit()
        self.__hideBFImageSelection()

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
    def _showBFImageSelection(self):
        """ shows image selection
        """
        self.__ui.selectCurrentBFPushButton.show()
        self.__ui.selectBFFilePushButton.show()
        self.__ui.selectBFPushButton.hide()

    @QtCore.pyqtSlot()
    def showScalingFactors(self, show=True):
        if show:
            self.__ui.bfsfWidget.show()
        else:
            self.__ui.bfsfWidget.hide()

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

    def isBFSubApplied(self):
        """ if brightfield correction applied
        :returns: apply status
        :rtype: :obj:`bool`
        """
        return self.__ui.applyBFCheckBox.isChecked()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    myapp = NormalizationWidget()
    myapp.show()
    sys.exit(app.exec_())
