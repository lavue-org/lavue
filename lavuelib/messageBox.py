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


""" error message box """

import sys

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

from pyqtgraph import QtCore, QtGui


class MessageBox(QtCore.QObject):

    """ error message box """

    def __init__(self, parent):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtCore.QObject.__init__(self, parent)

    @classmethod
    def getText(cls, default, error=None):
        """ provides error message text fro sys.exc_info()

        :param default: default message test
        :type default: :obj:`str`
        :param error: exception to describe
        :type error: :obj:`Exception`
        :returns: exception message
        :rtype: :obj:`str`
        """
        if error is None:
            error = sys.exc_info()[1]
        text = default
        try:
            if TANGO and isinstance(error, tango.DevFailed):
                text = str("\n".join(["%s " % (err.desc) for err in error]))
            else:
                text = str(error)
        except Exception:
            pass
        return text

    @classmethod
    def warning(cls, parent, title, text, detailedText=None, icon=None):
        """ creates warning messagebox

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param title: message box title
        :type title: :obj:`str`
        :param text: message box text
        :type text: :obj:`str`
        :param detailedText: message box detailed text
        :type detailedText: :obj:`str`
        :param icon: message box icon
        :type icon:  :class:`pyqtgraph.QtCore.QIcon`
        """
        msgBox = QtGui.QMessageBox(parent)
        msgBox.setText(title)
        msgBox.setInformativeText(text)
        if detailedText is not None:
            msgBox.setDetailedText(detailedText)
        if icon is None:
            icon = QtGui.QMessageBox.Warning
        msgBox.setIcon(icon)
        spacer = QtGui.QSpacerItem(800, 0, QtGui.QSizePolicy.Minimum,
                                   QtGui.QSizePolicy.Expanding)
        layout = msgBox.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        msgBox.exec_()
        msgBox.setParent(None)
