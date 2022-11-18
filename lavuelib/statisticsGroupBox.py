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


""" statistics widget """

from .qtuic import uic
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "StatisticsGroupBox.ui"))


class StatisticsGroupBox(QtWidgets.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_GroupBox') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj: `str`) scale label
        self.__scaling = "sqrt"
        self.__ui.scaleLabel.setText(self.__scaling)

    def updateStatistics(self, mean, maximum, variance, scaling):
        """ update image statistic values

        :param meanparent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        if self.__scaling is not scaling:
            self.__scaling = scaling
        self.__ui.scaleLabel.setText(self.__scaling)
        self.__ui.meanLineEdit.setText(mean)
        self.__ui.maxLineEdit.setText(maximum)
        self.__ui.varianceLineEdit.setText(variance)

    def changeView(self, showstats=False, showvariance=False):
        """ shows or hides the histogram widget

        :param showhistogram: if histogram should be shown
        :type showhistogram: :obj:`bool`
        """
        if showstats:
            self.show()
            if showvariance:
                self.__ui.varianceLineEdit.show()
                self.__ui.varianceLabel.show()
            else:
                self.__ui.varianceLineEdit.hide()
                self.__ui.varianceLabel.hide()
        else:
            self.hide()
