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


#: (:obj:`str`) file name
filename = ""
streams = ["stream1", "stream2"]
group_id = "12345678"
beamtime_cache = ""
token_cache = ""
server_cache = ""
datasource_cache = ""
source_path_cache = ""
usermeta = None


# old version
# def create_server_broker(server_name, source_path, has_filesystem,
#                          beamtime_id, stream, token, timeout_ms):


def create_consumer(server_name, source_path, has_filesystem,
                    beamtime_id, data_source, token, timeout_ms):
    global beamtime_cache
    global token_cache
    global server_cache
    global datasource_cache
    global source_path_cache

    token_cache = token
    beamtime_cache = beamtime_id
    server_cache = server_name
    datasource_cache = data_source
    source_path_cache = source_path
    return Broker(server_name, beamtime_id, data_source, token)


class Broker(object):
    """ mock asapo brocker """

    def __init__(self, server, beamtime, data_source, token,
                 source_path=""):
        print("Broker.__init()")
        self.server = server
        self.beamtime = beamtime
        self.data_source = data_source
        self.source_path = source_path
        self.token = token
        self.counter = 1
        self.gid = 1
        self.metaonly = True

    def generate_group_id(self):
        print("Broker.generate_group_id()")
        return group_id

    # old version
    # def get_substream_list(self, from_substream=''):

    def get_stream_list(self, from_substream=''):
        print("Broker.get_stream_list()")
        return streams

    # old version
    # def get_last(self, gid, substream="default", meta_only=True):

    def get_last(self, meta_only=True, stream="default"):
        print("Broker.get_last(%s, %s)" % (stream, meta_only))
        global filename
        # self.gid = gid
        self.metaonly = meta_only
        self.data = None
        if filename:
            self.data = np.fromfile(filename, dtype="int8")
            # with open(filename, 'rb') as ifile:
            #     self.data = ifile.read()
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
        datasourcebaseid = {
            "detector": 10000,
            "pilatus": 20000,
        }
        if stream in streambaseid.keys():
            iid += streambaseid[stream]
        if self.data_source in datasourcebaseid.keys():
            iid += datasourcebaseid[self.data_source]
        metadata = {"name": self.filename, "_id": iid}
        if usermeta:
            metadata["meta"] = dict(usermeta)
        return self.data, metadata
