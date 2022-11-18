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

""" detector axis widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "AxesDialog.ui"))


class AxesDialog(QtWidgets.QDialog):

    """ detector axis widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_AxesDialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`float`) x-coordinates of the first pixel
        self.xposition = None
        #: (:obj:`float`) y-coordinates of the first pixel
        self.yposition = None
        #: (:obj:`float`) x-scale of pixels
        self.xscale = None
        #: (:obj:`float`) y-scale of pixels
        self.yscale = None
        #: (:obj:`str`) text of x-axis
        self.xtext = None
        #: (:obj:`str`) text of y-axis
        self.ytext = None
        #: (:obj:`str`) units of x-axis
        self.xunits = None
        #: (:obj:`str`) units of y-axis
        self.yunits = None

    def createGUI(self):
        """ create GUI
        """
        self.__ui.xpositionLineEdit.setText(
            str(self.xposition if self.xposition is not None else ""))
        self.__ui.ypositionLineEdit.setText(
            str(self.yposition if self.yposition is not None else ""))
        self.__ui.xscaleLineEdit.setText(str(self.xscale or ""))
        self.__ui.yscaleLineEdit.setText(str(self.yscale or ""))
        self.__ui.xtextLineEdit.setText(str(self.xtext or ""))
        self.__ui.ytextLineEdit.setText(str(self.ytext or ""))
        self.__ui.xunitsLineEdit.setText(str(self.xunits or ""))
        self.__ui.yunitsLineEdit.setText(str(self.yunits or ""))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.xposition = float(self.__ui.xpositionLineEdit.text())
        except Exception:
            self.xposition = None
        try:
            self.yposition = float(self.__ui.ypositionLineEdit.text())
        except Exception:
            self.yposition = None

        try:
            xscale = float(self.__ui.xscaleLineEdit.text())
            if xscale <= 0:
                self.xscale = None
            else:
                self.xscale = xscale
        except Exception:
            self.xscale = None
        try:
            yscale = float(self.__ui.yscaleLineEdit.text())
            if yscale <= 0:
                self.yscale = None
            else:
                self.yscale = yscale
        except Exception:
            self.yscale = None

        self.xtext = str(self.__ui.xtextLineEdit.text()) or ""
        self.ytext = str(self.__ui.ytextLineEdit.text()) or ""
        self.xunits = str(self.__ui.xunitsLineEdit.text()) or ""
        self.yunits = str(self.__ui.yunitsLineEdit.text()) or ""

        QtWidgets.QDialog.accept(self)
