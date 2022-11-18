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

""" help widget """


from pyqtgraph import QtCore, QtGui
from .qtuic import QWebView

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


# detail help
class HelpForm(QtWidgets.QDialog):

    def __init__(self, page, parent=None):
        """ constructor

        :param page: the starting html page
        :type page: :obj:`str`
        :param parent: parent widget
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        super(HelpForm, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WA_GroupLeader)

        #:  help tool bar
        self.__toolBar = None
        #: help text Browser
        self.__textBrowser = None
        #: main label of the help
        self.__pageLabel = None

        self._page = page
        self.createGUI()
        self.createActions()

    def createGUI(self):
        """ creates dialogs for help dialog
        """

        #: help tool bar
        self.__toolBar = QtWidgets.QToolBar(self)
        #: help text Browser
        self.__textBrowser = QWebView(self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__toolBar)
        layout.addWidget(self.__textBrowser, 1)

        self.setLayout(layout)
        self._start()

        self.resize(1500, 700)
        self.setWindowTitle("%s Help" % (
            QtWidgets.QApplication.applicationName()))

    def createActions(self):
        """ creates actions and sets the command pool and stack
        """

        backAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("go-previous"),
            "&Back", self)
        backAction.setShortcut(QtGui.QKeySequence.Back)

        forwardAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("go-next"),
            "&Forward", self)
        forwardAction.setShortcut("Forward")

        homeAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("go-home"),
            "&Home", self)
        homeAction.setShortcut("Home")

        # main label of the help
        self.__pageLabel = QtWidgets.QLabel(self)

        self.__toolBar.addAction(backAction)
        self.__toolBar.addAction(forwardAction)
        self.__toolBar.addAction(homeAction)
        self.__toolBar.addSeparator()
        self.__toolBar.addWidget(self.__pageLabel)

        try:
            backAction.triggered.disconnect(self.__textBrowser.back)
        except Exception:
            pass
        try:
            forwardAction.triggered.disconnect(self.__textBrowser.forward)
        except Exception:
            pass
        try:
            homeAction.triggered.disconnect(self._home)
        except Exception:
            pass
        try:
            self.__textBrowser.loadFinished.disconnect(
                        self.updatePageTitle)
        except Exception:
            pass

        backAction.triggered.connect(self.__textBrowser.back)
        forwardAction.triggered.connect(self.__textBrowser.forward)
        homeAction.triggered.connect(self._start)
        self.__textBrowser.loadFinished.connect(
                    self.updatePageTitle)

        self.updatePageTitle()

    def _start(self):
        """ got to the home page
        """
        self.__textBrowser.load(QtCore.QUrl(self._page))

    def updatePageTitle(self):
        """ resets the __pageLabel withg the document title
        """

        self.__pageLabel.setText(
            "<p><b><font color='#0066ee' font size = 4>" +
            "&nbsp;&nbsp;" + self.__textBrowser.title()
            + "</b></p></br>"
        )
