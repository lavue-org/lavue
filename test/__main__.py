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

try:
    try:
        import tango
    except ImportError:
        import PyTango as tango
    # if module tango avalable
    tango.Database()
    TANGO_AVAILABLE = True
except ImportError as e:
    TANGO_AVAILABLE = False
    print("tango is not available: %s" % e)

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
import HidraImageSource_test
import ASAPOImageSource_test
import HttpImageSource_test
import PyTineImageSource_test
import EpicsImageSource_test

if not H5CPP_AVAILABLE and not H5PY_AVAILABLE:
    raise Exception("Please install h5py or pni")


# list of available databases
DB_AVAILABLE = []

if TANGO_AVAILABLE:
    import LavueController_test
    import GeneralTool_test
    import SpecializedTool_test
    import DiffractogramTool_test
    import TangoAttrImageSource_test
    import TangoFileImageSource_test
    import ZMQStreamImageSource_test

if H5PY_AVAILABLE:
    import H5PYWriter_test
    import FileWriterH5PY_test
    import ASAPOImageSourceH5PY_test
    import HidraImageSourceH5PY_test
if H5CPP_AVAILABLE:
    import H5CppWriter_test
    import FileWriterH5Cpp_test
    import CommandLineArgumentH5Cpp_test
    import ASAPOImageSourceH5Cpp_test
    import HidraImageSourceH5Cpp_test
    import NXSFileImageSource_test
if H5CPP_AVAILABLE and H5PY_AVAILABLE:
    import FileWriterH5CppH5PY_test


# main function
def main():

    # test server
    # ts = None
    # test suit
    basicsuite = unittest.TestSuite()
    generalsuite = unittest.TestSuite()
    specializedsuite = unittest.TestSuite()
    generalsuite = unittest.TestSuite()
    specializedsuite = unittest.TestSuite()
    diffractogramsuite = unittest.TestSuite()
    tangosuite = unittest.TestSuite()
    tangofilesuite = unittest.TestSuite()
    httpsuite = unittest.TestSuite()
    print("Using: %s" % qt_api)
    app = QtGui.QApplication([])
    CommandLineArgument_test.app = app
    HidraImageSource_test.app = app
    ASAPOImageSource_test.app = app
    HttpImageSource_test.app = app
    PyTineImageSource_test.app = app
    EpicsImageSource_test.app = app
    if TANGO_AVAILABLE:
        GeneralTool_test.app = app
        SpecializedTool_test.app = app
        DiffractogramTool_test.app = app
        TangoAttrImageSource_test.app = app
        TangoFileImageSource_test.app = app
        ZMQStreamImageSource_test.app = app
    if H5CPP_AVAILABLE:
        CommandLineArgumentH5Cpp_test.app = app
        NXSFileImageSource_test.app = app
        ASAPOImageSourceH5Cpp_test.app = app
        HidraImageSourceH5Cpp_test.app = app
    if H5PY_AVAILABLE:
        ASAPOImageSourceH5PY_test.app = app
        HidraImageSourceH5PY_test.app = app
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            CommandLineArgument_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            HidraImageSource_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            ASAPOImageSource_test))
    httpsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            HttpImageSource_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            PyTineImageSource_test))
    basicsuite.addTests(
        unittest.defaultTestLoader.loadTestsFromModule(
            EpicsImageSource_test))
    if H5PY_AVAILABLE:
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5PY_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5PYWriter_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                ASAPOImageSourceH5PY_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                HidraImageSourceH5PY_test))
    if H5CPP_AVAILABLE:
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSFileImageSource_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                CommandLineArgumentH5Cpp_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5Cpp_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                ASAPOImageSourceH5Cpp_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                HidraImageSourceH5Cpp_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5CppWriter_test))
    if H5CPP_AVAILABLE and H5PY_AVAILABLE:
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5CppH5PY_test))
    if TANGO_AVAILABLE:
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                LavueController_test))
        generalsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                GeneralTool_test))
        specializedsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                SpecializedTool_test))
        diffractogramsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                DiffractogramTool_test))
        tangosuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                TangoAttrImageSource_test))
        tangofilesuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                TangoFileImageSource_test))
        basicsuite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                ZMQStreamImageSource_test))

    # test runner
    runner = unittest.TextTestRunner()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'args', metavar='name', type=str, nargs='*',
        help='suite names: all, basic, tangosource, httpsource, '
        ' generaltools, specializedtools, diffractogram'
        ', tangofilesource'
    )
    options = parser.parse_args()

    namesuite = {
        "basic": [basicsuite],
        "httpsource": [httpsuite],
        "tangosource": [tangosuite],
        "tangofilesource": [tangofilesuite],
        "generaltools": [generalsuite],
        "specializedtools": [specializedsuite],
        "diffractogram": [diffractogramsuite],
        "all": [basicsuite, tangosuite, httpsuite,
                generalsuite, specializedsuite,
                diffractogramsuite],
    }

    # print(options.args)
    if not options.args:
        options.args = ["all"]

    ts = []
    for nm in options.args:
        if nm in namesuite.keys():
            ts.extend(namesuite[nm])

    suite = unittest.TestSuite(ts)

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
