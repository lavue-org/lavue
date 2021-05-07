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
import logging

from . import imageField
from . import imageFileHandler

_testformclass, _testbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TestSourceWidget.ui"))

_httpformclass, _httpbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HTTPSourceWidget.ui"))

_hidraformclass, _hidrabaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "HidraSourceWidget.ui"))

_asapoformclass, _asapobaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ASAPOSourceWidget.ui"))

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

_doocspropformclass, _doocspropbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "DOOCSPropSourceWidget.ui"))

_tinepropformclass, _tinepropbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "TinePropSourceWidget.ui"))

_epicspvformclass, _epicspvbaseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "EpicsPVSourceWidget.ui"))

__all__ = [
    'SourceBaseWidget',
    'HidraSourceWidget',
    'HTTPSourceWidget',
    'TangoAttrSourceWidget',
    'TangoEventsSourceWidget',
    'TangoFileSourceWidget',
    'DOOCSPropSourceWidget',
    'ZMQSourceWidget',
    'NXSFileSourceWidget',
    'TinePropSourceWidget',
    'EpicsPVSourceWidget',
    'ASAPOSourceWidget',
    # 'FixTestSourceWidget',
    'TestSourceWidget',
    'swproperties'
]

logger = logging.getLogger("lavue")


class SourceBaseWidget(QtGui.QWidget):

    """ general source widget """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) push button enabled signal
    buttonEnabled = QtCore.pyqtSignal(bool)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source state signal
    sourceStateChanged = QtCore.pyqtSignal(int)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) source label name signal
    sourceLabelChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) add Icon Clicked
    addIconClicked = QtCore.pyqtSignal(str, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) remove Icon Clicked
    removeIconClicked = QtCore.pyqtSignal(str, str)

    #: (:obj:`str`) source name
    name = "Test"
    #: (:obj:`str`) source alias
    alias = "test"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ()
    #: (:obj:`str`) datasource class name
    datasource = "BaseSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QWidget.__init__(self, parent)

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
        #: (:class:`Ui_SourceBaseWidget')
        #:     ui_sourcewidget object from qtdesigner
        self._ui = None
        #: (:obj:`bool`) source widget detached
        self.__detached = False

    def setActive(self, active=True):
        """ set active flag

        :param active: active flag
        :type active: :obj:`bool`
        """
        self.active = active

    @QtCore.pyqtSlot()
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
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ abstract updateComboBox
        """
        self.updateButton()

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self.sourceLabelChanged.emit()

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

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return ""

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
        combobox.lineEdit().editingFinished.connect(
            self.updateComboBox)
        combobox.currentIndexChanged.connect(
            self.updateButton)

    def _disconnectComboBox(self, combobox):
        combobox.lineEdit().textEdited.disconnect(
            self.updateButton)
        combobox.lineEdit().editingFinished.disconnect(
            self.updateComboBox)
        combobox.currentIndexChanged.disconnect(
            self.updateButton)

    def _updateComboBox(self, combobox, atdict, atlist, currentattr=None):
        """ updates a value of attr combo box
        """
        self._disconnectComboBox(combobox)
        currentattr = currentattr or str(combobox.currentText()).strip()
        combobox.clear()
        attrs = sorted(atdict.keys())
        mkicon = QtGui.QIcon.fromTheme("starred")
        if mkicon.isNull():
            mkicon = QtGui.QIcon(":/star2.png")
        umkicon = QtGui.QIcon.fromTheme("non-starred")
        if umkicon.isNull():
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


class TestSourceWidget(SourceBaseWidget):

    """ test source widget """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self._detachWidgets()


class FixTestSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Fix Test"
    #: (:obj:`str`) datasource class name
    datasource = "FixTestSource"
    #: (:obj:`str`) source alias
    alias = "fixtest"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _testformclass()
        self._ui.setupUi(self)

        self._detachWidgets()


class HTTPSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "HTTP response"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("REQUESTS",)
    #: (:obj:`str`) datasource class name
    datasource = "HTTPSource"
    #: (:obj:`str`) source alias
    alias = "http"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _httpformclass()
        self._ui.setupUi(self)

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
        url = self.configuration()
        if not url:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
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
        return url

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
            self.updateComboBox()
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.httpComboBox, self.__urls, self.__userurls)
        self.updateButton()

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


class HidraSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Hidra"
    #: (:obj:`str`) source alias
    alias = "hidra"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("HIDRA",)
    #: (:obj:`str`) datasource class name
    datasource = "HiDRASource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _hidraformclass()
        self._ui.setupUi(self)

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

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Hidra source
        """
        if not self.active:
            return
        if self._ui.serverComboBox.currentText() == "Pick a server" \
           or not self._ui.serverComboBox.currentText():
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return "%s,%s,%s" % (
            str(self._ui.serverComboBox.currentText()),
            self.__targetname,
            self.__portnumber
        )

    def updateMetaData(self, serverdict=None, hidraport=None, **kargs):
        """ update source input parameters

        :param serverdict: server dictionary
        :type serverdict: :obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
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
        if hidraport:
            self.__portnumber = hidraport
            self._ui.currenthostLabel.setText(
                "%s:%s" % (self.__targetname, self.__portnumber))
        self.sourceLabelChanged.emit()

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
        self.__sortedserverlist = sorted(self.__sortedserverlist)

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
        configuration = configuration.split(" ")
        if configuration:
            configuration = configuration[0]
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


class ASAPOSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "ASAPO"
    #: (:obj:`str`) source alias
    alias = "asapo"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("ASAPO",)
    #: (:obj:`str`) datasource class name
    datasource = "ASAPOSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _asapoformclass()
        self._ui.setupUi(self)

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "asapodatasourceLabel", "asapodatasourceComboBox",
            "asapostreamLabel", "asapostreamComboBox",
        ]

        #: (:obj:`str`>) asapo server i.e. host:port
        self.__server = ""
        #: (:obj:`str`>) beamtime id
        self.__beamtime = ""
        #: (:obj:`str`>) source path
        self.__sourcepath = ""
        #: (:obj:`str`>) asapo token
        self.__token = ""

        #: (:obj:`list` <:obj:`str`> >) datasource list
        self.__datasources = []
        #: (:obj:`list` <:obj:`str`> >) asapo streams
        self.__streams = []
        #: (:obj:`bool`) updating flag
        self.__updating = False
        #: (:class:`pyqtgraph.QtCore.QMutex`) update mutex
        self.__udmutex = QtCore.QMutex()

        #: (:class:`pyqtgraph.QtCore.QMutex`) zmq datasource mutex
        self.__mutex = QtCore.QMutex()

        self._detachWidgets()

        self._ui.asapodatasourceComboBox.addItems(["detector"])
        self._ui.asapostreamComboBox.addItems(["default", "**ALL**"])
        self._ui.asapodatasourceComboBox.currentIndexChanged.connect(
            self.updateButton)
        # self._connectComboBox()
        self._ui.asapostreamComboBox.currentIndexChanged.connect(
            self._updateStreamComboBox)

    @QtCore.pyqtSlot()
    def updateButton(self, disconnect=True):
        """ update slot for Asapo source
        """
        with QtCore.QMutexLocker(self.__udmutex):
            if not self.active or self.__updating:
                return
            else:
                self.__updating = True
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self._ui.asapostreamComboBox.\
                    currentIndexChanged.disconnect(
                        self._updateStreamComboBox)
            if not self._ui.asapostreamComboBox.count() \
               or not self._ui.asapodatasourceComboBox.currentText() \
               or not self.__server \
               or not self.__token \
               or not self.__beamtime:
                self.buttonEnabled.emit(False)
            else:
                self.buttonEnabled.emit(True)
                self.sourceLabelChanged.emit()
            if disconnect:
                self._ui.asapostreamComboBox.\
                    currentIndexChanged.connect(
                        self._updateStreamComboBox)
        with QtCore.QMutexLocker(self.__udmutex):
            self.__updating = False

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return "%s,%s,%s,%s,%s,%s" % (
            self.__server,
            str(self._ui.asapodatasourceComboBox.currentText()),
            str(self._ui.asapostreamComboBox.currentText()),
            self.__beamtime,
            self.__sourcepath,
            self.__token
        )

    def updateMetaData(self, asaposerver=None, asapotoken=None,
                       asapobeamtime=None,
                       asapodatasources=None, asapostreams=None,
                       asaposourcepath=None,
                       disconnect=True,
                       **kargs):
        """ update source input parameters

        :param asaposervers asapo servers, i.e. host:port
        :type asaposervers: :obj:`str`
        :param asapotoken: asapo token
        :type asapotoken: :obj:`str`
        :param asapobeamtime: beamtime id
        :type asapobeamtime: :obj:`str`
        :param asapodatasources: asapo datasource names
        :type asapodatasources: :obj:`list` <:obj:`str`> >
        :param asapostreams: asapo stream names
        :type asapostreams: :obj:`list` <:obj:`str`> >
        :param asaposourcepath: source path
        :type asaposourcepath: :obj:`str`
        :param disconnect: disconnect on update
        :type disconnect: :obj:`bool`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if disconnect:
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.asapostreamComboBox.currentIndexChanged.\
                    disconnect(self._updateStreamComboBox)
        text = None
        if isinstance(asapodatasources, list):
            self._ui.asapodatasourceComboBox.currentIndexChanged.disconnect(
                self.updateButton)
            self.__datasources = asapodatasources
            for i in reversed(
                    range(0, self._ui.asapodatasourceComboBox.count())):
                self._ui.asapodatasourceComboBox.removeItem(i)
            if not asapodatasources:
                self._ui.asapodatasourceComboBox.addItems(["detector"])
            self._ui.asapodatasourceComboBox.addItems(self.__datasources)
            self._ui.asapodatasourceComboBox.currentIndexChanged.connect(
                self.updateButton)
            self._ui.asapodatasourceComboBox.setCurrentIndex(0)
        if asaposerver is not None:
            self.__server = asaposerver
        if asapotoken is not None:
            self.__token = asapotoken
        if asapobeamtime is not None:
            self.__beamtime = asapobeamtime
        if asaposourcepath is not None:
            self.__sourcepath = asaposourcepath
        updatecombo = False
        if isinstance(asapostreams, list):
            with QtCore.QMutexLocker(self.__mutex):
                text = str(
                    self._ui.asapostreamComboBox.currentText())
            if not text or text not in asapostreams:
                if text not in ["default", "**ALL**"]:
                    text = None
            self.__streams = asapostreams
            updatecombo = True
        if updatecombo is True:
            with QtCore.QMutexLocker(self.__mutex):
                for i in reversed(
                        range(0, self._ui.asapostreamComboBox.count())):
                    self._ui.asapostreamComboBox.removeItem(i)
                if not self.__streams or \
                   "default" not in self.__streams:
                    self._ui.asapostreamComboBox.addItem("default")
                self._ui.asapostreamComboBox.addItems(
                    sorted(self.__streams))
                if not self.__streams or \
                   "**ALL**" not in self.__streams:
                    self._ui.asapostreamComboBox.addItem("**ALL**")
                if text:
                    tid = self._ui.asapostreamComboBox.findText(text)
                    if tid > -1:
                        self._ui.asapostreamComboBox.setCurrentIndex(tid)
        if disconnect:
            self.updateButton(disconnect=False)
            with QtCore.QMutexLocker(self.__mutex):
                self._ui.asapostreamComboBox.currentIndexChanged.connect(
                    self._updateStreamComboBox)
        if updatecombo is True and text is None:
            self._updateStreamComboBox()
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def _updateStreamComboBox(self):
        """ update ASAPO substream combobox
        """
        disconnected = False
        if self._connected:
            disconnected = True
            self.sourceStateChanged.emit(0)
        self.updateButton()
        if disconnected:
            self.sourceStateChanged.emit(-1)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.asapodatasourceComboBox.setEnabled(False)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.asapodatasourceComboBox.setEnabled(True)

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        cnflst = configuration.split(",")
        datasource = cnflst[0] if cnflst else ""
        stream = ""
        if len(cnflst) > 1:
            stream = cnflst[1]
            if not stream:
                stream = "default"
        iid = self._ui.asapodatasourceComboBox.findText(datasource)
        if iid == -1:
            self._ui.asapodatasourceComboBox.addItem(datasource)
            iid = self._ui.asapodatasourceComboBox.findText(datasource)
        self._ui.asapodatasourceComboBox.setCurrentIndex(iid)

        if stream:
            iid = self._ui.asapostreamComboBox.findText(stream)
            if iid == -1:
                self._ui.asapostreamComboBox.addItem(stream)
                iid = self._ui.asapostreamComboBox.findText(stream)
            self._ui.asapostreamComboBox.setCurrentIndex(iid)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.asapostreamComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class TangoAttrSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Tango Attribute"
    #: (:obj:`str`) source alias
    alias = "tangoattr"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("TANGO",)
    #: (:obj:`str`) datasource class name
    datasource = "TangoAttrSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _tangoattrformclass()
        self._ui.setupUi(self)

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
        currentattr = self.configuration()
        if not currentattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.attrComboBox.setToolTip(currentattr or self.__defaulttip)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        currentattr = str(self._ui.attrComboBox.currentText()).strip()
        if currentattr in self.__tangoattrs.keys():
            currentattr = str(self.__tangoattrs[currentattr]).strip()
        return currentattr

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
        self.sourceLabelChanged.emit()

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

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.attrComboBox, self.__tangoattrs, self.__userattrs)
        self.updateButton()

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


class TinePropSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Tine Property"
    #: (:obj:`str`) source alias
    alias = "tineprop"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYTINE",)
    #: (:obj:`str`) datasource class name
    datasource = "TinePropSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _tinepropformclass()
        self._ui.setupUi(self)

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "tinepropLabel", "tinepropComboBox"
        ]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, tine properties) items
        self.__tineprops = {}
        #: (:obj:`list` <:obj:`str`>) user tine property
        self.__userprops = []

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.tinepropComboBox.toolTip()

        self._connectComboBox(self._ui.tinepropComboBox)
        self._ui.tinepropComboBox.installEventFilter(self)

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
            combobox=self._ui.tinepropComboBox,
            varname="tineprops",
            atdict=self.__tineprops,
            atlist=self.__userprops
        )

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Tine property source
        """
        if not self.active:

            return
        currentprop = self.configuration()
        if not currentprop:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.tinepropComboBox.setToolTip(
            currentprop or self.__defaulttip)

    def configuration(self):
        """ provides configuration for the current image source

        :returns: configuration string
        :rtype: :obj:`str`
        """
        currentprop = str(self._ui.tinepropComboBox.currentText()).strip()
        if currentprop in self.__tineprops.keys():
            currentprop = str(self.__tineprops[currentprop]).strip()
        return currentprop

    def updateMetaData(self, tineprops=None, **kargs):
        """ update source input parameters

        :param tineprops: json dictionary with
                           (label, tine property) items
        :type tineprops: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if tineprops is not None:
            self.__tineprops = json.loads(tineprops)
            self._updateComboBox(
                self._ui.tinepropComboBox,
                self.__tineprops,
                self.__userprops)
        self.sourceLabelChanged.emit()

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.tinepropComboBox.findText(configuration)
        if iid == -1:
            self._ui.tinepropComboBox.addItem(configuration)
            iid = self._ui.tinepropComboBox.findText(configuration)
        self._ui.tinepropComboBox.setCurrentIndex(iid)

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.tinepropComboBox, self.__tineprops, self.__userprops)
        self.updateButton()

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.tinepropComboBox.lineEdit().setReadOnly(False)
        self._ui.tinepropComboBox.setEnabled(True)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.tinepropComboBox.lineEdit().setReadOnly(True)
        self._ui.tinepropComboBox.setEnabled(False)
        currentprop = str(self._ui.tinepropComboBox.currentText()).strip()
        props = self.__tineprops.keys()
        if currentprop not in props and currentprop not in self.__userprops:
            self.__userprops.append(currentprop)
            self._updateComboBox(
                self._ui.tinepropComboBox,
                self.__tineprops, self.__userprops)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.tinepropComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class TangoEventsSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Tango Events"
    #: (:obj:`str`) source alias
    alias = "tangoevents"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("TANGO",)
    #: (:obj:`str`) datasource class name
    datasource = "TangoEventsSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _tangoeventsformclass()
        self._ui.setupUi(self)

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
        currentattr = self.configuration()
        if not currentattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.evattrComboBox.setToolTip(currentattr or self.__defaulttip)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        currentattr = str(self._ui.evattrComboBox.currentText()).strip()
        if currentattr in self.__tangoevattrs.keys():
            currentattr = str(self.__tangoevattrs[currentattr]).strip()
        return currentattr

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
            self.updateComboBox()
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.evattrComboBox,
            self.__tangoevattrs, self.__userevattrs)
        self.updateButton()

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


class TangoFileSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Tango File"
    #: (:obj:`str`) source alias
    alias = "tangofile"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("TANGO",)
    #: (:obj:`str`) datasource class name
    datasource = "TangoFileSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _tangofileformclass()
        self._ui.setupUi(self)

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

        #: (:obj:`bool`) nexus file source keeps the file open
        self.__nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.__nxslast = False

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
        fattr, dattr, dt, no, nl = self.__configuration()
        if not fattr:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.fileattrComboBox.setToolTip(fattr or self.__defaultfiletip)
        self._ui.dirattrComboBox.setToolTip(dattr or self.__defaultdirtip)

    def __configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration tuple
        :rtype configuration: :obj:`tuple`
        """
        dattr = str(self._ui.dirattrComboBox.currentText()).strip()
        fattr = str(self._ui.fileattrComboBox.currentText()).strip()
        if fattr in self.__tangofileattrs.keys():
            fattr = str(self.__tangofileattrs[fattr]).strip()
        if dattr in self.__tangodirattrs.keys():
            dattr = str(self.__tangodirattrs[dattr]).strip()
        dt = self.__dirtrans
        return (fattr, dattr, dt, self.__nxsopen, self.__nxslast)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return "%s,%s,%s,%s,%s" % self.__configuration()

    def updateMetaData(self, tangofileattrs=None, tangodirattrs=None,
                       dirtrans=None, nxsopen=None, nxslast=None, **kargs):
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
        :param nxsopen: nexus file source keeps the file open
        :type nxsopen: :obj:`bool`
        :param nxslast: nexus file source starts from the last image
        :type nxslast: :obj:`bool`
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
        if nxsopen is not None:
            self.__nxsopen = nxsopen
        if nxslast is not None:
            self.__nxslast = nxslast
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.fileattrComboBox, self.__tangofileattrs,
            self.__userfileattrs)
        self._updateComboBox(
            self._ui.dirattrComboBox, self.__tangodirattrs,
            self.__userdirattrs)
        self.updateButton()

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


class EpicsPVSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "Epics PV"
    #: (:obj:`str`) source alias
    alias = "epicspv"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYEPICS",)
    #: (:obj:`str`) datasource class name
    datasource = "EpicsPVSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _epicspvformclass()
        self._ui.setupUi(self)

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "pvnameLabel", "pvnameComboBox",
            "pvshapeLabel", "pvshapeComboBox"
        ]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, pv name) items
        self.__epicspvnames = {}
        #: (:obj:`list` <:obj:`str`>) user pv names
        self.__userpvnames = []

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, pv shape) items
        self.__epicspvshapes = {}
        #: (:obj:`list` <:obj:`str`>) user pv shapes
        self.__userpvshapes = []

        self._detachWidgets()

        #: (:obj:`str`) default pv name tip
        self.__defaultpvnametip = self._ui.pvnameComboBox.toolTip()

        #: (:obj:`str`) default dir tip
        self.__defaultpvshapetip = self._ui.pvshapeComboBox.toolTip()

        self._connectComboBox(self._ui.pvnameComboBox)
        self._connectComboBox(self._ui.pvshapeComboBox)
        self._ui.pvnameComboBox.installEventFilter(self)
        self._ui.pvshapeComboBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        if obj == self._ui.pvnameComboBox:
            return self.eventObjectFilter(
                event,
                combobox=self._ui.pvnameComboBox,
                varname="epicspvnames",
                atdict=self.__epicspvnames,
                atlist=self.__userpvnames
            )
        if obj == self._ui.pvshapeComboBox:
            return self.eventObjectFilter(
                event,
                combobox=self._ui.pvshapeComboBox,
                varname="epicspvshapes",
                atdict=self.__epicspvshapes,
                atlist=self.__userpvshapes
            )
        return False

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Epics file source
        """
        if not self.active:
            return
        pvnm, pvsh = self.__configuration()
        if not pvnm:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.pvnameComboBox.setToolTip(pvnm or self.__defaultpvnametip)
        self._ui.pvshapeComboBox.setToolTip(pvsh or self.__defaultpvshapetip)

    def __configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration tuple
        :rtype configuration: :obj:`tuple`
        """
        pvsh = str(self._ui.pvshapeComboBox.currentText()).strip()
        pvnm = str(self._ui.pvnameComboBox.currentText()).strip()
        if pvnm in self.__epicspvnames.keys():
            pvnm = str(self.__epicspvnames[pvnm]).strip()
        if pvsh in self.__epicspvshapes.keys():
            pvsh = str(self.__epicspvshapes[pvsh]).strip()
        return (pvnm, pvsh)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return "%s,[%s]" % self.__configuration()

    def updateMetaData(self, epicspvnames=None, epicspvshapes=None, **kargs):
        """ update source input parameters

        :param epicspvnames: json dictionary with
                           (label, file epics attribute) items
        :type epicspvnames: :obj:`str`
        :param epicspvshapes: json dictionary with
                           (label, dir epics attribute) items
        :type epicspvshapes: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if epicspvnames is not None:
            self.__epicspvnames = json.loads(epicspvnames)
            self._updateComboBox(
                self._ui.pvnameComboBox, self.__epicspvnames,
                self.__userpvnames)
        if epicspvshapes is not None:
            self.__epicspvshapes = json.loads(epicspvshapes)
            self._updateComboBox(
                self._ui.pvshapeComboBox, self.__epicspvshapes,
                self.__userpvshapes)
        self.sourceLabelChanged.emit()

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.pvnameComboBox, self.__epicspvnames,
            self.__userpvnames)
        self._updateComboBox(
            self._ui.pvshapeComboBox, self.__epicspvshapes,
            self.__userpvshapes)
        self.updateButton()

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.pvnameComboBox.lineEdit().setReadOnly(True)
        self._ui.pvnameComboBox.setEnabled(False)
        pvnm = str(self._ui.pvnameComboBox.currentText()).strip()
        attrs = self.__epicspvnames.keys()
        if pvnm not in attrs and pvnm not in self.__userpvnames:
            self.__userpvnames.append(pvnm)
            self._updateComboBox(
                self._ui.pvnameComboBox, self.__epicspvnames,
                self.__userpvnames)
        self._ui.pvshapeComboBox.lineEdit().setReadOnly(True)
        self._ui.pvshapeComboBox.setEnabled(False)
        pvsh = str(self._ui.pvshapeComboBox.currentText()).strip()
        attrs = self.__epicspvshapes.keys()
        if pvsh not in attrs and pvsh not in self.__userpvshapes:
            self.__userpvshapes.append(pvsh)
            self._updateComboBox(
                self._ui.pvshapeComboBox, self.__epicspvshapes,
                self.__userpvshapes)

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.pvnameComboBox.lineEdit().setReadOnly(False)
        self._ui.pvnameComboBox.setEnabled(True)
        self._ui.pvshapeComboBox.lineEdit().setReadOnly(False)
        self._ui.pvshapeComboBox.setEnabled(True)

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        cnflst = configuration.split(",", 1)
        pvnm = cnflst[0] if cnflst else ""
        shcnf = cnflst[1] if len(cnflst) > 1 else ""

        iid = self._ui.pvnameComboBox.findText(pvnm)
        if iid == -1:
            self._ui.pvnameComboBox.addItem(pvnm)
            iid = self._ui.pvnameComboBox.findText(pvnm)
        self._ui.pvnameComboBox.setCurrentIndex(iid)

        iid = self._ui.pvshapeComboBox.findText(shcnf)
        if iid == -1:
            try:
                json.loads(shcnf)
                shcnf = shcnf[1:-1]
            except Exception:
                shcnf = ""
            self._ui.pvshapeComboBox.addItem(shcnf)
            iid = self._ui.pvshapeComboBox.findText(shcnf)
        self._ui.pvshapeComboBox.setCurrentIndex(iid)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.pvshapeComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


class NXSFileSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "NeXus File"
    #: (:obj:`str`) source alias
    alias = "nxsfile"
    #: (:obj:`str`) datasource class name
    datasource = "NXSFileSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _nxsfileformclass()
        self._ui.setupUi(self)

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "nxsFileLabel", "nxsFileLineEdit",
            "nxsFieldLabel", "nxsFieldLineEdit",
            "nxsDimLabel", "nxsDimSpinBox",
            "nxsFrameLabel", "nxsFrameSpinBox"
        ]
        #: (:obj:`bool`) nexus file source keeps the file open
        self.__nxsopen = False
        #: (:obj:`bool`) nexus file source starts from the last image
        self.__nxslast = False
        #: (:obj:`str`) the last nexus file
        self.__nxslastfile = "."

        self._detachWidgets()

        self._ui.nxsFileLineEdit.textEdited.connect(self.updateButton)
        self._ui.nxsFieldLineEdit.textEdited.connect(self.updateButton)
        self._ui.nxsFrameSpinBox.valueChanged.connect(
            self._updateFrameSpinBox)
        self._ui.nxsDimSpinBox.valueChanged.connect(self.updateButton)
        self._ui.nxsFileLineEdit.installEventFilter(self)
        self._ui.nxsFieldLineEdit.installEventFilter(self)

    @QtCore.pyqtSlot()
    def _updateFrameSpinBox(self):
        """ update nexus frame combobox
        """
        disconnected = False
        if self._connected:
            disconnected = True
            self.sourceStateChanged.emit(0)
        self.updateButton()
        if disconnected:
            self.sourceStateChanged.emit(-1)

    def eventFilter(self, obj, event):
        """ event filter

        :param obj: qt object
        :type obj: :class: `pyqtgraph.QtCore.QObject`
        :param event: qt event
        :type event: :class: `pyqtgraph.QtCore.QEvent`
        :returns: status flag
        :rtype: :obj:`bool`
        """
        if not self._ui.nxsDimSpinBox.isEnabled():
            return False
        if obj not in [self._ui.nxsFileLineEdit, self._ui.nxsFieldLineEdit]:
            return False
        if event.type() in [QtCore.QEvent.MouseButtonDblClick]:
            fileDialog = QtGui.QFileDialog()
            fileout = fileDialog.getOpenFileName(
                self._ui.nxsFileLineEdit, 'Load file', self.__nxslastfile)
            if isinstance(fileout, tuple):
                filename = str(fileout[0])
            else:
                filename = str(fileout)
            fieldpath = ""
            growing = 0
            if filename:
                if filename.endswith(".nxs") or filename.endswith(".h5") \
                   or filename.endswith(".nx") or filename.endswith(".ndf"):
                    try:
                        # self.__settings.filename = filename
                        handler = imageFileHandler.NexusFieldHandler(
                            str(filename))
                        fields = handler.findImageFields()
                    except Exception as e:
                        logger.warning(str(e))
                        # print(str(e))
                        fields = None
                    if fields:
                        imgfield = imageField.ImageField(self)
                        imgfield.fields = fields
                        imgfield.createGUI()
                        if imgfield.exec_():
                            fieldpath = imgfield.field
                            growing = imgfield.growing
                            # frame = imgfield.frame
                self._ui.nxsFileLineEdit.setText(filename)
                self.__nxslastfile = filename
                if fieldpath:
                    self._ui.nxsFieldLineEdit.setText(fieldpath)
                self._ui.nxsDimSpinBox.setValue(growing)
                self.updateButton()
            return True
        return False

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for nexus file source
        """
        if not self.active:
            return
        nfl, nfd, nsb, nfm, nxsopen, nxslast = self.__configuration()
        if not nfl or not nfd:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()

    def __configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration tuple
        :rtype configuration: :obj:`tuple`
        """
        nfl = str(self._ui.nxsFileLineEdit.text()).strip()
        nfd = str(self._ui.nxsFieldLineEdit.text()).strip()
        nfm = int(self._ui.nxsFrameSpinBox.value())
        nsb = int(self._ui.nxsDimSpinBox.value())
        return (nfl, nfd, nfm, nsb, self.__nxsopen, self.__nxslast)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        return "%s,%s,%s,%s,%s,%s" % self.__configuration()

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

    def updateMetaData(self, nxsopen=None, nxslast=None, **kargs):
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
        self.sourceLabelChanged.emit()

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

        try:
            nfm = int(cnflst[2].replace("m", "-"))
        except Exception:
            nfm = -1

        self._ui.nxsFileLineEdit.setText(filecnf)
        self._ui.nxsFieldLineEdit.setText(fieldcnf)
        self._ui.nxsDimSpinBox.setValue(growcnf)
        self._ui.nxsFrameSpinBox.setValue(nfm)
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


class ZMQSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "ZMQ Stream"
    #: (:obj:`str`) source alias
    alias = "zmq"
    #: (:obj:`str`) datasource class name
    datasource = "ZMQSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _zmqformclass()
        self._ui.setupUi(self)

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
        #: (:class:`pyqtgraph.QtCore.QMutex`) update mutex
        self.__udmutex = QtCore.QMutex()
        #: (:obj:`bool`) updating flag
        self.__updating = False

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
        with QtCore.QMutexLocker(self.__udmutex):
            if not self.active or self.__updating:
                return
            else:
                self.__updating = True
        with QtCore.QMutexLocker(self.__mutex):
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.disconnect(
                    self._updateZMQComboBox)
            hosturl = self.configuration()
            if hosturl:
                self.buttonEnabled.emit(True)
            else:
                self.buttonEnabled.emit(False)
            self._ui.pickleComboBox.setToolTip(hosturl or self.__defaulttip)
            if disconnect:
                self._ui.pickleTopicComboBox.currentIndexChanged.connect(
                    self._updateZMQComboBox)
        with QtCore.QMutexLocker(self.__udmutex):
            self.__updating = False

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        hosturl = str(self._ui.pickleComboBox.currentText()).strip()
        if hosturl in self.__servers.keys():
            hosturl = str(self.__servers[hosturl]).strip()
        if not hosturl or ":" not in hosturl:
            hosturl = ""
        else:
            try:
                _, sport = hosturl.split("/")[0].split(":")
                port = int(sport)
                if port > 65535 or port < 0:
                    raise Exception("Wrong port")
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
            except Exception:
                hosturl = ""
        return hosturl

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
                    if text != "**ALL**":
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
        if updatecombo is True and text is None:
            self._updateZMQComboBox()
        self.sourceLabelChanged.emit()

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

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.pickleComboBox, self.__servers, self.__userservers)
        self.updateButton()

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
        cnflst = configuration.replace("/", ",").split(",")
        srvcnf = cnflst[0] if cnflst else ""
        topiccnf = ""
        if len(cnflst) > 1:
            topiccnf = cnflst[1]
            if not topiccnf:
                topiccnf = "**ALL**"

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


class DOOCSPropSourceWidget(SourceBaseWidget):

    """ test source widget """

    #: (:obj:`str`) source name
    name = "DOOCS Property"
    #: (:obj:`str`) source alias
    alias = "doocsprop"
    #: (:obj:`tuple` <:obj:`str`>) capitalized required packages
    requires = ("PYDOOCS",)
    #: (:obj:`str`) datasource class name
    datasource = "DOOCSPropSource"

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        SourceBaseWidget.__init__(self, parent)

        self._ui = _doocspropformclass()
        self._ui.setupUi(self)

        #: (:obj:`list` <:obj:`str`>) subwidget object names
        self.widgetnames = [
            "doocspropLabel", "doocspropComboBox"
        ]

        #: (:obj:`dict` <:obj:`str`, :obj:`str`>) dictionary with
        #:                     (label, doocs property) items
        self.__doocsprops = {}
        #: (:obj:`list` <:obj:`str`>) user doocs properites
        self.__userprops = []

        self._detachWidgets()

        #: (:obj:`str`) default tip
        self.__defaulttip = self._ui.doocspropComboBox.toolTip()

        self._connectComboBox(self._ui.doocspropComboBox)
        self._ui.doocspropComboBox.installEventFilter(self)

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
            combobox=self._ui.doocspropComboBox,
            varname="doocsprops",
            atdict=self.__doocsprops,
            atlist=self.__userprops
        )

    @QtCore.pyqtSlot()
    def updateButton(self):
        """ update slot for Doocs attribute source
        """
        if not self.active:
            return
        currentprop = self.configuration()
        if not currentprop:
            self.buttonEnabled.emit(False)
        else:
            self.buttonEnabled.emit(True)
            self.sourceLabelChanged.emit()
        self._ui.doocspropComboBox.setToolTip(currentprop or self.__defaulttip)

    def configuration(self):
        """ provides configuration for the current image source

        :returns configuration: configuration string
        :rtype configuration: :obj:`str`
        """
        currentprop = str(self._ui.doocspropComboBox.currentText()).strip()
        if currentprop in self.__doocsprops.keys():
            currentprop = str(self.__doocsprops[currentprop]).strip()
        return currentprop

    def updateMetaData(self, doocsprops=None, **kargs):
        """ update source input parameters

        :param doocsprops: json dictionary with
                           (label, doocs attribute) items
        :type doocsprops: :obj:`str`
        :param kargs:  source widget input parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        if doocsprops is not None:
            self.__doocsprops = json.loads(doocsprops)
            self._updateComboBox(
                self._ui.doocspropComboBox,
                self.__doocsprops, self.__userprops)
        self.sourceLabelChanged.emit()

    def configure(self, configuration):
        """ set configuration for the current image source

        :param configuration: configuration string
        :type configuration: :obj:`str`
        """
        iid = self._ui.doocspropComboBox.findText(configuration)
        if iid == -1:
            self._ui.doocspropComboBox.addItem(configuration)
            iid = self._ui.doocspropComboBox.findText(configuration)
        self._ui.doocspropComboBox.setCurrentIndex(iid)

    @QtCore.pyqtSlot()
    def updateComboBox(self):
        """ updates ComboBox
        """
        self._updateComboBox(
            self._ui.doocspropComboBox, self.__doocsprops, self.__userprops)
        self.updateButton()

    def disconnectWidget(self):
        """ disconnects widget
        """
        self._connected = False
        self._ui.doocspropComboBox.lineEdit().setReadOnly(False)
        self._ui.doocspropComboBox.setEnabled(True)

    def connectWidget(self):
        """ connects widget
        """
        self._connected = True
        self._ui.doocspropComboBox.lineEdit().setReadOnly(True)
        self._ui.doocspropComboBox.setEnabled(False)
        currentprop = str(self._ui.doocspropComboBox.currentText()).strip()
        attrs = self.__doocsprops.keys()
        if currentprop not in attrs and currentprop not in self.__userprops:
            self.__userprops.append(currentprop)
            self._updateComboBox(
                self._ui.doocspropComboBox, self.__doocsprops,
                self.__userprops)

    def label(self):
        """ return a label of the current detector

        :return: label of the current detector
        :rtype: :obj:`str`
        """
        label = str(self._ui.doocspropComboBox.currentText()).strip()
        return re.sub("[^a-zA-Z0-9_]+", "_", label)


#: ( :obj:`dict` < :obj:`str`, any > ) source widget properties
swproperties = []
for nm in __all__:
    if nm.endswith("SourceWidget"):
        cl = globals()[nm]
        swproperties.append(
            {
                'alias': cl.alias,
                'name': cl.name,
                'widget': nm,
                'requires': cl.requires,
            })
