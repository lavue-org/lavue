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

try:
    from .LavueControllerSetUp import ControllerSetUp
    # from .LavueControllerSetUp import TangoCB
except Exception:
    from LavueControllerSetUp import ControllerSetUp
    # from LavueControllerSetUp import TangoCB

try:
    from .TestImageServerSetUp import TestImageServerSetUp
except Exception:
    from TestImageServerSetUp import TestImageServerSetUp

# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


# test fixture
class TangoAttrImageSourceTest(unittest.TestCase):

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
        self.__tisu = TestImageServerSetUp()

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
        self.__tisu.setUp()
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()
        self.__tisu.tearDown()

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def takeNewImage(self):
        self.__tisu.proxy.StartAcq()
        return self.__tisu.proxy.LastImage

    def getControllerAttr(self, name):
        return getattr(self.__lcsu.proxy, name)

    def test_readimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        lastimage = self.__tisu.proxy.LastImage.T

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/testimageserver/00/LastImage',
            instance='tgtest',
            tool='roi',
            log='debug',
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

        qtck = QtChecker(app, dialog, True, sleep=2000)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewImage"),
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

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)

        qtck.compareResults(
            self,
            [True, None, None, None, None, True, None, None,
             None, None, None, None, False],
            mask=[0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0])

        res = qtck.results()
        self.assertTrue(np.allclose(res[2], lastimage))

        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res[3], scaledimage))

        lastimage = res[4].T
        if not np.allclose(res[6], lastimage):
            print(res[6])
            print(lastimage)
        self.assertTrue(np.allclose(res[6], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res[7], scaledimage))

        lastimage = res[8].T
        self.assertTrue(np.allclose(res[9], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res[10], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/testimageserver/00/LastImage',
            instance='tgtest',
            tool='roi',
            log='debug',
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
