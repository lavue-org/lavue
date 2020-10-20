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
class NXSFileImageSourceTest(unittest.TestCase):

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
        self.__shape = None

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

    def closedetfile(self):
        if self.__datamn is not None:
            self.__datamn.close()
        if self.__file is not None:
            self.__file.close()

    def takeNewImage(self):
        global app
        amn = np.random.randint(0, 1000, self.__shape)
        self.__datamn.grow()
        self.__datamn[-1, :, :] = amn
        self.__file.flush()
        self.__counter += 1
        return amn

    def createdetfile(self, fname):
        nx = 128
        ny = 256
        dshapemn = [nx, ny]
        shapemn = [0, nx, ny]
        chunkmn = [1, nx, ny]

        file2 = h5cppWriter.create_file(fname, True)
        root = file2.root()
        en = root.create_group("entry", "NXentry")
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
        self.__file = file2
        self.__datamn = datamn
        self.__shape = dshapemn
        # file2.close()

    def test_readimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)
        try:
            self.createdetfile(self._fname)
            cfg = '[Configuration]\n' \
                'StoreGeometry=true\n' \
                'GeometryFromSource=true\n' \
                'NXSFileOpen=false\n' \
                'NXSLastImage=true\n' \
                '[Tools]\n' \
                'CenterX=1141.5\n' \
                'CenterY=1285.0\n' \
                'CorrectSolidAngle=true\n' \
                'DetectorDistance=162.75\n' \
                'DetectorName=Eiger4M\n' \
                'DetectorPONI1=0.125\n' \
                'DetectorPONI2=0.25\n' \
                'DetectorRot1=0.5\n' \
                'DetectorRot2=0.125\n' \
                'DetectorRot3=-0.25\n' \
                'DetectorSplineFile=\n' \
                'DiffractogramNPT=1000\n' \
                'Energy=13450.\n' \
                'PixelSizeX=75\n' \
                'PixelSizeY=65\n'

            if not os.path.exists(self.__cfgfdir):
                os.makedirs(self.__cfgfdir)
            with open(self.__cfgfname, "w+") as cf:
                cf.write(cfg)

            lastimage = None

            options = argparse.Namespace(
                mode='expert',
                source='nxsfile',
                configuration='%s://entry/instrument/detector/data'
                % self._fname,
                start=True,
                levels="0,1000",
                tool='intensity',
                transformation='none',
                log='error',
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
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            status = qtck3.executeChecksAndClose(delay=18000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck3.compareResults(
                self, [None, None, None, False], mask=[1, 1, 0, 0])

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(9)

            res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            self.assertTrue(np.allclose(res1[1], lastimage))
            self.assertTrue(np.allclose(res1[2], lastimage))

            lastimage = res1[3].T
            if not np.allclose(res2[1], lastimage):
                print(res2[1])
                print(lastimage)
            self.assertTrue(np.allclose(res2[1], lastimage))
            self.assertTrue(np.allclose(res2[2], lastimage))

            lastimage = res2[3].T

            if not np.allclose(res3[0], lastimage):
                print(res3[0])
                print(lastimage)
            self.assertTrue(np.allclose(res3[0], lastimage))
            self.assertTrue(np.allclose(res3[1], lastimage))

        finally:
            self.closedetfile()
            if os.path.isfile(self._fname):
                os.remove(self._fname)

    def test_readimage_fromstart(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)
        try:
            self.createdetfile(self._fname)
            cfg = '[Configuration]\n' \
                'StoreGeometry=true\n' \
                'GeometryFromSource=true\n' \
                'NXSFileOpen=false\n' \
                'NXSLastImage=false\n' \
                '[Tools]\n' \
                'CenterX=1141.5\n' \
                'CenterY=1285.0\n' \
                'CorrectSolidAngle=true\n' \
                'DetectorDistance=162.75\n' \
                'DetectorName=Eiger4M\n' \
                'DetectorPONI1=0.125\n' \
                'DetectorPONI2=0.25\n' \
                'DetectorRot1=0.5\n' \
                'DetectorRot2=0.125\n' \
                'DetectorRot3=-0.25\n' \
                'DetectorSplineFile=\n' \
                'DiffractogramNPT=1000\n' \
                'Energy=13450.\n' \
                'PixelSizeX=75\n' \
                'PixelSizeY=65\n'

            if not os.path.exists(self.__cfgfdir):
                os.makedirs(self.__cfgfdir)
            with open(self.__cfgfname, "w+") as cf:
                cf.write(cfg)

            lastimage = None

            options = argparse.Namespace(
                mode='expert',
                source='nxsfile',
                configuration='%s://entry/instrument/detector/data'
                % self._fname,
                start=True,
                levels="0,1000",
                tool='intensity',
                transformation='none',
                log='error',
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
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            status = qtck3.executeChecksAndClose(delay=18000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck3.compareResults(
                self, [None, None, None, False], mask=[1, 1, 0, 0])

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(9)

            res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            self.assertTrue(np.allclose(res1[1], lastimage))
            self.assertTrue(np.allclose(res1[2], lastimage))

            lastimage = res1[3].T
            if not np.allclose(res2[1], lastimage):
                print(res2[1])
                print(lastimage)
            self.assertTrue(np.allclose(res2[1], lastimage))
            self.assertTrue(np.allclose(res2[2], lastimage))

            lastimage = res2[3].T

            if not np.allclose(res3[0], lastimage):
                print(res3[0])
                print(lastimage)
            self.assertTrue(np.allclose(res3[0], lastimage))
            self.assertTrue(np.allclose(res3[1], lastimage))

        finally:
            self.closedetfile()
            if os.path.isfile(self._fname):
                os.remove(self._fname)

    def test_readimage_negativeframe(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)
        try:
            self.createdetfile(self._fname)
            cfg = '[Configuration]\n' \
                'StoreGeometry=true\n' \
                'GeometryFromSource=true\n' \
                'NXSFileOpen=false\n' \
                'NXSLastImage=true\n' \
                '[Tools]\n' \
                'CenterX=1141.5\n' \
                'CenterY=1285.0\n' \
                'CorrectSolidAngle=true\n' \
                'DetectorDistance=162.75\n' \
                'DetectorName=Eiger4M\n' \
                'DetectorPONI1=0.125\n' \
                'DetectorPONI2=0.25\n' \
                'DetectorRot1=0.5\n' \
                'DetectorRot2=0.125\n' \
                'DetectorRot3=-0.25\n' \
                'DetectorSplineFile=\n' \
                'DiffractogramNPT=1000\n' \
                'Energy=13450.\n' \
                'PixelSizeX=75\n' \
                'PixelSizeY=65\n'

            if not os.path.exists(self.__cfgfdir):
                os.makedirs(self.__cfgfdir)
            with open(self.__cfgfname, "w+") as cf:
                cf.write(cfg)

            lastimage = None

            options = argparse.Namespace(
                mode='expert',
                source='nxsfile',
                configuration='%s://entry/instrument/detector/data,0,m2'
                % self._fname,
                start=True,
                levels="0,1000",
                tool='intensity',
                transformation='none',
                log='error',
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
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ])

            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            status = qtck3.executeChecksAndClose(delay=18000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck3.compareResults(
                self, [None, None, None, False], mask=[1, 1, 0, 0])

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(8)

            res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            if not np.allclose(res1[1], lastimage):
                print(res1[1])
                print(lastimage)
            self.assertTrue(np.allclose(res1[1], lastimage))
            self.assertTrue(np.allclose(res1[2], lastimage))

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(9)
            lastimage2 = res1[3].T
            if not np.allclose(res2[1], lastimage):
                print(res2[1])
                print(lastimage)
            self.assertTrue(np.allclose(res2[1], lastimage))
            self.assertTrue(np.allclose(res2[2], lastimage))

            # lastimage3 = res2[3].T

            if not np.allclose(res3[0], lastimage2):
                print(res3[0])
                print(lastimage2)
            self.assertTrue(np.allclose(res3[0], lastimage2))
            self.assertTrue(np.allclose(res3[1], lastimage2))

        finally:
            self.closedetfile()
            if os.path.isfile(self._fname):
                os.remove(self._fname)

    def test_readimage_frame(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self._fname = '%s/%s%s.nxs' % (
            os.getcwd(), self.__class__.__name__, fun)
        try:
            self.createdetfile(self._fname)
            cfg = '[Configuration]\n' \
                'StoreGeometry=true\n' \
                'GeometryFromSource=true\n' \
                'NXSFileOpen=false\n' \
                'NXSLastImage=true\n' \
                '[Tools]\n' \
                'CenterX=1141.5\n' \
                'CenterY=1285.0\n' \
                'CorrectSolidAngle=true\n' \
                'DetectorDistance=162.75\n' \
                'DetectorName=Eiger4M\n' \
                'DetectorPONI1=0.125\n' \
                'DetectorPONI2=0.25\n' \
                'DetectorRot1=0.5\n' \
                'DetectorRot2=0.125\n' \
                'DetectorRot3=-0.25\n' \
                'DetectorSplineFile=\n' \
                'DiffractogramNPT=1000\n' \
                'Energy=13450.\n' \
                'PixelSizeX=75\n' \
                'PixelSizeY=65\n'

            if not os.path.exists(self.__cfgfdir):
                os.makedirs(self.__cfgfdir)
            with open(self.__cfgfname, "w+") as cf:
                cf.write(cfg)

            lastimage = None

            options = argparse.Namespace(
                mode='expert',
                source='nxsfile',
                configuration='%s://entry/instrument/detector/data,0,5'
                % self._fname,
                start=True,
                levels="0,1000",
                tool='intensity',
                transformation='none',
                log='error',
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
            # self._ui.nxsFrameSpinBox
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                # ExtCmdCheck(self, "takeNewImage"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg"
                    "._SourceTabWidget__sourcetabs[],0"
                    "._SourceForm__sourcewidgets[],NeXus File"
                    ".widgets[],7"
                    ".setValue", [7]),
            ])
            qtck2.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                # ExtCmdCheck(self, "takeNewImage"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg"
                    "._SourceTabWidget__sourcetabs[],0"
                    "._SourceForm__sourcewidgets[],NeXus File"
                    ".widgets[],7"
                    ".setValue", [-1]),
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

            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            status = qtck3.executeChecksAndClose(delay=18000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck3.compareResults(
                self, [None, None, None, False], mask=[1, 1, 0, 0])

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(5)

            res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            if not np.allclose(res1[1], lastimage):
                print(res1[1])
                print(lastimage)
            self.assertTrue(np.allclose(res1[1], lastimage))
            self.assertTrue(np.allclose(res1[2], lastimage))

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(7)
            # lastimage2 = res1[3].T
            if not np.allclose(res2[1], lastimage):
                print(res2[1])
                print(lastimage)
            self.assertTrue(np.allclose(res2[1], lastimage))
            self.assertTrue(np.allclose(res2[2], lastimage))

            # lastimage3 = res2[3].T

            lastimage = np.ones(shape=self.__shape).T
            lastimage.fill(9)
            if not np.allclose(res3[0], lastimage):
                print(res3[0])
                print(lastimage)
            self.assertTrue(np.allclose(res3[0], lastimage))
            self.assertTrue(np.allclose(res3[1], lastimage))

        finally:
            self.closedetfile()
            if os.path.isfile(self._fname):
                os.remove(self._fname)


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
