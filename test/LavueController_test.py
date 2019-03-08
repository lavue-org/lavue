#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the LavueController project
#
# GPL 2
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.
"""Contain the tests for the Lavue Controller."""

# Path
import sys
import os
import subprocess
import time
import unittest
import PyTango
import numpy as np

if sys.version_info > (3,):
    import queue as Queue
else:
    import Queue

# Path
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(path))

#: python3 running
PY3 = (sys.version_info > (3,))


class TangoCB(object):

    def __init__(self, queue):
        self.__queue = queue

    def push_event(self, *args, **kwargs):
        event_data = args[0]
        if event_data.err:
            result = event_data.errors
            print(result)
        else:
            result = event_data.attr_value.value
        self.__queue.put(result)


# Device test case
class LavueControllerTest(unittest.TestCase):
    """Test case for packet generation."""

    def __init__(self, methodName):
        """ constructor

        :param methodName: name of the test method
        """
        unittest.TestCase.__init__(self, methodName)
        self.instance = 'TEST'
        self.device = 'test/lavuecontroller/00'
        self.new_device_info_controller = PyTango.DbDevInfo()
        self.new_device_info_controller._class = "LavueController"
        self.new_device_info_controller.server = "LavueController/%s" % \
                                                 self.instance
        self.new_device_info_controller.name = self.device
        self.proxy = None

        if PY3:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python3 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python3 LavueController %s &" % self.instance
        else:
            if os.path.isfile("../LavueController"):
                self._startserver = \
                    "cd ..; python2 ./LavueController %s &" % self.instance
            else:
                self._startserver = \
                    "python2 LavueController %s &" % self.instance
        self._grepserver = \
            "ps -ef | grep 'LavueController %s' | grep -v grep" % \
            self.instance

    def setUp(self):
        print("\nsetting up ...")
        db = PyTango.Database()
        db.add_device(self.new_device_info_controller)
        db.add_server(
            self.new_device_info_controller.server,
            self.new_device_info_controller)
        self._psub = subprocess.call(
            self._startserver,
            stdout=None,
            stderr=None, shell=True)
        sys.stdout.write("waiting for server ")

        found = False
        cnt = 0
        dvname = self.new_device_info_controller.name
        while not found and cnt < 1000:
            try:
                sys.stdout.write(".")
                sys.stdout.flush()
                exl = db.get_device_exported(dvname)
                if dvname not in exl.value_string:
                    time.sleep(0.01)
                    cnt += 1
                    continue
                dp = PyTango.DeviceProxy(dvname)
                time.sleep(0.1)
                if dp.state() == PyTango.DevState.ON:
                    found = True
            except Exception:
                found = False
            cnt += 1
        print("")
        self.proxy = dp

    def tearDown(self):
        print("tearing down ...")
        db = PyTango.Database()
        db.delete_server(self.new_device_info_controller.server)

        if PY3:
            with subprocess.Popen(self._grepserver,
                                  stdout=subprocess.PIPE,
                                  shell=True) as proc:
                try:
                    outs, errs = proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()
                res = str(outs, "utf8").split("\n")
                for r in res:
                    sr = r.split()
                    if len(sr) > 2:
                        subprocess.call(
                            "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                            shell=True)
        else:
            pipe = subprocess.Popen(self._grepserver,
                                    stdout=subprocess.PIPE,
                                    shell=True).stdout

            res = str(pipe.read()).split("\n")
            for r in res:
                sr = r.split()
                if len(sr) > 2:
                    subprocess.call(
                        "kill -9 %s" % sr[1], stderr=subprocess.PIPE,
                        shell=True)
            pipe.close()

        self.proxy = None

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

        db = PyTango.Database()
        db.put_device_property(self.proxy.name(), {'DynamicROIs': True})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIs = str(wvl[0])
            rvl = self.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(hasattr(self.proxy, at))
                rvl = self.proxy.read_attribute(at).value
                self.assertTrue(np.array_equal(np.array(vl), rvl))

        db.put_device_property(self.proxy.name(), {'DynamicROIs': False})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIs = str(wvl[0])
            rvl = self.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(not hasattr(self.proxy, at))

        db.put_device_property(self.proxy.name(), {'DynamicROIs': True})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIs = str(wvl[0])
            rvl = self.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(hasattr(self.proxy, at))
                rvl = self.proxy.read_attribute(at).value
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

        db = PyTango.Database()
        db.put_device_property(self.proxy.name(), {'DynamicROIsValues': True})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.proxy.read_attribute(at).value
                if at.endswith("Sums"):
                    self.assertTrue(np.array_equal(np.array(vl), rvl))
                else:
                    self.assertEqual(vl[0], rvl)

        db.put_device_property(self.proxy.name(), {'DynamicROIsValues': False})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                self.assertTrue(not hasattr(self.proxy, at))

        db.put_device_property(self.proxy.name(), {'DynamicROIsValues': True})
        self.proxy.Init()

        for wvl in testvalues:
            self.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.proxy.read_attribute(at).value
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
        db = PyTango.Database()

        for wvl in testvalues:
            db.put_device_property(
                self.proxy.name(), {'ROIAttributesNames': wvl[0]})
            db.put_device_property(self.proxy.name(), {'DynamicROIs': wvl[1]})
            db.put_device_property(
                self.proxy.name(), {'DynamicROIsValues': wvl[2]})
            self.proxy.Init()
            self.proxy.DetectorROIs = DetectorROIs if wvl[3] else "{}"
            self.proxy.DetectorROIsValues = DetectorROIsValues \
                if wvl[3] else "{}"

            attrs = [el for el in dir(self.proxy)
                     if (el.endswith("ROI") or el.endswith("Sum")
                         or el.endswith("Sums"))]
            self.assertTrue(not (set(attrs) - set(wvl[4])))
            for at in wvl[4]:
                self.assertTrue(hasattr(self.proxy, at))
            for at in list(set(wvl[0]) - set(wvl[4])):
                self.assertTrue(not hasattr(self.proxy, at))

    def test_State(self):
        """Test for State"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        self.assertEqual(self.proxy.State(), PyTango.DevState.ON)

    def test_Status(self):
        """Test for Status"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        self.assertEqual(self.proxy.Status(), 'State is ON')

    def test_BeamCenterX(self):
        """Test for BeamCenterX"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.proxy.subscribe_event(
            "BeamCenterX", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.BeamCenterX = wvl
            rvl = self.proxy.BeamCenterX
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.proxy.unsubscribe_event(cb_id)

    def test_BeamCenterY(self):
        """Test for BeamCenterY"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.proxy.subscribe_event(
            "BeamCenterY", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.BeamCenterY = wvl
            rvl = self.proxy.BeamCenterY
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.proxy.unsubscribe_event(cb_id)

    def test_DetectorDistance(self):
        """Test for DetectorDistance"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.proxy.subscribe_event(
            "DetectorDistance", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.DetectorDistance = wvl
            rvl = self.proxy.DetectorDistance
            self.assertEqual(wvl, rvl)

            elem = queue.get(block=True, timeout=3)
            self.assertEqual(elem, wvl)

        self.proxy.unsubscribe_event(cb_id)

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
        cb_id = self.proxy.subscribe_event(
            "DetectorROIs", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.DetectorROIs = str(wvl[0])
            rvl = self.proxy.DetectorROIs
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.proxy.read_attribute(at).value
                self.assertTrue(np.array_equal(np.array(vl), rvl))

                elem = queue.get(block=True, timeout=3)
                self.assertEqual(elem, wvl[0])

        self.proxy.unsubscribe_event(cb_id)

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
        cb_id = self.proxy.subscribe_event(
            "DetectorROIsValues", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.DetectorROIsValues = str(wvl[0])
            rvl = self.proxy.DetectorROIsValues
            self.assertEqual(wvl[0], rvl)
            for at, vl in wvl[1]:
                rvl = self.proxy.read_attribute(at).value
                if at.endswith("Sums"):
                    self.assertTrue(np.array_equal(np.array(vl), rvl))
                else:
                    self.assertEqual(vl[0], rvl)

                elem = queue.get(block=True, timeout=3)
                self.assertEqual(elem, wvl[0])

        self.proxy.unsubscribe_event(cb_id)

    def test_Energy(self):
        """Test for Energy"""
        print("Run: %s.%s() " % (
            self.__class__.__name__, sys._getframe().f_code.co_name))
        testvalues = [12.3, 123.2, -3.43, 0., 23423.]

        queue = Queue.Queue()
        cb = TangoCB(queue)
        cb_id = self.proxy.subscribe_event(
            "Energy", PyTango.EventType.CHANGE_EVENT, cb)
        elem = queue.get(block=True, timeout=3)

        for wvl in testvalues:
            self.proxy.Energy = wvl
            rvl = self.proxy.Energy
            self.assertEqual(wvl, rvl)
            elem = queue.get(block=True, timeout=3)
            self.assertEqual(wvl, elem)

        self.proxy.unsubscribe_event(cb_id)


def main():
    """ main function"""
    unittest.main()


# Main execution
if __name__ == "__main__":
    main()
