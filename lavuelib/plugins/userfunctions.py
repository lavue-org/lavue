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

""" set of image sources """

import json


class LineCut(object):

    """ LineCut selection"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        try:
            #: (:obj: `int`) line cut index
            self.__index = int(json.loads(configuration)[0])
        except Exception:
            self.__index = 1
        try:
            #: (:obj: `int`) buffer length
            self.__buflen = max(int(json.loads(configuration)[1]), 1)
        except Exception:
            self.__buflen = 20

        #: (:obj: `list`) buffer
        self.__buffer = []

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        label = "linecut_%s" % self.__index
        if label in results:
            if len(self.__buffer) >= self.__buflen:
                self.__buffer.pop(0)
            self.__buffer.append([results[label][0], results[label][1]])
            userplot["nrplots"] = len(self.__buffer)
            for i, xy in enumerate(self.__buffer):
                userplot["x_%s" % (i + 1)] = xy[0]
                userplot["y_%s" % (i + 1)] = xy[1]
                if i != len(self.__buffer) - 1:
                    userplot["color_%s" % (i + 1)] = i/float(self.__buflen)
                else:
                    userplot["color_%s" % (i + 1)] = 'r'

            userplot["title"] = "History of %s" % label
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intensity"
        return userplot


class LineCutHistory(object):

    """ LineCut selection"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        try:
            #: (:obj: `int`) line cut index
            self.__index = int(json.loads(configuration)[0])
        except Exception:
            self.__index = 1
        try:
            #: (:obj: `int`) history length
            self.__maxhislen = max(int(json.loads(configuration)[1]), 1)
        except Exception:
            self.__maxhislen = 20

        #: (:obj: `int`) history len
        self.__hislen = 0

        #: (:obj: `int`) history index
        self.__bindex = -1

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        label = "linecut_%s" % self.__index
        if label in results:
            xx = results[label][0]
            yy = results[label][1]

            self.__bindex += 1
            self.__bindex = self.__bindex % self.__maxhislen
            if self.__bindex >= self.__hislen:
                self.__hislen += 1
            userplot["nrplots"] = self.__hislen

            for i in range(self.__hislen):
                if i == self.__bindex:
                    userplot["x_%s" % (i + 1)] = xx
                    userplot["y_%s" % (i + 1)] = yy
                else:
                    userplot["x_%s" % (i + 1)] = None
                    userplot["y_%s" % (i + 1)] = None

            for i in range(self.__maxhislen - self.__hislen,
                           self.__maxhislen - 1):
                uid = ((i - self.__maxhislen + self.__bindex + 1)
                       % self.__maxhislen) + 1
                userplot["color_%s" % uid] = i/float(self.__maxhislen)
            userplot["color_%s" % (self.__bindex + 1)] = 'r'

            userplot["title"] = "History of %s" % label
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intensity"
        return userplot


class LineCutFlat(object):

    """Flatten line cut"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__index = 1
        try:
            self.__flat = float(configuration)
        except Exception:
            self.__flat = 100000000.
            pass

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        # print("RESULTS", results)
        if "tool" in results and results["tool"] == "linecut":
            try:
                nrplots = int(results["nrlinecuts"])
            except Exception:
                nrplots = 0
            userplot["nrplots"] = nrplots
            userplot["title"] = "Linecuts flatten at '%s'" % (self.__flat)

            for i in range(nrplots):
                xlabel = "x_%s" % (i + 1)
                ylabel = "y_%s" % (i + 1)
                label = "linecut_%s" % (i + 1)
                cllabel = "hsvcolor_%s" % (i + 1)
                if label in results:
                    userplot[xlabel] = results[label][0]
                    userplot[ylabel] = [min(yy, self.__flat)
                                        for yy in results[label][1]]
                    userplot[cllabel] = i/float(nrplots)
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intensity"
        # print("USERPLOT", userplot)
        return userplot


def linecut_1(results):
    """ line rotate image by 45 deg

    :param results: dictionary with tool results
    :type results: :obj:`dict`
    :returns: dictionary with user plot data
    :rtype: :obj:`dict`
    """
    userplot = {}
    # print("USERPLOT", userplot)
    if "linecut_1" in results:
        userplot = {"x": results["linecut_1"][0],
                    "y": results["linecut_1"][1]}
    return userplot
