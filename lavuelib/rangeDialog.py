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

""" detector range widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "RangeDialog.ui"))


class RangeDialog(QtWidgets.QDialog):

    """ detector range widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) start position of radial coordinate
        self.radthstart = None
        #: (:obj:`float`) end position of radial coordinate
        self.radthend = None
        #: (:obj:`int`) grid size of radial coordinate
        self.radthsize = None
        #: (:obj:`float`) start position of radial coordinate
        self.radqstart = None
        #: (:obj:`float`) end position of radial coordinate
        self.radqend = None
        #: (:obj:`int`) grid size of radial coordinate
        self.radqsize = None
        #: (:obj:`float`) start position of polar angle
        self.polstart = None
        #: (:obj:`float`) end position of polar angle
        self.polend = None
        #: (:obj:`int`) grid size of polar angle
        self.polsize = None

    def createGUI(self):
        """ create GUI
        """
        self.__ui.polstartLineEdit.setText(
            str(self.polstart if self.polstart is not None else ""))
        self.__ui.polendLineEdit.setText(
            str(self.polend if self.polend is not None else ""))
        self.__ui.polsizeLineEdit.setText(
            str(self.polsize if self.polsize is not None else ""))
        self.__ui.radthstartLineEdit.setText(
            str(self.radthstart if self.radthstart is not None else ""))
        self.__ui.radthendLineEdit.setText(
            str(self.radthend if self.radthend is not None else ""))
        self.__ui.radthsizeLineEdit.setText(
            str(self.radthsize if self.radthsize is not None else ""))
        self.__ui.radqstartLineEdit.setText(
            str(self.radqstart if self.radqstart is not None else ""))
        self.__ui.radqendLineEdit.setText(
            str(self.radqend if self.radqend is not None else ""))
        self.__ui.radqsizeLineEdit.setText(
            str(self.radqsize if self.radqsize is not None else ""))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.polstart = float(self.__ui.polstartLineEdit.text())
        except Exception:
            self.polstart = None
        try:
            self.polend = float(self.__ui.polendLineEdit.text())
        except Exception:
            self.polend = None
        try:
            self.polsize = int(self.__ui.polsizeLineEdit.text())
        except Exception:
            self.polsize = None

        try:
            self.radthstart = float(self.__ui.radthstartLineEdit.text())
        except Exception:
            self.radthstart = None
        try:
            self.radthend = float(self.__ui.radthendLineEdit.text())
        except Exception:
            self.radthend = None
        try:
            self.radthsize = int(self.__ui.radthsizeLineEdit.text())
        except Exception:
            self.radthsize = None

        try:
            self.radqstart = float(self.__ui.radqstartLineEdit.text())
        except Exception:
            self.radqstart = None
        try:
            self.radqend = float(self.__ui.radqendLineEdit.text())
        except Exception:
            self.radqend = None
        try:
            self.radqsize = int(self.__ui.radqsizeLineEdit.text())
        except Exception:
            self.radqsize = None

        QtWidgets.QDialog.accept(self)
