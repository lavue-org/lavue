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

""" image display widget """

import pyqtgraph as _pg

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class AxesParameters(object):
    """ axes parameters
    """

    def __init__(self):
        """ constructor
        """

        #: (:obj:`bool`) enabled flag
        self.enabled = False
        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> ) image scale (x,y)
        self.scale = None
        #: (:obj:`tuple` <:obj:`float`, :obj:`float`> )
        #    position of the first pixel
        self.position = None
        #: (:obj:`str`) label of x-axis
        self.xtext = None
        #: (:obj:`str`) label of y-axis
        self.ytext = None
        #: (:obj:`str`) units of x-axis
        self.xunits = None
        #: (:obj:`str`) units of y-axis
        self.yunits = None


class CrossLinesParameters(object):
    """ axes parameters
    """

    def __init__(self):
        """ constructor
        """

        #: (:obj:`bool`) locker enabled flag
        self.locker = False
        #: (:obj:`bool`) center enabled flag
        self.center = False
        #: (:obj:`bool`) position mark enabled flag
        self.positionmark = False
        #: (:obj:`bool`) lock for double click
        self.doubleclicklock = False


class ROIsParameters(object):
    """ rois parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) enabled flag
        self.enabled = False
        #: (:obj:`int`) current roi id
        self.current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 rois coordinates
        self.coords = [[10, 10, 60, 60]]
        #: (:obj:`list` < (int, int, int) > ) list with roi colors
        self.colors = []


class CutsParameters(object):
    """ cuts parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) enabled flag
        self.enabled = False
        #: (:obj:`int`) current cut id
        self.current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2, width rois coordinates
        self.coords = [[10, 10, 60, 10, 0.00001]]


class IntensityParameters(object):
    """ intensity parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) do background substraction
        self.dobkgsubtraction = False
        #: (:obj:`bool`) calculate statistics without scaling
        self.statswoscaling = False
        #: (:obj:`str`) intensity scaling
        self.scaling = "sqrt"


class TransformationParameters(object):
    """ transformation parameters
    """

    def __init__(self):
        """ constructor
        """
        #: (:obj:`bool`) transpose coordinates flag
        self.transpose = False
        #: (:obj:`bool`) left-right flip coordinates flag
        self.leftrightflip = False
        #: (:obj:`bool`)  up-down flip coordinates flag
        self.updownflip = False
