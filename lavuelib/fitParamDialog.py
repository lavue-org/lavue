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

""" initial fit parameters widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os
from enum import Enum

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "FitParamDialog.ui"))


class PWD(Enum):
    """ Enum with Parameter Widget positions
    """
    label = 0
    write = 1


class FitParamDialog(QtWidgets.QDialog):

    """ initial fit parameters widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`list` <:obj: `float`>) initial parameters
        self.parameters = []
        #: (:obj:`list` <:obj: `float`>) last parameters
        self.last_parameters = []
        #: (:obj:`list` <:obj: `str`>) parameters names
        self.parameters_names = []

        #: (:obj:`list` <:obj:`list` <:class:`pyqtgraph.QtCore.QObject`> >)
        # widgets
        self.__widgets = []

    def createGUI(self):
        """ create GUI
        """
        layout = self.__ui.gridLayout
        while len(self.parameters_names) > len(self.__widgets):
            self.__widgets.append(
                [
                    QtWidgets.QLabel(parent=self),
                    QtWidgets.QLineEdit(parent=self),
                ]
            )
            last = len(self.__widgets)
            self.__widgets[-1][PWD.write.value].setAlignment(
                QtCore.Qt.AlignRight)
            for i, w in enumerate(self.__widgets[-1]):
                layout.addWidget(w, last, i)
        for i, pars in enumerate(self.parameters_names):
            self.__widgets[i][PWD.label.value].setText("%s:" % pars)
            if len(self.parameters) > i:
                self.__widgets[i][PWD.write.value].setText(
                    str(self.parameters[i]))
            else:
                self.__widgets[i][PWD.write.value].setText("")
            if len(self.last_parameters) > i:
                self.__widgets[i][PWD.label.value].setToolTip(
                    "%s" % self.last_parameters[i])
                self.__widgets[i][PWD.write.value].setToolTip(
                    "%s" % self.last_parameters[i])

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        parameters = []
        for wid, pars in enumerate(self.parameters_names):
            try:
                txt = str(self.__widgets[wid][PWD.write.value].text() or "")

                if not txt and pars.endswith("(optional)"):
                    break
                parameters.append(float(txt))
            except Exception:
                self.__ui.self.__widgets[wid][PWD.write.value].setFocus()
                return

        self.parameters = parameters
        QtWidgets.QDialog.accept(self)
