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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" image source selection """

from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os
import socket
import json
import re

_testformclass, _testbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TestSourceWidget.ui"))

_httpformclass, _httpbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HTTPSourceWidget.ui"))

_hidraformclass, _hidrabaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HidraSourceWidget.ui"))

_tangoattrformclass, _tangoattrbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TangoAttrSourceWidget.ui"))

_tangoeventsformclass, _tangoeventsbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TangoEventsSourceWidget.ui"))

_tangofileformclass, _tangofilebaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TangoFileSourceWidget.ui"))

_nxsfileformclass, _nxsfilebaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "NXSFileSourceWidget.ui"))

_zmqformclass, _zmqbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ZMQSourceWidget.ui"))


class BaseSourceWidget(QtGui.QWidget):

    """ general source widget """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabled = QtCore.pyqtSignal(bool)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceStateChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source server name signal
    configurationChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source label name signal
    sourceLabelChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) add Icon Clicked
    addIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) remove Icon Clicked
    removeIconClicked = QtCore.pyqtSignal(str, str)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QWidget.__init__(self, parent)

        #: (:obj:`str`) source name
        self.name = "Test"
        #: (:obj:`str`) datasource class name
        self.datasource = "BaseSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = []
        #: (:obj:`list` <:class:`PyQt5.QtGui.QWidget`>) subwidget objects
        self.widgets = []
        #: (:obj:`bool`) source widget active
        self.active = False
        #: (:obj:`bool`) expertmode flag
        self.expertmode = False
        #: (:obj:`bool`) source widget connected
        self._connected = False
        #: (:class:`Ui_BaseSourceWidget')
        #:     ui_sourcewidget object from qtdesigner
        self._ui = None
        #: (:obj:`bool`) source widget detached
        self.__detached = False

    def updateButton(self):
        """ update slot for test source
        """
        if not self.active:
            return
        self.buttonEnabled.emit(True)

    def updateMetaData(self, **kargs):
        """ update source input parameters

        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        self.sourceLabelChanged.emit(self.label())

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self.sourceLabelChanged.emit(self.label())

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False

    def _detachWidgets(self):
        """ detaches the form widgets from the gridLayout
        """

        for wnm in self.widgetnames:
            if hasattr(self._ui, wnm):
                wg = getattr(self._ui, wnm)
                if hasattr(self._ui, "gridLayout"):
                    self._ui.gridLayout.removeWidget(wg)
                self.widgets.append(wg)
        self.__detached = True

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        return self.name

    def eventObjectFilter(self, event, combobox, varname, atdict, atlist):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        if event.type() in \
           [QtCore.QEvent.MouseButtonPress]:
            if event.buttons() and QtCore.Qt.LeftButton and \
               combobox.isEnabled() and self.expertmode and \
               event.x() < 30:
                currentattr = str(combobox.currentText()).strip()
                attrs = sorted(atdict.keys())
                if currentattr in attrs:
                    if QtGui.QMessageBox.question(
                            combobox, "Removing Label",
                            'Would you like  to remove "%s"" ?' %
                            (currentattr),
                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.Yes) == QtGui.QMessageBox.No:
                        return False
                    value = str(atdict.pop(currentattr)).strip()
                    if value not in atlist:
                        atlist.append(value)
                    self._updateComboBox(combobox, atdict, atlist, value)
                    self.removeIconClicked.emit(varname, currentattr)
                elif currentattr in atlist:
                    self.addIconClicked.emit(varname, currentattr)
                elif currentattr:
                    self.addIconClicked.emit(varname, currentattr)

        return False

    def _connectComboBox(self, combobox):
        combobox.lineEdit().textEdited.connect(
            self.updateButton)
        combobox.currentIndexChanged.connect(
            self.updateButton)

    def _disconnectComboBox(self, combobox):
        combobox.lineEdit().textEdited.disconnect(
            self.updateButton)
        combobox.currentIndexChanged.disconnect(
            self.updateButton)

    def _updateComboBox(self, combobox, atdict, atlist, currentattr=None):
        """ updates a value of attr combo box
        """
        self._disconnectComboBox(combobox)
        currentattr = currentattr or str(combobox.currentText()).strip()
        combobox.clear()
        attrs = sorted(atdict.keys())
        try:
            mkicon = QtGui.QIcon.fromTheme("starred")
        except Exception:
            mkicon = QtGui.QIcon(":/star2.png")
        try:
            umkicon = QtGui.QIcon.fromTheme("non-starred")
        except Exception:
            umkicon = QtGui.QIcon(":/star1.png")
        for mt in attrs:
            combobox.addItem(mt)
            iid = combobox.findText(mt)
            combobox.setItemData(
                iid, str(atdict[mt]), QtCore.Qt.ToolTipRole)
            combobox.setItemIcon(iid, mkicon)
        for mt in list(atlist):
            if mt not in atdict.values():
                combobox.addItem(mt)
                iid = combobox.findText(mt)
                combobox.setItemIcon(iid, umkicon)
            else:
                atlist = [mmt for mmt in atlist if mmt != mt]
                if mt == currentattr:
                    for nm, vl in atdict.items():
                        if mt == vl:
                            currentattr = nm
                            break
        if currentattr not in attrs and currentattr not in atlist:
            combobox.addItem(currentattr)
            iid = combobox.findText(currentattr)
            combobox.setItemIcon(iid, umkicon)
        if currentattr:
            ind = combobox.findText(currentattr)
        else:
            ind = 0
        combobox.setCurrentIndex(ind)
        self._connectComboBox(combobox)


class TestSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self._detachWidgets()


class FixTestSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)
        #: (:obj:`str`) source name
        self.name = "Fix Test"
        #: (:obj:`str`) datasource class name
        self.datasource = "FixTestSource"

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self._detachWidgets()


class HTTPSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _httpformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "HTTP response"
        #: (:obj:`str`) datasource class name
        self.datasource = "HTTPSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = ["httpLabel", "httpComboBox"]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, url) items
        self.__urls = {}
        #: (:obj:`list` <:obj:`str`>) user urls
        self.__userurls = []

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.httpComboBox.toolTip()

        self._connectComboBox(self._ui.httpComboBox)
        self._ui.httpComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        return self.eventObjectFilter(
            event,
            combobox=self._ui.httpComboBox,
            varname="httpurls",
            atdict=self.__urls,
            atlist=self.__userurls
        )

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for HTTP response source
        """
        if not self.active:
            return
        url = str(self._ui.httpComboBox.currentText()).strip()
        if url in self.__urls.keys():
            url = str(self.__urls[url]).strip()

        if not url.startswith("http://") and not url.startswith("https://"):
            surl = url.split("/")
            if len(surl) == 2 and surl[0] and surl[1]:
                url = "http://%s/monitor/api/%s/images/monitor" \
                      % (surl[0], surl[1])
            else:
                url = None
        self._ui.httpComboBox.setToolTip(url or self.__defaulttip)
        if not url:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.configurationChanged.emit(url)
            self.sourceLabelChanged.emit(self.label())

    def updateMetaData(self, httpurls=None, **kargs):
        """ update source input parameters

        :param httpurls: json dictionary with
                           (label, http urls) items
        :type httpurls: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if httpurls is not None:
            self.__urls = json.loads(httpurls)
            self._updateComboBox(
                self._ui.httpComboBox, self.__urls, self.__userurls)
        self.sourceLabelChanged.emit(self.label())

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.httpComboBox.findText(configuration)
        if iid == -1:
            self._ui.httpComboBox.addItem(configuration)
            iid = self._ui.httpComboBox.findText(configuration)
        self._ui.httpComboBox.setCurrentIndex(iid)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.httpComboBox.lineEdit().setReadOnly(True)
        self._ui.httpComboBox.setEnabled(False)
        currenturl = str(self._ui.httpComboBox.currentText()).strip()
        urls = self.__urls.keys()
        if currenturl not in urls and currenturl not in self.__userurls:
            self.__userurls.append(currenturl)
            self._updateComboBox(
                self._ui.httpComboBox, self.__urls, self.__userurls)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.httpComboBox.lineEdit().setReadOnly(False)
        self._ui.httpComboBox.setEnabled(True)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.httpComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class HidraSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _hidraformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Hidra"
        #: (:obj:`str`) datasource class name
        self.datasource = "HiDRASource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "serverLabel", "serverComboBox",
            "hostLabel", "currenthostLabel"
        ]
        #: (:obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >)
        #:  server dictionary
        self.__serverdict = {}
        #: (:obj:`str`) hidra port number
        self.__portnumber = "50001"
        #: (:obj:`str`) hidra client server
        self.__targetname = socket.getfqdn()

        #: (:obj:`list` <:obj:`str`> >) sorted server list
        self.__sortedserverlist = []

        self._detachWidgets()

        self._ui.currenthostLabel.setText(
            "%s:%s" % (self.__targetname, self.__portnumber))

        self._connectComboBox(self._ui.serverComboBox)

    def updateButton(self):
        """ update slot for Hidra source
        """
        if not self.active:
            return
        if self._ui.serverComboBox.currentText() == "Pick a server":
            self.buttonEnabled.emit(False)
        else:
            self.configurationChanged.emit(
                "%s %s %s" % (
                    str(self._ui.serverComboBox.currentText()),
                    self.__targetname,
                    self.__portnumber
                )
            )
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit(self.label())

    def updateMetaData(self, serverdict=None, hidraport=None, **kargs):
        """ update source input parameters

        :param serverdict: server dictionary
        :type serverdict: :obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        update = False
        if isinstance(serverdict, dict):
            self._ui.serverComboBox.currentIndexChanged.disconnect(
                self.updateButton)

            self.__serverdict = serverdict
            self.__sortServerList(self.__targetname)
            for i in reversed(range(0, self._ui.serverComboBox.count())):
                self._ui.serverComboBox.removeItem(i)
            self._ui.serverComboBox.addItems(self.__sortedserverlist)
            self._ui.serverComboBox.currentIndexChanged.connect(
                self.updateButton)
            self._ui.serverComboBox.setCurrentIndex(0)
            update = True
        if hidraport:
            self.__portnumber = hidraport
            self._ui.currenthostLabel.setText(
                "%s:%s" % (self.__targetname, self.__portnumber))
            update = True
        if update:
            self.configurationChanged.emit(
                "%s %s %s" % (
                    str(self._ui.serverComboBox.currentText()),
                    self.__targetname,
                    self.__portnumber
                )
            )
        self.sourceLabelChanged.emit(self.label())

    def __sortServerList(self, name):
        """ small function to sort out the server list details.
        It searches the hostname for a
        string and return only the elements in the list that fit

        :param name: beamline name
        :type name: :obj:`str`
        """
        #
        beamlines = ['p03', 'p08', 'p09', 'p10', 'p11']

        self.__sortedserverlist = []
        for bl in beamlines:
            if bl in name and bl in self.__serverdict.keys():
                self.__sortedserverlist.extend(self.__serverdict[bl])
        self.__sortedserverlist.extend(self.__serverdict["pool"])

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.serverComboBox.setEnabled(False)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.serverComboBox.setEnabled(True)

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.serverComboBox.findText(configuration)
        if iid == -1:
            self._ui.serverComboBox.addItem(configuration)
            iid = self._ui.serverComboBox.findText(configuration)
        self._ui.serverComboBox.setCurrentIndex(iid)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        if self._ui.serverComboBox.currentText() == "Pick a server":
            return ""
        else:
            label = str(self._ui.serverComboBox.currentText()).strip()
            return re.sub("[^a-zA-Z0-9_]+", "_", label)


class TangoAttrSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _tangoattrformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Tango Attribute"
        #: (:obj:`str`) datasource class name
        self.datasource = "TangoAttrSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "attrLabel", "attrComboBox"
        ]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, tango attribute) items
        self.__tangoattrs = {}
        #: (:obj:`list` <:obj:`str`>) user tango attributes
        self.__userattrs = []

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.attrComboBox.toolTip()

        self._connectComboBox(self._ui.attrComboBox)
        self._ui.attrComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        return self.eventObjectFilter(
            event,
            combobox=self._ui.attrComboBox,
            varname="tangoattrs",
            atdict=self.__tangoattrs,
            atlist=self.__userattrs
        )

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango attribute source
        """
        if not self.active:
            return
        currentattr = str(self._ui.attrComboBox.currentText()).strip()
        if not currentattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            if currentattr in self.__tangoattrs.keys():
                currentattr = str(self.__tangoattrs[currentattr]).strip()
            self.configurationChanged.emit(currentattr)
            self.sourceLabelChanged.emit(self.label())
        self._ui.attrComboBox.setToolTip(currentattr or self.__defaulttip)

    def updateMetaData(self, tangoattrs=None, **kargs):
        """ update source input parameters

        :param tangoattrs: json dictionary with
                           (label, tango attribute) items
        :type tangoattrs: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if tangoattrs is not None:
            self.__tangoattrs = json.loads(tangoattrs)
            self._updateComboBox(
                self._ui.attrComboBox, self.__tangoattrs, self.__userattrs)
        self.sourceLabelChanged.emit(self.label())

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.attrComboBox.findText(configuration)
        if iid == -1:
            self._ui.attrComboBox.addItem(configuration)
            iid = self._ui.attrComboBox.findText(configuration)
        self._ui.attrComboBox.setCurrentIndex(iid)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.attrComboBox.lineEdit().setReadOnly(False)
        self._ui.attrComboBox.setEnabled(True)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.attrComboBox.lineEdit().setReadOnly(True)
        self._ui.attrComboBox.setEnabled(False)
        currentattr = str(self._ui.attrComboBox.currentText()).strip()
        attrs = self.__tangoattrs.keys()
        if currentattr not in attrs and currentattr not in self.__userattrs:
            self.__userattrs.append(currentattr)
            self._updateComboBox(
                self._ui.attrComboBox, self.__tangoattrs, self.__userattrs)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.attrComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class TangoEventsSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _tangoeventsformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Tango Events"
        #: (:obj:`str`) datasource class name
        self.datasource = "TangoEventsSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "evattrLabel", "evattrComboBox"
        ]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, tango attribute) items
        self.__tangoevattrs = {}
        #: (:obj:`list` <:obj:`str`>) user tango attributes
        self.__userevattrs = []

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.evattrComboBox.toolTip()

        self._connectComboBox(self._ui.evattrComboBox)
        self._ui.evattrComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        return self.eventObjectFilter(
            event,
            combobox=self._ui.evattrComboBox,
            varname="tangoevattrs",
            atdict=self.__tangoevattrs,
            atlist=self.__userevattrs
        )

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango attribute source
        """
        if not self.active:
            return
        currentattr = str(self._ui.evattrComboBox.currentText()).strip()
        if not currentattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            if currentattr in self.__tangoevattrs.keys():
                currentattr = str(self.__tangoevattrs[currentattr]).strip()
            self.configurationChanged.emit(currentattr)
            self.sourceLabelChanged.emit(self.label())
        self._ui.evattrComboBox.setToolTip(currentattr or self.__defaulttip)

    def updateMetaData(self, tangoevattrs=None, **kargs):
        """ update source input parameters

        :param tangoevattrs: json dictionary with
                           (label, tango attribute) items
        :type tangoevattrs: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if tangoevattrs is not None:
            self.__tangoevattrs = json.loads(tangoevattrs)
            self._updateComboBox(
                self._ui.evattrComboBox,
                self.__tangoevattrs, self.__userevattrs)
        self.sourceLabelChanged.emit(self.label())

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.evattrComboBox.findText(configuration)
        if iid == -1:
            self._ui.evattrComboBox.addItem(configuration)
            iid = self._ui.evattrComboBox.findText(configuration)
        self._ui.evattrComboBox.setCurrentIndex(iid)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.evattrComboBox.lineEdit().setReadOnly(False)
        self._ui.evattrComboBox.setEnabled(True)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.evattrComboBox.lineEdit().setReadOnly(True)
        self._ui.evattrComboBox.setEnabled(False)
        currentattr = str(self._ui.evattrComboBox.currentText()).strip()
        attrs = self.__tangoevattrs.keys()
        if currentattr not in attrs and currentattr not in self.__userevattrs:
            self.__userevattrs.append(currentattr)
            self._updateComboBox(
                self._ui.evattrComboBox,
                self.__tangoevattrs, self.__userevattrs)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.evattrComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class TangoFileSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _tangofileformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Tango File"
        #: (:obj:`str`) datasource class name
        self.datasource = "TangoFileSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "fileattrLabel", "fileattrComboBox",
            "dirattrLabel", "dirattrComboBox"
        ]

        #: (:obj:`str`) json dictionary with directory
        #:               and file name translation
        self.__dirtrans = '{"/ramdisk/": "/gpfs/"}'

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, file tango attribute) items
        self.__tangofileattrs = {}
        #: (:obj:`list` <:obj:`str`>) user file tango attributes
        self.__userfileattrs = []

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, dir tango attribute) items
        self.__tangodirattrs = {}
        #: (:obj:`list` <:obj:`str`>) user dir tango attributes
        self.__userdirattrs = []

        self._detachWidgets()

        #: (:obj:`str`) default file tip
        self.__defaultfiletip = self._ui.fileattrComboBox.toolTip()

        #: (:obj:`str`) default dir tip
        self.__defaultdirtip = self._ui.dirattrComboBox.toolTip()

        self._connectComboBox(self._ui.fileattrComboBox)
        self._connectComboBox(self._ui.dirattrComboBox)
        self._ui.fileattrComboBox.installEventFilter(self)
        self._ui.dirattrComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        if obj == self._ui.fileattrComboBox:
            return self.eventObjectFilter(
                event,
                combobox=self._ui.fileattrComboBox,
                varname="tangofileattrs",
                atdict=self.__tangofileattrs,
                atlist=self.__userfileattrs
            )
        if obj == self._ui.dirattrComboBox:
            return self.eventObjectFilter(
                event,
                combobox=self._ui.dirattrComboBox,
                varname="tangodirattrs",
                atdict=self.__tangodirattrs,
                atlist=self.__userdirattrs
            )
        return False

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango file source
        """
        if not self.active:
            return
        dattr = str(self._ui.dirattrComboBox.currentText()).strip()
        fattr = str(self._ui.fileattrComboBox.currentText()).strip()
        if not fattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            if fattr in self.__tangofileattrs.keys():
                fattr = str(self.__tangofileattrs[fattr]).strip()

            if dattr in self.__tangodirattrs.keys():
                dattr = str(self.__tangodirattrs[dattr]).strip()
            dt = self.__dirtrans
            sourcename = "%s,%s,%s" % (fattr, dattr, dt)
            self.configurationChanged.emit(sourcename)

            self.sourceLabelChanged.emit(self.label())
        self._ui.fileattrComboBox.setToolTip(fattr or self.__defaultfiletip)
        self._ui.dirattrComboBox.setToolTip(dattr or self.__defaultdirtip)

    def updateMetaData(self, tangofileattrs=None, tangodirattrs=None,
                       dirtrans=None, **kargs):
        """ update source input parameters

        :param tangofileattrs: json dictionary with
                           (label, file tango attribute) items
        :type tangofileattrs: :obj:`str`
        :param tangodirattrs: json dictionary with
                           (label, dir tango attribute) items
        :type tangodirattrs: :obj:`str`
        :param dirtrans: json dictionary with directory
                         and file name translation
        :type dirtrans: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if tangofileattrs is not None:
            self.__tangofileattrs = json.loads(tangofileattrs)
            self._updateComboBox(
                self._ui.fileattrComboBox, self.__tangofileattrs,
                self.__userfileattrs)
        if tangodirattrs is not None:
            self.__tangodirattrs = json.loads(tangodirattrs)
            self._updateComboBox(
                self._ui.dirattrComboBox, self.__tangodirattrs,
                self.__userdirattrs)
        if dirtrans is not None:
            self.__dirtrans = dirtrans
        self.sourceLabelChanged.emit(self.label())

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.fileattrComboBox.lineEdit().setReadOnly(True)
        self._ui.fileattrComboBox.setEnabled(False)
        fattr = str(self._ui.fileattrComboBox.currentText()).strip()
        attrs = self.__tangofileattrs.keys()
        if fattr not in attrs and fattr not in self.__userfileattrs:
            self.__userfileattrs.append(fattr)
            self._updateComboBox(
                self._ui.fileattrComboBox, self.__tangofileattrs,
                self.__userfileattrs)
        self._ui.dirattrComboBox.lineEdit().setReadOnly(True)
        self._ui.dirattrComboBox.setEnabled(False)
        dattr = str(self._ui.dirattrComboBox.currentText()).strip()
        attrs = self.__tangodirattrs.keys()
        if dattr not in attrs and dattr not in self.__userdirattrs:
            self.__userdirattrs.append(dattr)
            self._updateComboBox(
                self._ui.dirattrComboBox, self.__tangodirattrs,
                self.__userdirattrs)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.fileattrComboBox.lineEdit().setReadOnly(False)
        self._ui.fileattrComboBox.setEnabled(True)
        self._ui.dirattrComboBox.lineEdit().setReadOnly(False)
        self._ui.dirattrComboBox.setEnabled(True)

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        cnflst = configuration.split(",")
        filecnf = cnflst[0] if cnflst else ""
        dircnf = cnflst[1] if len(cnflst) > 1 else ""

        iid = self._ui.fileattrComboBox.findText(filecnf)
        if iid == -1:
            self._ui.fileattrComboBox.addItem(filecnf)
            iid = self._ui.fileattrComboBox.findText(filecnf)
        self._ui.fileattrComboBox.setCurrentIndex(iid)

        iid = self._ui.dirattrComboBox.findText(dircnf)
        if iid == -1:
            self._ui.dirattrComboBox.addItem(dircnf)
            iid = self._ui.dirattrComboBox.findText(dircnf)
        self._ui.dirattrComboBox.setCurrentIndex(iid)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.dirattrComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class NXSFileSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _nxsfileformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "Nexus File"
        #: (:obj:`str`) datasource class name
        self.datasource = "NXSFileSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "nxsFileLabel", "nxsFileLineEdit",
            "nxsFieldLabel", "nxsFieldLineEdit",
            "nxsDimLabel", "nxsDimSpinBox"
        ]
        #: (:obj:`bool`) nexus file source keeps the file open
        self.__nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.__nxslast = False

        self._detachWidgets()

        self._ui.nxsFileLineEdit.textEdited.connect(self.updateButton)
        self._ui.nxsFieldLineEdit.textEdited.connect(self.updateButton)
        self._ui.nxsDimSpinBox.valueChanged.connect(self.updateButton)

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tango file source
        """
        if not self.active:
            return
        nfl = str(self._ui.nxsFileLineEdit.text()).strip()
        nfd = str(self._ui.nxsFieldLineEdit.text()).strip()
        nsb = int(self._ui.nxsDimSpinBox.value())
        if not nfl or not nfd:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit(self.label())
            sourcename = "%s,%s,%s,%s,%s" % (
                nfl, nfd, nsb, self.__nxsopen, self.__nxslast)
            self.configurationChanged.emit(sourcename)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.nxsFileLineEdit.setReadOnly(True)
        self._ui.nxsFieldLineEdit.setReadOnly(True)
        self._ui.nxsDimSpinBox.setEnabled(False)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.nxsFileLineEdit.setReadOnly(False)
        self._ui.nxsFieldLineEdit.setReadOnly(False)
        self._ui.nxsDimSpinBox.setEnabled(True)

    def updateMetaData(self, nxsopen=None, nxslast=None,  **kargs):
        """ update source input parameters

        :param nxsopen: nexus file source keeps the file open
        :type nxsopen: :obj:`bool`
        :param nxslast: nexus file source starts from the last image
        :type nxslast: :obj:`bool`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        update = False
        if nxsopen is not None:
            if self.__nxsopen != nxsopen:
                self.__nxsopen = nxsopen
                update = True
        if nxslast is not None:
            if self.__nxslast != nxslast:
                self.__nxslast = nxslast
                update = True
        if update:
            self.updateButton()
        self.sourceLabelChanged.emit(self.label())

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        cnflst = configuration.split(",")
        filecnf = cnflst[0] if cnflst else ""
        if ":/" in filecnf:
            filecnf, fieldcnf = filecnf.split(":/", 1)
        else:
            fieldcnf = ""

        try:
            growcnf = int(cnflst[1])
        except Exception:
            growcnf = 0

        self._ui.nxsFileLineEdit.setText(filecnf)
        self._ui.nxsFieldLineEdit.setText(fieldcnf)
        self._ui.nxsDimSpinBox.setValue(growcnf)
        self.updateButton()

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.nxsFileLineEdit.text()).strip() + \
            ":/" + str(self._ui.nxsFieldLineEdit.text()).strip()
        if label == ":/":
            return ""
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class ZMQSourceWidget(BaseSourceWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseSourceWidget.__init__(self, parent)

        self._ui = _zmqformclass()
        self._ui.setupUi(self)

        #: (:obj:`str`) source name
        self.name = "ZMQ Stream"
        #: (:obj:`str`) datasource class name
        self.datasource = "ZMQSource"
        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "pickleLabel", "pickleComboBox",
            "pickleTopicLabel", "pickleTopicComboBox"
        ]

        #: (:obj:`list` <:obj:`str`> >) zmq source datasources
        self.__zmqtopics = []
        #: (:obj:`bool`) automatic zmq topics enabled
        self.__autozmqtopics = False

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, server:port) items
        self.__servers = {}
        #: (:obj:`list` <:obj:`str`>) user servers
        self.__userservers = []

        #: (:class:`pyqtgraph.QtCore.QMutex`) zmq datasource mutex
        self.__mutex = QtCore.QMutex()

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.pickleComboBox.toolTip()
        self._connectComboBox(self._ui.pickleComboBox)
        self._ui.pickleComboBox.installEventFilter(self)

        self._ui.pickleTopicComboBox.currentIndexChanged.connect(
            self._updateZMQComboBox)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        return self.eventObjectFilter(
            event,
            combobox=self._ui.pickleComboBox,
            varname="zmqservers",
            atdict=self.__servers,
            atlist=self.__userservers
        )

    @QtCore.pyqtSlot()
    def updateButton(self, disconnect=True):
        """ update slot for ZMQ source
        """
        if not self.active:
            return
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
            hosturl = str(self._ui.pickleComboBox.currentText()).strip()
            if hosturl in self.__servers.keys():
                hosturl = str(self.__servers[hosturl]).strip()
            self._ui.pickleComboBox.setToolTip(hosturl or self.__defaulttip)
            if not hosturl or ":" not in hosturl:
                self.buttonEnabled.emit(False)
            else:
                try:
                    _, sport = hosturl.split("/")[0].split(":")
                    port = int(sport)
                    if port > 65535 or port < 0:
                        raise Exception("Wrong port")
                    self.buttonEnabled.emit(True)
                    if self._ui.pickleTopicComboBox.currentIndex() >= 0:
                        text = self._ui.pickleTopicComboBox.currentText()
                        if text == "**ALL**":
                            text = ""
                        shost = hosturl.split("/")
                        if len(shost) > 2:
                            shost[1] = str(text)
                        else:
                            shost.append(str(text))
                        hosturl = "/".join(shost)
                    self.configurationChanged.emit(hosturl)
                except Exception:
                    self.buttonEnabled.emit(False)
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)

    @QtCore.pyqtSlot()
    def _updateZMQComboBox(self):
        """ update ZMQ datasource combobox
        """
        disconnected = False
        if self._connected:
            disconnected = True
            self.sourceStateChanged.emit(0)
        self.updateButton()
        if disconnected:
            self.sourceStateChanged.emit(-1)

    def updateMetaData(
            self,
            zmqtopics=None, autozmqtopics=None,
            datasources=None, disconnect=True, zmqservers=None,
            **kargs):
        """ update source input parameters

        :param zmqtopics: zmq source topics
        :type zmqtopics: :obj:`list` <:obj:`str`> >
        :param autozmqtopics: automatic zmq topics enabled
        :type autozmqtopics: :obj:`bool`
        :param datasources: automatic zmq source topics
        :type datasources: :obj:`list` <:obj:`str`> >
        :param disconnect: disconnect on update
        :type disconnect: :obj:`bool`
        :param zmqservers: json dictionary with
                           (label, zmq servers) items
        :type zmqservers: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """

        if disconnect:
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
        text = None
        updatecombo = False
        if zmqservers is not None:
            self.__servers = json.loads(zmqservers)
            self._updateComboBox(
                self._ui.pickleComboBox, self.__servers, self.__userservers)
        if isinstance(zmqtopics, list):
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self._ui.pickleTopicComboBox.currentText())
            if not text or text not in zmqtopics:
                text = None
            self.__zmqtopics = zmqtopics
            updatecombo = True
        if autozmqtopics is not None:
            self.__autozmqtopics = autozmqtopics
        if self.__autozmqtopics:
            updatecombo = True
            with QtCore.QMutexLocker(self.__mutex):
                text = str(self._ui.pickleTopicComboBox.currentText())
            if isinstance(datasources, list):
                if not text or text not in datasources:
                    text = None
                self.__zmqtopics = datasources
        if updatecombo is True:
            with QtCore.QMutexLocker(self.__mutex):
                for i in reversed(
                        range(0, self._ui.pickleTopicComboBox.count())):
                    self._ui.pickleTopicComboBox.removeItem(i)
                self._ui.pickleTopicComboBox.addItems(self.__zmqtopics)
                self._ui.pickleTopicComboBox.addItem("**ALL**")
                if text:
                    tid = self._ui.pickleTopicComboBox.findText(text)
                    if tid > -1:
                        self._ui.pickleTopicComboBox.setCurrentIndex(tid)
        if disconnect:
            self.updateButton(disconnect=False)
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)
        self.sourceLabelChanged.emit(self.label())

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.pickleComboBox.lineEdit().setReadOnly(True)
        self._ui.pickleComboBox.setEnabled(False)
        server = str(self._ui.pickleComboBox.currentText()).strip()
        servers = self.__servers.keys()
        if server not in servers and server not in self.__userservers:
            self.__userservers.append(server)
            self._updateComboBox(
                self._ui.pickleComboBox, self.__servers, self.__userservers)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.pickleComboBox.lineEdit().setReadOnly(False)
        self._ui.pickleComboBox.setEnabled(True)

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        cnflst = configuration.split(",")
        srvcnf = cnflst[0] if cnflst else ""
        topiccnf = cnflst[1] if len(cnflst) > 1 else ""

        iid = self._ui.pickleComboBox.findText(srvcnf)
        if iid == -1:
            self._ui.pickleComboBox.addItem(srvcnf)
            iid = self._ui.pickleComboBox.findText(srvcnf)
        self._ui.pickleComboBox.setCurrentIndex(iid)

        if topiccnf:
            iid = self._ui.pickleTopicComboBox.findText(topiccnf)
            if iid == -1:
                self._ui.pickleTopicComboBox.addItem(topiccnf)
                iid = self._ui.pickleTopicComboBox.findText(topiccnf)
            self._ui.pickleTopicComboBox.setCurrentIndex(iid)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.pickleComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)
