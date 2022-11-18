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


class EdDictDialog(QtWidgets.QDialog):
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
        self.headers = ["Label", "Value"]
        #: (:obj:`list` <:obj:`str`>) table headers
        self.newvalues = []
        #: (:obj:`dict` <:obj:`str`, `any`>) data (name, value) dictionary
        self.record = {}

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

        if len(self.newvalues) > 0:
            item = ""
        elif self.record:
            item = sorted(self.record.keys())[0]
        else:
            item = None
        self.__populateTable(item)
        self.__ui.addPushButton.clicked.connect(self.__add)
        self.__ui.removePushButton.clicked.connect(self.__remove)
        self.__ui.tableWidget.itemChanged.connect(
            self.__tableItemChanged)
        self.__ui.closeButtonBox.button(
            QtWidgets.QDialogButtonBox.Close).clicked.connect(self.accept)
        self.__ui.closePushButton.show()

    def __updateRecord(self):
        record = {}
        for i in range(self.__ui.tableWidget.rowCount()):
            item = self.__ui.tableWidget.item(i, 0)
            item2 = self.__ui.tableWidget.item(i, 1)
            if item is not None and item2 is not None:
                name = item.data(QtCore.Qt.UserRole)
                value = item2.data(QtCore.Qt.UserRole)
                if hasattr(name, "toString"):
                    name = name.toString()
                if hasattr(value, "toString"):
                    value = value.toString()
                record[str(name)] = str(value)
        self.record = record

    def __currentName(self):
        """ provides currently selected name

        :returns: currently selected name
        :rtype: :obj:`str`
        """
        item = self.__ui.tableWidget.item(
            self.__ui.tableWidget.currentRow(), 0)
        if item is None:
            return ""
        name = item.data(QtCore.Qt.UserRole)
        if hasattr(name, "toString"):
            name = name.toString()
        return name

    def __currentValue(self):
        """ provides currently selected name

        :returns: currently selected name
        :rtype: :obj:`str`
        """
        item = self.__ui.tableWidget.item(
            self.__ui.tableWidget.currentRow(), 1)
        if item is None:
            return ""
        value = item.data(QtCore.Qt.UserRole)
        if hasattr(value, "toString"):
            value = value.toString()
        return value

    @QtCore.pyqtSlot("QTableWidgetItem*")
    def __tableItemChanged(self, item):
        """ changes the current value of the variable

        :param item: current item
        :type item: :class:`QtWidgets.QTableWidgetItem`
        """
        record = dict(self.record)
        newvalues = list(self.newvalues)
        oldname = str(self.__currentName() or "").strip()
        if oldname and \
           oldname not in self.record.keys():
            return
        column = self.__ui.tableWidget.currentColumn()
        if column == 1:
            value = str(item.text() or "").strip()
            if not oldname:
                oldvalue = str(self.__currentValue() or "").strip()
                self.newvalues = [
                    str(vl).strip() for vl in self.newvalues
                    if str(vl).strip() != oldvalue]
                if value not in self.newvalues:
                    self.newvalues.append(value)
                else:
                    return
            else:
                self.record[oldname] = value
            self.dirty = True
        if column == 0:
            name = str(item.text()).strip()
            if oldname:
                value = self.record.pop(oldname)
            else:
                value = str(self.__currentValue() or "").strip()
                self.newvalues = [
                    str(vl).strip() for vl in self.newvalues
                    if str(vl).strip() != value]
            if not name:
                if oldname:
                    if value not in self.newvalues:
                        self.newvalues.append(value)
                else:
                    return
            else:
                if name in self.record.keys() and self.record[name] != value:
                    oldvalue = self.record[name]
                    if oldvalue not in self.newvalues:
                        self.newvalues.append(oldvalue)
                self.record[name] = value
            self.dirty = True
        if record != self.record or newvalues != self.newvalues:
            self.__populateTable()

    @QtCore.pyqtSlot()
    def __add(self):
        """ adds a new record into the table
        """
        self.newvalues.append("")
        self.dirty = True
        self.__populateTable()

    @QtCore.pyqtSlot()
    def __remove(self):
        """ removes the current record from the table
        """
        name = str(self.__currentName()).strip()
        if name and \
           name not in self.record.keys():
            return
        value = str(self.__currentValue()).strip()
        if QtWidgets.QMessageBox.question(
                self, "Removing Data",
                'Would you like  to remove "%s": "%s" ?' % (name, value),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.No:
            return
        if not name:
            self.newvalues = [
                str(vl).strip() for vl in self.newvalues
                if str(vl).strip() != value]
        else:
            self.record.pop(name)
        self.dirty = True
        self.__populateTable()

    def __populateTable(self, selected=None):
        """ populate table records

        :param selected: name of selected item
        :type selected: :obj:`str`
        """
        self.__ui.tableWidget.clear()
        sitem = None
        self.__ui.tableWidget.setSortingEnabled(False)
        names = sorted(self.record.keys())
        self.__ui.tableWidget.setRowCount(len(names) + len(self.newvalues))
        self.__ui.tableWidget.setColumnCount(len(self.headers))
        self.__ui.tableWidget.setHorizontalHeaderLabels(self.headers)
        row = 0
        for value in self.newvalues:
            name = ""
            item = QtWidgets.QTableWidgetItem(" ")
            item.setData(QtCore.Qt.UserRole, (name))
            self.__ui.tableWidget.setItem(row, 0, item)
            item2 = QtWidgets.QTableWidgetItem(value)
            item2.setData(QtCore.Qt.UserRole, (value))
            self.__ui.tableWidget.setItem(row, 1, item2)
            if selected is None or selected == name:
                sitem = item
            row += 1
        for name in names:
            item = QtWidgets.QTableWidgetItem(name)
            item.setData(QtCore.Qt.UserRole, (name))
            self.__ui.tableWidget.setItem(row, 0, item)
            value = self.record[name] or ""
            item2 = QtWidgets.QTableWidgetItem(value)
            item2.setData(QtCore.Qt.UserRole, (value))
            self.__ui.tableWidget.setItem(row, 1, item2)

            if selected is not None and selected == name:
                sitem = item
            row += 1
        self.__ui.tableWidget.setSortingEnabled(True)
        self.__ui.tableWidget.resizeColumnsToContents()
        # self.__ui.tableWidget.horizontalHeader().\
        #     setStretchLastSection(True)
        if hasattr(self.__ui.tableWidget.horizontalHeader(),
                   "setSectionResizeMode"):
            self.__ui.tableWidget.horizontalHeader().\
                setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        else:
            self.__ui.tableWidget.horizontalHeader().\
                setResizeMode(1, QtWidgets.QHeaderView.Stretch)
        if sitem is not None:
            sitem.setSelected(True)
            self.__ui.tableWidget.setCurrentItem(sitem)

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        self.__updateRecord()
        QtWidgets.QDialog.accept(self)
