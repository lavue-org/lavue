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
#: (:obj:`str`) file name2
filename2 = ""


class Transfer(object):

    def __init__(self, query, hostname):
        self.query = query
        self.hostname = hostname
        self.target = []
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
        global filename2
        self.timeout = timeout
        self.data = None
        metadata = None
        try:
            if len(self.target) > 3 and int(self.target[1]) > 50100:
                if filename2:
                    with open(filename2, 'rb') as ifile:
                        self.data = ifile.read()
                        self.filename = filename2.split("/")[-1]
                        # print("FILENAME: %s" % filename)
                        # print(self.data)
                        metadata = {"filename": self.filename}
            else:
                if filename:
                    with open(filename, 'rb') as ifile:
                        self.data = ifile.read()
                        self.filename = filename.split("/")[-1]
                        # print("FILENAME: %s" % filename)
                        # print(self.data)
                        metadata = {"filename": self.filename}
        except Exception as e:
            print(str(e))
        return metadata, self.data

    def stop(self):
        self.state = "INIT"
