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
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" omni qt thread """

from pyqtgraph import QtCore


try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    #: (:obj:`bool`) tango imported
    TANGO = True
    if hasattr(tango, "EnsureOmniThread"):
        EnsureOmniThread = tango.EnsureOmniThread
    else:
        EnsureOmniThread = None
except ImportError:
    #: (:obj:`bool`) tango imported
    TANGO = False
    EnsureOmniThread = None


class OmniQThread(QtCore.QThread):

    def __init__(self, parent=None):
        """ constructor
        """
        QtCore.QThread.__init__(self, parent)

    def run(self):
        """ runner of the fetching thread
        """
        if EnsureOmniThread is not None:
            with EnsureOmniThread():
                self._run()
        else:
            self._run()
