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
import unittest
import os
import sys
import random
import struct
import binascii
import time
import logging
import json
import numpy as np
import zmq

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest

try:
    import cPickle
except Exception:
    import _pickle as cPickle

from qtchecker.qtChecker import (
    QtChecker, CmdCheck, ExtCmdCheck, WrapAttrCheck)

#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int
    unicode = str

try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    #: (:obj:`bool`) tango imported
    TANGO = True
    if hasattr(tango, "EnsureOmniThread"):
        EnsureOmniThread = tango.EnsureOmniThread
    else:
        from lavuelib import cpplib
        EnsureOmniThread = cpplib.EnsureOmniThread
except ImportError:
    #: (:obj:`bool`) tango imported
    TANGO = False
    EnsureOmniThread = None


try:
    from .LavueControllerSetUp import ControllerSetUp
    # from .LavueControllerSetUp import TangoCB
except Exception:
    from LavueControllerSetUp import ControllerSetUp
    # from LavueControllerSetUp import TangoCB


# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


def tostr(x):
    """ decode bytes to str

    :param x: string
    :type x: :obj:`bytes`
    :returns:  decode string in byte array
    :rtype: :obj:`str`
    """
    if isinstance(x, str):
        return x
    if sys.version_info > (3,):
        return str(x, "utf8")
    else:
        return str(x)


# test fixture
class ZMQStreamImageSourceTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        global app
        if app is None:
            app = QtGui.QApplication([])
        app.setOrganizationName("DESY")
        app.setApplicationName("LaVue: unittests")
        app.setOrganizationDomain("desy.de")
        app.setApplicationVersion(lavuelib.__version__)

        self.__lcsu = ControllerSetUp()

        #: (:obj:`str`) lavue state
        self.__lavuestate = None

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
#        self.__seed = 332115341842367128541506422124286219441
        self.__rnd = random.Random(self.__seed)
        home = os.path.expanduser("~")
        self.__cfgfdir = "%s/%s" % (home, ".config/DESY")
        self.__cfgfname = "%s/%s" % (self.__cfgfdir, "LaVue: unittests.conf")
        self.__dialog = None
        self.__context = None
        self.__counter = 0
        self.__socketconn = None
        self.__socket = None
        #: (:class:`pyqtgraph.QtCore.QMutex`) mutex lock for zmq source
        self.__mutex = QtCore.QMutex()
        self.__tfilter = "12345"

        self.__defaultls = {
            '__timestamp__': 0.0,
            'version': lavuelib.__version__,
            'mode': 'user',
            'instance': 'test',
            'imagefile': '',
            'source': 'test',
            'configuration': '',
            'offset': '',
            'rangewindow': [None, None, None, None],
            'dsfactor': 1,
            'dsreduction': 'max',
            'filters': 0,
            'mbuffer': None,
            'channel': '',
            'bkgfile': '',
            'maskfile': '',
            'maskhighvalue': '',
            'transformation': 'none',
            'scaling': 'sqrt',
            'levels': '',
            'autofactor': '',
            'gradient': 'grey',
            'viewrange': '0,0,0,0',
            'connected': False,
            'tool': 'intensity',
            'tangodevice': 'test/lavuecontroller/00',
            'doordevice': '',
            'analysisdevice': '',
            'log': 'info',
        }

    def compareStates(self, state, defstate=None, exclude=None):
        if defstate is None:
            defstate = self.__defaultls
        if exclude is None:
            exclude = ['viewrange', '__timestamp__',
                       'configuration', 'source',
                       'doordevice']
        for ky, vl in defstate.items():
            if ky not in exclude:
                if state[ky] != vl:
                    print("%s: %s %s" % (ky, state[ky], vl))
                self.assertEqual(state[ky], vl)

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        self.__lcsu.setUp()
        self.__startzmq()
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()
        self.__closezmq()

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def getLavueStatePar(self):
        return self.__lcsu.proxy.LavueState

    def setLavueStatePar(self, arg):
        self.__lcsu.proxy.LavueState = arg

    def setZMQDataSources(self, *datasources):
        global app
        with QtCore.QMutexLocker(self.__mutex):
            socket = self.__socket
        # value = np.transpose(
        #     [
        #         [random.randint(0, 1000) for _ in range(512)]
        #         for _ in range(256)
        #     ])
        # shape = value.shape
        # dtype = value.dtype.name
        # imagename = "testimage_%s" % self.__counter
        # self.__tisu.proxy.StartAcq()
        # li = self.__tisu.proxy.LastImage
        metadata = {
                    "datasources": datasources}
        message = (
            "datasources".encode('ascii', 'ignore'),
            json.dumps(metadata).encode('ascii', 'ignore'),
            "JSON".encode('ascii', 'ignore')
        )
        # message = (
        #     self.__tfilter.encode('ascii', 'ignore'),
        #     value,
        #     json.dumps(shape).encode('ascii', 'ignore'),
        #     json.dumps(dtype).encode('ascii', 'ignore'),
        #     imagename.encode('ascii', 'ignore'),
        #     "JSON".encode('ascii', 'ignore')
        # )
        # self.__counter += 1
        with QtCore.QMutexLocker(self.__mutex):
            socket.send_multipart(message)
        app.sendPostedEvents()
        return message

    def takeNewJSONImageWithTopic(self, topic):
        global app
        with QtCore.QMutexLocker(self.__mutex):
            socket = self.__socket
        value = np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ])
        shape = value.shape
        dtype = value.dtype.name
        imagename = "testimage_%s" % self.__counter
        # self.__tisu.proxy.StartAcq()
        # li = self.__tisu.proxy.LastImage
        message = (
            topic.encode('ascii', 'ignore'),
            value,
            json.dumps(shape).encode('ascii', 'ignore'),
            json.dumps(dtype).encode('ascii', 'ignore'),
            imagename.encode('ascii', 'ignore'),
            "JSON".encode('ascii', 'ignore')
        )
        self.__counter += 1
        with QtCore.QMutexLocker(self.__mutex):
            socket.send_multipart(message)
        app.sendPostedEvents()
        return message

    def takeNewJSONImage(self):
        global app
        with QtCore.QMutexLocker(self.__mutex):
            socket = self.__socket
        value = np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ])
        shape = value.shape
        dtype = value.dtype.name
        imagename = "testimage_%s" % self.__counter
        # self.__tisu.proxy.StartAcq()
        # li = self.__tisu.proxy.LastImage
        message = (
            self.__tfilter.encode('ascii', 'ignore'),
            value,
            json.dumps(shape).encode('ascii', 'ignore'),
            json.dumps(dtype).encode('ascii', 'ignore'),
            imagename.encode('ascii', 'ignore'),
            "JSON".encode('ascii', 'ignore')
        )
        self.__counter += 1
        with QtCore.QMutexLocker(self.__mutex):
            socket.send_multipart(message)
        app.sendPostedEvents()
        return message

    def takeNewPickleImage(self):
        global app
        with QtCore.QMutexLocker(self.__mutex):
            socket = self.__socket
        value = np.transpose(
            [
                [random.randint(0, 1000) for _ in range(512)]
                for _ in range(256)
            ])
        shape = value.shape
        dtype = value.dtype.name
        imagename = "testimage_%s" % self.__counter
        # self.__tisu.proxy.StartAcq()
        # li = self.__tisu.proxy.LastImage
        message = (
            self.__tfilter.encode('ascii', 'ignore'),
            value,
            cPickle.dumps(shape),
            cPickle.dumps(dtype),
            imagename.encode('ascii', 'ignore'),
            "PICKLE".encode('ascii', 'ignore')
        )
        self.__counter += 1
        with QtCore.QMutexLocker(self.__mutex):
            socket.send_multipart(message)
        app.sendPostedEvents()
        return message

    def __closezmq(self):
        if self.__context:
            try:
                with QtCore.QMutexLocker(self.__mutex):
                    if self.__socket:
                        # if self.__socketconn:
                        #     self.__socket.unbind(self.__socketconn)
                        self.__socket.close(linger=0)
                        self.__socket = None
                if self.__context:
                    self.__context.destroy()
                    self.__context = None
                print("ZMQ disconnect")
            except Exception as e:
                print(str(e))
                pass

    def __startzmq(self):
        self.__context = zmq.Context()

    def getzmqsocket(self, port=None):
        with QtCore.QMutexLocker(self.__mutex):
            if self.__socket:
                self.__socket.close(linger=0)
            self.__socket = self.__context.socket(zmq.PUB)
            if port:
                conn = "tcp://*:%s" % (port)
                self.__socket.bind(conn)
            else:
                connecting = 10
                connected = False
                while not connected and connecting:
                    try:
                        conn = b"tcp://*:*"
                        self.__socket.bind(conn)
                        port = unicode(self.__socket.getsockopt(
                            zmq.LAST_ENDPOINT)).split(":")[-1]
                        if port.endswith("'"):
                            port = port[:-1]
                        connected = True
                    except Exception as e:
                        print(str(e))
                        connecting -= 1
            print("Connecting to: %s" % conn)

        self.__socketconn = conn
        return int(port)

    def getControllerAttr(self, name):
        return getattr(self.__lcsu.proxy, name)

    def test_readjsonimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        # port = 55536
        self.__lcsu.proxy.Init()
        port = self.getzmqsocket()
        self.__lavuestate = None
        lastimage = None

        zmqcnf = ':%s/%s' % (port, self.__tfilter)
        options = argparse.Namespace(
            mode='expert',
            source='zmq',
            configuration=zmqcnf,
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewJSONImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewJSONImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        status = qtck3.executeChecksAndClose(delay=3000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], lastimage)

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        self.assertEqual(res1[3], lastimage)

        mesg = res1[4]
        shape = json.loads(tostr(mesg[2]))
        # dtype = json.loads(tostr(mesg[3]))
        lastimage = mesg[1].T.reshape(shape)
        print(mesg)
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        mesg = res2[3]
        shape = json.loads(tostr(mesg[2]))
        # dtype = json.loads(tostr(mesg[3]))
        lastimage = mesg[1].T.reshape(shape)

        print(mesg)
        if not np.allclose(res3[0], lastimage):
            print(res3[0])
            print(lastimage)
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='zmq',
            configuration=zmqcnf,
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readpickleimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        # port = 55535
        self.__lcsu.proxy.Init()
        port = self.getzmqsocket()
        self.__lavuestate = None
        lastimage = None

        zmqcnf = ':%s/%s' % (port, self.__tfilter)
        options = argparse.Namespace(
            mode='expert',
            source='zmq',
            configuration=zmqcnf,
            instance='tgtest',
            tool='roi',
            log='debug',
            # log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewPickleImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewPickleImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        status = qtck3.executeChecksAndClose(delay=3000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], lastimage)

        self.assertEqual(res1[3], lastimage)

        mesg = res1[4]
        shape = cPickle.loads(mesg[2])
        # dtype = cPickle.loads(mesg[3])
        lastimage = mesg[1].T.reshape(shape)
        print(mesg)
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        mesg = res2[3]
        shape = cPickle.loads(mesg[2])
        # dtype = cPickle.loads(mesg[3])
        lastimage = mesg[1].T.reshape(shape)

        print(mesg)
        if not np.allclose(res3[0], lastimage):
            print(res3[0])
            print(lastimage)
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='zmq',
            configuration=zmqcnf,
            instance='tgtest',
            tool='roi',
            log='debug',
            # log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_autozmqtopics(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        # port = 55536
        self.__lcsu.proxy.Init()
        port = self.getzmqsocket()
        self.__lavuestate = None
        lastimage = None

        cfg = '[Configuration]\n' \
            'AutoZMQStreamTopics=true\n' \
            'ZMQStreamTopics=243, 234, 34\n' \
            'ZMQServers={}\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        zmqcnf = ':%s/%s' % (port, self.__tfilter)
        zmqcnf2 = ':%s/' % (port)
        options = argparse.Namespace(
            mode='expert',
            source='zmq',
            configuration=zmqcnf,
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            start=True,
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        cnf = {}
        cnf["source"] = "zmq"
        cnf["configuration"] = ":%s/" % (port)
        # cnf["configuration"] = ":%s/**ALL**" % (port)
        lavuestate1 = json.dumps(cnf)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck4 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck5 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck6 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck7 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck8 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck9 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewJSONImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setZMQDataSources", ["1235", "123", "23"]),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewJSONImageWithTopic", ["1235"]),
        ])
        qtck4.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setZMQDataSources", ["12345", "123", "23"]),
        ])
        qtck5.setChecks([
            ExtCmdCheck(self, "takeNewJSONImageWithTopic", ["12345"]),
        ])
        qtck6.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck7.setChecks([
            ExtCmdCheck(self, "takeNewJSONImageWithTopic", ["1234"]),
        ])
        qtck8.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setZMQDataSources", ["1345", "13", "23"]),
        ])
        qtck9.setChecks([
            ExtCmdCheck(self, "getLavueState"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        qtck3.executeChecks(delay=3000)
        qtck4.executeChecks(delay=4000)
        qtck5.executeChecks(delay=5000)
        qtck6.executeChecks(delay=6000)
        qtck7.executeChecks(delay=7000)
        qtck8.executeChecks(delay=8000)
        status = qtck9.executeChecksAndClose(delay=9000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck9.compareResults(
            self, [None,  None, False], mask=[1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        res4 = qtck4.results()
        res5 = qtck5.results()
        res6 = qtck6.results()
        res7 = qtck7.results()
        res8 = qtck8.results()
        # res9 = qtck9.results()
        self.assertEqual(res1[1], lastimage)

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        self.assertEqual(res1[2], lastimage)
        self.assertEqual(res2[1], lastimage)
        self.assertEqual(res3[1], lastimage)

        mesg = res3[3]
        shape = json.loads(tostr(mesg[2]))
        # dtype = json.loads(tostr(mesg[3]))
        lastimage = mesg[1].T.reshape(shape)
        print(mesg)
        if not np.allclose(res4[0], lastimage):
            print(res4[0])
            print(lastimage)
        self.assertTrue(np.allclose(res4[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res4[1], scaledimage))

        mesg = res5[0]
        shape = json.loads(tostr(mesg[2]))
        # dtype = json.loads(tostr(mesg[3]))
        lastimage = mesg[1].T.reshape(shape)
        print(mesg)
        if not np.allclose(res6[0], lastimage):
            print(res6[0])
            print(lastimage)
        self.assertTrue(np.allclose(res6[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res6[1], scaledimage))

        mesg = res7[0]
        shape = json.loads(tostr(mesg[2]))
        # dtype = json.loads(tostr(mesg[3]))
        lastimage = mesg[1].T.reshape(shape)
        print(mesg)
        if not np.allclose(res8[0], lastimage):
            print(res8[0])
            print(lastimage)
        self.assertTrue(np.allclose(res8[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res8[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='zmq',
            configuration=zmqcnf2,
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
