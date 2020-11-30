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
# import fabio
import random
import struct
import binascii
import time
import logging
import json
# import numpy as np

import argparse
import lavuelib
import lavuelib.liveViewer
from pyqtgraph import QtGui
# from pyqtgraph import QtCore
# from pyqtgraph.Qt import QtTest


from qtchecker.qtChecker import (
    QtChecker, CmdCheck, ExtCmdCheck,
    # WrapAttrCheck,
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

try:
    from .TestImageServerSetUp import TestImageServerSetUp
except Exception:
    from TestImageServerSetUp import TestImageServerSetUp

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
class SpecializedToolTest(unittest.TestCase):

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
            qtck10 = QtChecker(app, dialog, True, sleep=100,
                               withitem=EnsureOmniThread)
            qtck11 = QtChecker(app, dialog, True, sleep=100,
                               withitem=EnsureOmniThread)
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
            qtck11.setChecks([])

            print("execute")
            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            qtck3.executeChecks(delay=18000)
            qtck4.executeChecks(delay=24000)
            qtck5.executeChecks(delay=30000)
            qtck6.executeChecks(delay=36000)
            qtck7.executeChecks(delay=42000)
            qtck8.executeChecks(delay=48000)
            qtck9.executeChecks(delay=54000)
            qtck10.executeChecks(delay=60000)
            status = qtck11.executeChecksAndClose(delay=67000)

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

        qtck = QtChecker(app, dialog, True,
                         withitem=EnsureOmniThread)
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


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
