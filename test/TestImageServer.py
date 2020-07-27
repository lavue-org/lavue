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
        self.attr_LastImageTaken_read = ""
        self.attr_LastImagePath_read = ""
        self.attr_LastImage_read = [
            [i + 100 * j for i in range(512)] for j in range(256)]
        self.attr_ReadyEventImage_read = [
            [i + 100 * j for i in range(128)] for j in range(256)]
        self.attr_ChangeEventImage_read = [
            [i + 100 * j for i in range(512)] for j in range(128)]
        self.set_change_event("ChangeEventImage", True, False)
        self.ReadyEventImage = self.get_device_attr().get_attr_by_name(
            "ReadyEventImage")
        self.ReadyEventImage.set_data_ready_event(True)

    def read_LastImageTaken(self, attr):
        attr.set_value(self.attr_LastImageTaken_read)

    def write_LastImageTaken(self, attr):
        self.attr_LastImageTaken_read = attr.get_write_value()

    def read_LastImagePath(self, attr):
        attr.set_value(self.attr_LastImagePath_read)

    def write_LastImagePath(self, attr):
        self.attr_LastImagePath_read = attr.get_write_value()

    def read_LastImage(self, attr):
        attr.set_value(self.attr_LastImage_read)

    def read_ChangeEventImage(self, attr):
        attr.set_value(self.attr_ChangeEventImage_read)

    def read_ReadyEventImage(self, attr):
        attr.set_value(self.attr_ReadyEventImage_read)

    def StartAcq(self):
        """ Start the acquisition. """
        self.attr_LastImage_read = \
            [[random.randint(0, 1000) for i in range(512)] for j in range(256)]

    def ReadyEventAcq(self):
        """ Start the acquisition. """
        self.attr_ReadyEventImage_read = \
            [[random.randint(0, 1000) for i in range(128)] for j in range(256)]
        self.push_data_ready_event("ReadyEventImage", 0)

    def ChangeEventAcq(self):
        """ Start the acquisition. """
        self.attr_ChangeEventImage_read = \
            [[random.randint(0, 1000) for i in range(512)] for j in range(128)]
        self.push_change_event("ChangeEventImage",
                               self.attr_ChangeEventImage_read)


class TestImageServerClass(PyTango.DeviceClass):

    cmd_list = {
        'StartAcq':
        [[PyTango.DevVoid, "none"],
         [PyTango.DevVoid, "none"]],
        'ReadyEventAcq':
        [[PyTango.DevVoid, "none"],
         [PyTango.DevVoid, "none"]],
        'ChangeEventAcq':
        [[PyTango.DevVoid, "none"],
         [PyTango.DevVoid, "none"]],
        }

    attr_list = {
        'LastImageTaken':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ_WRITE],
         {
             'label': "LastImageTaken",
             'description': "provide last image taken name",
         }],
        'LastImagePath':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ_WRITE],
         {
             'label': "LastImagePath",
             'description': "provide last image path",
         }],
        'LastImage':
        [[PyTango.DevLong,
          PyTango.IMAGE,
          PyTango.READ, 4096, 4096],
         {
             'label': "LastImage",
             'description': "provide last image data",
         }],
        'ReadyEventImage':
        [[PyTango.DevLong,
          PyTango.IMAGE,
          PyTango.READ, 4096, 4096],
         {
             'label': "ReadyEventImage",
             'description': "provide ready event image data",
         }],
        'ChangeEventImage':
        [[PyTango.DevLong,
          PyTango.IMAGE,
          PyTango.READ, 4096, 4096],
         {
             'label': "ChangeEventImage",
             'description': "provide change event image data",
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
