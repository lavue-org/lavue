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

    def setLavueState(self):
        self.__lcsu.proxy.LavueState = self.__lavuestate

    def getLavueStatePar(self):
        return self.__lcsu.proxy.LavueState

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

    def test_tango_tools(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        tisu = TestImageServerSetUp()
        try:
            tisu.setUp()

            self.__lcsu.proxy.Init()
            self.__lavuestate = None
            filepath = "%s/%s" % (os.path.abspath(path), "test/images")
            filename = "%05d.tif" % 2
            imagefile = os.path.join(filepath, filename)
            options = argparse.Namespace(
                mode='expert',
                source='tangoattr',
                configuration='test/lavuecontroller/00/Image',
                instance='tgtest',
                tool='roi',
                transformation='flip-up-down',
                log='debug',
                # log='info',
                imagefile=imagefile,
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

            cnf = {}
            cnf["toolconfig"] = '{' \
                '"aliases": ["pilatus_roi1", "pilatus_roi2"],' \
                ' "rois_number": 2}'
            lavuestate1 = json.dumps(cnf)
            cnf2 = {}
            cnf2["toolconfig"] = '{"all_cuts": true, ' \
                '"x_coordinates": "x-pixels", ' \
                ' "cuts_number": 2}'
            cnf2["tool"] = "linecut"
            lavuestate2 = json.dumps(cnf2)
            cnf3 = {}
            toolcnf3 = {"units": "q-space", "plot_type": "polar-q"}
            toolcnf3["plot_range"] = [[2, 20, 100], [1, 30, 50], [4, 67, 123]]
            toolcnf3["geometry"] = {
                "centerx": 234.,
                "centery": 23.34,
                "energy": 13567.45,
                "pixelsizex": 75.0,
                "pixelsizey": 65.0,
                "detdistance": 136.3
            }
            cnf3["toolconfig"] = json.dumps(toolcnf3)
            cnf3["tool"] = "angle/q"
            lavuestate3 = json.dumps(cnf3)

            cnf4 = {}
            toolcnf4 = {
                "xunits": "mm", "yunits": "cm",
                "xtext": "Mil", "ytext": "Cen",
                "x_position": 24.34,
                "y_position": 4.14,
                "position": [4, 3],
                "scale": [2.3, 4.4],
                "motors": ["mot1", "mot2"],
            }
            cnf4["toolconfig"] = json.dumps(toolcnf4)
            cnf4["tool"] = "movemotors"
            lavuestate4 = json.dumps(cnf4)

            cnf5 = {}
            toolcnf5 = {
                "xunits": "cm", "yunits": "um",
                "xtext": "Ml", "ytext": "Cn",
                "x_intervals": 223,
                "y_intervals": 123,
                "interval_time": 0.1,
                "position": [3, 4],
                "scale": [4.3, 2.4],
                "motors": ["mot2", "mot3"],
            }
            cnf5["toolconfig"] = json.dumps(toolcnf5)
            cnf5["tool"] = "meshscan"
            lavuestate5 = json.dumps(cnf5)

            cnf6 = {}
            toolcnf6 = {
                "rows": "1:20:2",
                "columns": "20:120",
                "mapping": "sum",

            }
            cnf6["toolconfig"] = json.dumps(toolcnf6)
            cnf6["tool"] = "projections"
            lavuestate6 = json.dumps(cnf6)

            cnf7 = {}
            toolcnf7 = {
                "maxima_number": 10,
                "units": "q-space",
                "current_maximum": 2,

            }
            toolcnf7["geometry"] = {
                "centerx": 34.,
                "centery": 13.34,
                "energy": 13267.45,
                "pixelsizex": 55.0,
                "pixelsizey": 65.0,
                "detdistance": 216.3
            }
            cnf7["toolconfig"] = json.dumps(toolcnf7)
            cnf7["tool"] = "maxima"
            lavuestate7 = json.dumps(cnf7)

            cnf8 = {}
            toolcnf8 = {
                "units": "q-space",
                "aliases": ["pilatus_r1", "pilatus_r2"],
                "rois_number": 2,
                "rows": "1:10",
                "columns": "10:100:2",
                "mapping": "mean"
            }
            toolcnf8["geometry"] = {
                "centerx": 24.,
                "centery": 23.34,
                "energy": 12367.45,
                "pixelsizex": 70.0,
                "pixelsizey": 65.0,
                "detdistance": 126.3
            }
            cnf8["toolconfig"] = json.dumps(toolcnf8)
            cnf8["tool"] = "q+roi+proj"
            lavuestate8 = json.dumps(cnf8)

            cnf9 = {}
            toolcnf9 = {}
            toolcnf9["tango_det_attrs"] = {
                # 'lmbd2': 'p00/lambda/dellek/LiveLastImageData',
                'sepc': 'test/testimageserver/00/Spectrum2',
                # 'mca01': 'p00/mca/exp.01/Data'
            }
            cnf9["toolconfig"] = json.dumps(toolcnf9)
            cnf9["tool"] = "parameters"
            lavuestate9 = json.dumps(cnf9)

            qtck1 = QtChecker(app, dialog, True, sleep=100)
            qtck2 = QtChecker(app, dialog, True, sleep=100)
            qtck3 = QtChecker(app, dialog, True, sleep=100)
            qtck4 = QtChecker(app, dialog, True, sleep=100)
            qtck5 = QtChecker(app, dialog, True, sleep=100)
            qtck6 = QtChecker(app, dialog, True, sleep=100)
            qtck7 = QtChecker(app, dialog, True, sleep=100)
            qtck8 = QtChecker(app, dialog, True, sleep=100)
            qtck9 = QtChecker(app, dialog, True, sleep=100)
            qtck10 = QtChecker(app, dialog, True, sleep=100)
            qtck11 = QtChecker(app, dialog, True, sleep=100)
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
            ])
            qtck2.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate2])
            ])
            qtck3.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate3])
            ])
            qtck4.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate4])
            ])
            qtck5.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate5])
            ])
            qtck6.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate6])
            ])
            qtck7.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate7])
            ])
            qtck8.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate8])
            ])
            qtck9.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
                ExtCmdCheck(self, "setLavueStatePar", [lavuestate9])
            ])
            qtck10.setChecks([
                ExtCmdCheck(self, "getLavueStatePar"),
            ])
            qtck11.setChecks([
                ExtCmdCheck(self, "getLavueStatePar")
            ])

            print("execute")
            qtck1.executeChecks(delay=1000)
            qtck2.executeChecks(delay=2000)
            qtck3.executeChecks(delay=3000)
            qtck4.executeChecks(delay=4000)
            qtck5.executeChecks(delay=5000)
            qtck6.executeChecks(delay=6000)
            qtck7.executeChecks(delay=7000)
            qtck8.executeChecks(delay=8000)
            qtck9.executeChecks(delay=9000)
            qtck10.executeChecks(delay=12000)
            status = qtck11.executeChecksAndClose(delay=15000)

            self.assertEqual(status, 0)
            qtck1.compareResults(self, [False, None])
            # qtck2.compareResults(self, [None, None], mask=[1, 1])
            # qtck3.compareResults(self, [None, None], mask=[1, 1])
            # qtck4.compareResults(self, [None, None], mask=[1, 1])
            # qtck5.compareResults(self, [None, None], mask=[1, 1])
            # qtck6.compareResults(self, [None, None], mask=[1, 1])
            # qtck7.compareResults(self, [None], mask=[1])

            # res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            res4 = qtck4.results()
            res5 = qtck5.results()
            res6 = qtck6.results()
            res7 = qtck7.results()
            res8 = qtck8.results()
            res9 = qtck9.results()
            res10 = qtck10.results()
            # res11 = qtck11.results()

            ls = json.loads(res2[0])
            dls = dict(self.__defaultls)
            dls.update(dict(
                mode='expert',
                source='tangoattr',
                configuration='test/lavuecontroller/00/Image',
                instance='tgtest',
                tool='roi',
                transformation='flip-up-down',
                # log='info',
                log='debug',
                toolconfig='{"aliases": ["pilatus_roi1", "pilatus_roi2"],'
                ' "rois_number": 2}',
                scaling='log',
                imagefile=imagefile,
                levels='-20.0,20.0',
                gradient='thermal',
                tangodevice='test/lavuecontroller/00',
                autofactor=None
            ))
            self.compareStates(
                ls, dls,
                ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
            tc1 = json.loads(ls["toolconfig"])
            tc2 = json.loads(dls["toolconfig"])
            self.compareStates(tc1, tc2)

            ls2 = json.loads(res3[0])
            tc1 = json.loads(ls2["toolconfig"])
            tc2 = json.loads(cnf2["toolconfig"])
            self.compareStates(tc1, tc2)

            ls3 = json.loads(res4[0])
            tc1 = json.loads(ls3["toolconfig"])
            tc2 = json.loads(cnf3["toolconfig"])
            self.compareStates(tc1, tc2, ['geometry'])
            self.compareStates(tc1['geometry'], tc2['geometry'])

            ls4 = json.loads(res5[0])
            tc1 = json.loads(ls4["toolconfig"])
            tc2 = json.loads(cnf4["toolconfig"])
            self.compareStates(tc1, tc2, ["motors", "motor_state"])
            self.assertEqual(tc1["motor_state"], "ON")

            ls5 = json.loads(res6[0])
            tc1 = json.loads(ls5["toolconfig"])
            tc2 = json.loads(cnf5["toolconfig"])
            self.compareStates(tc1, tc2, ["motors", "motor_state"])
            self.assertEqual(tc1["motor_state"], "ON")

            ls6 = json.loads(res7[0])
            tc1 = json.loads(ls6["toolconfig"])
            tc2 = json.loads(cnf6["toolconfig"])
            self.compareStates(tc1, tc2)

            ls = json.loads(res8[0])
            tc1 = json.loads(ls["toolconfig"])
            tc2 = json.loads(cnf7["toolconfig"])
            self.compareStates(tc1, tc2, ['geometry'])
            self.compareStates(tc1['geometry'], tc2['geometry'])

            ls = json.loads(res9[0])
            tc1 = json.loads(ls["toolconfig"])
            tc2 = json.loads(cnf8["toolconfig"])
            self.compareStates(tc1, tc2, ['geometry'])
            self.compareStates(tc1['geometry'], tc2['geometry'])

            ls = json.loads(res10[0])
            tc1 = json.loads(ls["toolconfig"])
            tc2 = json.loads(cnf9["toolconfig"])
            self.compareStates(tc1, tc2, ['tango_det_attrs'])
            self.compareStates(tc1['tango_det_attrs'], tc2['tango_det_attrs'])
        finally:
            tisu.tearDown()

    def test_tango_diff(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None
        filepath = "%s/%s" % (os.path.abspath(path), "test/images")
        filename = "%05d.tif" % 2
        poniname = "eiger4n_al203_13.45kev.poni"
        imagefile = os.path.join(filepath, filename)
        ponifile = os.path.join(filepath, poniname)
        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='flip-up-down',
            log='debug',
            # log='info',
            imagefile=imagefile,
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

        cnf = {}
        toolcnf = {
            "calibration": ponifile,
            "diff_number": 2,
            "diff_ranges": [[10, 20, 0, 20], [0, 30, 5, 15]],
            "diff_units": "2th [deg]",
            "buffer_size": 512,
            "buffering": True,
            "collect": True,
            "show_diff": True,
            "main_plot": "buffer 1"
        }
        cnf["toolconfig"] = json.dumps(toolcnf)
        cnf["tool"] = "diffractogram"
        lavuestate1 = json.dumps(cnf)

        qtck1 = QtChecker(app, dialog, True, sleep=100)
        qtck2 = QtChecker(app, dialog, True, sleep=100)
        qtck3 = QtChecker(app, dialog, True, sleep=100)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "setLavueStatePar", [lavuestate1])
        ])
        qtck2.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
        ])
        qtck3.setChecks([
            ExtCmdCheck(self, "getLavueStatePar"),
        ])

        print("execute")
        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=3000)
        status = qtck3.executeChecksAndClose(delay=6000)

        self.assertEqual(status, 0)
        qtck1.compareResults(self, [False, None])
        # qtck2.compareResults(self, [None, None], mask=[1, 1])
        # qtck3.compareResults(self, [None, None], mask=[1, 1])
        # qtck4.compareResults(self, [None, None], mask=[1, 1])
        # qtck5.compareResults(self, [None, None], mask=[1, 1])
        # qtck6.compareResults(self, [None, None], mask=[1, 1])
        # qtck7.compareResults(self, [None], mask=[1])

        # res1 = qtck1.results()
        res2 = qtck2.results()

        ls = json.loads(res2[0])
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='roi',
            transformation='flip-up-down',
            # log='info',
            log='debug',
            toolconfig='{"aliases": ["pilatus_roi1", "pilatus_roi2"],'
            ' "rois_number": 2}',
            scaling='log',
            imagefile=imagefile,
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None
        ))

        ls = json.loads(res2[0])
        tc1 = json.loads(ls["toolconfig"])
        tc2 = json.loads(cnf["toolconfig"])
        # print(tc1)
        # print(tc2)
        self.compareStates(tc1, tc2)

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
        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        qtck3.executeChecks(delay=3000)
        qtck4.executeChecks(delay=4000)
        status = qtck5.executeChecksAndClose(delay=5000)

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
        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        status = qtck3.executeChecksAndClose(delay=3000)

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
        qtck1.executeChecks(delay=1000)
        qtck2.executeChecks(delay=2000)
        status = qtck3.executeChecksAndClose(delay=3000)

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

    def test_1dplot(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__lavuestate = None

        options = argparse.Namespace(
            mode='expert',
            source='tangoattr',
            configuration='test/lavuecontroller/00/Image',
            instance='tgtest',
            tool='1d-plot',
            toolconfig='{"rows_to_plot": "0,1"}',
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
            tool='1d-plot',
            transformation='flip-up-down',
            log='debug',
            scaling='log',
            toolconfig='{"xrow": false, "buffer_size": 1024, "labels": [], '
            '"rows_to_plot": "0,1", "collect": false}',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            autofactor=None
        ))
        self.compareStates(
            ls, dls,
            ['viewrange', '__timestamp__', 'doordevice', 'toolconfig'])
        tc1 = json.loads(ls["toolconfig"])
        tc2 = json.loads(dls["toolconfig"])
        self.compareStates(tc1, tc2)

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
