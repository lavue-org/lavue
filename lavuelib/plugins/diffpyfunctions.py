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


class DiffPDF(object):

    """diffpy PDF user function"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with config file and diff index
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__configfile = None

        config = None
        try:
            config = json.loads(configuration)
            try:
                self.__index = int(config[1])
            except Exception:
                self.__index = 1
            self.__configfile = str(config[0])
        except Exception:
            self.__index = 1
            self.__configfile = str(configuration)

        from diffpy.pdfgetx import loadPDFConfig
        self.__cfg = loadPDFConfig(self.__configfile)

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        from diffpy.pdfgetx import PDFGetter
        self.__pg = PDFGetter(config=self.__cfg)
        label = "diff_%s" % self.__index
        if label in results and self.__configfile:
            qq = results[label][0]
            df = results[label][1]
            data_gr = self.__pg(qq, df)
            x = data_gr[0]
            y = data_gr[1]

            userplot = {
                "x": x, "y": y,
                "title": "DiffPDF: %s with %s" % (label, self.__configfile)
            }
            #     userplot["bottom"] = ""
            #     userplot["left"] = ""
            # print("USERPLOT", len(qq), len(x))
        return userplot


class DiffPDFHistory(object):

    """diffpy PDF user function"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with config file and diff index
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__configfile = None

        #: (:obj: `int`) buffer length
        self.__buflen = 20
        #: (:obj: `float`) waterfall plot shift
        self.__shift = 1.0
        #: (:obj: `int`) diff label index
        self.__index = 1
        #: (:obj: `float`) number of characters cut from the image name
        self.__cut = -28
        #: (:obj: `list`) buffer
        self.__buffer = []
        #: (:obj: `int`) plot counter
        self.__counter = -1

        self.__imgbuffer = None
        self.__ximgbuffer = None

        try:
            config = json.loads(configuration)
            self.__configfile = str(config[0])
            try:
                self.__index = int(config[1])
            except Exception:
                pass

            try:
                self.__buflen = max(int(config[2]), 1)
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__shift = float(config[3])
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__cut = int(config[4])
            except Exception:
                pass

        except Exception:
            self.__configfile = str(configuration)

        self.__counter = - self.__buflen

        from diffpy.pdfgetx import loadPDFConfig
        #: configuration
        self.__cfg = loadPDFConfig(self.__configfile)

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        from diffpy.pdfgetx import PDFGetter
        self.__pg = PDFGetter(config=self.__cfg)
        label = "diff_%s" % self.__index

        if label in results and self.__configfile and "imagename" in results:
            qq = results[label][0]
            df = results[label][1]
            data_gr = self.__pg(qq, df)
            x = data_gr[0]
            y = data_gr[1]

            self.__counter += 1

            if len(self.__buffer) >= self.__buflen:
                self.__buffer.pop(0)
            if self.__shift:
                for i in range(len(self.__buffer)):
                    self.__buffer[i][1] = [(y + self.__shift)
                                           for y in self.__buffer[i][1]]
            self.__buffer.append([x, y, results["imagename"]])

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
            userplot["legend"] = True
            userplot["legend_offset"] = -1
            userplot["title"] = "DiffPDFHistory: %s with %s" % (
                label, self.__configfile)
            userplot["function"] = True

        return userplot


class DiffPDFImage(object):

    """diffpy PDF user function"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with config file and diff index
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__configfile = None

        #: (:obj: `int`) buffer length
        self.__buflen = 20
        #: (:obj: `float`) waterfall plot shift
        self.__shift = 1.0
        #: (:obj: `int`) diff label index
        self.__index = 1
        #: (:obj: `float`) number of characters cut from the image name
        self.__cut = -28
        #: (:obj: `list`) buffer
        self.__buffer = []
        #: (:obj: `int`) plot counter
        self.__counter = -1
        #: (:obj: `str`) plot mode i.e. all, image, function
        self.__mode = "all"

        self.__imgbuffer = None
        self.__ximgbuffer = None

        try:
            config = json.loads(configuration)
            self.__configfile = str(config[0])
            try:
                self.__index = int(config[1])
            except Exception:
                pass

            try:
                self.__buflen = max(int(config[2]), 1)
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__shift = float(config[3])
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__cut = int(config[4])
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__mode = str(config[5])
            except Exception:
                pass
        except Exception:
            self.__configfile = str(configuration)

        self.__counter = - self.__buflen

        from diffpy.pdfgetx import loadPDFConfig
        #: configuration
        self.__cfg = loadPDFConfig(self.__configfile)

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        from diffpy.pdfgetx import PDFGetter
        self.__pg = PDFGetter(config=self.__cfg)
        label = "diff_%s" % self.__index

        if label in results and self.__configfile and "imagename" in results:
            qq = results[label][0]
            df = results[label][1]
            data_gr = self.__pg(qq, df)
            x = data_gr[0]
            y = data_gr[1]

            self.__counter += 1

            if self.__mode != "image":
                if len(self.__buffer) >= self.__buflen:
                    self.__buffer.pop(0)
                if self.__shift:
                    for i in range(len(self.__buffer)):
                        self.__buffer[i][1] = [(y + self.__shift)
                                               for y in self.__buffer[i][1]]
                self.__buffer.append([x, y, results["imagename"]])

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
                userplot["legend"] = True
                userplot["legend_offset"] = -1
                userplot["title"] = "DiffPDFImage: %s with %s" % (
                    label, self.__configfile)
                userplot["function"] = True

            if self.__mode != "function":
                newrow = np.array(y)
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
                    self.__imgbuffer = np.array([y])
                if self.__imgbuffer is not None:
                    userplot["image"] = self.__imgbuffer.T
                    xbuf = np.array(x)
                    pos = 0.0
                    sc = 1.0
                    if len(xbuf) > 0:
                        pos = xbuf[0]
                    if len(xbuf) > 1:
                        sc = float(xbuf[-1] - xbuf[0])/(len(xbuf) - 1)
                    self.__ximgbuffer = results[label][0]
                    userplot["image_scale"] = [
                        [pos, max(0, self.__counter)], [sc, 1]]
                # userplot["colormap"] = 'plasma'
                # userplot["colormap_values"] = [0,1]

        return userplot


class DiffHistory(object):

    """diffpy PDF user function"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with config file and diff index
        :type configuration: :obj:`str`
        """
        #: (:obj: `int`) buffer length
        self.__buflen = 20
        #: (:obj: `float`) waterfall plot shift
        self.__shift = 1.0
        #: (:obj: `int`) diff label index
        self.__index = 1
        #: (:obj: `float`) number of characters cut from the image name
        self.__cut = -28
        #: (:obj: `list`) buffer
        self.__buffer = []
        #: (:obj: `int`) plot counter
        self.__counter = -1
        #: (:obj: `str`) plot mode i.e. all, image, function
        self.__mode = "all"

        self.__imgbuffer = None
        self.__ximgbuffer = None

        try:
            config = json.loads(configuration)
            try:
                self.__index = int(config[0])
            except Exception:
                pass

            try:
                self.__buflen = max(int(config[1]), 1)
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__shift = float(config[2])
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__cut = int(config[3])
            except Exception:
                pass

            try:
                #: (:obj: `float`) buffer length
                self.__mode = str(config[4])
            except Exception:
                pass
        except Exception:
            try:
                self.__index = int(configuration)
            except Exception:
                pass

        self.__counter = - self.__buflen

    def __call__(self, results):
        """ call method

        :param results: dictionary with tool results
        :type results: :obj:`dict`
        :returns: dictionary with user plot data
        :rtype: :obj:`dict`
        """
        userplot = {}
        label = "diff_%s" % self.__index

        if label in results and "imagename" in results:
            x = results[label][0]
            y = results[label][1]

            self.__counter += 1

            if self.__mode != "image":
                if len(self.__buffer) >= self.__buflen:
                    self.__buffer.pop(0)
                if self.__shift:
                    for i in range(len(self.__buffer)):
                        self.__buffer[i][1] = [(y + self.__shift)
                                               for y in self.__buffer[i][1]]
                self.__buffer.append([x, y, results["imagename"]])

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
                userplot["legend"] = True
                userplot["legend_offset"] = -1
                userplot["title"] = "DiffHistory: %s" % label
                userplot["function"] = True

            if self.__mode != "function":
                newrow = np.array(y)
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
                    self.__imgbuffer = np.array([y])
                if self.__imgbuffer is not None:
                    userplot["image"] = self.__imgbuffer.T
                    xbuf = np.array(x)
                    pos = 0.0
                    sc = 1.0
                    if len(xbuf) > 0:
                        pos = xbuf[0]
                    if len(xbuf) > 1:
                        sc = float(xbuf[-1] - xbuf[0])/(len(xbuf) - 1)
                    self.__ximgbuffer = results[label][0]
                    userplot["image_scale"] = [
                        [pos, max(0, self.__counter)], [sc, 1]]
                # userplot["colormap"] = 'plasma'
                # userplot["colormap_values"] = [0,1]

        return userplot
