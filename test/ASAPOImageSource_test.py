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

try:
    from . import asapo_consumer
except Exception:
    import asapo_consumer
try:
    from . import asapofake
except Exception:
    import asapofake

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest


from qtchecker.qtChecker import (
    QtChecker, CmdCheck, ExtCmdCheck, WrapAttrCheck, AttrCheck)

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
class ASAPOImageSourceTest(unittest.TestCase):

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
        print("ASAPO faked: %s" % asapofake.faked)

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")

    def takeNewImage(self):
        global app
        self.__counter += 1

        self.__tangoimgcounter += 1
        ipath = self.__tangofilepath
        iname = \
            self.__tangofilepattern % self.__tangoimgcounter
        fname = os.path.join(ipath, iname)
        asapo_consumer.filename = fname
        print("SET: %s" % asapo_consumer.filename)
        image = fabio.open(fname)
        li = image.data
        app.sendPostedEvents()
        return li

    def test_readimage_default(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        lastimage = None
        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        asapo_consumer.filename = ""
        cfg = '[Configuration]\n' \
            'ASAPOServer="haso.desy.de:8500"\n' \
            'ASAPOToken=2asaldskjsalkdjflsakjflksj \n' \
            'ASAPOBeamtime=123124 \n' \
            'ASAPOStreams=detector\n' \
            'StoreGeometry=true\n' \
            'GeometryFromSource=true'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        lastimage = None

        options = argparse.Namespace(
            mode='expert',
            source='asapo',
            configuration='hasyla.desy.de:8500',
            # % self._fname,
            start=True,
            # levels="0,1000",
            tool='intensity',
            transformation='none',
            # log='error',
            log='debug',
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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
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
            self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, None, False], mask=[1, 1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[1], None)
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        self.assertTrue(np.allclose(res2[2], lastimage))

        fnames = res2[3].split("(")
        self.assertTrue(len(fnames), 2)
        try:
            iid = int(fnames[1][:-1])
        except Exception:
            iid = -1
        self.assertTrue(iid > 1000)
        self.assertTrue(iid < 2000)
        self.assertEqual(fnames[0].strip(), "00001.tif")

        lastimage = res2[4].T

        if not np.allclose(res3[0], lastimage):
            print(res3[0])
            print(lastimage)
        self.assertTrue(np.allclose(res3[0], lastimage))
        self.assertTrue(np.allclose(res3[1], lastimage))

        fnames = res3[2].split("(")
        self.assertTrue(len(fnames), 2)
        try:
            iid = int(fnames[1][:-1])
        except Exception:
            iid = -1
        self.assertTrue(iid > 1000)
        self.assertTrue(iid < 2000)
        self.assertEqual(fnames[0].strip(), "00002.tif")

    def test_readimage_substream(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        lastimage = None
        asapo_consumer.filename = ""
        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        cfg = '[Configuration]\n' \
            'ASAPOServer="haso.desy.de:8500"\n' \
            'ASAPOToken=2asaldskjsalkdjflsakjflksj \n' \
            'ASAPOBeamtime=123124 \n' \
            'ASAPOStreams=detector\n' \
            'StoreGeometry=true\n' \
            'GeometryFromSource=true'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        lastimage = None

        options = argparse.Namespace(
            mode='expert',
            source='asapo',
            configuration='hasyla.desy.de:8500,stream2',
            # % self._fname,
            start=True,
            # levels="0,1000",
            tool='intensity',
            transformation='none',
            # log='error',
            log='debug',
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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
            ExtCmdCheck(self, "takeNewImage"),
        ])
        qtck3.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__imagename"),
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
            self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, None, False], mask=[1, 1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[1], None)
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        self.assertTrue(np.allclose(res2[2], lastimage))

        fnames = res2[3].split("(")
        self.assertTrue(len(fnames), 2)
        try:
            iid = int(fnames[1][:-1])
        except Exception:
            iid = -1
        self.assertTrue(iid > 5000)
        self.assertTrue(iid < 6000)
        self.assertEqual(fnames[0].strip(), "00001.tif")

        lastimage = res2[4].T

        if not np.allclose(res3[0], lastimage):
            print(res3[0])
            print(lastimage)
        self.assertTrue(np.allclose(res3[0], lastimage))
        self.assertTrue(np.allclose(res3[1], lastimage))

        fnames = res3[2].split("(")
        self.assertTrue(len(fnames), 2)
        try:
            iid = int(fnames[1][:-1])
        except Exception:
            iid = -1
        self.assertTrue(iid > 5000)
        self.assertTrue(iid < 6000)
        self.assertEqual(fnames[0].strip(), "00002.tif")


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
