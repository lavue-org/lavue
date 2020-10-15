# Copyright (C) 2017  DESY Notkestr. 85, D-22607 Hamburg
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

""" command thread """

from pyqtgraph import QtCore

from .omniQThread import OmniQThread

import logging
#: (:obj:`logging.Logger`) logger object
logger = logging.getLogger(__name__)


class CommandThread(OmniQThread):
    """ thread which executes a list of commands
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) finished signal
    finished = QtCore.pyqtSignal()

    def __init__(self, instance, commands, parent):
        """ thread contructor

        :param instance: command instance
        :type instance: :obj:`instanceobj` or :obj:`type`
        :param commands: a list of commands
        :type commands: :obj:`list` <:obj:`str`>
        :param parent: thread parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """

        OmniQThread.__init__(self, parent)
        #: (:obj:`instanceobj` or :obj:`type`) command instance
        self.instance = instance
        #: (:obj:`list` <:obj:`str`>) a list of commands
        self.commands = list(commands)
        #: (:obj:`Exception`) error thrown by the executed command
        self.error = None

    def _run(self):
        """ run thread method
        """
        try:
            for cmd in self.commands:
                getattr(self.instance, cmd)()
        except Exception as e:
            self.error = e
        finally:
            self.finished.emit()
