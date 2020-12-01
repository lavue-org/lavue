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
import numpy as np
import fabio
import threading
from shutil import copyfile, rmtree

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest


from qtchecker.qtChecker import (
    QtChecker, CmdCheck, ExtCmdCheck, WrapAttrCheck)

#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int
    unicode = str


# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))
if PY3:
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer
else:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import TCPServer


class TestHTTPServer(TCPServer):

    stopped = False
    allow_reuse_address = True

    def __init__(self, *args, **kw):
        TCPServer.__init__(self, *args, **kw)

    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()


# test fixture
class httpImageSourceTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        global app
        if app is None:
            app = QtGui.QApplication([])
        app.setOrganizationName("DESY")
        app.setApplicationName("LaVue: unittests")
        app.setOrganizationDomain("desy.de")
        app.setApplicationVersion(lavuelib.__version__)

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
        self.__counter = 0
        self.__tangoimgcounter = 0
        self.__tangofilepattern = "%05d.tif"
        self.__tangofilepath = ""
        self.__server = None
        self.__thread = None
        self.__directory = "monitor/api/1.5.0/images"

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        self.starthttpserver()
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def starthttpserver(self):
        import os
        if not os.path.exists(self.__directory):
            os.makedirs(self.__directory)
        self.__server = TestHTTPServer(("", 8082), SimpleHTTPRequestHandler)

        self.__thread = threading.Thread(None, self.__server.run)
        self.__thread.start()

    def stophttpserver(self):
        if self.__server is not None:
            self.__server.shutdown()
        if self.__thread is not None:
            self.__thread.join()
        if self.__directory:
            rmtree(self.__directory.split("/")[0])

    def tearDown(self):
        print("tearing down ...")
        self.stophttpserver()

    def takeNewImage(self):
        global app
        self.__counter += 1

        self.__tangoimgcounter += 1
        ipath = self.__tangofilepath
        iname = \
            self.__tangofilepattern % self.__tangoimgcounter
        fname = os.path.join(ipath, iname)
        copyfile(fname, os.path.join(self.__directory, "monitor"))
        image = fabio.open(fname)
        li = image.data
        app.sendPostedEvents()
        return li

    def test_readhttpimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        lastimage = None
        # lastimage = self.takeNewImage().T
        cfg = '[Configuration]\n' \
            'StoreGeometry=true\n' \
            'InterruptOnError=false\n'\
            'GeometryFromSource=true'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='http',
            configuration='localhost:8082/1.5.0',
            # % self._fname,
            start=True,
            # levels="0,1000",
            tool='intensity',
            transformation='none',
            log='debug',
            # log='error',
            instance='unittests',
            scaling='linear',
            gradient='spectrum',
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck4 = QtChecker(app, dialog, True, sleep=100)
        qtck5 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
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
        ])
        qtck4.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=13000)
        qtck3.executeChecks(delay=20000)
        qtck4.executeChecks(delay=27000)
        status = qtck5.executeChecksAndClose(delay=33000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None], mask=[1, 1, 0])

        qtck4.compareResults(self, [False])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[1], lastimage)
        self.assertEqual(res1[2], lastimage)

        lastimage = res1[3].T
        if not np.allclose(res2[2], lastimage):
            print(res2[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        self.assertTrue(np.allclose(res2[2], lastimage))

        lastimage = res2[3].T

        if not np.allclose(res3[0], lastimage):
            print(res3[0])
            print(lastimage)
        self.assertTrue(np.allclose(res3[0], lastimage))
        self.assertTrue(np.allclose(res3[1], lastimage))


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
