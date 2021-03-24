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
import lavuelib.h5cppwriter as h5cppWriter

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

MEMBUF = True


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
class ASAPOImageSourceH5CppTest(unittest.TestCase):

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

        self.__file = None
        self.__datamn = None
        self.__datamn2 = None
        self.__shape2 = None
        self.__shape = None

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

    def takeDefaultNewImage(self):
        global app
        self.__counter += 1

        asapo_consumer.filename = self._fname
        print("SET: %s" % asapo_consumer.filename)

        li = self.__datamn2
        app.sendPostedEvents()
        return li

    def takeNewPathImage(self):
        global app
        self.__counter += 1

        asapo_consumer.filename = self._fname
        print("SET: %s" % asapo_consumer.filename)

        li = self.__datamn
        app.sendPostedEvents()
        return li

    def createdetfile(self, fname):
        nx = 128
        ny = 256
        dshapemn = [nx, ny]
        shapemn = [0, nx, ny]
        chunkmn = [1, nx, ny]
        nx2 = 64
        ny2 = 256
        dshapemn2 = [nx2, ny2]
        shapemn2 = [0, nx2, ny2]
        chunkmn2 = [1, nx2, ny2]

        file2 = h5cppWriter.create_file(fname, True)
        root = file2.root()
        root.attributes.create("default", "string").write("entry")
        en = root.create_group("entry", "NXentry")
        en.attributes.create("default", "string").write("data1")
        dt = en.create_group("data1", "NXdata")
        datamn2 = dt.create_field(
            "det", "uint32", shape=shapemn2, chunk=chunkmn2)
        dt.attributes.create("signal", "string").write("det")
        ins = en.create_group("instrument", "NXinstrument")
        de = ins.create_group("detector", "NXdetector")
        datamn = de.create_field(
            "data", "uint32", shape=shapemn, chunk=chunkmn)

        dist = de.create_field(
            "distance", "float64", shape=[1], chunk=[1])
        dist.attributes.create(
            "units", "string").write("mm")
        dist[:] = 126.2
        wl = de.create_field(
            "wavelength", "float64", shape=[1], chunk=[1])
        wl[:] = 9e-11
        wl.attributes.create("units", "string").write("m")
        bcx = de.create_field(
            "beam_center_x", "float64", shape=[1], chunk=[1])
        bcx[:] = 1140
        bcy = de.create_field(
            "beam_center_y", "float64", shape=[1], chunk=[1])
        bcy[:] = 1286
        xps = de.create_field(
            "x_pixel_size", "float64", shape=[1], chunk=[1])
        xps[:] = 6.5e-5
        xps.attributes.create("units", "string").write("m")
        yps = de.create_field(
            "y_pixel_size", "float64", shape=[1], chunk=[1])
        yps[:] = 8.5e-5
        yps.attributes.create("units", "string").write("m")

        for i in range(10):
            amn = np.ones(shape=dshapemn)
            amn.fill(i)
            datamn.grow()
            datamn[i, :, :] = amn
            file2.flush()
        amn2 = np.fromfunction(np.vectorize(lambda i, j: (i + j * 4)),
                               shape=dshapemn2, dtype=int)
        datamn2.grow()
        datamn2[0, :, :] = amn2
        self.__file = file2
        self.__datamn = datamn.read()
        self.__datamn2 = datamn2.read()
        self.__shape2 = dshapemn2
        self.__shape = dshapemn
        file2.close()

    def test_readnxsfile_default(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if not MEMBUF:
            print("Loading a file from a memory buffer not supported")
            return
        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            self.createdetfile(self._fname)

            lastimage = None
            asapo_consumer.filename = ""
            asapo_consumer.usermeta = None
            asapo_consumer.substreams = ["stream1", "stream2"]
            cfg = '[Configuration]\n' \
                'ASAPOServer="haso.desy.de:8500"\n' \
                'ASAPOToken=2asaldskjsalkdjflsakjflksj \n' \
                'ASAPOBeamtime=123124 \n' \
                'ASAPOStreams=detector, \n' \
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
                configuration=None,
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
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                AttrCheck(
                    "_MainWindow__lavue._LiveViewer__imagename"),
                ExtCmdCheck(self, "takeDefaultNewImage"),
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
                WrapAttrCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg"
                    "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                    QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=3000)
            status = qtck2.executeChecksAndClose(delay=6000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None, None, False],
                mask=[0, 1, 1, 1, 0, 0])

            res1 = qtck1.results()
            res2 = qtck2.results()
            self.assertEqual(res1[1], None)
            self.assertEqual(res1[2], None)

            lastimage = res1[4][0, :, :].T
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
            self.assertTrue(iid > 11000)
            self.assertTrue(iid < 12000)
            self.assertEqual(
                fnames[0].strip(),
                "ASAPOImageSourceH5CppTesttest_readnxsfile_default.nxs")

        finally:
            if os.path.isfile(self._fname):
                os.remove(self._fname)

    def test_readnxsfile_nexuspath(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        if not MEMBUF:
            print("Loading a file from a memory buffer not supported")
            return

        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            self.createdetfile(self._fname)

            lastimage = None
            asapo_consumer.filename = ""
            asapo_consumer.usermeta = {
                "nexus_path": "/entry/instrument/detector/data"}
            asapo_consumer.substreams = ["stream1", "stream2"]
            cfg = '[Configuration]\n' \
                'ASAPOServer="haso.desy.de:8500"\n' \
                'ASAPOToken=2asaldskjsalkdjflsakjflksj \n' \
                'ASAPOBeamtime=123124 \n' \
                'ASAPOStreams=detector, \n' \
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
                configuration=None,
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
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                AttrCheck(
                    "_MainWindow__lavue._LiveViewer__imagename"),
                ExtCmdCheck(self, "takeNewPathImage"),
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
                WrapAttrCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg"
                    "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                    QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=3000)
            status = qtck2.executeChecksAndClose(delay=6000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None, None, False],
                mask=[0, 1, 1, 1, 0, 0])

            res1 = qtck1.results()
            res2 = qtck2.results()
            self.assertEqual(res1[1], None)
            self.assertEqual(res1[2], None)

            lastimage = np.sum(res1[4], 0).T
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
            self.assertTrue(iid > 11000)
            self.assertTrue(iid < 12000)
            self.assertEqual(
                fnames[0].strip(),
                "ASAPOImageSourceH5CppTesttest_readnxsfile_nexuspath.nxs")

        finally:
            if os.path.isfile(self._fname):
                os.remove(self._fname)

    def test_readnxsfile_nexusdatasetframe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        if not MEMBUF:
            print("Loading a file from a memory buffer not supported")
            return
        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            self.createdetfile(self._fname)

            lastimage = None
            asapo_consumer.filename = ""
            asapo_consumer.usermeta = {
                "nexus_image_frame": 3,
                "nexus_path": "/entry/instrument/detector/data"}
            asapo_consumer.substreams = ["stream1", "stream2"]
            cfg = '[Configuration]\n' \
                'ASAPOServer="haso.desy.de:8500"\n' \
                'ASAPOToken=2asaldskjsalkdjflsakjflksj \n' \
                'ASAPOBeamtime=123124 \n' \
                'ASAPOStreams=detector, \n' \
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
                configuration=None,
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
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                AttrCheck(
                    "_MainWindow__lavue._LiveViewer__imagename"),
                ExtCmdCheck(self, "takeNewPathImage"),
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
                WrapAttrCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg"
                    "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                    QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=3000)
            status = qtck2.executeChecksAndClose(delay=6000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None, None], mask=[0, 1, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None, None, False],
                mask=[0, 1, 1, 1, 0, 0])

            res1 = qtck1.results()
            res2 = qtck2.results()
            self.assertEqual(res1[1], None)
            self.assertEqual(res1[2], None)

            lastimage = res1[4][3, :, :].T
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
            self.assertTrue(iid > 11000)
            self.assertTrue(iid < 12000)
            self.assertEqual(
                fnames[0].strip(),
                "ASAPOImageSourceH5CppTesttest_readnxsfile_"
                "nexusdatasetframe.nxs")

        finally:
            if os.path.isfile(self._fname):
                os.remove(self._fname)


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
