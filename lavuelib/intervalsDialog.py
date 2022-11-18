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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" interval device widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "IntervalsDialog.ui"))


class IntervalsDialog(QtWidgets.QDialog):

    """ interval widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`int`) number of x intervals
        self.xintervals = 1
        #: (:obj:`int`) number of y intervals
        self.yintervals = 1
        #: (:obj:`float`) integration time in seconds
        self.itime = 1.0

    def createGUI(self):
        """ create GUI
        """
        self.__ui.xSpinBox.setValue(int(self.xintervals))
        self.__ui.ySpinBox.setValue(int(self.yintervals))
        self.__ui.timeDoubleSpinBox.setValue(float(self.itime))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        self.xintervals = int(self.__ui.xSpinBox.value())
        self.yintervals = int(self.__ui.ySpinBox.value())
        self.itime = float(self.__ui.timeDoubleSpinBox.value())
        QtWidgets.QDialog.accept(self)
