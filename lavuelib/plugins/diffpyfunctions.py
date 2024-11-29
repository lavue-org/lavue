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
