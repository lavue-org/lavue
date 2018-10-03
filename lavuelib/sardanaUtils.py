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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" sardana utils """

import pickle
import json
import time
import sys

try:
    import PyTango
    #: (:obj:`bool`) PyTango imported
    PYTANGO = True
except ImportError:
    #: (:obj:`bool`) PyTango imported
    PYTANGO = False

if sys.version_info > (3,):
    basestring = str


class SardanaUtils(object):

    """ sardanamacro server"""

    def __init__(self):
        """ constructor """

        #: (:obj:`list` <:class:`PyTango.DeviceProxy`>) pool tango servers
        self.__pools = []
        try:
            #: (:class:`PyTango.Database`) tango database
            self.__db = PyTango.Database()
        except Exception as e:
            print(str(e))
            self.__db = None

    @classmethod
    def openProxy(cls, device, counter=1000):
        """ opens device proxy of the given device

        :param device: device name
        :type device: :obj:`str`
        :returns: DeviceProxy of device
        :rtype: :class:`PyTango.DeviceProxy`
        """
        found = False
        cnt = 0
        cnfServer = PyTango.DeviceProxy(str(device))

        while not found and cnt < counter:
            if cnt > 1:
                time.sleep(0.01)
            try:
                cnfServer.ping()
                found = True
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                time.sleep(0.01)
                found = False
                if cnt == counter - 1:
                    raise
            cnt += 1

        return cnfServer

    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device proxy
        :rtype: :class:`PyTango.DeviceProxy`
        """
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        sdoor = door.split("/")
        tangohost = None
        if len(sdoor) > 1 and ":" in sdoor[0]:
            door = "/".join(sdoor[1:])
            tangohost = sdoor[0]
        if tangohost or not self.__db:
            host, port = tangohost.split(":")
            db = PyTango.Database(host, int(port))
        else:
            db = self.__db

        servers = db.get_device_exported_for_class("MacroServer").value_string
        ms = None

        for server in servers:
            dp = None
            if tangohost and ":" not in server:
                msname = "%s/%s" % (tangohost, server)
            else:
                msname = str(server)
            try:
                dp = self.openProxy(msname)
            except Exception as e:
                print(str(e))
                dp = None
            if hasattr(dp, "DoorList"):
                lst = dp.DoorList
                if lst and (door in lst or
                            ("%s/%s" % (tangohost, door) in lst)):
                    ms = dp
                    break
        return ms

    def getScanEnv(self, door, params=None):
        """ fetches Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :returns: JSON String with important variables
        :rtype: :obj:`str`
        """
        params = params or []
        res = {}
        msp = self.getMacroServer(door)
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    def getDeviceName(self, cname, db=None):
        """ finds device of give class

        :param cname: device class name
        :type cname: :obj:`str`
        :param db: tango database
        :type db: :class:`PyTango.Database`
        :returns: device name if exists
        :rtype: :obj:`str`
        """
        if db is None:
            db = self.__db
        try:
            servers = db.get_device_exported_for_class(cname).value_string
        except Exception:
            servers = []
        device = ''
        for server in servers:
            try:
                dp = self.openProxy(str(server))
                dp.ping()
                device = server
                break
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                pass
        return device

    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        data = json.loads(jdata)
        msp = self.getMacroServer(door)
        rec = msp.Environment
        if rec[0] == 'pickle':
            dc = pickle.loads(rec[1])
            if 'new' in dc.keys():
                for var in data.keys():
                    dc['new'][str(var)] = self.toString(data[var])
                pk = pickle.dumps(dc)
                msp.Environment = ['pickle', pk]

    def wait(self, name=None, proxy=None, maxcount=100):
        """ stores Scan Environment Data

        :param name: device name
        :type name: :obj:`str`
        :param proxy: door device proxy
        :type proxy: :obj:`str`
        :param maxcount: number of 0.01s to wait
        :type maxcount:  :obj:`int`
        """
        if proxy is None:
            proxy = self.openProxy(name)
        for _ in range(maxcount):
            if proxy.state() == PyTango.DevState.ON:
                break
            time.sleep(0.01)

    def runMacro(self, door, command, wait=True):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param command: list with the macro name and its parameters
        :type command: :obj:`list` <:obj:`str`>
        :param wait: wait till macro is finished
        :type wait: :obj:`bool`
        :returns: result, error or warning
        :rtype: [:obj:`str`, :obj:`str`]
        """
        doorproxy = self.openProxy(door)
        msp = self.getMacroServer(door)
        ml = msp.MacroList
        if len(command) == 0:
            raise Exception("Macro %s not found" % str(command))
        elif not command[0]:
            raise Exception("Macro %s not found" % str(command))
        elif command[0] not in ml:
            raise Exception("Macro '%s' not found" % str(command[0]))
        state = str(doorproxy.state())
        if state not in ["ON", "ALARM"]:
            raise Exception("Door in state '%s'" % str(state))

        try:
            doorproxy.RunMacro(command)
        except PyTango.DevFailed as e:
            if e.args[0].reason == 'API_CommandNotAllowed':
                self.wait(proxy=doorproxy)
                doorproxy.RunMacro(command)
            else:
                raise
        if wait:
            self.wait(proxy=doorproxy)
            warn = doorproxy.warning
            error = doorproxy.error
            res = doorproxy.result
            return res, error or warn
        else:
            return None, None

    def getError(self, door):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :returns: error or warning
        :rtype: :obj:`str`
        """
        doorproxy = self.openProxy(door)
        warn = doorproxy.warning
        error = doorproxy.error
        return error or warn

    @classmethod
    def toString(cls, obj):
        """ converts list/dict/object of unicode/string to string object

        :param obj: given unicode/string object
        :type obj: `any`
        :returns: string object
        :rtype: :obj:`str`
        """
        if isinstance(obj, basestring):
            return str(obj)
        elif isinstance(obj, list):
            return [cls.toString(el) for el in obj]
        elif isinstance(obj, dict):
            return dict([(cls.toString(key), cls.toString(value))
                         for key, value in obj.items()])
        else:
            return obj

    def getElementNames(self, door, listattr, typefilter=None):
        """ provides experimental Channels

        :param door: door device name
        :type door: :obj:`str`
        :param listattr: pool attribute with list
        :type listattr: :obj:`str`
        :param typefilter: pool attribute with list
        :type typefilter: :obj:`list` <:obj:`str`>
        :returns: names from given pool listattr
        :rtype: :obj:`list` <:obj:`str`>
        """
        lst = []
        elements = []
        if not self.__pools:
            self.getPools(door)
        for pool in self.__pools:
            if hasattr(pool, listattr):
                ellist = getattr(pool, listattr)
                if ellist:
                    lst += ellist
        for elm in lst:
            if elm:
                chan = json.loads(elm)
                if chan and isinstance(chan, dict):
                    if typefilter:
                        if chan['type'] not in typefilter:
                            continue
                    elements.append(chan['name'])
        return elements

    def getPools(self, door):
        """ provides pool devices

        :param door: door device name
        :type door: :obj:`str`
        """
        self.__pools = []
        host = None
        port = None
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        if ":" in door.split("/")[0] and len(door.split("/")) > 1:
            host, port = door.split("/")[0].split(":")
        msp = self.getMacroServer(door)
        poolNames = msp.get_property("PoolNames")["PoolNames"]
        if not poolNames:
            poolNames = []
        poolNames = ["%s/%s" % (door.split("/")[0], pn)
                     if (host and ":" not in pn)
                     else pn
                     for pn in poolNames]
        self.__pools = self.getProxies(poolNames)
        return self.__pools

    @classmethod
    def getProxies(cls, names):
        """ provides proxies of given device names

        :param names: given device names
        :type names: :obj:`list` <:obj:`str`>
        :returns: list of device DeviceProxies
        :rtype: :obj:`list` <:class:`PyTango.DeviceProxy`>
        """
        dps = []
        for name in names:
            dp = PyTango.DeviceProxy(str(name))
            try:
                dp.ping()
                dps.append(dp)
            except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
                pass
        return dps
