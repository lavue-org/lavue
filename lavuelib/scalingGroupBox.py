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

""" scalingGroupBox """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ScalingGroupBox.ui"))


class ScalingGroupBox(QtWidgets.QGroupBox):

    """
    Select how the image intensity is supposed to be scaled.
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) scaling changed signal
    scalingChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) simple scaling changed signal
    simpleScalingChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_ScalingGroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) the current scaling
        self.__current = "sqrt"

        self.__ui.linRadioButton.clicked.connect(self._onScalingChanged)
        self.__ui.logRadioButton.clicked.connect(self._onScalingChanged)
        self.__ui.sqrtRadioButton.clicked.connect(self._onScalingChanged)

    def currentScaling(self):
        """ provides the current scaling

        :returns: current scaline
        :rtype: :obj:`str`
        """
        return self.__current

    @QtCore.pyqtSlot()
    def _onScalingChanged(self):
        """ updates the current scaling
        """
        if self.__ui.linRadioButton.isChecked():
            self.__current = "linear"
        elif self.__ui.logRadioButton.isChecked():
            self.__current = "log"
        else:
            self.__current = "sqrt"
        self.scalingChanged.emit(self.__current)
        self.simpleScalingChanged.emit()

    def changeView(self, showscale=False):
        """ shows or hides the scale widget

        :param showscale: if scale widget should be shown
        :type showscale: :obj:`bool`
        """
        if showscale:
            self.show()
        else:
            self.hide()

    def setScaling(self, scaling):
        """ sets scaling from string

        :param scaling: scaling name, i.e. linear, log or sqrt
        :type scaling:
        """
        if scaling == "linear":
            self.__ui.linRadioButton.setChecked(True)
        elif scaling == "log":
            self.__ui.logRadioButton.setChecked(True)
        else:
            self.__ui.sqrtRadioButton.setChecked(True)
        self._onScalingChanged()
