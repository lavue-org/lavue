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
from scipy import ndimage


class HGap(object):

    """ Horizontal gap filter"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with horizontal gap pixels to add
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__indexes = [
            int(idx) for idx in json.loads(configuration)]

    def __call__(self, image, imagename, metadata, imagewg):
        """ call method

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
        return np.insert(image, self.__indexes, 0, axis=1)


class VGap(object):

    """ Vertical gap filter"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list with vertical gap pixels to add
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__indexes = [
            int(idx) for idx in json.loads(configuration)]

    def __call__(self, image, imagename, metadata, imagewg):
        """ call method

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
        return np.insert(image, self.__indexes, 0, axis=0)


def rot45(image, imagename, metadata, imagewg):
    """ rotate image by 45 deg

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
    if image is not None and image.dtype.kind == 'f' \
       and np.isnan(image.min()):
        image = np.nan_to_num(image)
    return ndimage.rotate(image, 45)


class WeightedSum(object):

    """ Weighted sum of channel images"""

    def __init__(self, configuration=None):
        """ constructor

        :param configuration: JSON list of channel image weights
        :type configuration: :obj:`str`
        """
        #: (:obj:`list` <:obj: `str`>) list of indexes for gap
        self.__weights = [
            wg for wg in json.loads(configuration or "[]")]

    def __call__(self, image, imagename, metadata, imagewg):
        """ call method

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
        if hasattr(image, "shape") and len(image.shape) == 3:

            weights = np.array(
                [(self.__weights[i]
                  if (len(self.__weights) > i and
                      type(self.__weights[i]) in [int, float])
                  else 1)
                 for i in range(image.shape[0])])

            if hasattr(np, "ma"):
                image_m = np.ma.array(image, mask=np.isnan(image))
                return np.ma.dot(image_m.T, weights).filled(np.nan).T
            else:
                return np.where(np.isnan(image), 0, image).T.dot(weights).T
