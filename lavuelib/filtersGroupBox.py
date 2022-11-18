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

""" filter widget """


from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "FiltersGroupBox.ui"))


class FiltersGroupBox(QtWidgets.QWidget):
    """
    Select how an image should be transformed.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) filter changed signal
    filtersChanged = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QWidget.__init__(self, parent)

        #: (:class:`Ui_FiltersGroupBox') ui_widget object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        self.__ui.checkBox.toggled.connect(
            self._onFilterChanged)

    @QtCore.pyqtSlot(bool)
    def _onFilterChanged(self, state):
        """ emits filter changed

        :param state: filter state
        :type state: :obj:`int`
        """
        self.filtersChanged.emit(state)

    def setState(self, state):
        """ sets filter state

        :param tname: filter state
        :type tname: :obj:`int`
        """
        if state:
            self.__ui.checkBox.setChecked(True)
        else:
            self.__ui.checkBox.setChecked(False)
        self.filtersChanged.emit(state)

    def setLabel(self, text):
        """ sets filter label

        :param text: label text
        :type text: :obj:`str`
        """
        self.__ui.label.setText(text)

    def setToolTip(self, text):
        """ sets filter label

        :param text: tool tip text
        :type text: :obj:`str`
        """
        self.__ui.label.setToolTip(text)

    def changeView(self, showfilters=None):
        """ show or hide widgets

        :param showfilters: filter widget shown
        :type showfilters: :obj:`bool`
        """
        if showfilters is not None:
            if showfilters:
                self.show()
            else:
                self.hide()
