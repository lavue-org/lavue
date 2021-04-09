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
import struct
import random
import binascii
import string
import h5py
import time
import io

import lavuelib.filewriter as FileWriter
import lavuelib.h5pywriter as H5PYWriter

try:
    from pninexus import h5cpp
    H5CPP = True
except ImportError:
    H5CPP = False

H5PYMAJOR, H5PYMINOR, H5PYPATCH = h5py.__version__.split(".", 2)

if int(H5PYMAJOR) > 1 or (int(H5PYMAJOR) == 1 and int(H5PYMINOR) > 4):
    SWMR = True
else:
    SWMR = False

if int(H5PYMAJOR) > 3 or (int(H5PYMAJOR) == 2 and int(H5PYMINOR) >= 9):
    MEMBUF = True
else:
    MEMBUF = False


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

if sys.version_info > (3,):
    long = int


class testwriter(object):

    def __init__(self):
        """ constructor
        """
        self.commands = []
        self.params = []
        self.result = None

    def open_file(self, filename, readonly=False):
        """ open the new file
        """
        self.commands.append("open_file")
        self.params.append([filename, readonly])
        return self.result

    def create_file(self, filename, overwrite=False):
        """ create a new file
        """
        self.commands.append("create_file")
        self.params.append([filename, overwrite])
        return self.result

    def link(self, target, parent, name):
        """ create link
        """
        self.commands.append("link")
        self.params.append([target, parent, name])
        return self.result

    def data_filter(self):
        self.commands.append("data_filter")
        self.params.append([])
        return self.result


# test fixture
class H5PYWriterTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        try:
            self.__seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            self.__seed = long(time.time() * 256)
#        self.__seed =241361343400098333007607831038323262554

        self.__rnd = random.Random(self.__seed)

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except Exception:
            error = True
        self.assertEqual(error, True)

    # float list tester
    def myAssertFloatList(self, list1, list2, error=0.0):

        self.assertEqual(len(list1), len(list2))
        for i, el in enumerate(list1):
            if abs(el - list2[i]) >= error:
                print("EL %s %s %s" % (el, list2[i], error))
            self.assertTrue(abs(el - list2[i]) < error)

    # float image tester
    def myAssertImage(self, image1, image2, error=None):

        self.assertEqual(len(image1), len(image2))
        for i in range(len(image1)):
            self.assertEqual(len(image1[i]), len(image2[i]))
            for j in range(len(image1[i])):
                if error is not None:
                    if abs(image1[i][j] - image2[i][j]) >= error:
                        print("EL %s %s %s" % (image1[i][j],
                                               image2[i][j], error))
                    self.assertTrue(abs(image1[i][j] - image2[i][j]) < error)
                else:
                    self.assertEqual(image1[i][j], image2[i][j])

    # float image tester
    def myAssertVector(self, image1, image2, error=None):

        self.assertEqual(len(image1), len(image2))
        for i in range(len(image1)):
            self.assertEqual(len(image1[i]), len(image2[i]))
            for j in range(len(image1[i])):
                self.assertEqual(len(image1[i][j]), len(image2[i][j]))
                for k in range(len(image1[i][j])):
                    if error is not None:
                        if abs(image1[i][j][k] - image2[i][j][k]) >= error:
                            print("EL %s %s %s" % (
                                image1[i][j][k], image2[i][j][k], error))
                        self.assertTrue(
                            abs(image1[i][j][k] - image2[i][j][k]) < error)
                    else:
                        self.assertEqual(image1[i][j][k], image2[i][j][k])

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.__seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    # constructor test
    # \brief It tests default settings
    def test_constructor(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        w = "weerew"
        el = FileWriter.FTObject(w)

        self.assertEqual(el.h5object, w)

    # default createfile test
    # \brief It tests default settings
    def test_default_createfile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)
        try:
            fl = H5PYWriter.create_file(self._fname)
            fl.close()
            fl = H5PYWriter.create_file(self._fname, True)
            fl.close()

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
                at.close()
            self.assertTrue(f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 0)
            f.close()
            fl.close()

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            self.assertEqual(
                f.attributes["file_name"][...], self._fname)
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.dtype, at.read()))
            self.assertTrue(f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 0)
            fl.close()
            fl.reopen()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 0)
            fl.close()

            self.myAssertRaise(
                Exception, H5PYWriter.create_file, self._fname)

            self.myAssertRaise(
                Exception, H5PYWriter.create_file, self._fname,
                False)

            fl2 = H5PYWriter.create_file(self._fname, True)
            fl2.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_default_loadfile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)
        try:
            fl = H5PYWriter.create_file(self._fname)
            fl.close()
            fl = H5PYWriter.create_file(self._fname, True)
            fl.close()

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
                at.close()
            self.assertTrue(f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 0)
            f.close()
            fl.close()

            with open(self._fname, "rb") as fh:
                buf = io.BytesIO(fh.read())

            if not H5PYWriter.is_image_file_supported():
                self.myAssertRaise(
                    Exception, H5PYWriter.load_file, buf, self._fname)
            else:
                fl = H5PYWriter.load_file(buf, self._fname, readonly=True)
                f = fl.root()
                self.assertEqual(5, len(f.attributes))
                self.assertEqual(
                    f.attributes["file_name"][...], self._fname)
                for at in f.attributes:
                    print("%s %s %s" % (at.name, at.dtype, at.read()))
                self.assertTrue(f.attributes["NX_class"][...], "NXroot")
                self.assertEqual(f.size, 0)
                fl.close()
                fl.reopen()
                self.assertEqual(5, len(f.attributes))
                for at in f.attributes:
                    print("%s %s %s" % (at.name, at.read(), at.dtype))
                self.assertEqual(
                    f.attributes["file_name"][...],
                    self._fname)
                self.assertTrue(f.attributes["NX_class"][...], "NXroot")
                self.assertEqual(f.size, 0)
                fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyfile(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        # overwrite = False
        nxfl = h5py.File(self._fname, "a", libver='latest')
        fl = H5PYWriter.H5PYFile(nxfl, self._fname)
        self.assertTrue(
            isinstance(fl, FileWriter.FTFile))

        self.assertEqual(fl.name, self._fname)
        self.assertEqual(fl.path, None)
        self.assertTrue(
            isinstance(fl.h5object, h5py.File))
        self.assertEqual(fl.parent, None)

        rt = fl.root()
        fl.flush()
        self.assertEqual(fl.h5object, rt.h5object)
        self.assertEqual(fl.is_valid, True)
        self.assertEqual(fl.h5object.name is not None, True)
        self.assertEqual(fl.readonly, False)
        self.assertEqual(fl.h5object.mode in ["r"], False)
        fl.close()
        self.assertEqual(fl.is_valid, False)
        self.assertEqual(fl.readonly, None)

        fl.reopen()
        self.assertEqual(fl.name, self._fname)
        self.assertEqual(fl.path, None)
        self.assertTrue(
            isinstance(fl.h5object, h5py.File))
        self.assertEqual(fl.parent, None)
        self.assertEqual(fl.readonly, False)
        self.assertEqual(fl.h5object.mode in ["r"], False)

        fl.close()

        fl.reopen(True)
        self.assertEqual(fl.name, self._fname)
        self.assertEqual(fl.path, None)
        self.assertTrue(
            isinstance(fl.h5object, h5py.File))
        self.assertEqual(fl.parent, None)
        self.assertEqual(fl.readonly, True)
        self.assertEqual(fl.h5object.mode in ["r"], True)

        fl.close()

        self.myAssertRaise(
            Exception, fl.reopen, True, True)
        if fl.hasswmr():
            fl.reopen(False, True)
        else:
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

        fl = H5PYWriter.open_file(self._fname, readonly=True)
        f = fl.root()
        self.assertEqual(1, len(f.attributes))
        for at in f.attributes:
            print("%s %s %s" % (at.name, at.read(), at.dtype))
#        self.assertEqual(
#            f.attributes["file_name"][...],
#            self._fname)
#        self.assertTrue(
#            f.attributes["NX_class"][...], "NXroot")
        self.assertEqual(f.size, 0)
        fl.close()

        os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pygroup(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            nt = rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            strscalar = entry.create_field("strscalar", "string")
            floatscalar = entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            strspec = ins.create_field("strspec", "string", [10], [6])
            floatspec = ins.create_field("floatspec", "float32", [20], [16])
            intspec = ins.create_field("intspec", "int64", [30], [5])
            strimage = det.create_field("strimage", "string", [2, 2], [2, 1])
            floatimage = det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            intimage = det.create_field("intimage", "uint32", [0, 30], [1, 30])
            strvec = det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            floatvec = det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            intvec = det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            lkintimage = H5PYWriter.link(
                "/entry12345/instrument/detector/intimage", dt, "lkintimage")
            lkfloatvec = H5PYWriter.link(
                "/entry12345/instrument/detector/floatvec", dt, "lkfloatvec")
            lkintspec = H5PYWriter.link(
                "/entry12345/instrument/intspec", dt, "lkintspec")
            lkdet = H5PYWriter.link(
                "/entry12345/instrument/detector", dt, "lkdet")
            lkno = H5PYWriter.link(
                "/notype/unknown", dt, "lkno")

            attr0 = rt.attributes
            attr1 = entry.attributes

            print(attr0.h5object)
            self.assertTrue(isinstance(attr0, H5PYWriter.H5PYAttributeManager))
            print(dir(attr0.h5object))
            self.assertTrue(
                isinstance(attr0.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr1, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr1.h5object, h5py.AttributeManager))

            print(dir(rt))
            self.assertTrue(
                isinstance(rt, H5PYWriter.H5PYGroup))
            self.assertEqual(rt.name, "/")
            self.assertEqual(rt.path, "/")
            attr = rt.attributes
            self.assertEqual(attr["NX_class"][...], "NXroot")
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(rt.parent, fl)
            self.assertEqual(rt.size, 2)
            self.assertEqual(rt.exists("entry12345"), True)
            self.assertEqual(rt.exists("notype"), True)
            self.assertEqual(rt.exists("strument"), False)

            for rr in rt:
                print(rr.name)

            self.assertTrue(
                isinstance(entry, H5PYWriter.H5PYGroup))
            self.assertEqual(entry.name, "entry12345")
            self.assertEqual(entry.path, "/entry12345:NXentry")
            self.assertEqual(
                len(entry.h5object.attrs), 1)
            attr = entry.attributes
            self.assertEqual(attr["NX_class"][...], "NXentry")
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(entry.parent, rt)
            self.assertEqual(entry.size, 5)
            self.assertEqual(entry.exists("instrument"), True)
            self.assertEqual(entry.exists("data"), True)
            self.assertEqual(entry.exists("floatscalar"), True)
            self.assertEqual(entry.exists("intscalar"), True)
            self.assertEqual(entry.exists("strscalar"), True)
            self.assertEqual(entry.exists("strument"), False)

            self.assertTrue(
                isinstance(nt, H5PYWriter.H5PYGroup))
            self.assertEqual(nt.name, "notype")
            self.assertEqual(nt.path, "/notype")
            print(list(nt.h5object.attrs.keys()))
            self.assertEqual(
                len(nt.h5object.attrs), 0)
            attr = nt.attributes
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(nt.is_valid, True)
            self.assertEqual(nt.parent, rt)
            self.assertEqual(nt.size, 0)
            self.assertEqual(nt.exists("strument"), False)

            self.assertTrue(
                isinstance(ins, H5PYWriter.H5PYGroup))
            self.assertEqual(ins.name, "instrument")
            self.assertEqual(
                ins.path, "/entry12345:NXentry/instrument:NXinstrument")
            self.assertEqual(
                len(ins.h5object.attrs), 1)
            attr = ins.attributes
            self.assertEqual(attr["NX_class"][...], "NXinstrument")
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(ins.is_valid, True)
            self.assertEqual(ins.parent, entry)
            self.assertEqual(ins.size, 4)
            self.assertEqual(ins.exists("detector"), True)
            self.assertEqual(ins.exists("floatspec"), True)
            self.assertEqual(ins.exists("intspec"), True)
            self.assertEqual(ins.exists("strspec"), True)
            self.assertEqual(ins.exists("strument"), False)

            kids = set()
            for en in ins:
                kids.add(en.name)

            self.assertEqual(kids, set(["detector", "floatspec",
                                        "intspec", "strspec"]))

            ins_op = entry.open("instrument")
            self.assertTrue(
                isinstance(ins_op, H5PYWriter.H5PYGroup))
            self.assertEqual(ins_op.name, "instrument")
            self.assertEqual(
                ins_op.path, "/entry12345:NXentry/instrument:NXinstrument")
            self.assertEqual(
                len(ins_op.h5object.attrs), 1)
            attr = ins_op.attributes
            self.assertEqual(attr["NX_class"][...], "NXinstrument")
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(ins_op.is_valid, True)
            self.assertEqual(ins_op.parent, entry)
            self.assertEqual(ins_op.size, 4)
            self.assertEqual(ins_op.exists("detector"), True)
            self.assertEqual(ins_op.exists("floatspec"), True)
            self.assertEqual(ins_op.exists("intspec"), True)
            self.assertEqual(ins_op.exists("strspec"), True)
            self.assertEqual(ins_op.exists("strument"), False)

            kids = set()
            for en in ins_op:
                kids.add(en.name)

            self.assertEqual(kids, set(["detector", "floatspec",
                                        "intspec", "strspec"]))

            ins_lk = entry.open_link("instrument")
            self.assertTrue(
                isinstance(ins_lk, H5PYWriter.H5PYLink))
            self.assertEqual(ins_lk.name, "instrument")
            self.assertEqual(
                ins_lk.path, "/entry12345:NXentry/instrument")
            self.assertEqual(ins_lk.is_valid, True)
            self.assertEqual(ins_lk.parent, entry)

            self.assertTrue(
                isinstance(det, H5PYWriter.H5PYGroup))
            self.assertEqual(det.name, "detector")
            self.assertEqual(
                det.path,
                "/entry12345:NXentry/instrument:NXinstrument/"
                "detector:NXdetector")
            self.assertEqual(
                len(det.h5object.attrs), 1)
            attr = det.attributes
            self.assertEqual(attr["NX_class"][...], "NXdetector")
            self.assertTrue(
                isinstance(attr, H5PYWriter.H5PYAttributeManager))
            self.assertEqual(det.is_valid, True)
            self.assertEqual(det.parent, ins)
            self.assertEqual(det.size, 6)
            self.assertEqual(det.exists("strimage"), True)
            self.assertEqual(det.exists("intvec"), True)
            self.assertEqual(det.exists("floatimage"), True)
            self.assertEqual(det.exists("floatvec"), True)
            self.assertEqual(det.exists("intimage"), True)
            self.assertEqual(det.exists("strvec"), True)
            self.assertEqual(det.exists("strument"), False)

            kids = set()
            for en in det:
                kids.add(en.name)
            print(kids)

            self.assertEqual(
                kids,
                set(['strimage', 'intvec', 'floatimage',
                     'floatvec', 'intimage', 'strvec']))

            self.assertTrue(isinstance(strscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strscalar.h5object, h5py.Dataset))
            self.assertEqual(strscalar.name, 'strscalar')
            self.assertEqual(strscalar.path, '/entry12345:NXentry/strscalar')
            self.assertEqual(strscalar.dtype, 'string')
            self.assertEqual(strscalar.shape, ())

            self.assertTrue(isinstance(floatscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatscalar.h5object, h5py.Dataset))
            self.assertEqual(floatscalar.name, 'floatscalar')
            self.assertEqual(
                floatscalar.path, '/entry12345:NXentry/floatscalar')
            self.assertEqual(floatscalar.dtype, 'float64')
            self.assertEqual(floatscalar.shape, (1,))

            self.assertTrue(isinstance(intscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intscalar.h5object, h5py.Dataset))
            self.assertEqual(intscalar.name, 'intscalar')
            self.assertEqual(intscalar.path, '/entry12345:NXentry/intscalar')
            self.assertEqual(intscalar.dtype, 'uint64')
            self.assertEqual(intscalar.shape, (1,))

            self.assertTrue(isinstance(strspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strspec.h5object, h5py.Dataset))
            self.assertEqual(strspec.name, 'strspec')
            self.assertEqual(
                strspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/strspec')
            self.assertEqual(strspec.dtype, 'string')
            self.assertEqual(strspec.shape, (10,))

            self.assertTrue(isinstance(floatspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatspec.h5object, h5py.Dataset))
            self.assertEqual(floatspec.name, 'floatspec')
            self.assertEqual(
                floatspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/floatspec')
            self.assertEqual(floatspec.dtype, 'float32')
            self.assertEqual(floatspec.shape, (20,))

            self.assertTrue(isinstance(intspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intspec.h5object, h5py.Dataset))
            self.assertEqual(intspec.name, 'intspec')
            self.assertEqual(
                intspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/intspec')
            self.assertEqual(intspec.dtype, 'int64')
            self.assertEqual(intspec.shape, (30,))

            self.assertTrue(isinstance(strimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strimage.h5object, h5py.Dataset))
            self.assertEqual(strimage.name, 'strimage')
            self.assertEqual(
                strimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strimage')
            self.assertEqual(strimage.dtype, 'string')
            self.assertEqual(strimage.shape, (2, 2))

            self.assertTrue(isinstance(floatimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatimage.h5object, h5py.Dataset))
            self.assertEqual(floatimage.name, 'floatimage')
            self.assertEqual(
                floatimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatimage')
            self.assertEqual(floatimage.dtype, 'float64')
            self.assertEqual(floatimage.shape, (20, 10))

            self.assertTrue(isinstance(intimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intimage.h5object, h5py.Dataset))
            self.assertEqual(intimage.name, 'intimage')
            self.assertEqual(
                intimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intimage')
            self.assertEqual(intimage.dtype, 'uint32')
            self.assertEqual(intimage.shape, (0, 30))

            self.assertTrue(isinstance(strvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strvec.h5object, h5py.Dataset))
            self.assertEqual(strvec.name, 'strvec')
            self.assertEqual(
                strvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strvec')
            self.assertEqual(strvec.dtype, 'string')
            self.assertEqual(strvec.shape, (0, 2, 2))

            self.assertTrue(isinstance(floatvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatvec.h5object, h5py.Dataset))
            self.assertEqual(floatvec.name, 'floatvec')
            self.assertEqual(
                floatvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatvec')
            self.assertEqual(floatvec.dtype, 'float64')
            self.assertEqual(floatvec.shape, (1, 20, 10))

            self.assertTrue(isinstance(intvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intvec.h5object, h5py.Dataset))
            self.assertEqual(intvec.name, 'intvec')
            self.assertEqual(
                intvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intvec')
            self.assertEqual(intvec.dtype, 'uint32')
            self.assertEqual(intvec.shape, (0, 2, 30))

            strscalar_op = entry.open("strscalar")
            floatscalar_op = entry.open("floatscalar")
            intscalar_op = entry.open("intscalar")
            strspec_op = ins.open("strspec")
            floatspec_op = ins.open("floatspec")
            intspec_op = ins.open("intspec")
            strimage_op = det.open("strimage")
            floatimage_op = det.open("floatimage")
            intimage_op = det.open("intimage")
            strvec_op = det.open("strvec")
            floatvec_op = det.open("floatvec")
            intvec_op = det.open("intvec")

            self.assertTrue(isinstance(strscalar_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strscalar_op.h5object, h5py.Dataset))
            self.assertEqual(strscalar_op.name, 'strscalar')
            self.assertEqual(
                strscalar_op.path, '/entry12345:NXentry/strscalar')
            self.assertEqual(strscalar_op.dtype, 'string')
            self.assertEqual(strscalar_op.shape, ())

            self.assertTrue(isinstance(floatscalar_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatscalar_op.h5object, h5py.Dataset))
            self.assertEqual(floatscalar_op.name, 'floatscalar')
            self.assertEqual(
                floatscalar_op.path, '/entry12345:NXentry/floatscalar')
            self.assertEqual(floatscalar_op.dtype, 'float64')
            self.assertEqual(floatscalar_op.shape, (1,))

            self.assertTrue(isinstance(intscalar_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intscalar_op.h5object, h5py.Dataset))
            self.assertEqual(intscalar_op.name, 'intscalar')
            self.assertEqual(
                intscalar_op.path, '/entry12345:NXentry/intscalar')
            self.assertEqual(intscalar_op.dtype, 'uint64')
            self.assertEqual(intscalar_op.shape, (1,))

            self.assertTrue(isinstance(strspec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strspec_op.h5object, h5py.Dataset))
            self.assertEqual(strspec_op.name, 'strspec')
            self.assertEqual(
                strspec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/strspec')
            self.assertEqual(strspec_op.dtype, 'string')
            self.assertEqual(strspec_op.shape, (10,))

            self.assertTrue(isinstance(floatspec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatspec_op.h5object, h5py.Dataset))
            self.assertEqual(floatspec_op.name, 'floatspec')
            self.assertEqual(
                floatspec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/floatspec')
            self.assertEqual(floatspec_op.dtype, 'float32')
            self.assertEqual(floatspec_op.shape, (20,))

            self.assertTrue(isinstance(intspec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intspec_op.h5object, h5py.Dataset))
            self.assertEqual(intspec_op.name, 'intspec')
            self.assertEqual(
                intspec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/intspec')
            self.assertEqual(intspec_op.dtype, 'int64')
            self.assertEqual(intspec_op.shape, (30,))

            self.assertTrue(isinstance(strimage_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strimage_op.h5object, h5py.Dataset))
            self.assertEqual(strimage_op.name, 'strimage')
            self.assertEqual(
                strimage_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strimage')
            self.assertEqual(strimage_op.dtype, 'string')
            self.assertEqual(strimage_op.shape, (2, 2))

            self.assertTrue(isinstance(floatimage_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatimage_op.h5object, h5py.Dataset))
            self.assertEqual(floatimage_op.name, 'floatimage')
            self.assertEqual(
                floatimage_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatimage')
            self.assertEqual(floatimage_op.dtype, 'float64')
            self.assertEqual(floatimage_op.shape, (20, 10))

            self.assertTrue(isinstance(intimage_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intimage_op.h5object, h5py.Dataset))
            self.assertEqual(intimage_op.name, 'intimage')
            self.assertEqual(
                intimage_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intimage')
            self.assertEqual(intimage_op.dtype, 'uint32')
            self.assertEqual(intimage_op.shape, (0, 30))

            self.assertTrue(isinstance(strvec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strvec_op.h5object, h5py.Dataset))
            self.assertEqual(strvec_op.name, 'strvec')
            self.assertEqual(
                strvec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strvec')
            self.assertEqual(strvec_op.dtype, 'string')
            self.assertEqual(strvec_op.shape, (0, 2, 2))

            self.assertTrue(isinstance(floatvec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatvec_op.h5object, h5py.Dataset))
            self.assertEqual(floatvec_op.name, 'floatvec')
            self.assertEqual(
                floatvec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatvec')
            self.assertEqual(floatvec_op.dtype, 'float64')
            self.assertEqual(floatvec_op.shape, (1, 20, 10))

            self.assertTrue(isinstance(intvec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intvec_op.h5object, h5py.Dataset))
            self.assertEqual(intvec_op.name, 'intvec')
            self.assertEqual(
                intvec_op.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intvec')
            self.assertEqual(intvec_op.dtype, 'uint32')
            self.assertEqual(intvec_op.shape, (0, 2, 30))
            self.assertEqual(intvec_op.parent, det)

            self.assertTrue(isinstance(lkintimage, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkintimage.h5object, h5py.SoftLink))
            self.assertTrue(lkintimage.target_path.endswith(
                "%s://entry12345/instrument/detector/intimage" % self._fname))
            self.assertEqual(
                lkintimage.path,
                "/entry12345:NXentry/data:NXdata/lkintimage")

            self.assertTrue(isinstance(lkfloatvec, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkfloatvec.h5object, h5py.SoftLink))
            self.assertTrue(lkfloatvec.target_path.endswith(
                "%s://entry12345/instrument/detector/floatvec" % self._fname))
            self.assertEqual(
                lkfloatvec.path,
                "/entry12345:NXentry/data:NXdata/lkfloatvec")

            self.assertTrue(isinstance(lkintspec, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkintspec.h5object, h5py.SoftLink))
            self.assertTrue(lkintspec.target_path.endswith(
                "%s://entry12345/instrument/intspec" % self._fname))
            self.assertEqual(
                lkintspec.path,
                "/entry12345:NXentry/data:NXdata/lkintspec")

            self.assertTrue(isinstance(lkdet, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkdet.h5object, h5py.SoftLink))
            self.assertTrue(lkdet.target_path.endswith(
                "%s://entry12345/instrument/detector" % self._fname))
            self.assertEqual(
                lkdet.path,
                "/entry12345:NXentry/data:NXdata/lkdet")

            self.assertTrue(isinstance(lkno, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkno.h5object, h5py.SoftLink))
            self.assertTrue(lkno.target_path.endswith(
                "%s://notype/unknown" % self._fname))
            self.assertEqual(
                lkno.path,
                "/entry12345:NXentry/data:NXdata/lkno")

            lkintimage_op = dt.open("lkintimage")
            lkfloatvec_op = dt.open("lkfloatvec")
            lkintspec_op = dt.open("lkintspec")
            dt.open("lkdet")
            lkno_op = dt.open("lkno")

            self.assertTrue(isinstance(lkintimage_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(lkintimage_op.h5object, h5py.Dataset))
            self.assertEqual(lkintimage_op.name, 'lkintimage')
            self.assertEqual(
                lkintimage_op.path,
                '/entry12345:NXentry/data:NXdata/lkintimage')
            self.assertEqual(lkintimage_op.dtype, 'uint32')
            self.assertEqual(lkintimage_op.shape, (0, 30))

            self.assertTrue(isinstance(lkfloatvec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(lkfloatvec_op.h5object, h5py.Dataset))
            self.assertEqual(lkfloatvec_op.name, 'lkfloatvec')
            self.assertEqual(lkfloatvec_op.path,
                             '/entry12345:NXentry/data:NXdata/lkfloatvec')
            self.assertEqual(lkfloatvec_op.dtype, 'float64')
            self.assertEqual(lkfloatvec_op.shape, (1, 20, 10))

            self.assertTrue(
                isinstance(lkintspec_op, H5PYWriter.H5PYField))
            self.assertTrue(
                isinstance(lkintspec_op.h5object, h5py.Dataset))
            self.assertEqual(lkintspec_op.name, 'lkintspec')
            self.assertEqual(lkintspec_op.path,
                             '/entry12345:NXentry/data:NXdata/lkintspec')
            self.assertEqual(lkintspec_op.dtype, 'int64')
            self.assertEqual(lkintspec_op.shape, (30,))

            self.assertTrue(isinstance(lkno_op, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkno_op.h5object, h5py.SoftLink))
            self.assertTrue(lkno_op.target_path.endswith(
                "%s://notype/unknown" % self._fname))
            self.assertEqual(
                lkno_op.path,
                "/entry12345:NXentry/data:NXdata/lkno")

            entry.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, False)
            self.assertEqual(dt.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyfield_scalar(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            strscalar = entry.create_field("strscalar", "string")
            floatscalar = entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertTrue(isinstance(strscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strscalar.h5object, h5py.Dataset))
            self.assertEqual(strscalar.name, 'strscalar')
            self.assertEqual(strscalar.h5object.name, '/entry12345/strscalar')
            self.assertEqual(strscalar.path, '/entry12345:NXentry/strscalar')
            self.assertEqual(strscalar.dtype, 'string')
            self.assertEqual(strscalar.h5object.dtype.name, 'object')
            self.assertEqual(strscalar.shape, ())
            self.assertEqual(strscalar.h5object.shape, ())
            self.assertEqual(strscalar.is_valid, True)
            self.assertEqual(strscalar.shape, ())
            self.assertEqual(strscalar.h5object.shape, ())

            vl = ["1234", "Somethin to test 1234", "2342;23ml243",
                  "sd", "q234", "12 123 ", "aqds ", "Aasdas"]
            strscalar[...] = vl[0]
            self.assertEqual(strscalar.read(), vl[0])
            strscalar.write(vl[1])
            self.assertEqual(strscalar[()], vl[1])
            strscalar[()] = vl[2]
            self.assertEqual(strscalar[...], vl[2])
            strscalar[()] = vl[0]

            strscalar.grow()
            self.assertEqual(strscalar.shape, ())
            self.assertEqual(strscalar.h5object.shape, ())

            self.assertEqual(strscalar[()], vl[0])
            strscalar[()] = vl[3]
            self.assertEqual(strscalar[()], vl[3])

            # strscalar.grow(ext=2)
            # self.assertEqual(strscalar.shape, (4,))
            # self.assertEqual(strscalar.h5object.shape, (4,))
            # strscalar[1:4] = vl[1:4]
            # self.assertEqual(list(strscalar.read()), vl[0:4])
            # self.assertEqual(list(strscalar[0:2]), vl[0:2])

            # strscalar.grow(0, 3)
            # self.assertEqual(strscalar.shape, (7,))
            # self.assertEqual(strscalar.h5object.shape, (7,))
            # strscalar.write(vl[0:7])
            # self.assertEqual(list(strscalar.read()), vl[0:7])
            # self.assertEqual(list(strscalar[...]), vl[0:7])

            attrs = strscalar.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            print(type(attrs.h5object))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, strscalar)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(floatscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatscalar.h5object, h5py.Dataset))
            self.assertEqual(floatscalar.name, 'floatscalar')
            self.assertEqual(
                floatscalar.h5object.name, '/entry12345/floatscalar')
            self.assertEqual(
                floatscalar.path, '/entry12345:NXentry/floatscalar')
            self.assertEqual(floatscalar.dtype, 'float64')
            self.assertEqual(floatscalar.h5object.dtype, 'float64')
            self.assertEqual(floatscalar.shape, (1,))
            self.assertEqual(floatscalar.h5object.shape, (1,))

            vl = [1123.34, 3234.3, 234.33, -4.4, 34, 0.0, 4.3, 434.5, 23.0, 0]

            floatscalar[...] = vl[0]
            self.assertEqual(floatscalar.read(), vl[0])
            floatscalar.write(vl[1])
            self.assertEqual(floatscalar[0], vl[1])
            floatscalar[0] = vl[2]
            self.assertEqual(floatscalar[...], vl[2])
            floatscalar[0] = vl[0]

            floatscalar.grow()
            self.assertEqual(floatscalar.shape, (2,))
            self.assertEqual(floatscalar.h5object.shape, (2,))

            self.assertEqual(floatscalar[0], vl[0])
            floatscalar[1] = vl[3]
            self.assertEqual(list(floatscalar[...]), [vl[0], vl[3]])

            floatscalar.grow(ext=2)
            self.assertEqual(floatscalar.shape, (4,))
            self.assertEqual(floatscalar.h5object.shape, (4,))
            floatscalar[1:4] = vl[1:4]
            self.assertEqual(list(floatscalar.read()), vl[0:4])
            self.assertEqual(list(floatscalar[0:2]), vl[0:2])

            floatscalar.grow(0, 3)
            self.assertEqual(floatscalar.shape, (7,))
            self.assertEqual(floatscalar.h5object.shape, (7,))
            floatscalar.write(vl[0:7])
            self.assertEqual(list(floatscalar.read()), vl[0:7])
            self.assertEqual(list(floatscalar[...]), vl[0:7])

            attrs = floatscalar.attributes
            self.assertTrue(isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, floatscalar)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(intscalar, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intscalar.h5object, h5py.Dataset))
            self.assertEqual(intscalar.name, 'intscalar')
            self.assertEqual(intscalar.h5object.name, '/entry12345/intscalar')
            self.assertEqual(intscalar.path, '/entry12345:NXentry/intscalar')
            self.assertEqual(intscalar.dtype, 'uint64')
            self.assertEqual(intscalar.h5object.dtype, 'uint64')
            self.assertEqual(intscalar.shape, (1,))
            self.assertEqual(intscalar.h5object.shape, (1,))

            vl = [243, 43, 45, 34, 45, 54, 23234]

            intscalar[...] = vl[0]
            self.assertEqual(intscalar.read(), vl[0])
            intscalar.write(vl[1])
            self.assertEqual(intscalar[0], vl[1])
            intscalar[0] = vl[2]
            self.assertEqual(intscalar[...], vl[2])
            intscalar[0] = vl[0]

            intscalar.grow()
            self.assertEqual(intscalar.shape, (2,))
            self.assertEqual(intscalar.h5object.shape, (2,))

            self.assertEqual(intscalar[0], vl[0])
            intscalar[1] = vl[3]
            self.assertEqual(list(intscalar[...]), [vl[0], vl[3]])

            intscalar.grow(ext=2)
            self.assertEqual(intscalar.shape, (4,))
            self.assertEqual(intscalar.h5object.shape, (4,))
            intscalar[1:4] = vl[1:4]
            self.assertEqual(list(intscalar.read()), vl[0:4])
            self.assertEqual(list(intscalar[0:2]), vl[0:2])

            intscalar.grow(0, 3)
            self.assertEqual(intscalar.shape, (7,))
            self.assertEqual(intscalar.h5object.shape, (7,))
            intscalar.write(vl[0:7])
            self.assertEqual(list(intscalar.read()), vl[0:7])
            self.assertEqual(list(intscalar[...]), vl[0:7])

            attrs = intscalar.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, intscalar)
            self.assertEqual(len(attrs), 0)

            intscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(det.is_valid, True)
            self.assertEqual(intscalar.is_valid, False)
            self.assertEqual(attrs.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(det.is_valid, True)
            self.assertEqual(intscalar.is_valid, True)
            self.assertEqual(attrs.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            self.assertEqual(fl.default_field(), None)
            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyfield_spectrum(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            strspec = ins.create_field("strspec", "string", [10], [6])
            floatspec = ins.create_field("floatspec", "float32", [20], [16])
            intspec = ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertTrue(isinstance(strspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strspec.h5object, h5py.Dataset))
            self.assertEqual(strspec.name, 'strspec')
            self.assertEqual(
                strspec.h5object.name, '/entry12345/instrument/strspec')
            self.assertEqual(
                strspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/strspec')
            self.assertEqual(strspec.dtype, 'string')
            self.assertEqual(strspec.h5object.dtype.name, 'object')
            self.assertEqual(strspec.shape, (10,))
            self.assertEqual(strspec.h5object.shape, (10,))

            chars = string.ascii_uppercase + string.digits
            vl = [
                ''.join(self.__rnd.choice(chars)
                        for _ in range(self.__rnd.randint(1, 10)))
                for _ in range(40)]

            strspec[...] = vl[0:10]
            self.assertEqual(list(strspec.read()), vl[0:10])
            strspec.write(vl[11:21])
            self.assertEqual(list(strspec[...]), vl[11:21])
            strspec[...] = vl[0:10]

            strspec.grow()
            self.assertEqual(strspec.shape, (11,))
            self.assertEqual(strspec.h5object.shape, (11,))

            self.assertEqual(list(strspec[0:10]), vl[0:10])
            strspec[10] = vl[10]
            self.assertEqual(list(strspec[...]), vl[0:11])

            strspec.grow(ext=2)
            self.assertEqual(strspec.shape, (13,))
            self.assertEqual(strspec.h5object.shape, (13,))
            strspec[1:13] = vl[1:13]
            self.assertEqual(list(strspec.read()), vl[0:13])
            self.assertEqual(list(strspec[0:2]), vl[0:2])

            strspec.grow(0, 3)
            self.assertEqual(strspec.shape, (16,))
            self.assertEqual(strspec.h5object.shape, (16,))
            strspec.write(vl[0:16])
            self.assertEqual(list(strspec.read()), vl[0:16])
            self.assertEqual(list(strspec[...]), vl[0:16])

            attrs = strspec.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, strspec)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(floatspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatspec.h5object, h5py.Dataset))
            self.assertEqual(floatspec.name, 'floatspec')
            self.assertEqual(
                floatspec.h5object.name, '/entry12345/instrument/floatspec')
            self.assertEqual(
                floatspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/floatspec')
            self.assertEqual(floatspec.dtype, 'float32')
            self.assertEqual(floatspec.h5object.dtype, 'float32')
            self.assertEqual(floatspec.shape, (20,))
            self.assertEqual(floatspec.h5object.shape, (20,))

            vl = [self.__rnd.uniform(-200.0, 200) for _ in range(80)]

            floatspec[...] = vl[0:20]
            self.myAssertFloatList(list(floatspec.read()), vl[0:20], 1e-4)
            floatspec.write(vl[21:41])
            self.myAssertFloatList(list(floatspec[...]), vl[21:41], 1e-4)
            floatspec[...] = vl[0:20]

            floatspec.grow()
            self.assertEqual(floatspec.shape, (21,))
            self.assertEqual(floatspec.h5object.shape, (21,))

            self.myAssertFloatList(list(floatspec[0:20]), vl[0:20], 1e-4)
            floatspec[20] = vl[20]
            self.myAssertFloatList(list(floatspec[...]), vl[0:21], 1e-4)

            floatspec.grow(ext=2)
            self.assertEqual(floatspec.shape, (23,))
            self.assertEqual(floatspec.h5object.shape, (23,))
            floatspec[1:23] = vl[1:23]
            self.myAssertFloatList(list(floatspec.read()), vl[0:23], 1e-4)
            self.myAssertFloatList(list(floatspec[0:2]), vl[0:2], 1e-4)

            floatspec.grow(0, 3)
            self.assertEqual(floatspec.shape, (26,))
            self.assertEqual(floatspec.h5object.shape, (26,))
            floatspec.write(vl[0:26])
            self.myAssertFloatList(list(floatspec.read()), vl[0:26], 1e-4)
            self.myAssertFloatList(list(floatspec[...]), vl[0:26], 1e-4)

            attrs = floatspec.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, floatspec)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(intspec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intspec.h5object, h5py.Dataset))
            self.assertEqual(intspec.name, 'intspec')
            self.assertEqual(
                intspec.path,
                '/entry12345:NXentry/instrument:NXinstrument/intspec')
            self.assertEqual(intspec.dtype, 'int64')
            self.assertEqual(intspec.shape, (30,))
            self.assertEqual(
                intspec.h5object.name, '/entry12345/instrument/intspec')
            self.assertEqual(intspec.h5object.dtype, 'int64')
            self.assertEqual(intspec.h5object.shape, (30,))

            vl = [self.__rnd.randint(1, 16000) for _ in range(100)]

            intspec[...] = vl[0:30]
            self.assertEqual(list(intspec.read()), vl[0:30])
            intspec.write(vl[31:61])
            self.assertEqual(list(intspec[...]), vl[31:61])
            intspec[...] = vl[0:30]

            intspec.grow()
            self.assertEqual(intspec.shape, (31,))
            self.assertEqual(intspec.h5object.shape, (31,))

            self.assertEqual(list(intspec[0:10]), vl[0:10])
            intspec[30] = vl[30]
            self.assertEqual(list(intspec[...]), vl[0:31])

            intspec.grow(ext=2)
            self.assertEqual(intspec.shape, (33,))
            self.assertEqual(intspec.h5object.shape, (33,))
            intspec[1:33] = vl[1:33]
            self.assertEqual(list(intspec.read()), vl[0:33])
            self.assertEqual(list(intspec[0:2]), vl[0:2])

            intspec.grow(0, 3)
            self.assertEqual(intspec.shape, (36,))
            self.assertEqual(intspec.h5object.shape, (36,))
            intspec.write(vl[0:36])
            self.assertEqual(list(intspec.read()), vl[0:36])
            self.assertEqual(list(intspec[...]), vl[0:36])

            attrs = intspec.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, intspec)
            self.assertEqual(len(attrs), 0)

            entry.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, False)
            self.assertEqual(dt.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyfield_image(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)
        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            strimage = det.create_field("strimage", "string", [2, 2], [2, 1])
            floatimage = det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            intimage = det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertTrue(isinstance(strimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strimage.h5object, h5py.Dataset))
            self.assertEqual(strimage.name, 'strimage')
            self.assertEqual(
                strimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strimage')
            self.assertEqual(strimage.dtype, 'string')
            self.assertEqual(strimage.shape, (2, 2))
            self.assertEqual(
                strimage.h5object.name,
                '/entry12345/instrument/detector/strimage')
            self.assertEqual(strimage.h5object.dtype.name, 'object')
            self.assertEqual(strimage.h5object.shape, (2, 2))

            chars = string.ascii_uppercase + string.digits
            vl = [
                [''.join(self.__rnd.choice(chars)
                         for _ in range(self.__rnd.randint(1, 10)))
                 for _ in range(10)]
                for _ in range(30)]

            vv = [[vl[j][i] for i in range(2)] for j in range(2)]
            strimage[...] = vv
            self.myAssertImage(strimage.read(), vv)
            vv2 = [[vl[j + 2][i + 2] for i in range(2)] for j in range(2)]
            strimage.write(vv2)
            self.myAssertImage(list(strimage[...]), vv2)
            strimage[...] = vv

            strimage.grow()
            self.assertEqual(strimage.shape, (3, 2))
            self.assertEqual(strimage.h5object.shape, (3, 2))

            iv = [[strimage[j, i] for i in range(2)] for j in range(2)]
            self.myAssertImage(iv, vv)
            strimage[2, :] = [vl[2][0], vl[2][1]]
            vv3 = [[vl[j][i] for i in range(2)] for j in range(3)]
            self.myAssertImage(strimage[...], vv3)

            strimage.grow(ext=2)
            self.assertEqual(strimage.shape, (5, 2))
            self.assertEqual(strimage.h5object.shape, (5, 2))
            vv4 = [[vl[j + 2][i] for i in range(2)] for j in range(3)]
            vv5 = [[vl[j][i] for i in range(2)] for j in range(5)]
            strimage[2:5, :] = vv4
            self.myAssertImage(strimage[...], vv5)
            self.myAssertImage(strimage[0:3, :], vv3)

            strimage.grow(1, 4)
            self.assertEqual(strimage.shape, (5, 6))
            self.assertEqual(strimage.h5object.shape, (5, 6))

            vv6 = [[vl[j][i] for i in range(6)] for j in range(5)]
            strimage.write(vv6)
            self.myAssertImage(strimage[...], vv6)
            self.myAssertImage(strimage.read(), vv6)

            attrs = strimage.attributes
            self.assertTrue(isinstance(
                attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(isinstance(
                attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, strimage)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(floatimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatimage.h5object, h5py.Dataset))
            self.assertEqual(floatimage.name, 'floatimage')
            self.assertEqual(
                floatimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatimage')
            self.assertEqual(floatimage.dtype, 'float64')
            self.assertEqual(floatimage.shape, (20, 10))
            self.assertEqual(
                floatimage.h5object.name,
                '/entry12345/instrument/detector/floatimage')
            self.assertEqual(floatimage.h5object.dtype, 'float64')
            self.assertEqual(floatimage.h5object.shape, (20, 10))

            vl = [
                [self.__rnd.uniform(-20000.0, 20000) for _ in range(50)]
                for _ in range(50)]

            vv = [[vl[j][i] for i in range(10)] for j in range(20)]
            floatimage[...] = vv
            self.myAssertImage(floatimage.read(), vv)
            vv2 = [[vl[j + 20][i + 10] for i in range(10)] for j in range(20)]
            floatimage.write(vv2)
            self.myAssertImage(list(floatimage[...]), vv2)
            floatimage[...] = vv

            floatimage.grow()
            self.assertEqual(floatimage.shape, (21, 10))
            self.assertEqual(floatimage.h5object.shape, (21, 10))

            iv = [[floatimage[j, i] for i in range(10)] for j in range(20)]
            self.myAssertImage(iv, vv)
            floatimage[20, :] = [vl[20][i] for i in range(10)]
            vv3 = [[vl[j][i] for i in range(10)] for j in range(21)]
            self.myAssertImage(floatimage[...], vv3)

            floatimage.grow(ext=2)
            self.assertEqual(floatimage.shape, (23, 10))
            self.assertEqual(floatimage.h5object.shape, (23, 10))
            vv4 = [[vl[j + 2][i] for i in range(10)] for j in range(21)]
            vv5 = [[vl[j][i] for i in range(10)] for j in range(23)]
            floatimage[2:23, :] = vv4
            self.myAssertImage(floatimage[...], vv5)
            self.myAssertImage(floatimage[0:21, :], vv3)

            floatimage.grow(1, 4)
            self.assertEqual(floatimage.shape, (23, 14))
            self.assertEqual(floatimage.h5object.shape, (23, 14))

            vv6 = [[vl[j][i] for i in range(14)] for j in range(23)]
            floatimage.write(vv6)
            self.myAssertImage(floatimage[...], vv6)
            self.myAssertImage(floatimage.read(), vv6)

            self.assertTrue(isinstance(intimage, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intimage.h5object, h5py.Dataset))
            self.assertEqual(intimage.name, 'intimage')
            self.assertEqual(
                intimage.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intimage')
            self.assertEqual(intimage.dtype, 'uint32')
            self.assertEqual(intimage.shape, (0, 30))
            self.assertEqual(
                intimage.h5object.name,
                '/entry12345/instrument/detector/intimage')
            self.assertEqual(intimage.h5object.dtype, 'uint32')
            self.assertEqual(intimage.h5object.shape, (0, 30))
            vl = [
                [self.__rnd.randint(1, 1600) for _ in range(80)]
                for _ in range(80)]

            intimage.grow(0, 20)
            vv = [[vl[j][i] for i in range(30)] for j in range(20)]
            intimage[...] = vv
            self.myAssertImage(intimage.read(), vv)
            vv2 = [[vl[j + 20][i + 10] for i in range(30)] for j in range(20)]
            intimage.write(vv2)
            self.myAssertImage(list(intimage[...]), vv2)
            intimage[...] = vv

            intimage.grow()
            self.assertEqual(intimage.shape, (21, 30))
            self.assertEqual(intimage.h5object.shape, (21, 30))

            iv = [[intimage[j, i] for i in range(30)] for j in range(20)]
            self.myAssertImage(iv, vv)
            intimage[20, :] = [vl[20][i] for i in range(30)]
            vv3 = [[vl[j][i] for i in range(30)] for j in range(21)]
            self.myAssertImage(intimage[...], vv3)

            intimage.grow(ext=2)
            self.assertEqual(intimage.shape, (23, 30))
            self.assertEqual(intimage.h5object.shape, (23, 30))
            vv4 = [[vl[j + 2][i] for i in range(30)] for j in range(21)]
            vv5 = [[vl[j][i] for i in range(30)] for j in range(23)]
            intimage[2:23, :] = vv4
            self.myAssertImage(intimage[...], vv5)
            self.myAssertImage(intimage[0:21, :], vv3)

            intimage.grow(1, 4)
            self.assertEqual(intimage.shape, (23, 34))
            self.assertEqual(intimage.h5object.shape, (23, 34))

            vv6 = [[vl[j][i] for i in range(34)] for j in range(23)]
            intimage.write(vv6)
            self.myAssertImage(intimage[...], vv6)
            self.myAssertImage(intimage.read(), vv6)

            entry.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, False)
            self.assertEqual(dt.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyfield_vec(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            strvec = det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            floatvec = det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            intvec = det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertTrue(isinstance(strvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(strvec.h5object, h5py.Dataset))
            self.assertEqual(strvec.name, 'strvec')
            self.assertEqual(
                strvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/strvec')
            self.assertEqual(strvec.dtype, 'string')
            self.assertEqual(strvec.shape, (0, 2, 2))
            self.assertEqual(strvec.h5object.name,
                             '/entry12345/instrument/detector/strvec')
            self.assertEqual(strvec.h5object.dtype.name, 'object')
            self.assertEqual(strvec.h5object.shape, (0, 2, 2))

            chars = string.ascii_uppercase + string.digits
            vl = [[[''.join(self.__rnd.choice(chars)
                            for _ in range(self.__rnd.randint(1, 10)))
                    for _ in range(10)]
                   for _ in range(20)]
                  for _ in range(30)]

            strvec.grow(ext=3)
            vv = [[[vl[k][j][i] for i in range(2)] for j in range(2)]
                  for k in range(3)]
            strvec[...] = vv
            self.myAssertVector(strvec.read(), vv)
            vv2 = [[[vl[k][j + 2][i + 2] for i in range(2)] for j in range(2)]
                   for k in range(3)]
            strvec.write(vv2)
            self.myAssertVector(list(strvec[...]), vv2)
            strvec[...] = vv

            strvec.grow()
            self.assertEqual(strvec.shape, (4, 2, 2))
            self.assertEqual(strvec.h5object.shape, (4, 2, 2))

            iv = [[[strvec[k, j, i] for i in range(2)] for j in range(2)]
                  for k in range(3)]
            self.myAssertVector(iv, vv)
            strvec[3, :, :] = [[vl[3][j][i] for i in range(2)]
                               for j in range(2)]
            vv3 = [[[vl[k][j][i] for i in range(2)] for j in range(2)]
                   for k in range(4)]
            self.myAssertVector(strvec[...], vv3)

            strvec.grow(2, 3)
            self.assertEqual(strvec.shape, (4, 2, 5))
            self.assertEqual(strvec.h5object.shape, (4, 2, 5))
            vv4 = [[[vl[k][j][i + 2] for i in range(3)] for j in range(2)]
                   for k in range(4)]
            vv5 = [[[vl[k][j][i] for i in range(5)] for j in range(2)]
                   for k in range(4)]

            strvec[:, :, 2:5] = vv4
            self.myAssertVector(strvec[...], vv5)
            self.myAssertVector(strvec[:, :, 0:2], vv3)

            strvec.grow(1, 4)
            self.assertEqual(strvec.shape, (4, 6, 5))
            self.assertEqual(strvec.h5object.shape, (4, 6, 5))

            vv6 = [[[vl[k][j][i] for i in range(5)] for j in range(6)]
                   for k in range(4)]
            strvec.write(vv6)
            self.myAssertVector(strvec[...], vv6)
            self.myAssertVector(strvec.read(), vv6)

            attrs = strvec.attributes
            self.assertTrue(
                isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, strvec)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(floatvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(floatvec.h5object, h5py.Dataset))
            self.assertEqual(floatvec.name, 'floatvec')
            self.assertEqual(
                floatvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/floatvec')
            self.assertEqual(floatvec.dtype, 'float64')
            self.assertEqual(floatvec.shape, (1, 20, 10))
            self.assertEqual(
                floatvec.h5object.name,
                '/entry12345/instrument/detector/floatvec')
            self.assertEqual(floatvec.h5object.dtype, 'float64')
            self.assertEqual(floatvec.h5object.shape, (1, 20, 10))

            vl = [[[self.__rnd.uniform(-20000.0, 20000)
                    for _ in range(70)]
                   for _ in range(80)]
                  for _ in range(80)]

            vv = [[[vl[k][j][i] for i in range(10)] for j in range(20)]
                  for k in range(1)]
            floatvec[...] = vv
            self.myAssertVector(floatvec.read(), vv)
            vv2 = [[[vl[k][j + 2][i + 2] for i in range(10)]
                    for j in range(20)]
                   for k in range(1)]
            floatvec.write(vv2)
            self.myAssertVector(floatvec.read(), vv2)

            # !!! PNI self.myAssertVector([floatvec[...]], vv2)
            self.myAssertVector(floatvec[...], vv2)
            floatvec[...] = vv

            floatvec.grow()
            self.assertEqual(floatvec.shape, (2, 20, 10))
            self.assertEqual(floatvec.h5object.shape, (2, 20, 10))

            iv = [[[floatvec[k, j, i] for i in range(10)] for j in range(20)]
                  for k in range(1)]
            self.myAssertVector(iv, vv)
            floatvec[1, :, :] = [[vl[1][j][i] for i in range(10)]
                                 for j in range(20)]
            vv3 = [[[vl[k][j][i] for i in range(10)] for j in range(20)]
                   for k in range(2)]
            self.myAssertVector(floatvec[...], vv3)

            floatvec.grow(2, 3)
            self.assertEqual(floatvec.shape, (2, 20, 13))
            self.assertEqual(floatvec.h5object.shape, (2, 20, 13))
            vv4 = [[[vl[k][j][i + 10] for i in range(3)] for j in range(20)]
                   for k in range(2)]
            vv5 = [[[vl[k][j][i] for i in range(13)] for j in range(20)]
                   for k in range(2)]

            floatvec[:, :, 10:13] = vv4
            self.myAssertVector(floatvec[...], vv5)
            self.myAssertVector(floatvec[:, :, 0:10], vv3)

            floatvec.grow(1, 4)
            self.assertEqual(floatvec.shape, (2, 24, 13))
            self.assertEqual(floatvec.h5object.shape, (2, 24, 13))

            vv6 = [[[vl[k][j][i] for i in range(13)] for j in range(24)]
                   for k in range(2)]
            floatvec.write(vv6)
            self.myAssertVector(floatvec[...], vv6)
            self.myAssertVector(floatvec.read(), vv6)

            attrs = floatvec.attributes
            self.assertTrue(isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, floatvec)
            self.assertEqual(len(attrs), 0)

            self.assertTrue(isinstance(intvec, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(intvec.h5object, h5py.Dataset))
            self.assertEqual(intvec.name, 'intvec')
            self.assertEqual(
                intvec.path,
                '/entry12345:NXentry/instrument:NXinstrument/'
                'detector:NXdetector/intvec')
            self.assertEqual(intvec.dtype, 'uint32')
            self.assertEqual(intvec.shape, (0, 2, 30))
            self.assertEqual(intvec.h5object.name,
                             '/entry12345/instrument/detector/intvec')
            self.assertEqual(intvec.h5object.dtype, 'uint32')
            self.assertEqual(intvec.h5object.shape, (0, 2, 30))

            vl = [[[self.__rnd.randint(1, 1600)
                    for _ in range(70)]
                   for _ in range(18)]
                  for _ in range(8)]

            intvec.grow()
            vv = [[[vl[k][j][i] for i in range(30)]
                   for j in range(2)] for k in range(1)]

            intvec[...] = vv
            self.myAssertVector(intvec.read(), vv)
            vv2 = [[[vl[k][j + 2][i + 2] for i in range(30)]
                    for j in range(2)] for k in range(1)]
            intvec.write(vv2)
            self.myAssertVector(intvec.read(), vv2)
            # !!! PNI self.myAssertVector([intvec[...]], vv2)
            self.myAssertVector(intvec[...], vv2)
            intvec[...] = vv

            intvec.grow()
            self.assertEqual(intvec.shape, (2, 2, 30))
            self.assertEqual(intvec.h5object.shape, (2, 2, 30))

            iv = [[[intvec[k, j, i] for i in range(30)]
                   for j in range(2)] for k in range(1)]
            self.myAssertVector(iv, vv)
            intvec[1, :, :] = [[vl[1][j][i] for i in range(30)]
                               for j in range(2)]
            vv3 = [[[vl[k][j][i] for i in range(30)]
                    for j in range(2)] for k in range(2)]
            self.myAssertVector(intvec[...], vv3)

            intvec.grow(2, 3)
            self.assertEqual(intvec.shape, (2, 2, 33))
            self.assertEqual(intvec.h5object.shape, (2, 2, 33))
            vv4 = [[[vl[k][j][i + 30] for i in range(3)]
                    for j in range(2)] for k in range(2)]
            vv5 = [[[vl[k][j][i] for i in range(33)]
                    for j in range(2)] for k in range(2)]

            intvec[:, :, 30:33] = vv4
            self.myAssertVector(intvec[...], vv5)
            self.myAssertVector(intvec[:, :, 0:30], vv3)

            intvec.grow(1, 4)
            self.assertEqual(intvec.shape, (2, 6, 33))
            self.assertEqual(intvec.h5object.shape, (2, 6, 33))

            vv6 = [[[vl[k][j][i] for i in range(33)]
                    for j in range(6)] for k in range(2)]
            intvec.write(vv6)
            self.myAssertVector(intvec[...], vv6)
            self.myAssertVector(intvec.read(), vv6)

            attrs = intvec.attributes
            self.assertTrue(isinstance(attrs, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attrs.h5object, h5py._hl.attrs.AttributeManager))
            self.assertEqual(attrs.parent, intvec)
            self.assertEqual(len(attrs), 0)

            entry.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, False)
            self.assertEqual(dt.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pydeflate(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = True

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertEqual(df0.rate, 0)
            self.assertEqual(df0.shuffle, False)
            self.assertEqual(df0.parent, None)
            self.assertEqual(df0.h5object, None)
            self.assertEqual(df1.rate, 2)
            self.assertEqual(df1.shuffle, False)
            self.assertEqual(df1.parent, None)
            self.assertEqual(df1.h5object, None)
            self.assertEqual(df2.rate, 4)
            self.assertEqual(df2.shuffle, True)
            self.assertEqual(df2.parent, None)
            self.assertEqual(df2.h5object, None)
        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pybitshuffle(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        if H5CPP and hasattr(h5cpp.filter, "is_filter_available") \
           and h5cpp.filter.is_filter_available(32008):
            try:
                # overwrite = False
                fl = H5PYWriter.create_file(self._fname)

                rt = fl.root()
                rt.create_group("notype")
                entry = rt.create_group("entry12345", "NXentry")
                ins = entry.create_group("instrument", "NXinstrument")
                det = ins.create_group("detector", "NXdetector")
                entry.create_group("data", "NXdata")

                df0 = H5PYWriter.data_filter()
                df1 = H5PYWriter.data_filter()
                df1.filterid = 32008
                df1.options = (0, 2)
                df2 = H5PYWriter.data_filter()
                df2.filterid = 32008
                df2.options = (0, 2)
                df2.shuffle = True

                entry.create_field("strscalar", "string")
                entry.create_field("floatscalar", "float64")
                entry.create_field("intscalar", "uint64")
                ins.create_field("strspec", "string", [10], [6])
                ins.create_field("floatspec", "float32", [20], [16])
                ins.create_field("intspec", "int64", [30], [5])
                det.create_field("strimage", "string", [2, 2], [2, 1])
                det.create_field(
                    "floatimage", "float64", [20, 10], dfilter=df0)
                det.create_field("intimage", "uint32", [0, 30], [1, 30])
                det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
                det.create_field(
                    "floatvec", "float64", [1, 20, 10], [1, 10, 10],
                    dfilter=df1)
                det.create_field(
                    "intvec", "uint32", [0, 2, 30], dfilter=df2)

                self.assertEqual(df0.rate, 0)
                self.assertEqual(df0.shuffle, False)
                self.assertEqual(df0.parent, None)
                self.assertEqual(df0.h5object, None)
                self.assertEqual(df1.rate, 0)
                self.assertEqual(df1.shuffle, False)
                self.assertEqual(df1.parent, None)
                self.assertEqual(df1.h5object, None)
                self.assertEqual(df2.rate, 0)
                self.assertEqual(df2.shuffle, True)
                self.assertEqual(df2.parent, None)
                self.assertEqual(df2.h5object, None)
            finally:
                os.remove(self._fname)
        else:
            print("Skip: %s.%s() " % (self.__class__.__name__, fun))

    # default createfile test
    # \brief It tests default settings
    def test_h5pydeflate_const(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            entry.create_group("data", "NXdata")

            df0 = H5PYWriter.H5PYDeflate()
            df1 = H5PYWriter.H5PYDeflate()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2 = H5PYWriter.H5PYDeflate()
            df2.rate = 4
            df2.shuffle = True

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            self.assertEqual(df0.rate, 0)
            self.assertEqual(df0.shuffle, False)
            self.assertEqual(df0.parent, None)
            self.assertEqual(df0.h5object, None)
            self.assertEqual(df1.rate, 2)
            self.assertEqual(df1.shuffle, False)
            self.assertEqual(df1.parent, None)
            self.assertEqual(df1.h5object, None)
            self.assertEqual(df2.rate, 4)
            self.assertEqual(df2.shuffle, True)
            self.assertEqual(df2.parent, None)
            self.assertEqual(df2.h5object, None)
        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pylink(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            dt.h5object["lkintimage"] = h5py.SoftLink(
                "/entry12345/instrument/detector/intimage")
            lkintimage = H5PYWriter.H5PYLink(
                dt.h5object.get(
                    "lkintimage", getlink=True), dt).setname("lkintimage")
            dt.h5object["lkfloatvec"] = h5py.SoftLink(
                "/entry12345/instrument/detector/floatvec")
            lkfloatvec = H5PYWriter.H5PYLink(
                dt.h5object.get(
                    "lkfloatvec", getlink=True), dt).setname("lkfloatvec")
            dt.h5object["lkintspec"] = h5py.SoftLink(
                "/entry12345/instrument/intspec")
            lkintspec = H5PYWriter.H5PYLink(
                dt.h5object.get(
                    "lkintspec", getlink=True), dt).setname("lkintspec")
            dt.h5object["lkdet"] = h5py.SoftLink(
                "/entry12345/instrument/detector")
            lkdet = H5PYWriter.H5PYLink(
                dt.h5object.get("lkdet", getlink=True), dt).setname("lkdet")
            dt.h5object["lkno"] = h5py.SoftLink("/notype/unknown")
            lkno = H5PYWriter.H5PYLink(
                dt.h5object.get("lkno", getlink=True), dt).setname("lkno")

            self.assertTrue(isinstance(lkintimage, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkintimage.h5object, h5py.SoftLink))
            self.assertTrue(lkintimage.target_path.endswith(
                "%s://entry12345/instrument/detector/intimage" % self._fname))
            self.assertEqual(
                lkintimage.path,
                "/entry12345:NXentry/data:NXdata/lkintimage")

            self.assertTrue(isinstance(lkfloatvec, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkfloatvec.h5object, h5py.SoftLink))
            self.assertTrue(lkfloatvec.target_path.endswith(
                "%s://entry12345/instrument/detector/floatvec" % self._fname))
            self.assertEqual(
                lkfloatvec.path,
                "/entry12345:NXentry/data:NXdata/lkfloatvec")

            self.assertTrue(isinstance(lkintspec, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkintspec.h5object, h5py.SoftLink))
            self.assertTrue(lkintspec.target_path.endswith(
                "%s://entry12345/instrument/intspec" % self._fname))
            self.assertEqual(
                lkintspec.path,
                "/entry12345:NXentry/data:NXdata/lkintspec")

            self.assertTrue(isinstance(lkdet, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkdet.h5object, h5py.SoftLink))
            self.assertTrue(lkdet.target_path.endswith(
                "%s://entry12345/instrument/detector" % self._fname))
            self.assertEqual(
                lkdet.path,
                "/entry12345:NXentry/data:NXdata/lkdet")

            self.assertTrue(isinstance(lkno, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkno.h5object, h5py.SoftLink))
            self.assertTrue(lkno.target_path.endswith(
                "%s://notype/unknown" % self._fname))
            self.assertEqual(
                lkno.path,
                "/entry12345:NXentry/data:NXdata/lkno")

            lkintimage_op = dt.open("lkintimage")
            lkfloatvec_op = dt.open("lkfloatvec")
            lkintspec_op = dt.open("lkintspec")
            dt.open("lkdet")
            lkno_op = dt.open("lkno")

            self.assertTrue(isinstance(lkintimage_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(lkintimage_op.h5object, h5py.Dataset))
            self.assertEqual(lkintimage_op.name, 'lkintimage')
            self.assertEqual(
                lkintimage_op.path,
                '/entry12345:NXentry/data:NXdata/lkintimage')
            self.assertEqual(lkintimage_op.dtype, 'uint32')
            self.assertEqual(lkintimage_op.shape, (0, 30))

            self.assertTrue(isinstance(lkfloatvec_op, H5PYWriter.H5PYField))
            self.assertTrue(isinstance(lkfloatvec_op.h5object, h5py.Dataset))
            self.assertEqual(lkfloatvec_op.name, 'lkfloatvec')
            self.assertEqual(lkfloatvec_op.path,
                             '/entry12345:NXentry/data:NXdata/lkfloatvec')
            self.assertEqual(lkfloatvec_op.dtype, 'float64')
            self.assertEqual(lkfloatvec_op.shape, (1, 20, 10))

            self.assertTrue(
                isinstance(lkintspec_op, H5PYWriter.H5PYField))
            self.assertTrue(
                isinstance(lkintspec_op.h5object, h5py.Dataset))
            self.assertEqual(lkintspec_op.name, 'lkintspec')
            self.assertEqual(lkintspec_op.path,
                             '/entry12345:NXentry/data:NXdata/lkintspec')
            self.assertEqual(lkintspec_op.dtype, 'int64')
            self.assertEqual(lkintspec_op.shape, (30,))

            self.assertTrue(isinstance(lkno_op, H5PYWriter.H5PYLink))
            self.assertTrue(isinstance(lkno_op.h5object, h5py.SoftLink))
            self.assertTrue(lkno_op.target_path.endswith(
                "%s://notype/unknown" % self._fname))
            self.assertEqual(
                lkno_op.path,
                "/entry12345:NXentry/data:NXdata/lkno")

            entry.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, False)
            self.assertEqual(dt.is_valid, False)

            entry.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            self.assertEqual(fl.default_field().name, "lkfloatvec")
            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyattributemanager(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            H5PYWriter.link(
                "/entry12345/instrument/detector/intimage", dt, "lkintimage")
            H5PYWriter.link(
                "/entry12345/instrument/detector/floatvec", dt, "lkfloatvec")
            H5PYWriter.link(
                "/entry12345/instrument/intspec", dt, "lkintspec")
            H5PYWriter.link(
                "/entry12345/instrument/detector", dt, "lkdet")
            H5PYWriter.link(
                "/notype/unknown", dt, "lkno")

            attr0 = rt.attributes
            attr1 = entry.attributes
            attr2 = intscalar.attributes

            print(attr0.h5object)
            self.assertTrue(isinstance(attr0, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr0.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr1, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr1.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr2, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr2.h5object, h5py.AttributeManager))

            self.assertEqual(len(attr0), 5)
            self.assertEqual(len(attr1), 1)
            self.assertEqual(len(attr2), 0)

            atintscalar = attr0.create("atintscalar", "int64")
            atfloatspec = attr0.create("atfloatspec", "float32", [12])
            atstrimage = attr0.create("atstrimage", "string", [2, 3])
            atstrscalar = attr1.create("atstrscalar", "string")
            atintspec = attr1.create("atintspec", "uint32", [2])
            atfloatimage = attr1.create("atfloatimage", "float64", [3, 2])
            atfloatscalar = attr2.create("atfloatscalar", "float64")
            atstrspec = attr2.create("atstrspec", "string", [4])
            atintimage = attr2.create("atintimage", "int32", [3, 2])

            self.assertEqual(len(attr0), 8)
            self.assertEqual(len(attr1), 4)
            self.assertEqual(len(attr2), 3)

            print(dir(atintscalar))
            print(dir(atintscalar.h5object))

            self.assertTrue(isinstance(atintscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintscalar.h5object, tuple))
            self.assertEqual(atintscalar.parent, rt)
            self.assertEqual(atintscalar.name, 'atintscalar')
            self.assertEqual(atintscalar.path, '/@atintscalar')
            self.assertEqual(atintscalar.dtype, 'int64')
            self.assertEqual(atintscalar.shape, (1,))
            self.assertEqual(atintscalar.is_valid, True)
            self.assertEqual(atintscalar.read(), 0)
            self.assertEqual(atintscalar[...], 0)
            self.assertEqual(atintscalar.parent.h5object, rt.h5object)
            self.assertEqual(
                atintscalar.h5object, (attr0.h5object, 'atintscalar'))

            self.assertTrue(isinstance(atfloatspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatspec.h5object, tuple))
            self.assertEqual(atfloatspec.parent, rt)
            self.assertEqual(atfloatspec.name, 'atfloatspec')
            self.assertEqual(atfloatspec.path, '/@atfloatspec')
            self.assertEqual(atfloatspec.dtype, 'float32')
            self.assertEqual(atfloatspec.shape, (12,))
            self.assertEqual(atfloatspec.is_valid, True)
            self.assertEqual(list(atfloatspec.read()), [0.] * 12)
            self.assertEqual(list(atfloatspec[...]), [0.] * 12)
            self.assertEqual(atfloatspec.parent.h5object, rt.h5object)
            self.assertEqual(
                atfloatspec.h5object, (attr0.h5object, 'atfloatspec'))

            self.assertTrue(isinstance(atstrimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrimage.h5object, tuple))
            self.assertEqual(atstrimage.parent, rt)
            self.assertEqual(atstrimage.name, 'atstrimage')
            self.assertEqual(atstrimage.path, '/@atstrimage')
            self.assertEqual(atstrimage.dtype, 'string')
            self.assertEqual(atstrimage.shape, (2, 3))
            self.assertEqual(atstrimage.is_valid, True)
            self.myAssertImage(atstrimage.read(), [[''] * 3] * 2)
            self.myAssertImage(atstrimage[...], [[''] * 3] * 2)
            self.assertEqual(atstrimage.parent.h5object, rt.h5object)
            self.assertEqual(
                atstrimage.h5object, (attr0.h5object, 'atstrimage'))

            self.assertTrue(isinstance(atstrscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrscalar.h5object, tuple))
            self.assertEqual(atstrscalar.parent, entry)
            self.assertEqual(atstrscalar.name, 'atstrscalar')
            self.assertEqual(
                atstrscalar.path, '/entry12345:NXentry@atstrscalar')
            self.assertEqual(atstrscalar.dtype, 'string')
            self.assertEqual(atstrscalar.shape, ())
            self.assertEqual(atstrscalar.is_valid, True)
            self.assertEqual(atstrscalar.read(), '')
            self.assertEqual(atstrscalar[...], '')
            self.assertEqual(atstrscalar.parent.h5object, entry.h5object)
            self.assertEqual(
                atstrscalar.h5object, (attr1.h5object, 'atstrscalar'))

            self.assertTrue(isinstance(atintspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintspec.h5object, tuple))
            self.assertEqual(atintspec.parent, entry)
            self.assertEqual(atintspec.name, 'atintspec')
            self.assertEqual(atintspec.path, '/entry12345:NXentry@atintspec')
            self.assertEqual(atintspec.dtype, 'uint32')
            self.assertEqual(atintspec.shape, (2,))
            self.assertEqual(atintspec.is_valid, True)
            self.assertEqual(list(atintspec.read()), [0] * 2)
            self.assertEqual(list(atintspec[...]), [0] * 2)
            self.assertEqual(atintspec.parent.h5object, entry.h5object)
            self.assertEqual(atintspec.h5object, (attr1.h5object, 'atintspec'))

            self.assertTrue(isinstance(atfloatimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatimage.h5object, tuple))
            self.assertEqual(atfloatimage.parent, entry)
            self.assertEqual(atfloatimage.name, 'atfloatimage')
            self.assertEqual(
                atfloatimage.path, '/entry12345:NXentry@atfloatimage')
            self.assertEqual(atfloatimage.dtype, 'float64')
            self.assertEqual(atfloatimage.shape, (3, 2))
            self.assertEqual(atfloatimage.is_valid, True)
            self.myAssertImage(atfloatimage.read(), [[0.] * 2] * 3)
            self.myAssertImage(atfloatimage[...], [[0.] * 2] * 3)
            self.assertEqual(atfloatimage.parent.h5object, entry.h5object)
            self.assertEqual(
                atfloatimage.h5object, (attr1.h5object, 'atfloatimage'))

            self.assertTrue(
                isinstance(atfloatscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatscalar.h5object, tuple))
            self.assertEqual(atfloatscalar.parent, intscalar)
            self.assertEqual(atfloatscalar.name, 'atfloatscalar')
            self.assertEqual(atfloatscalar.path,
                             '/entry12345:NXentry/intscalar@atfloatscalar')
            self.assertEqual(atfloatscalar.dtype, 'float64')
            self.assertEqual(atfloatscalar.shape, (1,))
            self.assertEqual(atfloatscalar.is_valid, True)
            self.assertEqual(atfloatscalar.read(), 0)
            self.assertEqual(atfloatscalar[...], 0)
            self.assertEqual(atfloatscalar.parent.h5object, intscalar.h5object)
            self.assertEqual(
                atfloatscalar.h5object, (attr2.h5object, 'atfloatscalar'))

            self.assertTrue(isinstance(atstrspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrspec.h5object, tuple))
            self.assertEqual(atstrspec.parent, intscalar)
            self.assertEqual(atstrspec.name, 'atstrspec')
            self.assertEqual(atstrspec.path,
                             '/entry12345:NXentry/intscalar@atstrspec')
            self.assertEqual(atstrspec.dtype, 'string')
            self.assertEqual(atstrspec.shape, (4,))
            self.assertEqual(atstrspec.is_valid, True)
            self.assertEqual(list(atstrspec.read()), [''] * 4)
            self.assertEqual(list(atstrspec[...]), [''] * 4)
            self.assertEqual(atstrspec.parent.h5object, intscalar.h5object)
            self.assertEqual(atstrspec.h5object, (attr2.h5object, 'atstrspec'))

            self.assertTrue(isinstance(atintimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintimage.h5object, tuple))
            self.assertEqual(atintimage.parent, intscalar)
            self.assertEqual(atintimage.name, 'atintimage')
            self.assertEqual(atintimage.path,
                             '/entry12345:NXentry/intscalar@atintimage')
            self.assertEqual(atintimage.dtype, 'int32')
            self.assertEqual(atintimage.shape, (3, 2))
            self.assertEqual(atintimage.is_valid, True)
            self.myAssertImage(atintimage.read(), [[0] * 2] * 3)
            self.myAssertImage(atintimage[...], [[0] * 2] * 3)
            self.assertEqual(atintimage.parent.h5object, intscalar.h5object)
            self.assertEqual(
                atintimage.h5object, (attr2.h5object, 'atintimage'))

            print("WW %s" % attr1["NX_class"].name)

            for at in attr0:
                print(at.name)
            for at in attr1:
                print(at.name)
            for at in attr2:
                print(at.name)

            at = None

            atintscalar = attr0["atintscalar"]
            atfloatspec = attr0["atfloatspec"]
            atstrimage = attr0["atstrimage"]
            atstrscalar = attr1["atstrscalar"]
            atintspec = attr1["atintspec"]
            atfloatimage = attr1["atfloatimage"]
            atfloatscalar = attr2["atfloatscalar"]
            atstrspec = attr2["atstrspec"]
            atintimage = attr2["atintimage"]

            self.assertTrue(isinstance(atintscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintscalar.h5object, tuple))
            self.assertEqual(atintscalar.parent, rt)
            self.assertEqual(atintscalar.name, 'atintscalar')
            self.assertEqual(atintscalar.path, '/@atintscalar')
            self.assertEqual(atintscalar.dtype, 'int64')
            self.assertEqual(atintscalar.shape, (1,))
            self.assertEqual(atintscalar.is_valid, True)
            self.assertEqual(atintscalar.read(), 0)
            self.assertEqual(atintscalar[...], 0)
            self.assertEqual(atintscalar.parent.h5object, rt.h5object)
            self.assertEqual(
                atintscalar.h5object, (attr0.h5object, 'atintscalar'))

            self.assertTrue(isinstance(atfloatspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatspec.h5object, tuple))
            self.assertEqual(atfloatspec.parent, rt)
            self.assertEqual(atfloatspec.name, 'atfloatspec')
            self.assertEqual(atfloatspec.path, '/@atfloatspec')
            self.assertEqual(atfloatspec.dtype, 'float32')
            self.assertEqual(atfloatspec.shape, (12,))
            self.assertEqual(atfloatspec.is_valid, True)
            self.assertEqual(list(atfloatspec.read()), [0.] * 12)
            self.assertEqual(list(atfloatspec[...]), [0.] * 12)
            self.assertEqual(atfloatspec.parent.h5object, rt.h5object)
            self.assertEqual(
                atfloatspec.h5object, (attr0.h5object, 'atfloatspec'))

            self.assertTrue(isinstance(atstrimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrimage.h5object, tuple))
            self.assertEqual(atstrimage.parent, rt)
            self.assertEqual(atstrimage.name, 'atstrimage')
            self.assertEqual(atstrimage.path, '/@atstrimage')
            self.assertEqual(atstrimage.dtype, 'string')
            self.assertEqual(atstrimage.shape, (2, 3))
            self.assertEqual(atstrimage.is_valid, True)
            self.myAssertImage(atstrimage.read(), [[''] * 3] * 2)
            self.myAssertImage(atstrimage[...], [[''] * 3] * 2)
            self.assertEqual(atstrimage.parent.h5object, rt.h5object)
            self.assertEqual(
                atstrimage.h5object, (attr0.h5object, 'atstrimage'))

            self.assertTrue(isinstance(atstrscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrscalar.h5object, tuple))
            self.assertEqual(atstrscalar.parent, entry)
            self.assertEqual(atstrscalar.name, 'atstrscalar')
            self.assertEqual(
                atstrscalar.path, '/entry12345:NXentry@atstrscalar')
            self.assertEqual(atstrscalar.dtype, 'string')
            self.assertEqual(atstrscalar.shape, ())
            self.assertEqual(atstrscalar.is_valid, True)
            self.assertEqual(atstrscalar.read(), '')
            self.assertEqual(atstrscalar[...], '')
            self.assertEqual(atstrscalar.parent.h5object, entry.h5object)
            self.assertEqual(
                atstrscalar.h5object, (attr1.h5object, 'atstrscalar'))

            self.assertTrue(isinstance(atintspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintspec.h5object, tuple))
            self.assertEqual(atintspec.parent, entry)
            self.assertEqual(atintspec.name, 'atintspec')
            self.assertEqual(atintspec.path, '/entry12345:NXentry@atintspec')
            self.assertEqual(atintspec.dtype, 'uint32')
            self.assertEqual(atintspec.shape, (2,))
            self.assertEqual(atintspec.is_valid, True)
            self.assertEqual(list(atintspec.read()), [0] * 2)
            self.assertEqual(list(atintspec[...]), [0] * 2)
            self.assertEqual(atintspec.parent.h5object, entry.h5object)
            self.assertEqual(atintspec.h5object, (attr1.h5object, 'atintspec'))

            self.assertTrue(
                isinstance(atfloatimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatimage.h5object, tuple))
            self.assertEqual(atfloatimage.parent, entry)
            self.assertEqual(atfloatimage.name, 'atfloatimage')
            self.assertEqual(
                atfloatimage.path, '/entry12345:NXentry@atfloatimage')
            self.assertEqual(atfloatimage.dtype, 'float64')
            self.assertEqual(atfloatimage.shape, (3, 2))
            self.assertEqual(atfloatimage.is_valid, True)
            self.myAssertImage(atfloatimage.read(), [[0.] * 2] * 3)
            self.myAssertImage(atfloatimage[...], [[0.] * 2] * 3)
            self.assertEqual(atfloatimage.parent.h5object, entry.h5object)
            self.assertEqual(
                atfloatimage.h5object, (attr1.h5object, 'atfloatimage'))

            self.assertTrue(
                isinstance(atfloatscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatscalar.h5object, tuple))
            self.assertEqual(atfloatscalar.parent, intscalar)
            self.assertEqual(atfloatscalar.name, 'atfloatscalar')
            self.assertEqual(atfloatscalar.path,
                             '/entry12345:NXentry/intscalar@atfloatscalar')
            self.assertEqual(atfloatscalar.dtype, 'float64')
            self.assertEqual(atfloatscalar.shape, (1,))
            self.assertEqual(atfloatscalar.is_valid, True)
            self.assertEqual(atfloatscalar.read(), 0)
            self.assertEqual(atfloatscalar[...], 0)
            self.assertEqual(atfloatscalar.parent.h5object, intscalar.h5object)
            self.assertEqual(
                atfloatscalar.h5object, (attr2.h5object, 'atfloatscalar'))

            self.assertTrue(isinstance(atstrspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrspec.h5object, tuple))
            self.assertEqual(atstrspec.parent, intscalar)
            self.assertEqual(atstrspec.name, 'atstrspec')
            self.assertEqual(atstrspec.path,
                             '/entry12345:NXentry/intscalar@atstrspec')
            self.assertEqual(atstrspec.dtype, 'string')
            self.assertEqual(atstrspec.shape, (4,))
            self.assertEqual(atstrspec.is_valid, True)
            self.assertEqual(list(atstrspec.read()), [''] * 4)
            self.assertEqual(list(atstrspec[...]), [''] * 4)
            self.assertEqual(atstrspec.parent.h5object, intscalar.h5object)
            self.assertEqual(atstrspec.h5object, (attr2.h5object, 'atstrspec'))

            self.assertTrue(isinstance(atintimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintimage.h5object, tuple))
            self.assertEqual(atintimage.parent, intscalar)
            self.assertEqual(atintimage.name, 'atintimage')
            self.assertEqual(atintimage.path,
                             '/entry12345:NXentry/intscalar@atintimage')
            self.assertEqual(atintimage.dtype, 'int32')
            self.assertEqual(atintimage.shape, (3, 2))
            self.assertEqual(atintimage.is_valid, True)
            self.myAssertImage(atintimage.read(), [[0] * 2] * 3)
            self.myAssertImage(atintimage[...], [[0] * 2] * 3)
            self.assertEqual(atintimage.parent.h5object, intscalar.h5object)
            self.assertEqual(
                atintimage.h5object, (attr2.h5object, 'atintimage'))

            self.myAssertRaise(
                Exception, attr2.create, "atintimage", "uint64", [4])
            atintimage = attr2.create("atintimage", "uint64", [4], True)

            self.assertTrue(isinstance(atintimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintimage.h5object, tuple))
            self.assertEqual(atintimage.parent, intscalar)
            self.assertEqual(atintimage.name, 'atintimage')
            self.assertEqual(atintimage.path,
                             '/entry12345:NXentry/intscalar@atintimage')
            self.assertEqual(atintimage.dtype, 'uint64')
            self.assertEqual(atintimage.shape, (4,))
            self.assertEqual(atintimage.is_valid, True)
            self.assertEqual(list(atintimage.read()), [0] * 4)
            self.assertEqual(list(atintimage[...]), [0] * 4)
            self.assertEqual(atintimage.parent.h5object, intscalar.h5object)
            self.assertEqual(
                atintimage.h5object, (attr2.h5object, 'atintimage'))

            attr2.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)

            attr2.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)

            intscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, False)
            self.assertEqual(atintimage.is_valid, False)

            intscalar.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            # self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyattribute_scalar(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            H5PYWriter.link(
                "/entry12345/instrument/detector/intimage", dt, "lkintimage")
            H5PYWriter.link(
                "/entry12345/instrument/detector/floatvec", dt, "lkfloatvec")
            H5PYWriter.link(
                "/entry12345/instrument/intspec", dt, "lkintspec")
            H5PYWriter.link(
                "/entry12345/instrument/detector", dt, "lkdet")
            H5PYWriter.link(
                "/notype/unknown", dt, "lkno")

            attr0 = rt.attributes
            attr1 = entry.attributes
            attr2 = intscalar.attributes

            print(attr0.h5object)
            self.assertTrue(isinstance(attr0, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr0.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr1, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr1.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr2, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr2.h5object, h5py.AttributeManager))

            self.assertEqual(len(attr0), 5)
            self.assertEqual(len(attr1), 1)
            self.assertEqual(len(attr2), 0)

            atintscalar = attr0.create("atintscalar", "int64")
            attr0.create("atfloatspec", "float32", [12])
            attr0.create("atstrimage", "string", [2, 3])
            atstrscalar = attr1.create("atstrscalar", "string")
            attr1.create("atintspec", "uint32", [2])
            attr1.create("atfloatimage", "float64", [3, 2])
            atfloatscalar = attr2.create("atfloatscalar", "float64")
            attr2.create("atstrspec", "string", [4])
            atintimage = attr2.create("atintimage", "int32", [3, 2])

            self.assertEqual(len(attr0), 8)
            self.assertEqual(len(attr1), 4)
            self.assertEqual(len(attr2), 3)

            print(dir(atintscalar))
            print(dir(atintscalar.h5object))

            chars = string.ascii_uppercase + string.digits
            stvl = [
                ''.join(self.__rnd.choice(chars)
                        for _ in range(self.__rnd.randint(1, 10)))
                for _ in range(10)]
            itvl = [self.__rnd.randint(1, 16000) for _ in range(100)]

            flvl = [self.__rnd.uniform(-200.0, 200) for _ in range(80)]

            atintscalar.write(itvl[0])

            self.assertTrue(isinstance(atintscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintscalar.h5object, tuple))
            self.assertEqual(atintscalar.parent, rt)
            self.assertEqual(atintscalar.name, 'atintscalar')
            self.assertEqual(atintscalar.path, '/@atintscalar')
            self.assertEqual(atintscalar.dtype, 'int64')
            self.assertEqual(atintscalar.shape, ())
            self.assertEqual(atintscalar.is_valid, True)
            self.assertEqual(atintscalar.read(), itvl[0])
            self.assertEqual(atintscalar[...], itvl[0])
            self.assertEqual(atintscalar.parent.h5object, rt.h5object)
            self.assertEqual(
                atintscalar.h5object, (attr0.h5object, 'atintscalar'))

            atintscalar[...] = itvl[1]

            self.assertEqual(atintscalar.h5object[0]['atintscalar'], itvl[1])
            self.assertEqual(atintscalar.read(), itvl[1])
            self.assertEqual(atintscalar[...], itvl[1])

            atintscalar[:] = itvl[2]

            self.assertEqual(atintscalar.h5object[0]['atintscalar'], itvl[2])
            self.assertEqual(atintscalar.read(), itvl[2])
            self.assertEqual(atintscalar[...], itvl[2])

            atintscalar[0] = itvl[3]

            self.assertEqual(atintscalar.h5object[0]['atintscalar'], itvl[3])
            self.assertEqual(atintscalar.read(), itvl[3])
            self.assertEqual(atintscalar[...], itvl[3])

            print("%s %s" % (stvl[0], type(stvl[0])))

            atstrscalar.write(stvl[0])

            self.assertTrue(isinstance(atstrscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrscalar.h5object, tuple))
            self.assertEqual(atstrscalar.parent, entry)
            self.assertEqual(atstrscalar.name, 'atstrscalar')
            self.assertEqual(
                atstrscalar.path, '/entry12345:NXentry@atstrscalar')
            self.assertEqual(atstrscalar.dtype, 'string')
            self.assertEqual(atstrscalar.shape, ())
            self.assertEqual(atstrscalar.is_valid, True)
            self.assertEqual(atstrscalar.read(), stvl[0])
            self.assertEqual(atstrscalar[...], stvl[0])
            self.assertEqual(atstrscalar.parent.h5object, entry.h5object)

            atstrscalar[...] = stvl[1]

            self.assertEqual(atstrscalar.h5object[0]['atstrscalar'], stvl[1])
            self.assertEqual(atstrscalar.read(), stvl[1])
            self.assertEqual(atstrscalar[...], stvl[1])

            atstrscalar[:] = stvl[2]

            self.assertEqual(atstrscalar.h5object[0]['atstrscalar'], stvl[2])
            self.assertEqual(atstrscalar.read(), stvl[2])
            self.assertEqual(atstrscalar[...], stvl[2])

            atstrscalar[0] = stvl[3]

            self.assertEqual(atstrscalar.h5object[0]['atstrscalar'], stvl[3])
            self.assertEqual(atstrscalar.read(), stvl[3])
            self.assertEqual(atstrscalar[...], stvl[3])

            atfloatscalar.write(flvl[0])

            self.assertTrue(
                isinstance(atfloatscalar, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatscalar.h5object, tuple))
            self.assertEqual(atfloatscalar.parent, intscalar)
            self.assertEqual(atfloatscalar.name, 'atfloatscalar')
            self.assertEqual(atfloatscalar.path,
                             '/entry12345:NXentry/intscalar@atfloatscalar')
            self.assertEqual(atfloatscalar.dtype, 'float64')
            self.assertEqual(atfloatscalar.shape, ())
            self.assertEqual(atfloatscalar.is_valid, True)
            self.assertEqual(atfloatscalar.read(), flvl[0])
            self.assertEqual(atfloatscalar[...], flvl[0])
            self.assertEqual(
                atfloatscalar.parent.h5object, intscalar.h5object)

            atfloatscalar[...] = flvl[1]

            self.assertEqual(
                atfloatscalar.h5object[0]['atfloatscalar'], flvl[1])
            self.assertEqual(atfloatscalar.read(), flvl[1])
            self.assertEqual(atfloatscalar[...], flvl[1])

            atfloatscalar[:] = flvl[2]

            self.assertEqual(
                atfloatscalar.h5object[0]['atfloatscalar'], flvl[2])
            self.assertEqual(atfloatscalar.read(), flvl[2])
            self.assertEqual(atfloatscalar[...], flvl[2])

            atfloatscalar[0] = flvl[3]

            self.assertEqual(
                atfloatscalar.h5object[0]['atfloatscalar'], flvl[3])
            self.assertEqual(atfloatscalar.read(), flvl[3])
            self.assertEqual(atfloatscalar[...], flvl[3])

            atfloatscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atfloatscalar.is_valid, False)

            atfloatscalar.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atfloatscalar.is_valid, True)

            intscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, False)
            self.assertEqual(atintimage.is_valid, False)
            self.assertEqual(atfloatscalar.is_valid, False)

            intscalar.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)
            self.assertEqual(atfloatscalar.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            # self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyattribute_spectrum(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)

        try:
            # overwrite = False
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            H5PYWriter.link(
                "/entry12345/instrument/detector/intimage", dt, "lkintimage")
            H5PYWriter.link(
                "/entry12345/instrument/detector/floatvec", dt, "lkfloatvec")
            H5PYWriter.link(
                "/entry12345/instrument/intspec", dt, "lkintspec")
            H5PYWriter.link(
                "/entry12345/instrument/detector", dt, "lkdet")
            H5PYWriter.link(
                "/notype/unknown", dt, "lkno")

            attr0 = rt.attributes
            attr1 = entry.attributes
            attr2 = intscalar.attributes

            print(attr0.h5object)
            self.assertTrue(isinstance(attr0, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr0.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr1, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr1.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr2, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr2.h5object, h5py.AttributeManager))

            self.assertEqual(len(attr0), 5)
            self.assertEqual(len(attr1), 1)
            self.assertEqual(len(attr2), 0)

            atintscalar = attr0.create("atintscalar", "int64")
            atfloatspec = attr0.create("atfloatspec", "float32", [12])
            attr0.create("atstrimage", "string", [2, 3])
            attr1.create("atstrscalar", "string")
            atintspec = attr1.create("atintspec", "uint32", [2])
            attr1.create("atfloatimage", "float64", [3, 2])
            attr2.create("atfloatscalar", "float64")
            atstrspec = attr2.create("atstrspec", "string", [4])
            atintimage = attr2.create("atintimage", "int32", [3, 2])

            self.assertEqual(len(attr0), 8)
            self.assertEqual(len(attr1), 4)
            self.assertEqual(len(attr2), 3)

            print(dir(atintscalar))
            print(dir(atintscalar.h5object))

            chars = string.ascii_uppercase + string.digits
            stvl = [
                [
                    ''.join(self.__rnd.choice(chars)
                            for _ in range(self.__rnd.randint(1, 10)))
                    for _ in range(4)]
                for _ in range(10)]

            itvl = [[self.__rnd.randint(1, 16000)
                     for _ in range(2)] for _ in range(10)]

            flvl = [[self.__rnd.uniform(-200.0, 200)
                     for _ in range(12)] for _ in range(10)]

            atfloatspec.write(flvl[0])

            self.assertTrue(isinstance(atfloatspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatspec.h5object, tuple))
            self.assertEqual(atfloatspec.parent, rt)
            self.assertEqual(atfloatspec.name, 'atfloatspec')
            self.assertEqual(atfloatspec.path, '/@atfloatspec')
            self.assertEqual(atfloatspec.dtype, 'float32')
            self.assertEqual(atfloatspec.shape, (12,))
            self.assertEqual(atfloatspec.is_valid, True)
            self.myAssertFloatList(list(atfloatspec.read()), flvl[0], 1e-3)
            self.myAssertFloatList(list(atfloatspec[...]), flvl[0], 1e-3)
            self.assertEqual(atfloatspec.parent.h5object, rt.h5object)

            atfloatspec[...] = flvl[1]

            self.myAssertFloatList(
                list(atfloatspec.h5object[0]['atfloatspec']), flvl[1], 1e-3)
            self.myAssertFloatList(list(atfloatspec.read()), flvl[1], 1e-3)
            self.myAssertFloatList(list(atfloatspec[...]), flvl[1], 1e-3)

            atfloatspec[:] = flvl[2]

            self.myAssertFloatList(
                list(atfloatspec.h5object[0]['atfloatspec']), flvl[2], 1e-3)
            self.myAssertFloatList(list(atfloatspec.read()), flvl[2], 1e-3)
            self.myAssertFloatList(list(atfloatspec[...]), flvl[2], 1e-3)

            atfloatspec[0:12] = flvl[3]

            self.myAssertFloatList(
                list(atfloatspec.h5object[0]['atfloatspec']), flvl[3], 1e-3)
            self.myAssertFloatList(list(atfloatspec.read()), flvl[3], 1e-3)
            self.myAssertFloatList(list(atfloatspec[...]), flvl[3], 1e-3)

            atfloatspec[1:10] = flvl[4][1:10]

            self.myAssertFloatList(
                list(atfloatspec.h5object[0]['atfloatspec'][1:10]),
                flvl[4][1:10], 1e-3)
            self.myAssertFloatList(
                list(atfloatspec.read()[1:10]), flvl[4][1:10], 1e-3)
            self.myAssertFloatList(
                list(atfloatspec[1:10]), flvl[4][1:10], 1e-3)

            atfloatspec[1:10] = flvl[3][1:10]

            self.myAssertFloatList(
                list(atfloatspec.h5object[0]['atfloatspec']), flvl[3], 1e-3)
            self.myAssertFloatList(list(atfloatspec.read()), flvl[3], 1e-3)
            self.myAssertFloatList(list(atfloatspec[...]), flvl[3], 1e-3)

            atintspec.write(itvl[0])

            self.assertTrue(isinstance(atintspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintspec.h5object, tuple))
            self.assertEqual(atintspec.parent, entry)
            self.assertEqual(atintspec.name, 'atintspec')
            self.assertEqual(atintspec.path, '/entry12345:NXentry@atintspec')
            self.assertEqual(atintspec.dtype, 'uint32')
            self.assertEqual(atintspec.shape, (2,))
            self.assertEqual(atintspec.is_valid, True)
            self.assertEqual(list(atintspec.read()), itvl[0])
            self.assertEqual(list(atintspec[...]), itvl[0])
            self.assertEqual(atintspec.parent.h5object, entry.h5object)

            atintspec[...] = itvl[1]

            self.assertEqual(list(atintspec.h5object[0]['atintspec']), itvl[1])
            self.assertEqual(list(atintspec.read()), itvl[1])
            self.assertEqual(list(atintspec[...]), itvl[1])

            atintspec[:] = itvl[2]

            self.assertEqual(list(atintspec.h5object[0]['atintspec']), itvl[2])
            self.assertEqual(list(atintspec.read()), itvl[2])
            self.assertEqual(list(atintspec[...]), itvl[2])

            atintspec[0:2] = itvl[3]

            self.assertEqual(list(atintspec.h5object[0]['atintspec']), itvl[3])
            self.assertEqual(list(atintspec.read()), itvl[3])
            self.assertEqual(list(atintspec[...]), itvl[3])

            atintspec[1:] = itvl[4][1:]

            self.assertEqual(
                list(atintspec.h5object[0]['atintspec'][1:]), itvl[4][1:])
            self.assertEqual([atintspec.read()[1:]], itvl[4][1:])
            self.assertEqual([atintspec[1:]], itvl[4][1:])

            atintspec[1:] = itvl[3][1:]

            self.assertEqual(list(atintspec.h5object[0]['atintspec']), itvl[3])
            self.assertEqual(list(atintspec.read()), itvl[3])
            self.assertEqual(list(atintspec[...]), itvl[3])

            atstrspec.write(stvl[0])

            self.assertTrue(isinstance(atstrspec, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrspec.h5object, tuple))
            self.assertEqual(atstrspec.parent, intscalar)
            self.assertEqual(atstrspec.name, 'atstrspec')
            self.assertEqual(atstrspec.path,
                             '/entry12345:NXentry/intscalar@atstrspec')
            self.assertEqual(atstrspec.dtype, 'string')
            self.assertEqual(atstrspec.shape, (4,))
            self.assertEqual(atstrspec.is_valid, True)
            self.assertEqual(list(atstrspec.read()), stvl[0])
            self.assertEqual(list(atstrspec[...]), stvl[0])
            self.assertEqual(atstrspec.parent.h5object, intscalar.h5object)

            atstrspec[...] = stvl[1]

            self.assertEqual(list(atstrspec.h5object[0]['atstrspec']), stvl[1])
            self.assertEqual(list(atstrspec.read()), stvl[1])
            self.assertEqual(list(atstrspec[...]), stvl[1])

            atstrspec[:] = stvl[2]

            self.assertEqual(list(atstrspec.h5object[0]['atstrspec']), stvl[2])
            self.assertEqual(list(atstrspec.read()), stvl[2])
            self.assertEqual(list(atstrspec[...]), stvl[2])

            atstrspec[0:4] = stvl[3]

            self.assertEqual(list(atstrspec.h5object[0]['atstrspec']), stvl[3])
            self.assertEqual(list(atstrspec.read()), stvl[3])
            self.assertEqual(list(atstrspec[...]), stvl[3])

            atstrspec[:3] = stvl[4][:3]

            self.assertEqual(
                list(atstrspec.h5object[0]['atstrspec'][:3]), stvl[4][:3])
            self.assertEqual(list(atstrspec.read())[:3], stvl[4][:3])
            self.assertEqual(list(atstrspec[:3]), stvl[4][:3])

            atstrspec[:3] = stvl[3][:3]

            self.assertEqual(list(atstrspec.h5object[0]['atstrspec']), stvl[3])
            self.assertEqual(list(atstrspec.read()), stvl[3])
            self.assertEqual(list(atstrspec[...]), stvl[3])

            atfloatspec.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)
            self.assertEqual(atfloatspec.is_valid, False)

            atfloatspec.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)
            self.assertEqual(atfloatspec.is_valid, True)

            intscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, False)
            self.assertEqual(atintimage.is_valid, False)
            self.assertEqual(atfloatspec.is_valid, True)

            intscalar.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)
            self.assertEqual(atfloatspec.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            # self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    # default createfile test
    # \brief It tests default settings
    def test_h5pyattribute_image(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        self._fname = '%s/%s%s.h5' % (os.getcwd(),
                                      self.__class__.__name__, fun)
        try:
            fl = H5PYWriter.create_file(self._fname)

            rt = fl.root()
            rt.create_group("notype")
            entry = rt.create_group("entry12345", "NXentry")
            ins = entry.create_group("instrument", "NXinstrument")
            det = ins.create_group("detector", "NXdetector")
            dt = entry.create_group("data", "NXdata")

            df0 = H5PYWriter.data_filter()
            df1 = H5PYWriter.data_filter()
            df1.rate = 2
            df2 = H5PYWriter.data_filter()
            df2.rate = 4
            df2.shuffle = 6

            entry.create_field("strscalar", "string")
            entry.create_field("floatscalar", "float64")
            intscalar = entry.create_field("intscalar", "uint64")
            ins.create_field("strspec", "string", [10], [6])
            ins.create_field("floatspec", "float32", [20], [16])
            ins.create_field("intspec", "int64", [30], [5])
            det.create_field("strimage", "string", [2, 2], [2, 1])
            det.create_field(
                "floatimage", "float64", [20, 10], dfilter=df0)
            det.create_field("intimage", "uint32", [0, 30], [1, 30])
            det.create_field("strvec", "string", [0, 2, 2], [1, 2, 2])
            det.create_field(
                "floatvec", "float64", [1, 20, 10], [1, 10, 10], dfilter=df1)
            det.create_field(
                "intvec", "uint32", [0, 2, 30], dfilter=df2)

            H5PYWriter.link(
                "/entry12345/instrument/detector/intimage", dt, "lkintimage")
            H5PYWriter.link(
                "/entry12345/instrument/detector/floatvec", dt, "lkfloatvec")
            H5PYWriter.link(
                "/entry12345/instrument/intspec", dt, "lkintspec")
            H5PYWriter.link(
                "/entry12345/instrument/detector", dt, "lkdet")
            H5PYWriter.link(
                "/notype/unknown", dt, "lkno")

            attr0 = rt.attributes
            attr1 = entry.attributes
            attr2 = intscalar.attributes

            print(attr0.h5object)
            self.assertTrue(isinstance(attr0, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr0.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr1, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr1.h5object, h5py.AttributeManager))
            self.assertTrue(isinstance(attr2, H5PYWriter.H5PYAttributeManager))
            self.assertTrue(
                isinstance(attr2.h5object, h5py.AttributeManager))

            self.assertEqual(len(attr0), 5)
            self.assertEqual(len(attr1), 1)
            self.assertEqual(len(attr2), 0)

            atintscalar = attr0.create("atintscalar", "int64")
            attr0.create("atfloatspec", "float32", [12])
            atstrimage = attr0.create("atstrimage", "string", [2, 3])
            attr1.create("atstrscalar", "string")
            attr1.create("atintspec", "uint32", [2])
            atfloatimage = attr1.create("atfloatimage", "float64", [3, 2])
            attr2.create("atfloatscalar", "float64")
            attr2.create("atstrspec", "string", [4])
            atintimage = attr2.create("atintimage", "int32", [3, 2])

            self.assertEqual(len(attr0), 8)
            self.assertEqual(len(attr1), 4)
            self.assertEqual(len(attr2), 3)

            print(dir(atintscalar))
            print(dir(atintscalar.h5object))

            chars = string.ascii_uppercase + string.digits
            stvl = [
                [
                    [
                        ''.join(
                            self.__rnd.choice(chars)
                            for _ in range(self.__rnd.randint(1, 10)))
                        for _ in range(3)]
                    for _ in range(2)]
                for _ in range(10)]

            itvl = [[[self.__rnd.randint(1, 16000) for _ in range(2)]
                     for _ in range(3)] for _ in range(10)]

            flvl = [[[self.__rnd.uniform(-200.0, 200) for _ in range(2)]
                     for _ in range(3)]
                    for _ in range(10)]

            atstrimage.write(stvl[0])

            self.assertTrue(isinstance(atstrimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atstrimage.h5object, tuple))
            self.assertEqual(atstrimage.parent, rt)
            self.assertEqual(atstrimage.name, 'atstrimage')
            self.assertEqual(atstrimage.path, '/@atstrimage')
            self.assertEqual(atstrimage.dtype, 'string')
            self.assertEqual(atstrimage.shape, (2, 3))
            self.assertEqual(atstrimage.is_valid, True)
            self.myAssertImage(atstrimage.read(), stvl[0])
            self.myAssertImage(atstrimage[...], stvl[0])
            self.assertEqual(atstrimage.parent.h5object, rt.h5object)

            atstrimage[...] = stvl[1]

            self.myAssertImage(atstrimage.h5object[0]['atstrimage'], stvl[1])
            self.myAssertImage(atstrimage.read(), stvl[1])
            self.myAssertImage(atstrimage[:, :], stvl[1])

            atstrimage[:, :] = stvl[2]

            self.myAssertImage(atstrimage.read(), stvl[2])
            self.myAssertImage(atstrimage[...], stvl[2])
            self.myAssertImage(atstrimage.h5object[0]['atstrimage'], stvl[2])

            atstrimage[0:2, :] = stvl[3]

            self.myAssertImage(atstrimage.read(), stvl[3])
            self.myAssertImage(atstrimage[...], stvl[3])
            self.myAssertImage(atstrimage.h5object[0]['atstrimage'], stvl[3])

            vv1 = [[stvl[4][j][i] for i in range(2)] for j in range(2)]

            print("TR %s" % str(atstrimage.read()))

            print("TRct", atstrimage[:, 1:])

            atstrimage[:, 1:] = vv1

            self.myAssertImage(atstrimage.read()[:, 1:], vv1)
            self.myAssertImage(atstrimage[:, 1:], vv1)
            self.myAssertImage(
                atstrimage.h5object[0]['atstrimage'][:, 1:], vv1)

            vv2 = [[stvl[3][j][i + 1] for i in range(2)] for j in range(2)]
            atstrimage[:, 1:] = vv2

            self.myAssertImage(atstrimage.read(), stvl[3])
            self.myAssertImage(atstrimage[...], stvl[3])
            self.myAssertImage(atstrimage.h5object[0]['atstrimage'], stvl[3])

            atfloatimage.write(flvl[0])

            self.assertTrue(isinstance(atfloatimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atfloatimage.h5object, tuple))
            self.assertEqual(atfloatimage.parent, entry)
            self.assertEqual(atfloatimage.name, 'atfloatimage')
            self.assertEqual(
                atfloatimage.path, '/entry12345:NXentry@atfloatimage')
            self.assertEqual(atfloatimage.dtype, 'float64')
            self.assertEqual(atfloatimage.shape, (3, 2))
            self.assertEqual(atfloatimage.is_valid, True)
            self.myAssertImage(atfloatimage.read(), flvl[0])
            self.myAssertImage(atfloatimage[...], flvl[0])
            self.assertEqual(atfloatimage.parent.h5object, entry.h5object)

            atfloatimage[...] = flvl[1]

            self.myAssertImage(atfloatimage.read(), flvl[1])
            self.myAssertImage(atfloatimage[:, :], flvl[1])
            self.myAssertImage(
                atfloatimage.h5object[0]['atfloatimage'], flvl[1])

            atfloatimage[:, :] = flvl[2]

            self.myAssertImage(atfloatimage.read(), flvl[2])
            self.myAssertImage(atfloatimage[...], flvl[2])
            self.myAssertImage(
                atfloatimage.h5object[0]['atfloatimage'], flvl[2])

            atfloatimage[0:3, :] = flvl[3]

            self.myAssertImage(atfloatimage.read(), flvl[3])
            self.myAssertImage(atfloatimage[...], flvl[3])
            self.myAssertImage(
                atfloatimage.h5object[0]['atfloatimage'], flvl[3])

            vv1 = [[flvl[4][j][i] for i in range(2)] for j in range(2)]
            atfloatimage[1:, :] = vv1

            self.myAssertImage(atfloatimage.read()[1:, :], vv1)
            self.myAssertImage(atfloatimage[1:, :], vv1)
            self.myAssertImage(
                atfloatimage.h5object[0]['atfloatimage'][1:, :], vv1)

            vv2 = [[flvl[3][j + 1][i] for i in range(2)] for j in range(2)]
            atfloatimage[1:, :] = vv2

            self.myAssertImage(atfloatimage.read(), flvl[3])
            self.myAssertImage(atfloatimage[...], flvl[3])
            self.myAssertImage(atfloatimage.h5object[0]['atfloatimage'],
                               flvl[3])

            atintimage.write(itvl[0])

            self.assertTrue(isinstance(atintimage, H5PYWriter.H5PYAttribute))
            self.assertTrue(isinstance(atintimage.h5object, tuple))
            self.assertEqual(atintimage.parent, intscalar)
            self.assertEqual(atintimage.name, 'atintimage')
            self.assertEqual(atintimage.path,
                             '/entry12345:NXentry/intscalar@atintimage')
            self.assertEqual(atintimage.dtype, 'int32')
            self.assertEqual(atintimage.shape, (3, 2))
            self.assertEqual(atintimage.is_valid, True)
            self.myAssertImage(atintimage.read(), itvl[0])
            self.myAssertImage(atintimage[...], itvl[0])
            self.assertEqual(atintimage.parent.h5object, intscalar.h5object)

            atintimage[...] = itvl[1]

            self.myAssertImage(atintimage.read(), itvl[1])
            self.myAssertImage(atintimage[:, :], itvl[1])
            self.myAssertImage(atintimage.h5object[0]['atintimage'], itvl[1])

            atintimage[:, :] = itvl[2]

            self.myAssertImage(atintimage.read(), itvl[2])
            self.myAssertImage(atintimage[...], itvl[2])
            self.myAssertImage(atintimage.h5object[0]['atintimage'], itvl[2])

            atintimage[0:3, :] = itvl[3]

            self.myAssertImage(atintimage.read(), itvl[3])
            self.myAssertImage(atintimage[...], itvl[3])
            self.myAssertImage(atintimage.h5object[0]['atintimage'], itvl[3])

            vv1 = [[itvl[4][j][i] for i in range(2)] for j in range(2)]
            atintimage[1:, :] = vv1

            self.myAssertImage(atintimage.read()[1:, :], vv1)
            self.myAssertImage(atintimage[1:, :], vv1)
            self.myAssertImage(
                atintimage.h5object[0]['atintimage'][1:, :], vv1)

            vv2 = [[itvl[3][j + 1][i] for i in range(2)] for j in range(2)]
            atintimage[1:, :] = vv2

            self.myAssertImage(atintimage.read(), itvl[3])
            self.myAssertImage(atintimage[...], itvl[3])
            self.myAssertImage(atintimage.h5object[0]['atintimage'], itvl[3])

            atintimage.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, False)

            atintimage.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)

            intscalar.close()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, False)
            self.assertEqual(atintimage.is_valid, False)

            intscalar.reopen()
            self.assertEqual(rt.is_valid, True)
            self.assertEqual(entry.is_valid, True)
            self.assertEqual(dt.is_valid, True)
            self.assertEqual(attr2.is_valid, True)
            self.assertEqual(atintimage.is_valid, True)

            fl.reopen()
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, False)

            fl.close()

            fl.reopen(True)
            self.assertEqual(fl.name, self._fname)
            self.assertEqual(fl.path, None)
            self.assertTrue(
                isinstance(fl.h5object, h5py.File))
            self.assertEqual(fl.parent, None)
            self.assertEqual(fl.readonly, True)

            fl.close()

            self.myAssertRaise(
                Exception, fl.reopen, True, True)
            self.myAssertRaise(
                Exception, fl.reopen, False, True)

            fl = H5PYWriter.open_file(self._fname, readonly=True)
            f = fl.root()
            # self.assertEqual(5, len(f.attributes))
            for at in f.attributes:
                print("%s %s %s" % (at.name, at.read(), at.dtype))
            self.assertEqual(
                f.attributes["file_name"][...],
                self._fname)
            self.assertTrue(
                f.attributes["NX_class"][...], "NXroot")
            self.assertEqual(f.size, 2)
            fl.close()

        finally:
            os.remove(self._fname)

    def test_h5py_vitualfield_image_concatinate(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        if not H5PYWriter.is_vds_supported():
            print("Skip the test: VDS not supported")
            return
        self._fname = '%s/%s%s.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname1 = '%s/%s%s_1.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname2 = '%s/%s%s_2.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname3 = '%s/%s%s_3.h5' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            vl = [[[self.__rnd.randint(1, 1600) for _ in range(20)]
                   for _ in range(10)]
                  for _ in range(30)]

            fl = H5PYWriter.create_file(fname1, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry1", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(fname2, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry2", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n + 10][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(fname3, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry3", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n + 20][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(self._fname, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry123", "NXentry")
            dt = entry.create_group("data", "NXdata")

            ef1 = H5PYWriter.target_field_view(
                fname1, "/entry1/data/data", [10, 10, 20], "uint32")
            ef2 = H5PYWriter.target_field_view(
                fname2, "/entry2/data/data", [10, 10, 20], "uint32")
            ef3 = H5PYWriter.target_field_view(
                fname3, "/entry3/data/data", [10, 10, 20], "uint32")

            vfl = H5PYWriter.virtual_field_layout([30, 10, 20], "uint32")
            vfl[0:10, :, :] = ef1
            vfl[10:20, :, :] = ef2
            vfl[20:30, :, :] = ef3

            intimage = dt.create_virtual_field("data", vfl)
            rw = intimage.read()
            for i in range(30):
                self.myAssertImage(rw[i], vl[i])
            intimage.close()

            dt.close()
            entry.close()
            fl.close()

        finally:
            os.remove(fname1)
            os.remove(fname2)
            os.remove(fname3)
            os.remove(self._fname)

    def test_h5py_vitualfield_image_interleaving(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        if not H5PYWriter.is_vds_supported():
            print("Skip the test: VDS not supported")
            return
        self._fname = '%s/%s%s.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname1 = '%s/%s%s_1.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname2 = '%s/%s%s_2.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname3 = '%s/%s%s_3.h5' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            vl = [[[self.__rnd.randint(1, 1600) for _ in range(20)]
                   for _ in range(10)]
                  for _ in range(30)]

            fl = H5PYWriter.create_file(fname1, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry1", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[3 * n][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(fname2, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry2", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[3 * n + 1][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(fname3, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry3", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "uint32", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[3 * n + 2][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(self._fname, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry123", "NXentry")
            dt = entry.create_group("data", "NXdata")

            ef1 = H5PYWriter.target_field_view(
                fname1, "/entry1/data/data", [10, 10, 20], "uint32")
            ef2 = H5PYWriter.target_field_view(
                fname2, "/entry2/data/data", [10, 10, 20], "uint32")
            ef3 = H5PYWriter.target_field_view(
                fname3, "/entry3/data/data", [10, 10, 20], "uint32")

            vfl = H5PYWriter.virtual_field_layout([30, 10, 20], "uint32")
            vfl[0:28:3, :, :] = ef1
            vfl[1:29:3, :, :] = ef2
            vfl[2:30:3, :, :] = ef3

            intimage = dt.create_virtual_field("data", vfl)
            rw = intimage.read()
            for i in range(30):
                self.myAssertImage(rw[i], vl[i])
            intimage.close()

            dt.close()
            entry.close()
            fl.close()

        finally:
            os.remove(fname1)
            os.remove(fname2)
            os.remove(fname3)
            os.remove(self._fname)

    def test_h5py_vitualfield_image_gap(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        if not H5PYWriter.is_vds_supported():
            print("Skip the test: VDS not supported")
            return
        self._fname = '%s/%s%s.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname1 = '%s/%s%s_1.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname3 = '%s/%s%s_3.h5' % (
            os.getcwd(), self.__class__.__name__, fun)

        try:
            vl = [[[self.__rnd.randint(1, 1600) for _ in range(20)]
                   for _ in range(10)]
                  for _ in range(30)]
            mone = [[[-1 for _ in range(20)]
                     for _ in range(10)]
                    for _ in range(10)]

            fl = H5PYWriter.create_file(fname1, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry1", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "int16", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(fname3, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry3", "NXentry")
            dt = entry.create_group("data", "NXdata")
            intimage = dt.create_field(
                "data", "int16", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n + 20][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage[...] = vv
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])
            intimage.close()
            dt.close()
            entry.close()
            fl.close()

            fl = H5PYWriter.create_file(self._fname, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry123", "NXentry")
            dt = entry.create_group("data", "NXdata")

            ef1 = H5PYWriter.target_field_view(
                fname1, "/entry1/data/data", [10, 10, 20], "int16")
            ef3 = H5PYWriter.target_field_view(
                fname3, "/entry3/data/data", [10, 10, 20], "int16")

            vfl = H5PYWriter.virtual_field_layout([30, 10, 20], "int16")
            vfl[0:10, :, :] = ef1
            vfl[20:30, :, :] = ef3

            intimage = dt.create_virtual_field("data", vfl, fillvalue=-1)
            rw = intimage.read()
            for i in range(10):
                self.myAssertImage(rw[i], vl[i])
            for i in range(10, 20):
                self.myAssertImage(rw[i], mone[i - 10])
            for i in range(20, 30):
                self.myAssertImage(rw[i], vl[i])
            intimage.close()

            dt.close()
            entry.close()
            fl.close()

        finally:
            os.remove(fname1)
            os.remove(fname3)
            os.remove(self._fname)

    def test_h5py_vitualfield_image_unlimited(self):
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))
        if not H5PYWriter.is_unlimited_vds_supported():
            print("Skip the test: unlimited VDS not supported")
            return
        self._fname = '%s/%s%s.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        fname1 = '%s/%s%s_1.h5' % (
            os.getcwd(), self.__class__.__name__, fun)
        # fname3 = '%s/%s%s_3.h5' % (
        #     os.getcwd(), self.__class__.__name__, fun)

        try:
            vl = [[[self.__rnd.randint(1, 1600) for _ in range(20)]
                   for _ in range(10)]
                  for _ in range(30)]

            fl1 = H5PYWriter.create_file(fname1, overwrite=True)
            rt1 = fl1.root()
            entry1 = rt1.create_group("entry1", "NXentry")
            dt1 = entry1.create_group("data", "NXdata")
            intimage1 = dt1.create_field(
                "data", "int16", [10, 10, 20], [1, 10, 20])
            vv = [[[vl[n][j][i] for i in range(20)]
                   for j in range(10)] for n in range(10)]
            vv2 = [[[vl[n][j][i]*2 for i in range(20)]
                   for j in range(10)] for n in range(10)]
            intimage1[...] = vv
            rw = intimage1.read()
            for i in range(10):
                self.myAssertImage(rw[i], vv[i])

            fl = H5PYWriter.create_file(self._fname, overwrite=True)
            rt = fl.root()
            entry = rt.create_group("entry123", "NXentry")
            dt = entry.create_group("data", "NXdata")

            ef1 = H5PYWriter.target_field_view(
                fname1, "/entry1/data/data", [10, 10, 20], "int16")

            vfl = H5PYWriter.virtual_field_layout([10, 10, 20], "int16")
            vfl.add(
                (slice(None, H5PYWriter.unlimited()),
                 slice(None), slice(None)),
                ef1,
                (slice(None, H5PYWriter.unlimited()),
                 slice(None), slice(None)))

            intimage = dt.create_virtual_field("data", vfl, fillvalue=-1)
            rw = intimage.read()

            for i in range(10):
                self.myAssertImage(rw[i], vl[i])

            intimage1.grow(0, 10)

            intimage1[10:, :, :] = vv2
            intimage1.close()
            dt1.close()
            entry1.close()
            fl1.close()

            rw2 = intimage.read()
            for i in range(10):
                self.myAssertImage(rw2[i], vl[i])
                for i in range(10):
                    self.myAssertImage(rw2[i + 10], vv2[i])
            intimage.close()

            dt.close()
            entry.close()
            fl.close()

        finally:
            os.remove(fname1)
            os.remove(self._fname)


if __name__ == '__main__':
    unittest.main()
