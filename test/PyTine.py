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

import time
import fabio
import numpy as np

#: (:obj:`str`) file name
filename = ""
gladdress = ""
glproperty = None
gltimeout = 1000
header = False
pdata = None
width = 245
height = 124


def get(address, property, timeout):
    global gladdress
    global glproperty
    global gltimeout
    global filename
    global header
    gladdress = address
    glproperty = property
    gltimeout = timeout

    prop = {}
    # print("FILENAME: %s" % filename)
    # print(self.data)
    prop["data"] = {}

    if header and pdata:
        data = np.ones(shape=(height, width), dtype='u2')
        data.fill(pdata)
        fheader = {}
        fheader["bytesPerPixel"] = 2
        fheader["sourceHeight"] = data.shape[0]
        fheader["sourceWidth"] = data.shape[1]
        prop["data"] = {"frameHeader": fheader,
                        "imageBytes": data.tobytes()}
    else:
        global filename
        data = None
        if filename:
            image = fabio.open(filename)
            data = image.data
        prop["data"] = {"imageMatrix": data}
    prop["timestamp"] = str(time.time())
    return prop
