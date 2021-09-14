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
import fabio
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
    QtChecker, CmdCheck, ExtCmdCheck, WrapAttrCheck,
    # AttrCheck
)

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

# try:
#     from .TestImageServerSetUp import TestImageServerSetUp
# except Exception:
#     from TestImageServerSetUp import TestImageServerSetUp

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


# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


# test fixture
class GeneralToolTest(unittest.TestCase):

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

    def setLavueState(self):
        self.__lcsu.proxy.LavueState = self.__lavuestate

    def getLavueStatePar(self):
        try:
            ls = self.__lcsu.proxy.LavueState
            # print("getLavueState")
            # os.system("ps -ef | grep DataBaseds | grep -v 'grep'")
        except Exception as e:
            print(str(e))
            print("getLavueState EXCEPT")
            os.system("ps -ef | grep DataBaseds | grep -v 'grep'")
            db = tango.Database()
            print(db.get_db_host())
            dp = tango.DeviceProxy('test/lavuecontroller/00')
            ls = dp.LavueState
        return ls

    def setLavueStatePar(self, arg):
        self.__lcsu.proxy.LavueState = arg

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

        qtck = QtChecker(app, dialog, True, withitem=EnsureOmniThread)
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

        qtck = QtChecker(app, dialog, True, withitem=EnsureOmniThread)
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

    def test_tango_corrections(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        dffilename = "%05d.tif" % 2
        dfimagefile = os.path.join(filepath, dffilename)
        bffilename = "%05d.tif" % 3
        bfimagefile = os.path.join(filepath, bffilename)
        image = fabio.open(imagefile)
        t1 = image.data
        image = fabio.open(dfimagefile)
        t2 = image.data
        image = fabio.open(bfimagefile)
        t3 = image.data
        t12 = (t1 - t2)
        with np.errstate(divide='ignore', invalid='ignore'):
            t12d32 = np.true_divide(
                t12, t3 - t2, dtype="float64")
        t12d32[np.isinf(t12d32)] = np.nan
        with np.errstate(divide='ignore', invalid='ignore'):
            t1d3 = np.true_divide(
                t1, t3, dtype="float64")
        t1d3[np.isinf(t1d3)] = np.nan

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            bkgfile=dfimagefile,
            brightfieldfile=bfimagefile,
            scaling='linear',
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

        cnf1 = {"bkgfile": '', "brightfieldfile": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"bkgfile": dfimagefile, "brightfieldfile": ''}
        lavuestate2 = json.dumps(cnf2)
        cnf3 = {"bkgfile": '', "brightfieldfile": bfimagefile}
        lavuestate3 = json.dumps(cnf3)
        cnf4 = {"bkgfile": dfimagefile, "brightfieldfile": bfimagefile}
        lavuestate4 = json.dumps(cnf4)

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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])
        qtck4.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate4])
        ])
        qtck5.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        qtck3.executeChecks(delay=18000)
        qtck4.executeChecks(delay=24000)
        status = qtck5.executeChecksAndClose(delay=30000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        lastimage = t12d32.T
        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        res4 = qtck4.results()
        res5 = qtck5.results()

        lastimage = t12d32.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res2[1])
            print(res2[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t12.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[1])
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        lastimage = t1d3.T
        if not np.allclose(res4[2], lastimage, equal_nan=True):
            print(res4[1])
            print(res4[2])
            print(lastimage)
        self.assertTrue(np.allclose(res4[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res4[2], lastimage, equal_nan=True))

        lastimage = t12d32.T
        if not np.allclose(res5[2], lastimage, equal_nan=True):
            print(res5[1])
            print(res5[2])
            print(lastimage)
        self.assertTrue(np.allclose(res5[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res5[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res4[0])
        dls.update(cnf3)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res5[0])
        dls.update(cnf4)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_corrections_scale(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        dffilename = "%05d.tif" % 2
        dfimagefile = os.path.join(filepath, dffilename)
        bffilename = "%05d.tif" % 3
        bfimagefile = os.path.join(filepath, bffilename)
        image = fabio.open(imagefile)
        t1 = image.data
        image = fabio.open(dfimagefile)
        t2 = image.data
        image = fabio.open(bfimagefile)
        t3 = image.data

        sdfa = 1.4
        sdfb = 1.2
        sbfi = 1.1
        sbfj = 1.3

        t12a = (t1 - t2 * sdfa)
        t12b = (t1 - t2 * sdfb)

        with np.errstate(divide='ignore', invalid='ignore'):
            t12d32bj = np.true_divide(
                t12b, t3 * sbfj - t2 * sdfb, dtype="float64")

        t12d32bj[np.isinf(t12d32bj)] = np.nan

        with np.errstate(divide='ignore', invalid='ignore'):
            t1d3i = np.true_divide(
                t1, t3 * sbfi, dtype="float64")
        t1d3i[np.isinf(t1d3i)] = np.nan

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            bkgfile=dfimagefile,
            brightfieldfile=bfimagefile,
            bkgscale=sdfb,
            brightfieldscale=sbfj,
            scaling='linear',
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

        cnf1 = {"bkgfile": '', "brightfieldfile": '',
                "bkgscale": None,  "brightfieldscale": None}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"bkgfile": dfimagefile, "brightfieldfile": '',
                "bkgscale": sdfa,  "brightfieldscale": None}
        lavuestate2 = json.dumps(cnf2)
        cnf3 = {"bkgfile": '', "brightfieldfile": bfimagefile,
                "bkgscale": None,  "brightfieldscale": sbfi}
        lavuestate3 = json.dumps(cnf3)
        cnf4 = {"bkgfile": dfimagefile, "brightfieldfile": bfimagefile,
                "bkgscale": sdfb,  "brightfieldscale": sbfj}
        lavuestate4 = json.dumps(cnf4)

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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])
        qtck4.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate4])
        ])
        qtck5.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        qtck3.executeChecks(delay=18000)
        qtck4.executeChecks(delay=24000)
        status = qtck5.executeChecksAndClose(delay=30000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        lastimage = t12d32bj.T
        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        res4 = qtck4.results()
        res5 = qtck5.results()

        lastimage = t12d32bj.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res2[1])
            print(res2[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t12a.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[1])
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        lastimage = t1d3i.T
        if not np.allclose(res4[2], lastimage, equal_nan=True):
            print(res4[1])
            print(res4[2])
            print(lastimage)
        self.assertTrue(np.allclose(res4[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res4[2], lastimage, equal_nan=True))

        lastimage = t12d32bj.T
        if not np.allclose(res5[2], lastimage, equal_nan=True):
            print(res5[1])
            print(res5[2])
            print(lastimage)
        self.assertTrue(np.allclose(res5[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res5[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res4[0])
        dls.update(cnf3)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res5[0])
        dls.update(cnf4)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_maskfile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        maskfilename = "%05d.tif" % 2
        maskimagefile = os.path.join(filepath, maskfilename)
        image = fabio.open(imagefile)
        t1 = image.data
        image = fabio.open(maskimagefile)
        t2 = image.data
        m2z = (t2 == 0)
        t12z0 = np.array(t1)
        t12z0[m2z] = 0

        cfg = '[Configuration]\n' \
            'MaskingAsNAN=false\n' \
            'MaskingWithZeros=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            maskfile=maskimagefile,
            scaling='linear',
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

        cnf1 = {"maskfile": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"maskfile": maskimagefile}
        lavuestate2 = json.dumps(cnf2)
        lavuestate3 = json.dumps(cnf2)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()

        lastimage = t12z0.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t12z0.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_maskfile_nan(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        maskfilename = "%05d.tif" % 2
        maskimagefile = os.path.join(filepath, maskfilename)
        image = fabio.open(imagefile)
        t1 = image.data
        image = fabio.open(maskimagefile)
        t2 = image.data
        m2a = (t2 != 0)
        t12z0 = np.array(t1, dtype="float64")
        t12z0[m2a] = np.nan

        cfg = '[Configuration]\n' \
            'MaskingAsNAN=true\n' \
            'MaskingWithZeros=false\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            maskfile=maskimagefile,
            scaling='linear',
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

        cnf1 = {"maskfile": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"maskfile": maskimagefile}
        lavuestate2 = json.dumps(cnf2)
        lavuestate3 = json.dumps(cnf2)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()

        lastimage = t12z0.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t12z0.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,
        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_negmaskhighvalue(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data
        print(np.iinfo(t1.dtype).max)
        m14 = (t1 > 7)
        t1m14 = np.array(t1)
        t1m14[m14] = 0
        m4 = (t1 > 4)
        t1m4 = np.array(t1)
        t1m4[m4] = 0

        cfg = '[Configuration]\n' \
            'MaskingAsNAN=false\n' \
            'AddMaxValueToNegativeMask=true\n' \
            'MaskingWithZeros=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            maskhighvalue=-2147483640,
            scaling='linear',
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

        cnf1 = {"maskhighvalue": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"maskhighvalue": '4'}
        lavuestate2 = json.dumps(cnf2)
        lavuestate3 = json.dumps(cnf2)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()

        lastimage = t1m14.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t1m4.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_maskhighvalue(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data
        m14 = (t1 > 14)
        t1m14 = np.array(t1)
        t1m14[m14] = 0
        m4 = (t1 > 4)
        t1m4 = np.array(t1)
        t1m4[m4] = 0

        cfg = '[Configuration]\n' \
            'MaskingAsNAN=false\n' \
            'MaskingWithZeros=true\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            maskhighvalue=14,
            scaling='linear',
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

        cnf1 = {"maskhighvalue": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"maskhighvalue": '4'}
        lavuestate2 = json.dumps(cnf2)
        lavuestate3 = json.dumps(cnf2)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()

        lastimage = t1m14.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t1m4.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_maskhighvalue_nan(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data
        m14 = (t1 > 14)
        t1m14 = np.array(t1, dtype="float64")
        t1m14[m14] = np.nan
        m4 = (t1 > 4)
        t1m4 = np.array(t1, dtype="float64")
        t1m4[m4] = np.nan

        cfg = '[Configuration]\n' \
            'MaskingAsNAN=true\n' \
            'MaskingWithZeros=false\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            maskhighvalue=14,
            scaling='linear',
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

        cnf1 = {"maskhighvalue": ''}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"maskhighvalue": '4'}
        lavuestate2 = json.dumps(cnf2)
        lavuestate3 = json.dumps(cnf2)

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()

        lastimage = t1m14.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t1m4.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_trans(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data

        cfg = '[Configuration]\n' \
            'KeepOriginalCoordinates=false\n' \
            'GeometryFromSource=false\n' \
            'SourceDisplayParams=false\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            scaling='linear',
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

        cnf1 = {"transformation": 'flip-up-down'}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"transformation": 'flip-left-right'}
        lavuestate2 = json.dumps(cnf2)
        cnf3 = {"transformation": 'transpose'}
        lavuestate3 = json.dumps(cnf3)
        cnf4 = {"transformation": 'rot90'}
        lavuestate4 = json.dumps(cnf4)
        cnf5 = {"transformation": 'rot180'}
        lavuestate5 = json.dumps(cnf5)
        cnf6 = {"transformation": 'rot270'}
        lavuestate6 = json.dumps(cnf6)
        cnf7 = {"transformation": 'rot180+transpose'}
        lavuestate7 = json.dumps(cnf7)

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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])
        qtck4.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate4])
        ])
        qtck5.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate5])
        ])
        qtck6.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate6])
        ])
        qtck7.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate7])
        ])
        qtck8.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData")
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        qtck3.executeChecks(delay=18000)
        qtck4.executeChecks(delay=24000)
        qtck5.executeChecks(delay=30000)
        qtck6.executeChecks(delay=36000)
        qtck7.executeChecks(delay=42000)
        status = qtck8.executeChecksAndClose(delay=48000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        res4 = qtck4.results()
        res5 = qtck5.results()
        res6 = qtck6.results()
        res7 = qtck7.results()
        res8 = qtck8.results()

        lastimage = t1.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = np.flipud(t1).T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = np.fliplr(t1).T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        lastimage = t1
        if not np.allclose(res4[2], lastimage, equal_nan=True):
            print(res4[2])
            print(lastimage)
        self.assertTrue(np.allclose(res4[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res4[2], lastimage, equal_nan=True))

        lastimage = np.fliplr(t1)
        if not np.allclose(res5[2], lastimage, equal_nan=True):
            print(res5[2])
            print(lastimage)
        self.assertTrue(np.allclose(res5[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res5[2], lastimage, equal_nan=True))

        lastimage = np.flipud(np.fliplr(t1)).T
        if not np.allclose(res6[2], lastimage, equal_nan=True):
            print(res6[2])
            print(lastimage)
        self.assertTrue(np.allclose(res6[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res6[2], lastimage, equal_nan=True))

        lastimage = np.flipud(t1)
        if not np.allclose(res7[2], lastimage, equal_nan=True):
            print(res7[2])
            print(lastimage)
        self.assertTrue(np.allclose(res7[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res7[2], lastimage, equal_nan=True))

        lastimage = np.flipud(np.fliplr(t1))
        if not np.allclose(res8[2], lastimage, equal_nan=True):
            print(res8[2])
            print(lastimage)
        self.assertTrue(np.allclose(res8[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res8[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_displayparams(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data

        cfg = '[Configuration]\n' \
            'KeepOriginalCoordinates=false\n' \
            'GeometryFromSource=false\n' \
            'SourceDisplayParams=true\n' \
            '\n' \
            '[Source_test_lavuecontroller_00_Image]\n' \
            'autofactor=4\n' \
            'bkgfile=\n' \
            'gradient=grey\n' \
            'maskfile=\n' \
            'maskhighvalue=\n' \
            'offset=\n' \
            'scaling=sqrt\n' \
            'tool=roi\n' \
            'toolconfig="{\\"rois_number\\": 1, '\
            '\\"aliases\\": [\\"\\"]}"\n' \
            'transformation=transpose\n' \
            'viewrange="-75.0358508012,' \
            '-64.4760017023,150.0717016,128.952003405"\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool=None,
            # transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            scaling='linear',
            # levels='m20,20',
            gradient='thermal',
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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData")
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        status = qtck2.executeChecksAndClose(delay=12000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None], mask=[0, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()

        lastimage = t1
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='transpose',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            # levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor='4',
        ))

        ls = json.loads(res2[0])
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_displayparams_auto(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data

        cfg = '[Configuration]\n' \
            'KeepOriginalCoordinates=false\n' \
            'GeometryFromSource=false\n' \
            'SourceDisplayParams=true\n' \
            '\n' \
            '[Source_test_lavuecontroller_00_Image]\n' \
            'autofactor=\n' \
            'bkgfile=\n' \
            'gradient=grey\n' \
            'maskfile=\n' \
            'maskhighvalue=\n' \
            'offset=\n' \
            'scaling=sqrt\n' \
            'tool=roi\n' \
            'toolconfig="{\\"rois_number\\": 1, ' \
            '\\"aliases\\": [\\"\\"]}"\n' \
            'transformation=transpose\n' \
            'viewrange="-75.0358508012,-64.4760017023,' \
            '150.0717016,128.952003405"\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool=None,
            # transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            scaling='linear',
            # levels='m20,20',
            gradient='thermal',
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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData")
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        status = qtck2.executeChecksAndClose(delay=12000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None], mask=[0, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()

        lastimage = t1
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='transpose',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            # levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor='',
        ))

        ls = json.loads(res2[0])
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

    def test_tango_trans_keeporigin(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 1
        imagefile = os.path.join(filepath, filename)
        image = fabio.open(imagefile)
        t1 = image.data

        cfg = '[Configuration]\n' \
            'KeepOriginalCoordinates=true\n' \
            'GeometryFromSource=false\n' \
            'SourceDisplayParams=false\n'

        if not os.path.exists(self.__cfgfdir):
            os.makedirs(self.__cfgfdir)
        with open(self.__cfgfname, "w+") as cf:
            cf.write(cfg)

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            # log='debug',
            log='info',
            imagefile=imagefile,
            scaling='linear',
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

        cnf1 = {"transformation": 'flip-up-down'}
        lavuestate1 = json.dumps(cnf1)
        cnf2 = {"transformation": 'flip-left-right'}
        lavuestate2 = json.dumps(cnf2)
        cnf3 = {"transformation": 'transpose'}
        lavuestate3 = json.dumps(cnf3)
        cnf4 = {"transformation": 'rot90'}
        lavuestate4 = json.dumps(cnf4)
        cnf5 = {"transformation": 'rot180'}
        lavuestate5 = json.dumps(cnf5)
        cnf6 = {"transformation": 'rot270'}
        lavuestate6 = json.dumps(cnf6)
        cnf7 = {"transformation": 'rot180+transpose'}
        lavuestate7 = json.dumps(cnf7)

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
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
        ])
        qtck4.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate4])
        ])
        qtck5.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate5])
        ])
        qtck6.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate6])
        ])
        qtck7.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate7])
        ])
        qtck8.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData")
        ])

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        qtck3.executeChecks(delay=18000)
        qtck4.executeChecks(delay=24000)
        qtck5.executeChecks(delay=30000)
        qtck6.executeChecks(delay=36000)
        qtck7.executeChecks(delay=42000)
        status = qtck8.executeChecksAndClose(delay=48000)

        self.assertEqual(status, 0)
        qtck1.compareResults(
            self, [False, None, None, None], mask=[0, 1, 1, 1])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        res4 = qtck4.results()
        res5 = qtck5.results()
        res6 = qtck6.results()
        res7 = qtck7.results()
        res8 = qtck8.results()

        lastimage = t1.T
        if not np.allclose(res1[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res1[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res1[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res2[2], lastimage, equal_nan=True):
            print(res1[2])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res2[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res3[2], lastimage, equal_nan=True):
            print(res3[2])
            print(lastimage)
        self.assertTrue(np.allclose(res3[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res3[2], lastimage, equal_nan=True))

        lastimage = t1
        if not np.allclose(res4[2], lastimage, equal_nan=True):
            print(res4[2])
            print(lastimage)
        self.assertTrue(np.allclose(res4[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res4[2], lastimage, equal_nan=True))

        lastimage = t1
        if not np.allclose(res5[2], lastimage, equal_nan=True):
            print(res5[2])
            print(lastimage)
        self.assertTrue(np.allclose(res5[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res5[2], lastimage, equal_nan=True))

        lastimage = t1.T
        if not np.allclose(res6[2], lastimage, equal_nan=True):
            print(res6[2])
            print(lastimage)
        self.assertTrue(np.allclose(res6[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res6[2], lastimage, equal_nan=True))

        lastimage = t1
        if not np.allclose(res7[2], lastimage, equal_nan=True):
            print(res7[2])
            print(lastimage)
        self.assertTrue(np.allclose(res7[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res7[2], lastimage, equal_nan=True))

        lastimage = t1
        if not np.allclose(res8[2], lastimage, equal_nan=True):
            print(res8[2])
            print(lastimage)
        self.assertTrue(np.allclose(res8[1], lastimage, equal_nan=True))
        self.assertTrue(np.allclose(res8[2], lastimage, equal_nan=True))

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='none',
            log='info',
            # log='debug',
            scaling='linear',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None,

        ))

        ls = json.loads(res2[0])
        dls.update(cnf1)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        ls = json.loads(res3[0])
        dls.update(cnf2)
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])

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

        qtck = QtChecker(app, dialog, True,
                         withitem=EnsureOmniThread)
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
            tool='intensity',
            toolconfig='{"crosshair_locker": true, '
            '"xunits":"xpixel", "yunits":"ypixel",'
            '"xtext":"fast", "ytext":"slow",'
            '"position":[21,33], "scale":[2,3]}',
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

        qtck = QtChecker(app, dialog, True, sleep=100)
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

        status = qtck.executeChecksAndClose(delay=6000)

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
            tool='intensity',
            toolconfig='{"crosshair_locker": true, '
            '"xunits":"xpixel", "yunits":"ypixel",'
            '"xtext":"fast", "ytext":"slow",'
            '"position":[21,33], "scale":[2,3]}',
            transformation='flip-up-down',
            log='error',
            scaling='linear',
            mbuffer=10,
            channel='0,1,2',
            autofactor='1.3',
            gradient='flame',
            tangodevice='test/lavuecontroller/00'
        ))
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        tc1 = json.loads(ls["toolconfig"])
        tc2 = json.loads(dls["toolconfig"])
        self.compareStates(tc1, tc2)


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
