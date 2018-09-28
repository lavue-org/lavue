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


""" tango lavue controller client"""

from PyQt4 import QtCore

import PyTango


class TangoCB(object):

    """ tango attribute callback class"""

    def __init__(self, client, name, signal):
        """ constructor

        :param client: tango controller client
        :type client: :class:`str`
        :param name: attribute name
        :type name: :obj:`str`
        :param signal: signal to emit
        :type signal: :class:`PyQt4.QtCore.pyqtSignal`
        """
        self.__client = client
        self.__name = name
        self.__signal = signal

    def push_event(self, *args, **kwargs):
        '''callback method receiving the event'''
        event_data = args[0]
        if event_data.err:
            result = event_data.errors
            print(result)
        else:
            result = event_data.attr_value.value
            self.__signal.emit(result)


class ControllerClient(QtCore.QObject):

    """ lavue controller client """

    #: (:class:`PyQt4.QtCore.pyqtSignal`) energy changed signal
    energyChanged = QtCore.pyqtSignal(float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) detector distance changed signal
    detectorDistanceChanged = QtCore.pyqtSignal(float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) detector ROIs changed signal
    detectorROIsChanged = QtCore.pyqtSignal(str)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) beam Center X changed siganal
    beamCenterXChanged = QtCore.pyqtSignal(float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) beam Center Y changed siganal
    beamCenterYChanged = QtCore.pyqtSignal(float)

    def __init__(self, device):
        """ constructor

        :param device: tango device name
        :type device: :obj:`str`
        """
        QtCore.QObject.__init__(self)
        #: :class:`PyTango.DeviceProxy` controller device proxy
        self.__dp = PyTango.DeviceProxy(device)
        #: subscribe flag
        self.__subscribed = False

    def subscribe(self):
        """ subscribe callback methods
        """

        energy_cb = TangoCB(self, "Energy", self.energyChanged)
        distance_cb = TangoCB(
            self, "DetectorDistance", self.detectorDistanceChanged)
        rois_cb = TangoCB(
            self, "DetectorROIs", self.detectorROIsChanged)
        centerx_cb = TangoCB(
            self, "BeamCenterX", self.beamCenterXChanged)
        centery_cb = TangoCB(
            self, "BeamCenterY", self.beamCenterYChanged)

        self.__energy_id = self.__dp.subscribe_event(
            "Energy",
            PyTango.EventType.CHANGE_EVENT,
            energy_cb)
        self.__distance_id = self.__dp.subscribe_event(
            "DetectorDistance",
            PyTango.EventType.CHANGE_EVENT,
            distance_cb)
        self.__rois_id = self.__dp.subscribe_event(
            "DetectorROIs",
            PyTango.EventType.CHANGE_EVENT,
            rois_cb)
        self.__centerx_id = self.__dp.subscribe_event(
            "BeamCenterX",
            PyTango.EventType.CHANGE_EVENT,
            centerx_cb)
        self.__centery_id = self.__dp.subscribe_event(
            "BeamCenterY",
            PyTango.EventType.CHANGE_EVENT,
            centery_cb)
        self.__subscribed = True

    def writeAttribute(self, name, value):
        """ writes attribute value of device

        :param name: attribute name
        :type name: :obj:`str`
        :param value: attribute value
        :type value: :obj:`any`
        """
        self.__dp.write_attribute(name, value)

    def unsubscribe(self):
        """ unsubscribe callback methods
        """
        if self.__subscribed:
            self.__dp.unsubscribe_event(self.__energy_id)
            self.__dp.unsubscribe_event(self.__distance_id)
            self.__dp.unsubscribe_event(self.__rois_id)
            self.__dp.unsubscribe_event(self.__centerx_id)
            self.__dp.unsubscribe_event(self.__centery_id)
        self.__subscribed = False
