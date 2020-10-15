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
#     Jan Kotanski <jan.kotanski@desy.de>

import cffi

pffi = cffi.FFI()
pffi.cdef("void* EnsureOmniThread();")
eotlib = pffi.verify(r"""
    #include <omnithread.h>

    void* EnsureOmniThread(){
    return new omni_thread::ensure_self;
    }
""", source_extension='.cpp', libraries=["omnithread"])


class EnsureOmniThread(object):
    "ensure omni thread class"

    def __init__(self):
        """ constructor """
        self.__eot = None

    def __enter__(self):
        """ enter operator """
        self.__eot = eotlib.EnsureOmniThread()
        return self.__eot

    def __exit__(self, type, value, traceback):
        """ exit operator """
        self.__eot = None
