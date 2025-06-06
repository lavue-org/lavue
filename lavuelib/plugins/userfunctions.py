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
import numpy as np
import time
import scipy


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

        try:
            #: (:obj: `float`) buffer length
            self.__shift = float(json.loads(configuration)[2])
        except Exception:
            self.__shift = 1.0

        try:
            #: (:obj: `float`) buffer length
            self.__cut = int(json.loads(configuration)[3])
        except Exception:
            self.__cut = -28

        #: (:obj: `list`) buffer
        self.__buffer = []

        self.__counter = -1

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        label = "linecut_%s" % self.__index
        label = "linecut_%s" % self.__index
        if label in results and "imagename" in results:
            if len(self.__buffer) >= self.__buflen:
                self.__buffer.pop(0)
                self.__counter += 1
            if self.__shift:
                for i in range(len(self.__buffer)):
                    self.__buffer[i][1] = [(y + self.__shift)
                                           for y in self.__buffer[i][1]]
            self.__buffer.append([results[label][0], results[label][1],
                                  results["imagename"]])
            userplot["nrplots"] = len(self.__buffer)
            for i, xy in enumerate(self.__buffer):
                userplot["x_%s" % (i + 1)] = xy[0]
                userplot["y_%s" % (i + 1)] = xy[1]
                userplot["name_%s" % (i + 1)] = "%s (+ %s)" % (
                    xy[2][self.__cut:],
                    ((len(self.__buffer) - i - 1) * self.__shift))
                userplot["hsvcolor_%s" % (i + 1)] = \
                    ((i + self.__counter) % self.__buflen)/float(self.__buflen)

            userplot["title"] = "History of %s" % label
            if "unit" in results:
                userplot["bottom"] = results["unit"]
                userplot["left"] = "intensity"
            userplot["legend"] = True
            userplot["legend_offset"] = -1
        return userplot


class LineCutImage(object):

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

        try:
            #: (:obj: `float`) buffer length
            self.__shift = float(json.loads(configuration)[2])
        except Exception:
            self.__shift = 1.0

        try:
            #: (:obj: `float`) buffer length
            self.__cut = int(json.loads(configuration)[3])
        except Exception:
            self.__cut = -28

        try:
            #: (:obj: `float`) buffer length
            self.__mode = str(json.loads(configuration)[4])
        except Exception:
            self.__mode = "all"

        #: (:obj: `list`) buffer
        self.__buffer = []

        self.__counter = - self.__buflen

        self.__imgbuffer = None
        self.__ximgbuffer = None

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        label = "linecut_%s" % self.__index
        label = "linecut_%s" % self.__index
        if label in results and "imagename" in results:
            self.__counter += 1

            if self.__mode != "image":
                if len(self.__buffer) >= self.__buflen:
                    self.__buffer.pop(0)
                if self.__shift:
                    for i in range(len(self.__buffer)):
                        self.__buffer[i][1] = [(y + self.__shift)
                                               for y in self.__buffer[i][1]]
                self.__buffer.append([results[label][0], results[label][1],
                                      results["imagename"]])
                userplot["nrplots"] = len(self.__buffer)
                for i, xy in enumerate(self.__buffer):
                    userplot["x_%s" % (i + 1)] = xy[0]
                    userplot["y_%s" % (i + 1)] = xy[1]
                    userplot["name_%s" % (i + 1)] = "%s (+ %s)" % (
                        xy[2][self.__cut:],
                        ((len(self.__buffer) - i - 1) * self.__shift))
                    userplot["hsvcolor_%s" % (i + 1)] = \
                        ((i + max(0, self.__counter)) % self.__buflen) \
                        / float(self.__buflen)

                userplot["title"] = "History of %s" % label
                if "unit" in results:
                    userplot["bottom"] = results["unit"]
                    userplot["left"] = "intensity"
                userplot["legend"] = True
                userplot["legend_offset"] = -1
                userplot["function"] = True

            if self.__mode != "function":
                newrow = np.array(results[label][1])
                if self.__imgbuffer is not None and \
                   self.__imgbuffer.shape[1] == newrow.shape[0]:
                    if self.__imgbuffer.shape[0] >= self.__buflen:
                        self.__imgbuffer = np.vstack(
                            [self.__imgbuffer[
                                self.__imgbuffer.shape[0]
                                - self.__buflen + 1:,
                                :],
                             newrow]
                        )
                    else:
                        self.__imgbuffer = np.vstack(
                            [self.__imgbuffer, newrow])
                else:
                    self.__imgbuffer = np.array([results[label][1]])
                if self.__imgbuffer is not None:
                    userplot["image"] = self.__imgbuffer.T
                    xbuf = np.array(results[label][0])
                    pos = 0.0
                    sc = 1.0
                    if len(xbuf) > 0:
                        pos = xbuf[0]
                    if len(xbuf) > 1:
                        sc = float(xbuf[-1] - xbuf[0])/(len(xbuf) - 1)
                    self.__ximgbuffer = results[label][0]
                    userplot["image_scale"] = [
                        [pos, max(0, self.__counter)], [sc, 1]]

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


class FitParameters(object):

    """Show Fitted parameters"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        self._x = []
        self._values = []

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        # print("RESULTS", results)
        if "tool" in results and results["tool"] == "twodfit":
            try:
                params = list(results["fitted_parameters"])
            except Exception:
                params = []
            try:
                names = list(results["parameters_names"])
            except Exception:
                names = []

            if self._values and len(params) != len(self._values):
                self._values = []
            if not self._values:
                self._values = [[pr] for pr in params]
            else:
                for ip, pr in enumerate(params):
                    self._values[ip].append(pr)
            self._x.append(len(self._x))
            nrplots = len(params)
            userplot["nrplots"] = nrplots
            userplot["title"] = "TwoDFit paramaters"

            for i in range(nrplots):
                xlabel = "x_%s" % (i + 1)
                ylabel = "y_%s" % (i + 1)
                nlabel = "name_%s" % (i + 1)
                name = names[i] if len(names) > i else ("a_%s" % i)
                cllabel = "hsvcolor_%s" % (i + 1)
                userplot[xlabel] = self._x
                userplot[ylabel] = self._values[i]
                userplot[nlabel] = name
                userplot[cllabel] = i/float(nrplots)
            userplot["legend"] = True
            userplot["legend_offset"] = -1
        # print("USERPLOT", userplot)
        return userplot


class FitProjections(object):

    """Fit projection parameters"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        try:
            #: (:obj: `int`) line cut index
            self.__initparams = json.loads(configuration)
        except Exception:
            self.__initparams = []

        self._startt = time.time()
        self._t = []
        self._values = []

    @classmethod
    def gauss(cls, x, amplitude, x0, sigma, offset=0.0):
        return offset + amplitude * np.exp(-(x - x0)**2 / (2 * sigma**2))

    @classmethod
    def generator(cls, x, val):
        mean = (x * val).sum() / val.sum()
        sigma = np.sqrt((val * (x - mean) ** 2).sum() / (val.sum()))
        return [np.max(val), mean, sigma, 0.0]

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        # print("RESULTS", results)
        if "tool" in results and results["tool"] == "projections":
            try:
                xx = np.array(results["xx"])
                sx = np.array(results["sx"])
                yy = np.array(results["yy"])
                sy = np.array(results["sy"])
            except Exception:
                xx = []
                sx = []
                yy = []
                sy = []
            xinitparams = self.generator(xx, sx)
            # print("xINIT", xinitparams)
            yinitparams = self.generator(yy, sy)
            # print("yINIT", yinitparams)

            xparams, _ = scipy.optimize.curve_fit(
                self.gauss, xx, sx, p0=xinitparams)
            yparams, _ = scipy.optimize.curve_fit(
                self.gauss, yy, sy, p0=yinitparams)
            # print("xPARAM", xparams)
            # print("yPARAM", yparams)
            params = list(xparams) + list(yparams)
            names = ["amp_x", "x_0", "sigma_x", "offset_x",
                     "amp_y", "y_0", "sigma_y", "offset_y"]

            if self._values and len(params) != len(self._values):
                self._values = []
            if not self._values:
                self._values = [[pr] for pr in params]
            else:
                for ip, pr in enumerate(params):
                    self._values[ip].append(pr)
            self._t.append(results["timestamp"] - self._startt)
            nrplots = len(params)
            userplot["nrplots"] = nrplots
            userplot["title"] = "Projection fit paramaters from " \
                "timestamp: %s s" % (self._startt)

            for i in range(nrplots):
                xlabel = "x_%s" % (i + 1)
                ylabel = "y_%s" % (i + 1)
                nlabel = "name_%s" % (i + 1)
                name = names[i] if len(names) > i else ("a_%s" % i)
                cllabel = "hsvcolor_%s" % (i + 1)
                userplot[xlabel] = self._t
                userplot[ylabel] = self._values[i]
                userplot[nlabel] = name
                userplot[cllabel] = i/float(nrplots)
            userplot["legend"] = True
            userplot["legend_offset"] = -1
        # print("USERPLOT", userplot)
        return userplot
