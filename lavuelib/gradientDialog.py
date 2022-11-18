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

""" gradient dialog """

from .qtuic import uic
from pyqtgraph import QtCore
from . import messageBox
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "GradientDialog.ui"))


class GradientDialog(QtWidgets.QDialog):

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

        #: (:obj:`int`) gradient name
        self.name = ""
        self.protectednames = []

    def createGUI(self):
        """ create GUI
        """
        self.__ui.nameLineEdit.setText(str(self.name))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        name = str(self.__ui.nameLineEdit.text()).strip().lower()
        if name in self.protectednames:
            self.__ui.nameLineEdit.setFocus()
            messageBox.MessageBox.warning(
                self,
                "Gradient: '%s' cannot be overwritten" % str(name),
                None,
                None)
            return False
        self.name = name
        QtWidgets.QDialog.accept(self)
