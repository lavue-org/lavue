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

""" detector geometry widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "GeometryDialog.ui"))


class GeometryDialog(QtWidgets.QDialog):

    """ detector geometry widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) x-coordinates of the center of the image
        self.centerx = 0.0
        #: (:obj:`float`) y-coordinates of the center of the image
        self.centery = 0.0
        #: (:obj:`float`) energy in eV
        self.energy = 0.0
        #: (:obj:`float`) pixel x-size in um
        self.pixelsizex = 0.0
        #: (:obj:`float`) pixel y-size in um
        self.pixelsizey = 0.0
        #: (:obj:`float`) detector distance in mm
        self.detdistance = 0.0

    def createGUI(self):
        """ create GUI
        """
        self.__ui.centerxLineEdit.setText(str(self.centerx))
        self.__ui.centeryLineEdit.setText(str(self.centery))
        self.__ui.energyLineEdit.setText(str(self.energy))
        self.__ui.pixelsizexLineEdit.setText(str(self.pixelsizex))
        self.__ui.pixelsizeyLineEdit.setText(str(self.pixelsizey))
        self.__ui.detdistanceLineEdit.setText(str(self.detdistance))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.centerx = float(self.__ui.centerxLineEdit.text())
        except Exception:
            self.__ui.centerxLineEdit.setFocus()
            return

        try:
            self.centery = float(self.__ui.centeryLineEdit.text())
        except Exception:
            self.__ui.centeryLineEdit.setFocus()
            return

        try:
            energy = float(self.__ui.energyLineEdit.text())
            if energy <= 0:
                raise Exception("Wrong value")
            else:
                self.energy = energy
        except Exception:
            self.__ui.energyLineEdit.setFocus()
            return

        try:
            pixelsizex = float(self.__ui.pixelsizexLineEdit.text())
            if pixelsizex <= 0:
                raise Exception("Wrong value")
            else:
                self.pixelsizex = pixelsizex
        except Exception:
            self.__ui.pixelsizexLineEdit.setFocus()
            return

        try:
            pixelsizey = float(self.__ui.pixelsizeyLineEdit.text())
            if pixelsizey <= 0:
                raise Exception("Wrong value")
            else:
                self.pixelsizey = pixelsizey
        except Exception:
            self.__ui.pixelsizeyLineEdit.setFocus()
            return

        try:
            detdistance = float(self.__ui.detdistanceLineEdit.text())
            if detdistance <= 0:
                raise Exception("Wrong value")
            else:
                self.detdistance = detdistance
        except Exception:
            self.__ui.detdistanceLineEdit.setFocus()
            return

        QtWidgets.QDialog.accept(self)
