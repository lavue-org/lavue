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

""" test filters """

# import json
# import numpy as np
# from scipy import ndimage


imagestack = []
imagenamestack = []


def ImageStack(image, imagename, metadata, imagewg):
    """ image stack filter

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
    # global imagestack
    # global imagenamestack
    imagestack.append(image)
    print("Image name: '%s'" % imagename)
    imagenamestack.append(imagename)
