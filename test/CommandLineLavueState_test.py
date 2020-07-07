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


# test fixture
class CommandLineLavueStateTest(unittest.TestCase):

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
        home = os.path.expanduser("~")
        fname = "%s/%s" % (home, ".config/DESY/LaVue: unittests.conf")
        if os.path.exists(fname):
            print("removing '%s'" % fname)
            os.remove(fname)

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def getControllerAttr(self, name):
        return getattr(self.__lcsu.proxy, name)

    def test_run(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            log='info',
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [False, None])

        self.compareStates(json.loads(self.__lavuestate))

    def test_start(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='user',
            instance='test',
            tool=None,
            start=True,
            source='test',
            log='info',
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [True, None])

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update({"connected": True, "source": "test"})
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_tango(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='flip-up-down',
            log='debug',
            scaling='log',
            levels='m20,20',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [False, None])

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='flip-up-down',
            log='debug',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_multi(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='expert',
            source='test;test;test',
            offset=';200,m300,r45;400,3,r180t',
            start=True,
            instance='test3',
            tool='projections',
            transformation='flip-up-down',
            log='error',
            rangewindow='10:600,20:800',
            dsreduction='min',
            dsfactor=2,
            scaling='linear',
            autofactor='1.3',
            gradient='flame',
            maskhighvalue='100',
            tangodevice='test/lavuecontroller/00'
        )
        logging.basicConfig(
             format="%(levelname)s: %(message)s")
        logger = logging.getLogger("lavue")
        lavuelib.liveViewer.setLoggerLevel(logger, options.log)
        dialog = lavuelib.liveViewer.MainWindow(options=options)
        dialog.show()

        qtck = QtChecker(app, dialog, True)
        qtck.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState")
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [True, None])

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='test;test;test',
            configuration=';;',
            connected=True,
            instance='test3',
            offset=';200,m300,r45;400,3,r180t',
            tool='projections',
            transformation='flip-up-down',
            log='error',
            scaling='linear',
            dsfactor=2,
            rangewindow=[10, 20, 600, 800],
            dsreduction='min',
            autofactor='1.3',
            gradient='flame',
            maskhighvalue='100',
            tangodevice='test/lavuecontroller/00'
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_mbuffer(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='expert',
            source='test',
            start=True,
            instance='test3',
            channel='rgb',
            mbuffer=10,
            tool='rgbintensity',
            transformation='flip-up-down',
            log='error',
            scaling='linear',
            autofactor='1.3',
            gradient='flame',
            tangodevice='test/lavuecontroller/00'
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
            ExtCmdCheck(self, "getLavueState"),
            WrapAttrCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg"
                "._SourceTabWidget__sourcetabs[],0._ui.pushButton",
                QtTest.QTest.mouseClick, [QtCore.Qt.LeftButton]),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__mbufferwg.bufferSize"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__channelwg.rgbchannels"),
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(self, [True, None, None, False, 10, (0, 1, 2)])

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='test',
            configuration='',
            connected=True,
            instance='test3',
            tool='rgbintensity',
            transformation='flip-up-down',
            log='error',
            scaling='linear',
            mbuffer=10,
            channel='0,1,2',
            autofactor='1.3',
            gradient='flame',
            tangodevice='test/lavuecontroller/00'
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_geometry(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        self.__lcsu.proxy.BeamCenterX = 1232.25
        self.__lcsu.proxy.BeamCenterY = 1222.5
        self.__lcsu.proxy.DetectorDistance = 154.0
        self.__lcsu.proxy.Energy = 13449.0
        self.__lcsu.proxy.PixelSizeX = 76.0
        self.__lcsu.proxy.PixelSizeY = 74.0

        cfg = '[Configuration]\n' \
            'StoreGeometry=true\n' \
            '[Tools]\n' \
            'CenterX=1141.4229212387716\n' \
            'CenterY=1285.4342087919763\n' \
            'CorrectSolidAngle=true\n' \
            'DetectorDistance=162.68360421509144\n' \
            'DetectorName=Eiger4M\n' \
            'DetectorPONI1=0.09638188689262517\n' \
            'DetectorPONI2=0.08616367970669807\n' \
            'DetectorRot1=0.0034235683458327527\n' \
            'DetectorRot2=0.0001578439093215932\n' \
            'DetectorRot3=-2.4724757830623586e-07\n' \
            'DetectorSplineFile=\n' \
            'DiffractogramNPT=1000\n' \
            'Energy=13449.999523070861\n' \
            'PixelSizeX=75\n' \
            'PixelSizeY=75\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)
        options = argparse.Namespace(
            mode='expert',
            source='test',
            start=True,
            tool='diffractogram',
            transformation='flip-up-down',
            log='error',
            instance='unittests',
            scaling='linear',
            autofactor='1.3',
            gradient='flame',
            tangodevice='test/lavuecontroller/00'
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
            ExtCmdCheck(self, "getLavueState"),
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
                "_MainWindow__lavue._LiveViewer__settings.energy"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.pixelsizex"),
            AttrCheck(
                "_MainWindow__lavue._LiveViewer__settings.pixelsizey"),
            ExtCmdCheck(self, "getControllerAttr", ["BeamCenterX"]),
            ExtCmdCheck(self, "getControllerAttr", ["BeamCenterY"]),
            ExtCmdCheck(self, "getControllerAttr", ["DetectorDistance"]),
            ExtCmdCheck(self, "getControllerAttr", ["Energy"]),
            ExtCmdCheck(self, "getControllerAttr", ["PixelSizeX"]),
            ExtCmdCheck(self, "getControllerAttr", ["PixelSizeY"]),
        ])

        status = qtck.executeChecksAndClose()

        self.assertEqual(status, 0)
        qtck.compareResults(
            self,
            [
                True, None, None, False,
                # LavueController overwrites the values
                1232.25, 1222.5, 154., 13449., 76., 74.,
                1232.25, 1222.5, 154., 13449., 76., 74.
            ]
        )

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='test',
            instance='unittests',
            configuration='',
            connected=True,
            tool='diffractogram',
            transformation='flip-up-down',
            log='error',
            scaling='linear',
            autofactor='1.3',
            gradient='flame',
            tangodevice='test/lavuecontroller/00'
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
