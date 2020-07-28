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


import fabio

#: (:obj:`str`) file name
filename = ""


class PV(object):

    def __init__(self, pvname):
        self.pvname = pvname
        self.timeout = None
        self.as_numpy = True
        self.data = None

    def get(self, as_numpy, timeout):
        global filename
        self.timeout = timeout
        self.as_numpy = as_numpy
        if filename:
            image = fabio.open(filename)
            data = image.data
            return data
