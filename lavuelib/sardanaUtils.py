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
import logging
import functools
import numpy as np

try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    #: (:obj:`bool`) tango imported
    TANGO = True
except ImportError:
    #: (:obj:`bool`) tango imported
    TANGO = False

if sys.version_info > (3,):
    basestring = str

logger = logging.getLogger("lavue")

if sys.version_info > (3,):
    unicode = str


def debugmethod(method):
    """ debug wrapper for methods
    :param method: any class method
    :type method: :class:`any`
    :returns: wrapped class method
    :rtype: :class:`any`
    """
    if logger.getEffectiveLevel() >= 10:
        @functools.wraps(method)
        def decmethod(*args, **kwargs):
            name = "%s.%s.%s" % (
                args[0].__class__.__module__,
                args[0].__class__.__name__,
                method.__name__
            )
            if args[1:]:
                margs = " with %s " % str(args[1:])
            else:
                margs = ""
            logger.debug("%s: excecuted %s" % (name, margs))
            ret = method(*args, **kwargs)
            logger.debug("%s: returns %s" % (
                name, str(ret) if ret is not None else ''))
            return ret
        return decmethod
    else:
        return method


class numpyEncoder(json.JSONEncoder):
    """ numpy json encoder with list
    """
    def default(self, obj):
        """ default encoder

        :param obj: numpy array object
        :type obj: :obj:`object` or `any`
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray) and obj.ndim > 0:
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class SardanaUtils(object):

    """ sardanamacro server"""

    @debugmethod
    def __init__(self):
        """ constructor """

        #: (:obj:`list` <:class:`tango.DeviceProxy`>) pool tango servers
        self.__pools = []
        try:
            #: (:class:`tango.Database`) tango database
            self.__db = tango.Database()
        except Exception:
            self.__db = None

    @classmethod
    def openProxy(cls, device, counter=100):
        """ opens device proxy of the given device

        :param device: device name
        :type device: :obj:`str`
        :returns: DeviceProxy of device
        :rtype: :class:`tango.DeviceProxy`
        """
        found = False
        cnt = 0
        cnfServer = tango.DeviceProxy(str(device))

        while not found and cnt < counter:
            if cnt > 1:
                time.sleep(0.01)
            try:
                cnfServer.ping()
                found = True
            except tango.DevFailed:
                time.sleep(0.01)
                found = False
                if cnt == counter - 1:
                    raise
            cnt += 1

        return cnfServer

    @debugmethod
    def getMacroServer(self, door):
        """ door macro server device name

        :param door: door device name
        :type door: :obj:`str`
        :returns: macroserver device proxy
        :rtype: :class:`tango.DeviceProxy`
        """
        if not door:
            raise Exception("Door '%s' cannot be found" % door)
        logger.debug("SardanaUtils.getMacroServer: Door = %s" % door)
        sdoor = door.split("/")
        tangohost = None
        if len(sdoor) > 1 and ":" in sdoor[0]:
            door = "/".join(sdoor[1:])
            tangohost = sdoor[0]
        logger.debug(
            "SardanaUtils.getMacroServer: Tango Host = %s" % tangohost)
        if tangohost or not self.__db:
            host, port = tangohost.split(":")
            db = tango.Database(host, int(port))
        else:
            db = self.__db
        logger.debug("SardanaUtils.getMacroServer: Database = %s" % str(db))

        servers = db.get_device_exported_for_class("MacroServer").value_string
        logger.debug(
            "SardanaUtils.getMacroServer: MacroSevers = %s" % str(servers))
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
                logger.warning("SardanaUtils.getMacroServer: %s" % str(e))
                # print(str(e))
                dp = None
            if hasattr(dp, "DoorList") and dp.DoorList:
                lst = [str(dr).lower() for dr in dp.DoorList]
                logger.debug(
                    "SardanaUtils.getMacroServer: DoorList = %s" % str(lst))
                if lst and (door.lower() in lst or
                            ("%s/%s" % (tangohost, door.lower()) in lst)):
                    ms = dp
                    logger.debug(
                        "SardanaUtils.getMacroServer: "
                        "Door MacroServer = %s" % str(ms))
                    break
        return ms

    @classmethod
    def pickleloads(cls, bytestr):
        """ loads pickle byte string
        :param bytestr: byte string to convert
        :type bytesstr: :obj:`bytes`
        :returns: loaded bytestring
        :rtype: :obj:`any`
        """
        if sys.version_info > (3,):
            return pickle.loads(bytestr, encoding='latin1')
        else:
            return pickle.loads(bytestr)

    @debugmethod
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
            dc = self.pickleloads(rec[1])
            if 'new' in dc.keys():
                for var in params:
                    if var in dc['new'].keys():
                        res[var] = dc['new'][var]
        return json.dumps(res)

    @debugmethod
    def getDeviceName(self, cname, db=None):
        """ finds device of give class

        :param cname: device class name
        :type cname: :obj:`str`
        :param db: tango database
        :type db: :class:`tango.Database`
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
            except tango.DevFailed:
                pass
        return device

    @debugmethod
    def setScanEnv(self, door, jdata):
        """ stores Scan Environment Data

        :param door: door device
        :type door: :obj:`str`
        :param jdata: JSON String with important variables
        :type jdata: :obj:`str`
        """
        data = json.loads(jdata)
        msp = self.getMacroServer(door)
        dc = {'new': {}}
        for var in data.keys():
            dc['new'][str(var)] = self.toString(data[var])
        try:
            pk = pickle.dumps(dc, protocol=2)
            msp.Environment = ['pickle', pk]
        except Exception:
            if sys.version_info < (3,):
                raise
            if isinstance(data, dict):
                newvalue = {}
                for key, vl in dc.items():
                    if isinstance(vl, dict):
                        nvl = {}
                        for ky, it in vl.items():
                            nvl[bytes(ky, "utf8")
                                if isinstance(ky, unicode) else ky] = it
                        newvalue[bytes(key, "utf8")
                                 if isinstance(key, unicode) else key] = nvl
                    else:
                        newvalue[bytes(key, "utf8")
                                 if isinstance(key, unicode) else key] = vl
            else:
                newvalue = dc
            pk = pickle.dumps(newvalue, protocol=2)
            msp.Environment = ['pickle', pk]

    @debugmethod
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
            if proxy.state() == tango.DevState.ON:
                break
            time.sleep(0.01)

    @debugmethod
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
        except tango.DevFailed as e:
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

    @debugmethod
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

    @debugmethod
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

    @debugmethod
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
        :rtype: :obj:`list` <:class:`tango.DeviceProxy`>
        """
        dps = []
        for name in names:
            dp = tango.DeviceProxy(str(name))
            try:
                dp.ping()
                dps.append(dp)
            except tango.DevFailed:
                pass
        return dps
