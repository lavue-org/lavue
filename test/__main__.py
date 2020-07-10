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

# import os
import sys


from lavuelib.qtuic import qt_api
from pyqtgraph import QtGui
# from pyqtgraph import QtCore

try:
    import PyTango
    # if module PyTango avalable
    PyTango.Database()
    PYTANGO_AVAILABLE = True
except ImportError as e:
    PYTANGO_AVAILABLE = False
    print("PyTango is not available: %s" % e)

try:
    try:
        __import__("pni.io.nx.h5")
    except Exception:
        __import__("pni.nx.h5")
    # if module pni avalable
    PNI_AVAILABLE = True
except ImportError as e:
    PNI_AVAILABLE = False
    print("pni is not available: %s" % e)

try:
    __import__("h5py")
    # if module h5py avalable
    H5PY_AVAILABLE = True
except ImportError as e:
    H5PY_AVAILABLE = False
    print("h5py is not available: %s" % e)

try:
    __import__("pninexus.h5cpp")
    # if module h5cpp avalable
    H5CPP_AVAILABLE = True
except ImportError as e:
    H5CPP_AVAILABLE = False
    print("h5cpp is not available: %s" % e)


import unittest
import CommandLineArgument_test

if not PNI_AVAILABLE and not H5PY_AVAILABLE:
    raise Exception("Please install h5py or pni")

# if PNI_AVAILABLE:
# if H5PY_AVAILABLE:
# if PNI_AVAILABLE and H5PY_AVAILABLE:


# list of available databases
DB_AVAILABLE = []


if PYTANGO_AVAILABLE:
    import LavueController_test
    import CommandLineLavueState_test
    import TangoAttrImageSource_test
    import ZMQStreamImageSource_test


if PNI_AVAILABLE:
    import FileWriter_test
    import PNIWriter_test
if H5PY_AVAILABLE:
    import H5PYWriter_test
    import FileWriterH5PY_test
if H5CPP_AVAILABLE:
    import H5CppWriter_test
    import FileWriterH5Cpp_test
if PNI_AVAILABLE and H5PY_AVAILABLE:
    import FileWriterPNIH5PY_test
# if PNI_AVAILABLE and H5Cpp_AVAILABLE:
#     import FileWriterPNIH5Cpp_test
# if H5CPP_AVAILABLE and H5PY_AVAILABLE:
#     import FileWriterH5CppH5PY_test


# main function
def main():

    # test server
    # ts = None
    # test suit
    suite = unittest.TestSuite()
    print("Using: %s" % qt_api)
    app = QtGui.QApplication([])
    CommandLineArgument_test.app = app
    CommandLineLavueState_test.app = app
    suite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            CommandLineArgument_test))
    if PNI_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(FileWriter_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(PNIWriter_test))
    if H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5PY_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5PYWriter_test))
    if H5CPP_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5Cpp_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5CppWriter_test))
    if PNI_AVAILABLE and H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterPNIH5PY_test))
    if PYTANGO_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                LavueController_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                CommandLineLavueState_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                TangoAttrImageSource_test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                ZMQStreamImageSource_test))

    # test runner
    runner = unittest.TextTestRunner()
    # test result

    tresult = runner.run(suite)
    print("Errors: %s" % tresult.errors)
    print("Failures: %s" % tresult.failures)
    print("Skipped: %s" % tresult.skipped)
    print("UnexpectedSuccesses: %s" % tresult.unexpectedSuccesses)
    print("ExpectedFailures: %s" % tresult.expectedFailures)
    result = tresult.wasSuccessful()
    print("Result: %s" % result)
    with open('testresult.txt', 'w') as fl:
        fl.write(str(int(not result)) + '\n')
    sys.exit(not result)


if __name__ == "__main__":
    main()
