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

""" motor device widget """

from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os

try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    #: (:obj:`bool`) tango imported
    TANGO = True
except ImportError:
    #: (:obj:`bool`) tango imported
    TANGO = False


_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TakeMotorsDialog.ui"))


class TakeMotorsDialog(QtGui.QDialog):

    """ detector geometry widget class"""

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QDialog.__init__(self, parent)

        #: (:class:`Ui_Dialog') ui_dialog object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`str`) x motor name
        self.xmotorname = ""
        #: (:obj:`str`) y motor name
        self.ymotorname = ""
        #: (:obj:`list`<:obj:`str`>) motortips list
        self.motortips = []
        #: (:obj:`str`) group title
        self.title = None
        #: (:class:`tango.DeviceProxy`) x motor device
        self.xmotordevice = None
        #: (:class:`tango.DeviceProxy`) y motor device
        self.ymotordevice = None

    def createGUI(self):
        """ create GUI
        """
        if self.title is not None:
            self.__ui.groupBox.setTitle(str(self.title))

        self.__updateComboBox(self.__ui.xComboBox, str(self.xmotorname))
        self.__updateComboBox(self.__ui.yComboBox, str(self.ymotorname))

    @QtCore.pyqtSlot()
    def accept(self):
        """ updates class variables with the form content
        """
        try:
            self.xmotorname = str(self.__ui.xComboBox.currentText())
            self.xmotordevice = tango.DeviceProxy(self.xmotorname)
            for attr in ["state", "position"]:
                if not hasattr(self.xmotordevice, attr):
                    raise Exception("Missing %s" % attr)
        except Exception:
            self.__ui.xComboBox.setFocus()
            return
        try:
            self.ymotorname = str(self.__ui.yComboBox.currentText())
            self.ymotordevice = tango.DeviceProxy(self.ymotorname)
            for attr in ["state", "position"]:
                if not hasattr(self.ymotordevice, attr):
                    raise Exception("Missing %s" % attr)
        except Exception:
            self.__ui.yComboBox.setFocus()
            return

        QtGui.QDialog.accept(self)

    def __updateComboBox(self, combobox, motorname):
        """ updates a value of motor combo box
        """
        combobox.clear()
        for mt in sorted(self.motortips):
            combobox.addItem(mt)
        if motorname not in self.motortips:
            combobox.addItem(motorname)
        ind = combobox.findText(motorname)
        combobox.setCurrentIndex(ind)
