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

#: (:obj:`str`) file name
filename = ""


class Transfer(object):

    def __init__(self, query, hostname):
        self.query = query
        self.hostname = hostname
        self.target = ""
        self.state = "ON"
        self.timeout = None
        self.filename = ""
        self.data = None

    def initiate(self, target):
        self.target = target
        self.state = "INIT"

    def start(self):
        self.state = "RUNNING"

    def get(self, timeout):
        global filename
        self.timeout = timeout
        self.data = None
        if filename:
            with open(filename, 'rb') as ifile:
                self.data = ifile.read()
        self.filename = filename.split("/")[-1]
        # print("FILENAME: %s" % filename)
        # print(self.data)
        metadata = {"filename": self.filename}
        return metadata, self.data

    def stop(self):
        self.state = "INIT"
