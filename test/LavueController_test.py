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

"""Contain the tests for the Lavue Controller."""

# Path
import sys
import os
import unittest
try:
    import tango
except ImportError:
    import PyTango as tango
import numpy as np

if sys.version_info > (3,):
    import queue as Queue
else:
    import Queue

try:
    from .LavueControllerSetUp import ControllerSetUp, TangoCB
except Exception:
    from LavueControllerSetUp import ControllerSetUp, TangoCB


# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


# Device test case
class LavueControllerTest(unittest.TestCase):
    """Test case for packet generation."""

    def __init__(self, methodName):
        """ constructor

        :param methodName: name of the test method
        """
        unittest.TestCase.__init__(self, methodName)
        self.__lcsu = ControllerSetUp()

    def setUp(self):
        print("\nsetting up ...")
        self.__lcsu.setUp()

    def tearDown(self):
        print("tearing down ...")
        self.__lcsu.tearDown()

    def test_property_DynamicROIs(self):
        """ test the property DynamicROIs """
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

        testvalues = [
            ['{"Pilatus": [[61, 91, 83, 146], [332, 93, 382, 141], '
             '[116, 69, 279, 94], [91, 155, 157, 199]]}',
             [["PilatusROI",
               [61, 91, 83, 146, 332, 93, 382, 141,
                116, 69, 279, 94, 91, 155, 157, 199]]]],
            ['{"Pilatus1": [[61, 91, 83, 146], [332, 93, 382, 141], '
             '[116, 69, 279, 94]], "Pilatus2": [[91, 155, 157, 199]]}',
             [["Pilatus1ROI",
               [61, 91, 83, 146, 332, 93, 382, 141,
                116, 69, 279, 94]]],
             [["Pilatus2ROI",
               [91, 155, 157, 199]]]],
            ['{"lambda": [[61, 91, 83, 146]]}',
             [["LambdaROI",
               [61, 91, 83, 146]]]],
            ['{"lambda2": [[61, 91, 83, 146], [1, 21, 33, 146]]}',
             [["Lambda2ROI",
               [61, 91, 83, 146, 1, 21, 33, 146]]]],
            ['{"__null__": [[61, 91, 83, 146]]}',
             [["ROI",
               [61, 91, 83, 146]]]],
            ['{"__null__": [[61, 91, 83, 146], [1, 21, 33, 146]]}',
             [["ROI",
               [61, 91, 83, 146, 1, 21, 33, 146]]]],
        ]

        db = tango.Database()
        db.put_device_property(self.__lcsu.proxy.name(), {'DynamicROIs': True})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIs = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(hasattr(self.__lcsu.proxy, at))
                rvl = self.__lcsu.proxy.read_attribute(at).value
                self.assertTrue(np.array_equal(np.array(vl), rvl))

        db.put_device_property(
            self.__lcsu.proxy.name(), {'DynamicROIs': False})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIs = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(not hasattr(self.__lcsu.proxy, at))

        db.put_device_property(self.__lcsu.proxy.name(), {'DynamicROIs': True})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIs = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(hasattr(self.__lcsu.proxy, at))
                rvl = self.__lcsu.proxy.read_attribute(at).value
                self.assertTrue(np.array_equal(np.array(vl), rvl))

    def test_property_DynamicROIsValues(self):
        """ test the property DynamicROIsValues """
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

        testvalues = [
            ['{"Pilatus": [1.23, 12.321, 83.323, 146.32]}',
             [["PilatusSums",
               [1.23, 12.321, 83.323, 146.32]]]],
            ['{"Pilatus1": [1.23, 12.321, 83.323], '
             '"Pilatus2": [146.32]}',
             [["Pilatus1Sums",
               [1.23, 12.321, 83.323]]],
             [["Pilatus2Sum",
               [146.32]]]],
            ['{"lambda": [16.1]}',
             [["LambdaSum",
               [16.1]]]],
            ['{"lambda2": [1231.61, 14.6]}',
             [["Lambda2Sums",
               [1231.61, 14.6]]]],
            ['{"__null__": [12323.0]}',
             [["Sum",
               [12323.]]]],
            ['{"__null__": [12312.0, 1232131.0]}',
             [["Sums",
               [12312., 1232131.]]]],
        ]

        db = tango.Database()
        db.put_device_property(
            self.__lcsu.proxy.name(), {'DynamicROIsValues': True})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.__lcsu.proxy.read_attribute(at).value
                if at.endswith("Sums"):
                    self.assertTrue(np.array_equal(np.array(vl), rvl))
                else:
                    self.assertEqual(vl[0], rvl)

        db.put_device_property(
            self.__lcsu.proxy.name(), {'DynamicROIsValues': False})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(not hasattr(self.__lcsu.proxy, at))

        db.put_device_property(
            self.__lcsu.proxy.name(), {'DynamicROIsValues': True})
        self.__lcsu.proxy.Init()

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.__lcsu.proxy.read_attribute(at).value
                if at.endswith("Sums"):
                    self.assertTrue(np.array_equal(np.array(vl), rvl))
                else:
                    self.assertEqual(vl[0], rvl)

    def test_property_ROIAttributesNames(self):
        """ test the property ROIAttributesNames """
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

        DetectorROIsValues = \
            '{"Pilatus1": [1.23, 12.321, 83.323], "Pilatus2": [146.32]}'
        DetectorROIs = \
            '{"Pilatus1": [[61, 91, 83, 146], [332, 93, 382, 141], ' \
            '[116, 69, 279, 94]], "Pilatus2": [[91, 155, 157, 199]]}'
        testvalues = [
            [[], True, True, False, []],
            [["MyROI"], True, True, False, ["MyROI"]],
            [["MyROI"], True, True, False, ["MyROI"]],
            [["MySum"], True, True, False, ["MySum"]],
            [["MySums"], True, True, False, ["MySums"]],
            [["MySuma"], True, True, False, []],
            [["YROI", "YSum", "YSums", "YSuma"], True, True, False,
             ["YROI", "YSum", "YSums"]],
            [["YROI", "YSum", "YSums", "YSuma"], True, True, False,
             ["YROI", "YSum", "YSums"]],
            [[], False, False, False, []],
            [["MyROI"], False, False, False, ["MyROI"]],
            [["MySum"], False, False, False, ["MySum"]],
            [["MySums"], False, False, False, ["MySums"]],
            [["MySuma"], False, False, False, []],
            [["YROI", "YSum", "YSums", "YSuma"], False, False, False,
             ["YROI", "YSum", "YSums"]],
            [["Pilatus1ROI", "Pilatus2ROI", "Pilatus1Sum", "Pilatus2Sum"],
             False, False, False,
             ["Pilatus1ROI", "Pilatus2ROI", "Pilatus1Sum", "Pilatus2Sum"]],
            [[], True, True, True,
             ["Pilatus1ROI", "Pilatus2ROI", "Pilatus1Sums", "Pilatus2Sum"]],
        ]
        db = tango.Database()

        for wvl in testvalues:
            db.put_device_property(
                self.__lcsu.proxy.name(), {'ROIAttributesNames': wvl[0]})
            db.put_device_property(
                self.__lcsu.proxy.name(), {'DynamicROIs': wvl[1]})
            db.put_device_property(
                self.__lcsu.proxy.name(), {'DynamicROIsValues': wvl[2]})
            self.__lcsu.proxy.Init()
            self.__lcsu.proxy.DetectorROIs = DetectorROIs if wvl[3] else "{}"
            self.__lcsu.proxy.DetectorROIsValues = DetectorROIsValues \
                if wvl[3] else "{}"

            attrs = [el for el in dir(self.__lcsu.proxy)
                     if (el.endswith("ROI") or el.endswith("Sum")
                         or el.endswith("Sums"))]
            self.assertTrue(not (set(attrs) - set(wvl[4])))
            for at in wvl[4]:
                self.assertTrue(hasattr(self.__lcsu.proxy, at))
            for at in list(set(wvl[0]) - set(wvl[4])):
                self.assertTrue(not hasattr(self.__lcsu.proxy, at))

    def test_State(self):
        """Test for State"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        self.assertEqual(self.__lcsu.proxy.state(), tango.DevState.ON)

    def test_Status(self):
        """Test for Status"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        self.assertEqual(self.__lcsu.proxy.Status(), 'State is ON')

    def test_BeamCenterX(self):
        """Test for BeamCenterX"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "BeamCenterX", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.BeamCenterX = wvl
            rvl = self.__lcsu.proxy.BeamCenterX
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.__lcsu.proxy.unsubscribe_event(cb_id)

    def test_BeamCenterY(self):
        """Test for BeamCenterY"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "BeamCenterY", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.BeamCenterY = wvl
            rvl = self.__lcsu.proxy.BeamCenterY
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.__lcsu.proxy.unsubscribe_event(cb_id)

    def test_DetectorDistance(self):
        """Test for DetectorDistance"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "DetectorDistance", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorDistance = wvl
            rvl = self.__lcsu.proxy.DetectorDistance
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.__lcsu.proxy.unsubscribe_event(cb_id)

    def test_DetectorROIs(self):
        """Test for DetectorROIs"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))

        testvalues = [
            ['{"Pilatus": [[61, 91, 83, 146], [332, 93, 382, 141], '
             '[116, 69, 279, 94], [91, 155, 157, 199]]}',
             [["PilatusROI",
               [61, 91, 83, 146, 332, 93, 382, 141,
                116, 69, 279, 94, 91, 155, 157, 199]]]],
            ['{"Pilatus1": [[61, 91, 83, 146], [332, 93, 382, 141], '
             '[116, 69, 279, 94]], "Pilatus2": [[91, 155, 157, 199]]}',
             [["Pilatus1ROI",
               [61, 91, 83, 146, 332, 93, 382, 141,
                116, 69, 279, 94]]],
             [["Pilatus2ROI",
               [91, 155, 157, 199]]]],
            ['{"lambda": [[61, 91, 83, 146]]}',
             [["LambdaROI",
               [61, 91, 83, 146]]]],
            ['{"lambda2": [[61, 91, 83, 146], [1, 21, 33, 146]]}',
             [["Lambda2ROI",
               [61, 91, 83, 146, 1, 21, 33, 146]]]],
            ['{"__null__": [[61, 91, 83, 146]]}',
             [["ROI",
               [61, 91, 83, 146]]]],
            ['{"__null__": [[61, 91, 83, 146], [1, 21, 33, 146]]}',
             [["ROI",
               [61, 91, 83, 146, 1, 21, 33, 146]]]],
        ]
        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "DetectorROIs", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIs = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.__lcsu.proxy.read_attribute(at).value
                self.assertTrue(np.array_equal(np.array(vl), rvl))

                elem = queue.get(block=True, timeout=3)
                self.assertEqual(elem, wvl[0])

        self.__lcsu.proxy.unsubscribe_event(cb_id)

    def test_DetectorROIsValues(self):
        """Test for DetectorROIsValues"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [
            ['{"Pilatus": [1.23, 12.321, 83.323, 146.32]}',
             [["PilatusSums",
               [1.23, 12.321, 83.323, 146.32]]]],
            ['{"Pilatus1": [1.23, 12.321, 83.323], '
             '"Pilatus2": [146.32]}',
             [["Pilatus1Sums",
               [1.23, 12.321, 83.323]]],
             [["Pilatus2Sum",
               [146.32]]]],
            ['{"lambda": [16.1]}',
             [["LambdaSum",
               [16.1]]]],
            ['{"lambda2": [1231.61, 14.6]}',
             [["Lambda2Sums",
               [1231.61, 14.6]]]],
            ['{"__null__": [12323.0]}',
             [["Sum",
               [12323.]]]],
            ['{"__null__": [12312.0, 1232131.0]}',
             [["Sums",
               [12312., 1232131.]]]],
        ]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "DetectorROIsValues", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.__lcsu.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.__lcsu.proxy.read_attribute(at).value
                if at.endswith("Sums"):
                    self.assertTrue(np.array_equal(np.array(vl), rvl))
                else:
                    self.assertEqual(vl[0], rvl)

                elem = queue.get(block=True, timeout=3)
                self.assertEqual(elem, wvl[0])

        self.__lcsu.proxy.unsubscribe_event(cb_id)

    def test_Energy(self):
        """Test for Energy"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.__lcsu.proxy.subscribe_event(
            "Energy", tango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.__lcsu.proxy.Energy = wvl
            rvl = self.__lcsu.proxy.Energy
            self.assertEqual(wvl, rvl)
            elem = queue.get(block=True, timeout=3)
            self.assertEqual(wvl, elem)

        self.__lcsu.proxy.unsubscribe_event(cb_id)


def main():
    """ main function"""
    unittest.main()


# Main execution
if __name__ == "__main__":
    main()
