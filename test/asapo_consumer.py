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
server_cache = ""


def create_server_broker(server_name, source_path, has_filesystem,
                         beamtime_id, stream, token, timeout_ms):
    global beamtime_cache
    global token_cache
    global server_cache

    token_cache = token
    beamtime_cache = beamtime_id
    server_cache = server_name
    return Broker(server_name, beamtime_id, token)


class Broker(object):
    """ mock asapo brocker """

    def __init__(self, server, beamtime, token):
        self.server = server
        self.beamtime = beamtime
        self.token = token
        self.counter = 1
        self.gid = 1
        self.metaonly = True

    def generate_group_id(self):
        print("Broker.generate_group_id()")
        return group_id

    def get_substream_list(self, from_substream=''):
        print("Broker.get_substream_list()")
        return ["stream1", "stream2"]

    def get_last(self, gid, substream="default", meta_only=True):
        print("Broker.get_last(%s, %s, %s)" % (gid, substream, meta_only))
        global filename
        self.gid = gid
        self.metaonly = meta_only
        self.data = None
        if filename:
            with open(filename, 'rb') as ifile:
                self.data = ifile.read()
        self.filename = filename.split("/")[-1]
        self.counter += 1
        iid = self.counter
        streambaseid = {
            "default": 1000,
            "sub1": 2000,
            "sub2": 3000,
            "stream1": 4000,
            "stream2": 5000,
        }
        if substream in streambaseid.keys():
            iid += streambaseid[substream]
        metadata = {"name": self.filename, "_id": iid}
        return self.data, metadata
