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
import fabio
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

#: (:obj:`bool`) PyTango bug #213 flag related to EncodedAttributes in python3
PYTG_BUG_213 = False
if sys.version_info > (3,):
    try:
        PYTGMAJOR, PYTGMINOR, PYTGPATCH = list(
            map(int, tango.__version__.split(".")[:3]))
        if PYTGMAJOR <= 9:
            if PYTGMAJOR == 9:
                if PYTGMINOR < 2:
                    PYTG_BUG_213 = True
                elif PYTGMINOR == 2 and PYTGPATCH <= 4:
                    PYTG_BUG_213 = True
            else:
                PYTG_BUG_213 = True
    except Exception:
        pass


# test fixture
class TangoFileImageSourceTest(unittest.TestCase):

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
        self.__counter = 0
        self.__file = None
        self.__datamn = None
        self.__shape = None
        self.__tangoimgcounter = 0
        self.__tangofilepattern = "%05d.tif"
        self.__tangofilepath = ""

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

    def closedetfile(self):
        if self.__datamn is not None:
            self.__datamn.close()
        if self.__file is not None:
            self.__file.close()

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

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def takeNewImage(self):
        global app
        self.__tisu.proxy.StartAcq()
        li = self.__tisu.proxy.LastImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewEncodedImage(self):
        global app
        self.__tangoimgcounter += 1
        if self.__tangoimgcounter % 2:
            self.__tisu.proxy.StartAcq()
        else:
            self.__tisu.proxy.ReadyEventAcq()
        li = self.__tisu.proxy.ImageEncoded
        # print(li)
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewSpectra(self):
        global app
        self.__tisu.proxy.StartAcq()
        l1 = self.__tisu.proxy.Spectrum1
        l2 = self.__tisu.proxy.Spectrum2
        app.sendPostedEvents()
        # yieldCurrentThread()
        return l1, l2

    def takeNewTangoFileImage(self):
        global app
        self.__tangoimgcounter += 1
        self.__tisu.proxy.LastImagePath = self.__tangofilepath
        self.__tisu.proxy.LastImageTaken = \
            self.__tangofilepattern % self.__tangoimgcounter
        fname = os.path.join(
            self.__tisu.proxy.LastImagePath,
            self.__tisu.proxy.LastImageTaken)
        image = fabio.open(fname)
        li = image.data
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewTangoFileNXSURLImage(self):
        global app
        fname = "%s::%s" % (
            self.__tangofilepath, self.__tangofilepattern)
        self.__tisu.proxy.LastImagePath = ""
        self.__tisu.proxy.LastImageTaken = "h5file://%s" % fname
        amn = np.random.randint(0, 1000, self.__shape)
        self.__datamn.grow()
        self.__datamn[-1, :, :] = amn
        self.__file.flush()
        self.__counter += 1
        return amn

    def takeNewTangoFileURLImage(self):
        global app
        self.__tangoimgcounter += 1
        fname = "%s/%s" % (
            self.__tangofilepath,
            (self.__tangofilepattern % self.__tangoimgcounter))
        self.__tisu.proxy.LastImagePath = ""
        self.__tisu.proxy.LastImageTaken = "file://%s" % fname
        image = fabio.open(fname)
        li = image.data
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewChangeEventImage(self):
        global app
        self.__tisu.proxy.ChangeEventAcq()
        li = self.__tisu.proxy.ChangeEventImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def takeNewReadyEventImage(self):
        global app
        self.__tisu.proxy.ReadyEventAcq()
        li = self.__tisu.proxy.ReadyEventImage
        app.sendPostedEvents()
        # yieldCurrentThread()
        return li

    def getControllerAttr(self, name):
        return getattr(self.__lcsu.proxy, name)

    def test_readtangofileimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        # lastimage = self.__tisu.proxy.ReadyEventImage.T
        lastimage = None
        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        options = argparse.Namespace(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken,'
            'test/testimageserver/00/LastImagePath',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
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

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileImage"),
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

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)
        # self.assertTrue(np.allclose(res1[2], lastimage))

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        # self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken,'
            'test/testimageserver/00/LastImagePath,{"/ramdisk/": "/gpfs/"}'
            ',False,False',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readtangofile_urlimage(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
        self.__lavuestate = None
        # lastimage = self.__tisu.proxy.ReadyEventImage.T
        lastimage = None
        self.__tangoimgcounter = 0
        self.__tangofilepath = "%s/%s" % (os.path.abspath(path), "test/images")
        self.__tangofilepattern = "%05d.tif"
        options = argparse.Namespace(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
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

        qtck1 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck2 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck3 = QtChecker(app, dialog, True, sleep=100,
                          withitem=EnsureOmniThread)
        qtck1.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            ExtCmdCheck(self, "getLavueState"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileURLImage"),
        ])
        qtck2.setChecks([
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
            CmdCheck(
                "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
            ExtCmdCheck(self, "takeNewTangoFileURLImage"),
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

        print("execute")
        qtck1.executeChecks(delay=6000)
        qtck2.executeChecks(delay=12000)
        status = qtck3.executeChecksAndClose(delay=18000)

        self.assertEqual(status, 0)

        qtck1.compareResults(
            self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
        qtck2.compareResults(
            self, [True, None, None, None], mask=[0, 1, 1, 1])
        qtck3.compareResults(
            self, [None, None, None, False], mask=[1, 1, 0, 0])

        res1 = qtck1.results()
        res2 = qtck2.results()
        res3 = qtck3.results()
        self.assertEqual(res1[2], None)
        self.assertEqual(res1[3], None)
        # self.assertTrue(np.allclose(res1[2], lastimage))

        # scaledimage = np.clip(lastimage, 10e-3, np.inf)
        # scaledimage = np.log10(scaledimage)
        # self.assertTrue(np.allclose(res1[3], scaledimage))

        lastimage = res1[4].T
        if not np.allclose(res2[1], lastimage):
            print(res2[1])
            print(lastimage)
        self.assertTrue(np.allclose(res2[1], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res2[2], scaledimage))

        lastimage = res2[3].T
        self.assertTrue(np.allclose(res3[0], lastimage))
        scaledimage = np.clip(lastimage, 10e-3, np.inf)
        scaledimage = np.log10(scaledimage)
        self.assertTrue(np.allclose(res3[1], scaledimage))

        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update(dict(
            mode='expert',
            source='tangofile',
            configuration='test/testimageserver/00/LastImageTaken,,'
            '{"/ramdisk/": "/gpfs/"},False,False',
            instance='tgtest',
            tool='roi',
            # log='debug',
            log='info',
            scaling='log',
            levels='-20.0,20.0',
            gradient='thermal',
            tangodevice='test/lavuecontroller/00',
            connected=True,
            autofactor=None
        ))
        self.compareStates(ls, dls,
                           ['viewrange', '__timestamp__', 'doordevice'])

    def test_readtangofile_urlimage_h5file(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        self.__lcsu.proxy.Init()
        self.__tisu.proxy.Init()
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
            self.__lavuestate = None
            # lastimage = self.__tisu.proxy.ReadyEventImage.T
            lastimage = None
            self.__tangofilepath = self._fname
            self.__tangofilepattern = "/entry/instrument/detector/data"
            options = argparse.Namespace(
                mode='expert',
                source='tangofile',
                configuration='test/testimageserver/00/LastImageTaken',
                instance='tgtest',
                tool='intensity',
                # log='debug',
                log='info',
                scaling='linear',
                levels='0,1000',
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

            qtck1 = QtChecker(app, dialog, True, sleep=100,
                              withitem=EnsureOmniThread)
            qtck2 = QtChecker(app, dialog, True, sleep=100,
                              withitem=EnsureOmniThread)
            qtck3 = QtChecker(app, dialog, True, sleep=100,
                              withitem=EnsureOmniThread)
            qtck1.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                ExtCmdCheck(self, "getLavueState"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                ExtCmdCheck(self, "takeNewTangoFileNXSURLImage"),
            ])
            qtck2.setChecks([
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__sourcewg.isConnected"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.rawData"),
                CmdCheck(
                    "_MainWindow__lavue._LiveViewer__imagewg.currentData"),
                ExtCmdCheck(self, "takeNewTangoFileNXSURLImage"),
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

            print("execute")
            qtck1.executeChecks(delay=6000)
            qtck2.executeChecks(delay=12000)
            status = qtck3.executeChecksAndClose(delay=18000)

            self.assertEqual(status, 0)

            qtck1.compareResults(
                self, [True, None, None, None, None], mask=[0, 0, 1, 1, 1])
            qtck2.compareResults(
                self, [True, None, None, None], mask=[0, 1, 1, 1])
            qtck3.compareResults(
                self, [None, None, None, False], mask=[1, 1, 0, 0])

            res1 = qtck1.results()
            res2 = qtck2.results()
            res3 = qtck3.results()
            self.assertEqual(res1[2], None)
            self.assertEqual(res1[3], None)
            # self.assertTrue(np.allclose(res1[2], lastimage))

            # scaledimage = np.clip(lastimage, 10e-3, np.inf)
            # scaledimage = np.log10(scaledimage)
            # self.assertTrue(np.allclose(res1[3], scaledimage))

            lastimage = res1[4].T
            if not np.allclose(res2[1], lastimage):
                print(res2[1])
                print(lastimage)
            self.assertTrue(np.allclose(res2[1], lastimage))
            self.assertTrue(np.allclose(res2[2], lastimage))

            lastimage = res2[3].T
            self.assertTrue(np.allclose(res3[0], lastimage))
            self.assertTrue(np.allclose(res3[1], lastimage))

            ls = json.loads(self.__lavuestate)
            dls = dict(self.__defaultls)
            dls.update(dict(
                mode='expert',
                source='tangofile',
                configuration='test/testimageserver/00/LastImageTaken,,'
                '{"/ramdisk/": "/gpfs/"},False,True',
                instance='tgtest',
                tool='intensity',
                # log='debug',
                log='info',
                scaling='linear',
                levels='0.0,1000.0',
                gradient='thermal',
                tangodevice='test/lavuecontroller/00',
                connected=True,
                autofactor=None
            ))
            self.compareStates(ls, dls,
                               ['viewrange', '__timestamp__', 'doordevice'])

        finally:
            self.closedetfile()
            if os.path.isfile(self._fname):
                os.remove(self._fname)


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()
