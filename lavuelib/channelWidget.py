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

""" level widget """

from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "ChannelWidget.ui"))


class ChannelWidget(QtGui.QWidget):

    """
    Set minimum and maximum displayed values and its color.
    """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) color channel changed signal
    channelChanged = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) rgb color channel changed signal
    rgbChanged = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, settings=None, expertmode=False):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        :param expertmode: expert mode flag
        :type expertmode: :obj:`bool`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_LevelsWidget') ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj: `bool`) levels shown
        self.__levels = True
        #: (:obj: `bool`) colors to be shown
        self.__colors = True
        #: (:obj: `bool`) rgb flag
        self.__rgb = False
        #: (:obj: `int`) red channel
        self.__rindex = 0
        #: (:obj: `int`) green channel
        self.__gindex = 1
        #: (:obj: `int`) blue channel
        self.__bindex = 2
        #: (:obj: `int`) current color channel
        self.__colorchannel = 0
        #: (:obj: `int`) number of color channels
        self.__numberofchannels = 0
        #: (:class:`lavuelib.settings.Settings`) settings
        self.__settings = settings
        #: (:obj:`bool`) expert mode
        self.__expertmode = expertmode

        #: (:obj:`dict`) channellabels
        self.__channellabels = {}

        self.__connectChannels()
        self.setNumberOfChannels(-1)
        self.__ui.rComboBox.currentIndexChanged.connect(
            self._onRChannelChanged)
        self.__ui.gComboBox.currentIndexChanged.connect(
            self._onGChannelChanged)
        self.__ui.bComboBox.currentIndexChanged.connect(
            self._onBChannelChanged)

    def changeView(self, showhistogram=None, showlevels=None,
                   showadd=None):
        """ shows or hides the histogram widget

        :param showhistogram: if histogram should be shown
        :type showhistogram: :obj:`bool`
        :param showlevels: if levels should be shown
        :type showlevels: :obj:`bool`
        :param showadd: if additional histogram should be shown
        :type showadd: :obj:`bool`
        """
        if showlevels is True and self.__levels is False:
            if self.__colors:
                self.__ui.channelGroupBox.show()
                self.__ui.channelComboBox.show()
            else:
                self.__ui.channelGroupBox.hide()
                self.__ui.channelComboBox.hide()
            self.__ui.rLabel.hide()
            self.__ui.gLabel.hide()
            self.__ui.bLabel.hide()
            self.__ui.rComboBox.hide()
            self.__ui.gComboBox.hide()
            self.__ui.bComboBox.hide()
        elif showlevels is False and self.__levels is True:
            self.__ui.channelGroupBox.hide()
            self.__ui.channelComboBox.hide()
            self.__ui.rLabel.show()
            self.__ui.gLabel.show()
            self.__ui.bLabel.show()
            self.__ui.rComboBox.show()
            self.__ui.gComboBox.show()
            self.__ui.bComboBox.show()

        if showlevels is not None:
            self.__levels = showlevels

        if not self.__levels:
            self.hide()
        else:
            self.show()

    @QtCore.pyqtSlot()
    def _setWidgetChannel(self):
        """ update channel comboboxs and sets color channel

        """
        channel = self.__ui.channelHorizontalSlider.value()
        if self.__colorchannel != channel:
            self.__ui.channelComboBox.setCurrentIndex(channel)
            self.setChannel(channel)
        self.__ui.channelComboBox.currentIndexChanged.connect(
            self.setChannel)

    @QtCore.pyqtSlot()
    def _skipChannels(self):
        """ disconnects channel combobox

        """
        self.__ui.channelComboBox.currentIndexChanged.disconnect(
            self.setChannel)

    @QtCore.pyqtSlot()
    def _setChannelTips(self):
        """ update channel comboboxes
        """
        channel = self.__ui.channelHorizontalSlider.value()
        if self.__colorchannel != channel:
            self.__ui.channelComboBox.setCurrentIndex(channel)

    @QtCore.pyqtSlot(int)
    def setChannel(self, channel, force=False):
        """ sets color channel

        :param channel: color channel
        :type channel: :obj:`int`
        :param force: force change
        :type force: :obj:`bool`
        """
        if self.__colorchannel != channel or force:

            if channel >= 0 and channel <= self.__numberofchannels + 2:
                if channel == self.__numberofchannels + 2:
                    self.__colorchannel = channel
                    self.showGradient(False)
                    self.rgbChanged.emit(True)
                elif self.__colorchannel == self.__numberofchannels + 2:
                    self.__colorchannel = channel
                    self.showGradient(True)
                    self.rgbChanged.emit(False)
                else:
                    self.__colorchannel = channel
                    if force:
                        self.showGradient(True)
                    self.channelChanged.emit()
                self.__ui.channelHorizontalSlider.setValue(channel)

    def showGradient(self, status=True):
        """ resets color channel

        :param status: show gradient flag
        :type status: :obj:`bool`
        """
        if status:
            self.__ui.rLabel.hide()
            self.__ui.gLabel.hide()
            self.__ui.bLabel.hide()
            self.__ui.rComboBox.hide()
            self.__ui.gComboBox.hide()
            self.__ui.bComboBox.hide()
        else:
            self.__ui.rLabel.show()
            self.__ui.gLabel.show()
            self.__ui.bLabel.show()
            self.__ui.rComboBox.show()
            self.__ui.gComboBox.show()
            self.__ui.bComboBox.show()

    @QtCore.pyqtSlot(int)
    def _onRChannelChanged(self, index):
        """ set red channel
        """
        if index < self.__numberofchannels:
            self.__rindex = index
        else:
            self.__rindex = -1
        self.channelChanged.emit()

    @QtCore.pyqtSlot(int)
    def _onGChannelChanged(self, index):
        """ set green channel
        """
        if index < self.__numberofchannels:
            self.__gindex = index
        else:
            self.__gindex = -1
        self.channelChanged.emit()

    @QtCore.pyqtSlot(int)
    def _onBChannelChanged(self, index):
        """ set blue channel
        """
        if index < self.__numberofchannels:
            self.__bindex = index
        else:
            self.__bindex = -1
        self.channelChanged.emit()

    def updateChannelLabels(self, chlabels):
        """ update red channel

        :param chlabels: dictionary with channel labels
        :type chlabels: :obj:`dict` <:obj:`int` :obj:`str`>
        """
        if isinstance(chlabels, dict):
            for ky, vl in chlabels.items():
                if not vl:
                    if ky in self.__channellabels.keys():
                        self.__channellabels.pop(ky)
                else:
                    try:
                        self.__channellabels[int(ky)] = vl
                        self.setChannelItemText(ky, vl)
                    except Exception as e:
                        print(str(e))

    def setChannelItemText(self, iid, text):
        """ sets channel item text

        :param iid: label id
        :type iid: :obj:`int`
        :param iid: label text
        :type iid: :obj:`str`
        """
        self.__ui.channelComboBox.setItemText(
            iid + 1, text)
        self.__ui.channelComboBox.setItemData(
            iid + 1, text, QtCore.Qt.ToolTipRole)

    def updateRChannel(self):
        """ update red channel
        """
        current = self.__ui.rComboBox.currentIndex()
        if self.__rindex != self.__numberofchannels:
            if self.__rindex != current:
                self.__ui.rComboBox.setCurrentIndex(self.__rindex)
        elif self.__rindex != -1:
            self.__ui.rComboBox.setCurrentIndex(self.__numberofchannels)

    def updateGChannel(self):
        """ update green channel
        """
        current = self.__ui.gComboBox.currentIndex()
        if self.__gindex != self.__numberofchannels:
            if self.__gindex != current:
                self.__ui.gComboBox.setCurrentIndex(self.__gindex)
        elif self.__gindex != -1:
            self.__ui.gComboBox.setCurrentIndex(self.__numberofchannels)

    def updateBChannel(self):
        """ update blue channel
        """
        current = self.__ui.bComboBox.currentIndex()
        if self.__bindex != self.__numberofchannels:
            if self.__bindex != current:
                self.__ui.bComboBox.setCurrentIndex(self.__bindex)
        elif self.__bindex != -1:
            self.__ui.bComboBox.setCurrentIndex(self.__numberofchannels)

    def rgbchannels(self):
        return (self.__rindex, self.__gindex, self.__bindex)

    def colorChannel(self):
        """ provides color channel

        :returns: color channel
        :rtype: :obj:`int`
        """
        return self.__colorchannel

    def __connectChannels(self):
        """ connects channel signals
        """
        self.__ui.channelComboBox.currentIndexChanged.connect(
            self.setChannel)
        self.__ui.channelHorizontalSlider.sliderReleased.connect(
            self._setWidgetChannel)
        self.__ui.channelHorizontalSlider.sliderPressed.connect(
            self._skipChannels)
        self.__ui.channelHorizontalSlider.valueChanged.connect(
            self._setChannelTips)

    def __disconnectChannels(self):
        """ connects channel signals
        """
        self.__ui.channelComboBox.currentIndexChanged.disconnect(
            self.setChannel)
        self.__ui.channelHorizontalSlider.sliderReleased.disconnect(
            self._setWidgetChannel)
        self.__ui.channelHorizontalSlider.sliderPressed.disconnect(
            self._skipChannels)
        self.__ui.channelHorizontalSlider.valueChanged.disconnect(
            self._setChannelTips)

    def setNumberOfChannels(self, number):
        """ sets maximum number of color channel

        :param number:  number of color channel
        :type number: :obj:`int`
        """
        if number != self.__numberofchannels:
            self.__disconnectChannels()
            self.__numberofchannels = int(max(number, 0))
            if self.__numberofchannels > 0:
                for i in reversed(
                        range(0, self.__ui.channelComboBox.count())):
                    self.__ui.channelComboBox.removeItem(i)
                self.__ui.channelComboBox.addItem("sum")
                # self.__ui.channelComboBox.setSizeAdjustPolicy(
                # QtGui.QComboBox.AdjustToMinimumContentsLength)
                self.__ui.channelGroupBox.show()
                self.__ui.channelComboBox.show()
                self.__ui.channelComboBox.setSizeAdjustPolicy(
                    QtGui.QComboBox.AdjustToContents)

                self.__ui.channelComboBox.addItems(
                    ["channel %s" % (ch)
                     for ch in range(self.__numberofchannels)])

                for ky, vl in self.__channellabels.items():
                    if vl and ky < self.__numberofchannels:
                        self.setChannelItemText(ky, vl)
                self.__ui.channelComboBox.addItem("mean")
                self.__ui.channelComboBox.addItem("RGB")
                self.__colors = True
                for i in reversed(
                        range(0, self.__ui.rComboBox.count())):
                    self.__ui.rComboBox.removeItem(i)
                for i in reversed(
                        range(0, self.__ui.gComboBox.count())):
                    self.__ui.gComboBox.removeItem(i)
                for i in reversed(
                        range(0, self.__ui.bComboBox.count())):
                    self.__ui.bComboBox.removeItem(i)

                self.__ui.rComboBox.addItems(
                    ["%s" % (ch)
                     for ch in range(self.__numberofchannels)])
                self.__ui.bComboBox.addItems(
                    ["%s" % (ch)
                     for ch in range(self.__numberofchannels)])
                self.__ui.gComboBox.addItems(
                    ["%s" % (ch)
                     for ch in range(self.__numberofchannels)])
                self.__ui.rComboBox.addItem("None")
                self.__ui.bComboBox.addItem("None")
                self.__ui.gComboBox.addItem("None")
                self.__rindex = 0
                if self.__numberofchannels > 1:
                    self.__gindex = 1
                else:
                    self.__gindex = -1
                if self.__numberofchannels > 2:
                    self.__bindex = 2
                else:
                    self.__bindex = -1
                self.__ui.channelHorizontalSlider.setMaximum(
                    self.__numberofchannels + 2)
                self.updateRChannel()
                self.updateGChannel()
                self.updateBChannel()
            else:
                self.__ui.channelGroupBox.hide()
                self.__ui.channelComboBox.hide()
                self.__colors = False
            channel = self.__ui.channelHorizontalSlider.value()
            self.__ui.channelComboBox.setCurrentIndex(channel)
            self.setChannel(channel, True)
            self.__connectChannels()
