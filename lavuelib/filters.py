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

import sys
import json


def _tostr(text):
    """ converts text  to str type

    :param text: text
    :type text: :obj:`bytes` or :obj:`unicode`
    :returns: text in str type
    :rtype: :obj:`str`
    """
    if isinstance(text, str):
        return text
    elif sys.version_info > (3,):
        return str(text, "utf8")
    else:
        return str(text)


class BaseFilter(object):

    """ filter base class"""

    def __init__(self, configuration=None):
        """ constructor

        :param name: image name
        :type metadata: :obj:`str`
        """
        #: (:obj:`str`) configuration string
        self.__configuration = configuration

    def __call__(self, image, imagename, metadata, imagewg):
        """ get metadata

        :param image: numpy array with an image
        :type image: :class:`numpy.ndarray`
        :param imagename: image name
        :type imagename: :obj:`str`
        :param metadata: JSON dictionary with metadata
        :type metadata: :obj:`str`
        :param imagewg: image wigdet
        :type imagewg: :class:`lavuelib.imageWidget.ImageWidget`
        :returns: numpy array with an image
        :rtype: :class:`numpy.ndarray` or `None`
        """
        return None

    def initialize(self):
        """ initialize the filter
        """
        pass

    def terminate(self):
        """ stop filter
        """
        pass


class FilterList(list):

    """ Filter list
    """

    def __init__(self, configlist=None, onlyfirst=False):
        """ constructor

        :param configlist: list with filter configuration
        :type configlist: \
        :    :obj:`list` < [:obj:`str` , :obj:`str`] >
        """
        list.__init__(self)
        self.__onlyfirst = onlyfirst
        self.currentconfig = ""
        self.errors = []
        if configlist:
            self.appendFilter(configlist)

    def reset(self, configlist):
        """ reset filters

        :param configlist: list with filter configuration
        :type configlist: \
        :    :obj:`list` < [:obj:`str` , :obj:`str`] >
        """
        self[:] = []
        self.appendFilters(configlist)

    def appendFilters(self, configlist):
        """ appends filters

        :param configlist: list with filter configuration
        :type configlist: \
        :    :obj:`list` < [:obj:`str` , :obj:`str`] >
        """
        self.currentconfig = ""
        self.errors = []
        newconfig = []
        found = False
        for configitem in configlist:
            if len(configitem) == 2:
                configitem.append(True)
            modulename, params, checked = configitem
            if modulename and checked and not (found and self.__onlyfirst):
                try:
                    pkl = _tostr(modulename).split(".")
                    pkg = ".".join(pkl[:-1])
                    if pkg in sys.modules.keys():
                        pdec = sys.modules[pkg]
                        dec = pdec
                    else:
                        dec = __import__(pkg, globals(),
                                         locals(), pkl[-1])
                    self.__append(getattr(dec, pkl[-1]), params)
                    newconfig.append([modulename, params, True])
                    found = True
                except Exception as e:
                    import traceback
                    value = traceback.format_exc()
                    self.errors.append((str(e), value))
                    newconfig.append([modulename, params, False])
            else:
                newconfig.append([modulename, params, False])
        self.currentconfig = json.dumps(newconfig)

    def __append(self, imgfilter, params):
        """ adds additional imgfilter

        :param imgfilter: imgfilter class or function
        :type imgfilter: :class:`BaseFilter`
        :param params:  constructor parameters
        :type params: :obj:`str`
        :returns: name of imgfilter
        :rtype: :obj:`str`
        """
        if type(imgfilter).__name__ == 'function':
            instance = imgfilter
        else:
            instance = imgfilter(params)
        if not hasattr(instance, '__call__'):
            return
        self.append(instance)
