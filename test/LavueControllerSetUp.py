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

"""Contain the Lavue Controller launcher"""

# Path
import sys
import os
import subprocess
import time
try:
    import tango
except ImportError:
    import PyTango as tango


# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


class TangoCB(object):

    def __init__(self, queue):
        self.__queue = queue

    def push_event(self, *args, **kwargs):
        event_data = args[0]
        if event_data.err:
            result = event_data.errors
            print(result)
        else:
            result = event_data.attr_value.value
        self.__queue.put(result)


# Device test case
class ControllerSetUp(object):
    """Test case for packet generation."""

    def __init__(self):
        """ constructor
        """
        self.instance = 'TEST'
        self.device = 'test/lavuecontroller/00'
        self.new_device_info_controller = tango.DbDevInfo()
        self.new_device_info_controller._class = "LavueController"
        self.new_device_info_controller.server = "LavueController/%s" % \
                                                 self.instance
        self.new_device_info_controller.name = self.device
        self.proxy = None

        if PY3:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python3 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python3 LavueController %s &" % self.instance
        else:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python2 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python2 LavueController %s &" % self.instance
        self._grepserver = \
            "ps -ef | grep 'LavueController %s' | grep -v grep" % \
            self.instance

    def setUp(self):
        print("\nsetting up ...")
        counts = 10
        ci = 0
        db = None
        while not db and ci < counts:
            ci += 1
            try:
                db = tango.Database()
            except Exception as e:
                print(str(e))

        db.add_device(self.new_device_info_controller)
        db.add_server(
            self.new_device_info_controller.server,
            self.new_device_info_controller)
        self._psub = subprocess.call(
            self._startserver,
            stdout=None,
            stderr=None, shell=True)
        sys.stdout.write("waiting for server ")

        found = False
        cnt = 0
        dvname = self.new_device_info_controller.name
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                sys.stdout.flush()
                exl = db.get_device_exported(dvname)
                if dvname not in exl.value_string:
                    time.sleep(0.05)
                    cnt += 1
                    continue
                dp = tango.DeviceProxy(dvname)
                time.sleep(0.2)
                if dp.state() == tango.DevState.ON:
                    found = True
            except Exception as e:
                found = False
                sys.stdout.write("%s\n" % str(e))
            cnt += 1
        print("")
        self.proxy = dp

    def tearDown(self):
        print("tearing down ...")
        counts = 10
        ci = 0
        db = None
        while not db and ci < counts:
            ci += 1
            try:
                db = tango.Database()
            except Exception as e:
                print(str(e))
        db.delete_server(self.new_device_info_controller.server)

        if PY3:
            with subprocess.Popen(self._grepserver,
                                  stdout=subprocess.PIPE,
                                  shell=True) as proc:
                try:
                    outs, errs = proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                res = str(outs, "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
        else:
            pipe = subprocess.Popen(self._grepserver,
                                    stdout=subprocess.PIPE,
                                    shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()

        self.proxy = None
