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

import os
import sys
import subprocess

try:
    import tango
except ImportError:
    import PyTango as tango
import time

try:
    import TestImageServer
except Exception:
    from . import TestImageServer


# test fixture
class TestImageServerSetUp(object):

    # constructor
    # \brief defines server parameters

    def __init__(self, device="test/testimageserver/00", instance="S1"):
        self.new_device_info = tango.DbDevInfo()
        self.new_device_info._class = "TestImageServer"
        self.new_device_info.server = "TestImageServer/%s" % instance
        self.new_device_info.name = device

        # server instance
        self.instance = instance
        self._psub = None
        # device proxy
        self.proxy = None
        # device properties
        self.device_prop = {
        }

        # class properties
        self.class_prop = {
        }

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        print("\nsetting up...")
        db = tango.Database()
        db.add_device(self.new_device_info)
        db.add_server(
            self.new_device_info.server, self.new_device_info)
        # db.put_device_property(
        #     self.new_device_info.name, self.device_prop)
        # db.put_class_property(
        #     self.new_device_info._class, self.class_prop)

        path = os.path.dirname(os.path.abspath(TestImageServer.__file__))
        if os.path.isfile("%s/TestImageServer.py" % path):
            if sys.version_info > (3,):
                self._psub = subprocess.call(
                    "cd %s; python3 ./TestImageServer.py %s &" %
                    (path, self.instance), stdout=None,
                    stderr=None, shell=True)
            else:
                self._psub = subprocess.call(
                    "cd %s; python ./TestImageServer.py %s &" %
                    (path, self.instance), stdout=None,
                    stderr=None, shell=True)
            sys.stdout.write("waiting for simple server ")

        found = False
        cnt = 0
        dvname = self.new_device_info.name
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                sys.stdout.flush()
                exl = db.get_device_exported(dvname)
                if dvname not in exl.value_string:
                    time.sleep(0.01)
                    cnt += 1
                    continue
                self.proxy = tango.DeviceProxy(dvname)
                self.proxy.set_source(tango.DevSource.DEV)
                time.sleep(0.01)
                if self.proxy.state() == tango.DevState.ON:
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")

    # test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self):
        print("tearing down ...")
        db = tango.Database()
        db.delete_server(self.new_device_info.server)
        if sys.version_info > (3,):
            with subprocess.Popen(
                    "ps -ef | grep 'TestImageServer.py %s' | grep -v grep" %
                    self.instance,
                    stdout=subprocess.PIPE, shell=True) as proc:

                pipe = proc.stdout
                res = str(pipe.read(), "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
                pipe.close()
        else:
            pipe = subprocess.Popen(
                "ps -ef | grep 'TestImageServer.py %s' | grep -v grep" %
                self.instance,
                stdout=subprocess.PIPE, shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()


if __name__ == "__main__":
    simps = TestImageServerSetUp()
    simps.setUp()
    print(simps.proxy.status())
    simps.tearDown()
