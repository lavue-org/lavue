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

""" detector range widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


_tformclass, _tbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "DiffRangeTabDialog.ui"))


class DiffRangeTabDialog(QtWidgets.QDialog):

    """ diffractogram range widget class"""

    def __init__(self, nranges=1, parent=None):
        """ constructort

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _tformclass()
        self.__ui.setupUi(self)

        #: (:obj:`int`) a number of ranges
        self.__nranges = min(4, nranges)
        #: (:obj:`float`) start position of radial coordinate
        self.radstart = []
        #: (:obj:`float`) end position of radial coordinate
        self.radend = []
        #: (:obj:`float`) start position of azimuth angle
        self.azstart = []
        #: (:obj:`float`) end position of azimuth angle
        self.azend = []
        #: (:obj:`int`) radial angle index
        self.radunitindex = 2
        #: (:obj:`list` <:obj:`unicode`>) list of units
        self.radunits = [u"1/nm", u"1/\u212B", u"deg", u"rad", u"mm"]
        #: (:obj:`list` <:class:`pyqtgraph.QtWidgets.QLineEdit`>)
        #          list of azstartLineEdit widgets
        self.__azstartLineEdit = [self.__ui.azstartLineEdit,
                                  self.__ui.azstart2LineEdit,
                                  self.__ui.azstart3LineEdit,
                                  self.__ui.azstart4LineEdit]
        #: (:obj:`list` <:class:`pyqtgraph.QtWidgets.QLineEdit`>)
        #          list of azendLineEdit widgets
        self.__azendLineEdit = [self.__ui.azendLineEdit,
                                self.__ui.azend2LineEdit,
                                self.__ui.azend3LineEdit,
                                self.__ui.azend4LineEdit]
        #: (:obj:`list` <:class:`pyqtgraph.QtWidgets.QLineEdit`>)
        #          list of radstartLineEdit widgets
        self.__radstartLineEdit = [self.__ui.radstartLineEdit,
                                   self.__ui.radstart2LineEdit,
                                   self.__ui.radstart3LineEdit,
                                   self.__ui.radstart4LineEdit]
        #: (:obj:`list` <:class:`pyqtgraph.QtWidgets.QLineEdit`>)
        #          list of radendLineEdit widgets
        self.__radendLineEdit = [self.__ui.radendLineEdit,
                                 self.__ui.radend2LineEdit,
                                 self.__ui.radend3LineEdit,
                                 self.__ui.radend4LineEdit]

    def createGUI(self):
        """ create GUI
        """

        for i in reversed(range(self.__nranges, 4)):
            self.__ui.tabWidget.removeTab(i)

        for i in range(self.__nranges):
            if len(self.azstart) > i and self.azstart[i] is not None:
                self.__azstartLineEdit[i].setText(str(self.azstart[i]))
            if len(self.azend) > i and self.azend[i] is not None:
                self.__azendLineEdit[i].setText(str(self.azend[i]))
            if len(self.radstart) > i and self.radstart[i] is not None:
                self.__radstartLineEdit[i].setText(str(self.radstart[i]))
            if len(self.radend) > i and self.radend[i] is not None:
                self.__radendLineEdit[i].setText(str(self.radend[i]))

        # self.__ui.radendLabel.setText("End [%s]:" %
        #                               self.radunits[self.radunitindex])
        # self.__ui.radstartLabel.setText("Start [%s]:" %
        #                                 self.radunits[self.radunitindex])

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        self.azstart = []
        self.azend = []
        self.radstart = []
        self.radend = []
        for i in range(self.__nranges):
            try:
                self.azstart.append(
                    float(self.__azstartLineEdit[i].text()))
            except Exception:
                self.azstart.append(None)
            try:
                self.azend.append(float(self.__azendLineEdit[i].text()))
            except Exception:
                self.azend.append(None)

            if self.azend[-1] is not None and self.azstart[-1] is not None \
               and self.azend[-1] < self.azstart[-1]:
                self.azstart[-1], self.azend[-1] = \
                    self.azend[-1], self.azstart[-1]
            try:
                self.radstart.append(
                    min(float(self.__radstartLineEdit[i].text()), 90))
            except Exception:
                self.radstart.append(None)
            try:
                self.radend.append(
                    min(float(self.__radendLineEdit[i].text()), 90))
            except Exception:
                self.radend.append(None)

            if self.radend[-1] is not None and self.radstart[-1] is not None \
               and self.radend[-1] < self.radstart[-1]:
                self.radstart[-1], self.radend[-1] = \
                    self.radend[-1], self.radstart[-1]
        QtWidgets.QDialog.accept(self)
