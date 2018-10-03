#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
# \package test nexdatas
# \file runtest.py
# the unittest runner
#

# import os
import sys

try:
    import PyTango
    # if module PyTango avalable
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

if not PNI_AVAILABLE and not H5PY_AVAILABLE:
    raise Exception("Please install h5py or pni")

# if PNI_AVAILABLE:
# if H5PY_AVAILABLE:
# if PNI_AVAILABLE and H5PY_AVAILABLE:


# list of available databases
DB_AVAILABLE = []

db = PyTango.Database()

if PNI_AVAILABLE:
    import FileWriter_test
    import PNIWriter_test
if H5PY_AVAILABLE:
    import H5PYWriter_test
    import FileWriterH5PY_test
if H5PY_AVAILABLE:
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

    # test runner
    runner = unittest.TextTestRunner()
    # test result
    result = runner.run(suite).wasSuccessful()
    sys.exit(not result)

    #   if ts:
    #       ts.tearDown()


if __name__ == "__main__":
    main()
