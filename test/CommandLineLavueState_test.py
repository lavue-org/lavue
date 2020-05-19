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

#  Qt-application
app = None

# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    unicode = str
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

        self.__lcsu = ControllerSetUp()

        #: (:obj:`str`) lavue state
        self.__lavuestate = None

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
#        self.__seed = 332115341842367128541506422124286219441
        self.__rnd = random.Random(self.__seed)
        self.__dialog = None

        self.__defaultls = {
            '__timestamp__': 0.0,
            'viewrange': '0,0,0,0',
            'mbuffer': None,
            'doordevice': '',
            'filters': 0,
            'analysisdevice': '',
            'log': 'info',
            'instance': 'test',
            'gradient': 'grey',
            'imagefile': '',
            'source': 'test',
            'version': lavuelib.__version__,
            'dsreduction': 'max',
            'transformation': 'none',
            'channel': '',
            'tool': 'intensity',
            'dsfactor': 1,
            'scaling': 'sqrt',
            'levels': '',
            'connected': False,
            'bkgfile': '',
            'offset': '',
            'configuration': '',
            'tangodevice': 'test/lavuecontroller/00',
            'maskhighvalue': '',
            'maskfile': '',
            'rangewindow': [None, None, None, None],
            'mode': 'user',
            'autofactor': ''}

    def compareStates(self, state, defstate=None, exclude=None):
        if defstate is None:
            defstate = self.__defaultls
        if exclude is None:
            exclude = ['viewrange', '__timestamp__',
                       'configuration', 'source']
        for ky, vl in defstate.items():
            if ky not in exclude:
                if state[ky] != vl:
                    print("%s: %s %s" % (ky, state[ky], vl))
                self.assertEqual(state[ky], vl)

    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)
        self.__lcsu.setUp()

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()

    def closeDialog(self):
        if self.__dialog:
            self.__dialog.close()
            sys.stderr.write("closing a dialog\n")
            self.__dialog = None

    def getLavueState(self):
        self.__lavuestate = self.__lcsu.proxy.LavueState

    def getLavueStateAndClose(self):
        self.getLavueState()
        self.closeDialog()

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
        self.__dialog = dialog

        # loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(1000, self.getLavueStateAndClose)
        status = app.exec_()
        self.assertEqual(status, 0)
        ls = json.loads(self.__lavuestate)
        self.compareStates(ls)

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
        self.__dialog = dialog

        QtCore.QTimer.singleShot(1000, self.getLavueStateAndClose)
        status = app.exec_()
        self.assertEqual(status, 0)
        ls = json.loads(self.__lavuestate)
        dls = dict(self.__defaultls)
        dls.update({"connected": True, "source": "test"})
        self.compareStates(ls, dls, ['viewrange', '__timestamp__'])


if __name__ == '__main__':
    if app is None:
        app = QtGui.QApplication([])
    unittest.main()