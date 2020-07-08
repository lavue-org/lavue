#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""This is a tango server project for detetor."""

__all__ = ["TestImageServer", "TestImageServerClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
import random


class TestImageServer (PyTango.Device_4Impl):

    def __init__(self, cl, name):
        PyTango.Device_4Impl.__init__(self, cl, name)
        TestImageServer.init_device(self)

    def init_device(self):
        self.set_state(PyTango.DevState.ON)
        self.get_device_properties(self.get_device_class())
        # self.attr_LastImage_read = [[10]*2048]*1024
        self.attr_LastImage_read = [
            [i + 100 * j for i in range(512)] for j in range(256)]

    def read_LastImage(self, attr):
        attr.set_value(self.attr_LastImage_read)

    def StartAcq(self):
        """ Start the acquisition. """
        self.attr_LastImage_read = \
            [[random.randint(0, 1000) for i in range(512)] for j in range(256)]


class TestImageServerClass(PyTango.DeviceClass):

    cmd_list = {
        'StartAcq':
        [[PyTango.DevVoid, "none"],
         [PyTango.DevVoid, "none"]],
        }

    attr_list = {
        'LastImage':
        [[PyTango.DevLong,
          PyTango.IMAGE,
          PyTango.READ, 4096, 4096],
         {
             'label': "LastImage",
             'description': "provide last image data",
         }],
    }


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(TestImageServerClass, TestImageServer, 'TestImageServer')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed as e:
        print('-------> Received a DevFailed exception: %s' % str(e))
    except Exception as e:
        print('-------> An unforeseen exception occured.... %s' % str(e))


if __name__ == '__main__':
    main()
