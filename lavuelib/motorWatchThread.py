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

""" motor watch thread """

from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import logging

from pyqtgraph import QtCore

from .omniQThread import OmniQThread
# from .sardanaUtils import debugmethod


#: (:obj:`float`) refresh rate in seconds
GLOBALREFRESHRATE = .1
#: (:obj:`float`) polling inverval in seconds
POLLINGINTERVAL = 1.

logger = logging.getLogger("lavue")


# subclass for threading
class MotorWatchThread(OmniQThread):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) signal with motor status
    motorStatusSignal = QtCore.pyqtSignal(float, str, float, str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) watching finished
    watchingFinished = QtCore.pyqtSignal()

    def __init__(self, motor1, motor2, server=None):
        """ constructor

        :param motor1: first motor device proxy
        :type motor1: :class:`tango.DeviceProxy`
        :param motor2: second motor device proxy
        :type motor2: :class:`tango.DeviceProxy`
        :param mserver: door server device proxy
        :type mserver: :class:`tango.DeviceProxy`
        """
        OmniQThread.__init__(self)
        #: (:obj:`bool`) execute loop flag
        self.__loop = False
        #: (:class:`tango.DeviceProxy`) first motor device proxy
        self.__motor1 = motor1
        #: (:class:`tango.DeviceProxy`) second motor device proxy
        self.__motor2 = motor2
        #: (:class:`tango.DeviceProxy`) door server device proxy
        self.__mserver = server

    # @debugmethod
    def _run(self):
        """ runner of the fetching thread
        """
        self.__loop = True
        while self.__loop:
            if time:
                time.sleep(GLOBALREFRESHRATE)
            try:
                state1 = str(self.__motor1.state())
                pos1 = float(self.__motor1.position)
                state2 = str(self.__motor2.state())
                pos2 = float(self.__motor2.position)
                self.motorStatusSignal.emit(pos1, state1, pos2, state2)
                if self.__mserver is not None:
                    mstate = str(self.__mserver.state())
                else:
                    if state1 == "MOVING" or state2 == "MOVING":
                        mstate = "MOVING"
                    elif state1 == "RUNNING" or state2 == "RUNNING":
                        mstate = "RUNNING"
                    else:
                        mstate = "ON"
                if mstate not in ["RUNNING", "MOVING"]:
                    self.watchingFinished.emit()
            except Exception as e:
                logger.warning(str(e))

    # @debugmethod
    def isWatching(self):
        """ is datasource source connected

        :returns: if datasource source connected
        :rtype: :obj:`bool`
        """
        return self.__loop

    # @debugmethod
    def stop(self):
        """ stops loop

        """
        self.__loop = False


# subclass for threading
class AttributeWatchThread(OmniQThread):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) signal with attribute values
    attrValuesSignal = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) watching finished
    watchingFinished = QtCore.pyqtSignal()

    def __init__(self, aproxies, refreshtime=None):
        """ constructor

        :param refreshtime: refresh time
        :type refreshtime: :class:`tango.DeviceProxy`
        :param aproxies: attribute proxies
        :type aproxies: :obj:`list` <:class:`tango.DeviceProxy`>
        """
        OmniQThread.__init__(self)
        #: (:obj:`bool`) execute loop flag
        self.__loop = False
        #: (:obj:`bool`) execute loop flag
        self.__refreshtime = refreshtime or POLLINGINTERVAL

        #: (:obj:`list` <:class:`tango.DeviceProxy`>)  attribute proxies
        self.__aproxies = aproxies or []

    # @debugmethod
    def _run(self):
        """ runner of the fetching thread
        """
        self.__loop = True
        while self.__loop:
            # logger.debug("ATTR LOOP %s" % (self.__loop))
            try:
                attrs = []
                for ap in self.__aproxies:
                    ra = ap.read()
                    vl = ra.value
                    if hasattr(vl, "tolist"):
                        vl = vl.tolist()
                    attrs.append(vl)
                self.attrValuesSignal.emit(str(json.dumps(attrs)))
            except Exception as e:
                logger.warning(str(e))
            if time and self.__loop:
                time.sleep(self.__refreshtime)

    # @debugmethod
    def isWatching(self):
        """ is datasource source connected

        :returns: if datasource source connected
        :rtype: :obj:`bool`
        """
        return self.__loop

    # @debugmethod
    def stop(self):
        """ stops loop

        """
        self.__loop = False
        # logger.debug("STOP LOOP %s" % (self.__loop))
