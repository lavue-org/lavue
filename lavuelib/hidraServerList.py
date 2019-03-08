# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

"""A list of possible hidra servers. Take your pick."""

#: (:obj:`dict` < :obj:`str`, :obj:`list` <:obj:`str`> >)
#:  server dictionary
HIDRASERVERLIST = {
    "p03": ['haspp03pilatus.desy.de'],
    "p08": ['haspp08pil100.desy.de',
            'haspp08perk01.desy.de'],
    "p09": ['haspp09pilatus.desy.de'],
    "p10": ['haspp10pilatus.desy.de'],
    "p11": ['haspp11pilatus.desy.de'],
    "pool": [
        'haspilatus300k.desy.de',
        'haspilatus1m.desy.de',
        'haspilatus100k.desy.de'
    ]
}
