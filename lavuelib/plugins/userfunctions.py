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


class LineCut(object):

    """ LineCut selection"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__index = 1
        try:
            self.__index = int(configuration)
        except Exception:
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
        label = "linecut_%s" % self.__index
        if label in results:
            userplot = {"x": results[label][0],
                        "y": results[label][1],
                        "title": label}
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intencity"
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
        label = "linecut_%s" % self.__index
        if label in results:
            userplot = {"x": results[label][0],
                        "y": [min(yy, self.__flat)
                              for yy in results[label][1]],
                        "title":
                        "%s flatten at '%s'" % (label, self.__flat)}
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intencity"
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
