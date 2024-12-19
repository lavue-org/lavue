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


initial_parameters = [3, 100, 100, 20, 40, 0, 10]
initial_parameters = [3, 100, 100, 20, 40, 0]

parameters_names = ["Amp", "x0", "y0", "sigma_x", "sigma_y",
                    "offset", "theta (optional)"]


def function(xy, amplitude, x0, y0, sigma_x, sigma_y, offset=0.0, theta=0.0):
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
