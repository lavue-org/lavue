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
group_id = "12345678"
beamtime_cache = ""
gtoken_cache = ""
endpoint_cache = ""


def create_server_broker(endpoint, p1, p2, beamtime, p3, token, p4):
    global beamtime_cache
    global token_cache
    global endpoint_cache

    token_cache = token
    beamtime_cache = beamtime
    endpoint_cache = endpoint_cache
    return Broker(endpoint, beamtime, token)


class Broker(object):
    """ mock asapo brocker """

    def __init__(self, endpoint, beamtime, token):
        self.endpoint = endpoint
        self.beamtime = beamtime
        self.token = token
        self.counter = 1
        self.gid = 1
        self.metaonly = True

    def generate_group_id(self):
        return group_id

    def get_last(self, gid, meta_only):
        global filename
        self.gid = gid
        self.metaonly = meta_only
        self.data = None
        if filename:
            with open(filename, 'rb') as ifile:
                self.data = ifile.read()
        self.filename = filename.split("/")[-1]
        # print("FILENAME: %s" % filename)
        # print(self.data)
        self.counter += 1
        metadata = {"name": self.filename, "_id": self.counter}
        return self.data, metadata
