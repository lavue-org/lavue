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

import numpy as np


class GaussianFit:

    #: (:obj:`list` <:obj:`float`>) initial parameters
    initial_parameters = [30, 100, 100, 20, 40, 10, 0]
    initial_parameters = [30, 100, 100, 20, 40, 0]
    initial_parameters = [30, 100, 100, 20, 40]

    parameters_names = ["Amp", "x_0", "y_0", "sigma_x", "sigma_y",
                        "offset (optional)", "theta (optional)"]

    @classmethod
    def function(cls, xy, amplitude, x0, y0, sigma_x, sigma_y,
                 offset=0.0, theta=0.0):
        """2d guasian function

        :param xy: 2d gausian x,y coordinates
        :type xy: (:obj:`float`, :obj:`float`)
        :param amplitude: gaussian amplitude parameter
        :type amplitude: :obj:`float`
        :param x0: gaussian x_0 parameter
        :type x0: :obj:`float`
        :param y0: gaussian y_0 parameter
        :type y0: :obj:`float`
        :param sigma_x: gaussian sigma_x parameter
        :type sigma_x: :obj:`float`
        :param sigma_y: gausian sigma_x parameter
        :type sigma_y: :obj:`float`
        :param offset: gaussian offset parameter
        :type offset: :obj:`float`
        :param theta: gaussian theta parameter
        :type theta: :obj:`float`
        :returns: gaussian function value
        :rtype: :obj:`float`
        """
        (x, y) = xy
        x0 = float(x0)
        y0 = float(y0)
        a = (np.sin(theta) ** 2) / (2*sigma_y ** 2) \
            + (np.cos(theta) ** 2) / (2 * sigma_x ** 2)
        b = (np.sin(2 * theta)) / (4 * sigma_y ** 2) \
            - (np.sin(2 * theta)) / (4 * sigma_x ** 2)
        c = (np.cos(theta) ** 2) / (2 * sigma_y ** 2) \
            + (np.sin(theta)**2)/(2*sigma_x**2)
        g = amplitude * np.exp(
            -(a * ((x - x0) ** 2) + 2 * b * (x - x0) * (y - y0)
              + c * ((y - y0) ** 2))) + offset
        return g.ravel()

    @classmethod
    def generator(cls, dts, length=None):
        """2d guasian parameter generator

        :param dts: 2d image
        :type dts: :obj:`numpy.ndarray`
        :param length: number of parameters
        :type length: :obj:`int`
        :returns: list of generated paramters
        :rtype: :obj:`list` <:obj:`float`>
        """
        ym, xm = dts.shape
        x = np.linspace(0, xm - 1, xm)
        y = np.linspace(0, ym - 1, ym)
        x, y = np.meshgrid(x, y)
        mean_x = (x * dts).sum() / (dts.sum())
        mean_y = (y * dts).sum() / (dts.sum())
        sigma_x = np.sqrt((dts * (x - mean_x) ** 2).sum() / (dts.sum()))
        sigma_y = np.sqrt((dts * (y - mean_y) ** 2).sum() / (dts.sum()))
        # print("GEN", np.max(dts), mean_x, mean_y, sigma_x, sigma_y, 0., 0.)
        res = [np.max(dts), mean_x, mean_y, sigma_x, sigma_y, 0., 0.]
        if length is not None and length < len(res):
            res = res[:length]
        return res
