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

"""  editable list dialog """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

# from .EdDataDlg import EdDataDlg

import logging
#: (:obj:`logging.Logger`) logger object
logger = logging.getLogger("lavue")

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "EdDictDialog.ui"))


class EdListDialog(QtWidgets.QDialog):
    """  editable list dialog
    """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`bool`) dirty flag
        self.dirty = False
        #: (:obj:`str`) dialog title
        self.title = False
        #: (:obj:`list` <:obj:`str`>) table headers
        self.headers = ["Label"]
        #: (:obj:`dict` <:obj:`str`, `any`>) data (name, value) dictionary
        self.record = []

    def createGUI(self):
        """ creates widget GUI
        """
        self.setWindowTitle(self.title or "Source Parameters Labels")
        if hasattr(self.__ui, "addPushButton"):
            self.__ui.addPushButton.clicked.disconnect(self.__add)
            self.__ui.removePushButton.clicked.disconnect(self.__remove)
            self.__ui.tableWidget.itemChanged.disconnect(
                self.__tableItemChanged)

        self.__ui.closePushButton = self.__ui.closeButtonBox.button(
            QtWidgets.QDialogButtonBox.Close)

        self.__ui.closeButtonBox.button(
            QtWidgets.QDialogButtonBox.Close).hide()
        if not hasattr(self.__ui, "addPushButton"):
            self.__ui.addPushButton = \
                self.__ui.addEditRemoveButtonBox.addButton(
                    "&Add", QtWidgets.QDialogButtonBox.ActionRole)
            self.__ui.removePushButton = \
                self.__ui.addEditRemoveButtonBox.addButton(
                    "&Remove", QtWidgets.QDialogButtonBox.ActionRole)

        self.__populateTable()
        self.__ui.addPushButton.clicked.connect(self.__add)
        self.__ui.removePushButton.clicked.connect(self.__remove)
        self.__ui.tableWidget.itemChanged.connect(
            self.__tableItemChanged)
        self.__ui.closeButtonBox.button(
            QtWidgets.QDialogButtonBox.Close).clicked.connect(self.accept)
        self.__ui.closePushButton.show()

    def __updateRecord(self):
        record = []
        for i in range(self.__ui.tableWidget.rowCount()):
            item = self.__ui.tableWidget.item(i, 0)
            name = ""
            if item is not None:
                # name = item.data(QtCore.Qt.UserRole)
                # name = item.data(QtCore.Qt.EditRole)
                name = item.data(QtCore.Qt.DisplayRole)
                if hasattr(name, "toString"):
                    name = name.toString()
            record.append(str(name or ""))
        self.record = record

    @QtCore.pyqtSlot()
    def __add(self):
        """ adds a new record into the table
        """
        self.dirty = True
        self.record.append("")
        self.__ui.tableWidget.itemChanged.disconnect(
            self.__tableItemChanged)
        self.__populateTable()
        self.__ui.tableWidget.itemChanged.connect(
            self.__tableItemChanged)

    @QtCore.pyqtSlot()
    def __remove(self):
        """ removes the current record from the table
        """
        idx = self.__ui.tableWidget.currentRow()
        if idx >= 0 and idx < self.__ui.tableWidget.rowCount():
            self.record.pop(idx)
            self.dirty = True
            self.__ui.tableWidget.itemChanged.disconnect(
                self.__tableItemChanged)
            self.__populateTable()
            self.__ui.tableWidget.itemChanged.connect(
                self.__tableItemChanged)

    def __populateTable(self):
        """ populate table records

        :param selected: name of selected item
        :type selected: :obj:`str`
        """
        self.__ui.tableWidget.clear()
        self.__ui.tableWidget.setSortingEnabled(False)
        names = self.record
        self.__ui.tableWidget.setRowCount(len(names))
        self.__ui.tableWidget.setColumnCount(len(self.headers))
        self.__ui.tableWidget.setHorizontalHeaderLabels(self.headers)
        row = 0
        for row, name in enumerate(names):

            item = QtWidgets.QTableWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, (name))
            item.setData(QtCore.Qt.EditRole, (name))
            item.setData(QtCore.Qt.DisplayRole, (name))
            self.__ui.tableWidget.setItem(row, 0, item)
        self.__ui.tableWidget.resizeColumnsToContents()
        if hasattr(self.__ui.tableWidget.horizontalHeader(),
                   "setSectionResizeMode"):
            self.__ui.tableWidget.horizontalHeader().\
                setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        else:
            self.__ui.tableWidget.horizontalHeader().\
                setResizeMode(0, QtWidgets.QHeaderView.Stretch)

    @QtCore.pyqtSlot("QTableWidgetItem*")
    def __tableItemChanged(self, item):
        """ changes the current value of the variable

        :param item: current item
        :type item: :class:`QtWidgets.QTableWidgetItem`
        """
        self.dirty = True
        self.__updateRecord()

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        self.__updateRecord()
        QtWidgets.QDialog.accept(self)
