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

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtTest

from qtchecker.qtChecker import (
    QtChecker, CmdCheck, WrapAttrCheck, AttrCheck)


try:
    import testFilters
except Exception:
    from . import testFilters


#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    unicode = str
    long = int


# test fixture
class CommandLineArgumentTest(unittest.TestCase):

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

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        if os.path.exists(self.__cfgfname):
            print("removing '%s'" % self.__cfgfname)
            os.remove(self.__cfgfname)

    def tearDown(self):
        print("tearing down ...")

    def test_run(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            log='info')
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [False])

    def test_start(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            start=True,
            source='test',
            log='info')
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True, sleep=100)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                ".toggleServerConnection"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(
            self, [True, None, False, None, True, None, False])

    def test_filters(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        cfg = '[Configuration]\n' \
            'Filters="[[\\"test.testFilters.ImageStack\\", \\"\\"]]\n'
        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)
        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            source='test',
            filters=True,
            log='info')
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True, sleep=1000)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                ".toggleServerConnection"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(
            self, [False, None, True, None, False])

        self.assertEqual(
            len(testFilters.imagenamestack),
            len(testFilters.imagestack))
        for i, iname in enumerate(testFilters.imagenamestack):
            image = testFilters.imagestack[i]
            self.assertEqual(iname, '__random_%s__' % (i + 1))
            self.assertEqual(image.shape, (512, 256))
            self.assertEqual(str(image.dtype), "int64")

    def test_geometry(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        cfg = '[Configuration]\n' \
            'StoreGeometry=true\n' \
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
        options = argparse.Namespace(
            mode='expert',
            source='test',
            start=True,
            tool='intensity',
            transformation='flip-up-down',
            log='error',
            instance='unittests',
            scaling='linear',
            autofactor='1.3',
            gradient='flame',
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True, sleep=1000)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.centerx"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.centery"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detdistance"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detname"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detrot1"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detrot2"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detrot3"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.energy"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.pixelsizex"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.pixelsizey"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detponi1"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.detponi2"),
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(
            self,
            [
                True, None, False,
                1141.5,
                1285.0,
                162.75,
                "Eiger4M",
                0.5,
                0.125,
                -0.25,
                13450.,
                75,
                65,
                0.125,
                0.25
            ]
        )


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
