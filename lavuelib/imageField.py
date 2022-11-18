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

""" configuration widget """

from .qtuic import uic
from pyqtgraph import QtCore
import os

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ImageField.ui"))


class ImageField(QtWidgets.QDialog):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtWidgets.QDialog.__init__(self, parent)

        #: (:class:`Ui_ConfigDialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`dict` <:obj:`str`,  :obj:`dict` <:obj:`str`, :obj:`any`>>)
        #: image field dictionary
        self.fields = {}
        #: (:obj:`str`) selected field
        self.field = None
        #: (:obj:`int`) growing dimension
        self.growing = 0
        #: (:obj:`int`) frame
        self.frame = -1

    def createGUI(self):
        """ create GUI
        """
        self.__ui.growingSpinBox.setValue(self.growing)
        self.__ui.frameSpinBox.setValue(self.frame)

        self.__populateElements()

    def __populateElements(self):
        """fills in the element list
        """
        selected = None
        self.__ui.imageListWidget.clear()

        for name in sorted(self.fields.keys()):
            item = QtWidgets.QListWidgetItem("%s" % name)
            item.setData(QtCore.Qt.UserRole, "%s" % name)
            if selected is None:
                selected = item
            field = self.fields[name]
            item.setToolTip("shape = %s, dtype = %s"
                            % (field["shape"], field["dtype"]))
            self.__ui.imageListWidget.addItem(item)

        if selected is not None:
            selected.setSelected(True)
            self.__ui.imageListWidget.setCurrentItem(selected)

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        item = self.__ui.imageListWidget.currentItem()
        if item is not None:
            vfield = item.data(QtCore.Qt.UserRole)
            if hasattr(vfield, "toString"):
                field = str(vfield.toString())
            else:
                field = str(vfield)
            if field and field in self.fields.keys():
                self.field = field
        self.growing = int(self.__ui.growingSpinBox.value())
        self.frame = int(self.__ui.frameSpinBox.value())
        if self.field:
            QtWidgets.QDialog.accept(self)
