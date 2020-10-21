#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""This is a tango server project for detetor."""

__all__ = ["TestImageServer", "TestImageServerClass", "main"]

__docformat__ = 'restructuredtext'

try:
    import tango
except ImportError:
    import PyTango as tango

import sys
import random


class TestImageServer (tango.Device_4Impl):

    def __init__(self, cl, name):
        tango.Device_4Impl.__init__(self, cl, name)
        TestImageServer.init_device(self)

    def init_device(self):
        self.set_state(tango.DevState.ON)
        self.get_device_properties(self.get_device_class())
        # self.attr_LastImage_read = [[10]*2048]*1024
        self.attr_LastImageTaken_read = ""
        self.attr_LastImagePath_read = ""
        self.attr_Spectrum1_read = [3 * j for j in range(256)]
        self.attr_Spectrum2_read = [2 * j for j in range(256)]
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

    def read_Spectrum1(self, attr):
        attr.set_value(self.attr_Spectrum1_read)

    def read_Spectrum2(self, attr):
        attr.set_value(self.attr_Spectrum2_read)

    def read_ChangeEventImage(self, attr):
        attr.set_value(self.attr_ChangeEventImage_read)

    def read_ReadyEventImage(self, attr):
        attr.set_value(self.attr_ReadyEventImage_read)

    def StartAcq(self):
        """ Start the acquisition. """
        self.attr_LastImage_read = \
            [[random.randint(0, 1000) for i in range(512)] for j in range(256)]
        self.attr_Spectrum1_read = \
            [random.randint(0, 1000) for j in range(256)]
        self.attr_Spectrum2_read = \
            [random.randint(0, 1000) for j in range(256)]

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


class TestImageServerClass(tango.DeviceClass):

    cmd_list = {
        'StartAcq':
        [[tango.DevVoid, "none"],
         [tango.DevVoid, "none"]],
        'ReadyEventAcq':
        [[tango.DevVoid, "none"],
         [tango.DevVoid, "none"]],
        'ChangeEventAcq':
        [[tango.DevVoid, "none"],
         [tango.DevVoid, "none"]],
        }

    attr_list = {
        'LastImageTaken':
        [[tango.DevString,
          tango.SCALAR,
          tango.READ_WRITE],
         {
             'label': "LastImageTaken",
             'description': "provide last image taken name",
         }],
        'LastImagePath':
        [[tango.DevString,
          tango.SCALAR,
          tango.READ_WRITE],
         {
             'label': "LastImagePath",
             'description': "provide last image path",
         }],
        'LastImage':
        [[tango.DevLong,
          tango.IMAGE,
          tango.READ, 4096, 4096],
         {
             'label': "LastImage",
             'description': "provide last image data",
         }],
        'Spectrum1':
        [[tango.DevLong,
          tango.SPECTRUM,
          tango.READ, 4096],
         {
             'label': "Spectrum1",
             'description': "provide last spectrum data",
         }],
        'Spectrum2':
        [[tango.DevLong,
          tango.SPECTRUM,
          tango.READ, 4096],
         {
             'label': "Spectrum2",
             'description': "provide last spectrum data",
         }],
        'ReadyEventImage':
        [[tango.DevLong,
          tango.IMAGE,
          tango.READ, 4096, 4096],
         {
             'label': "ReadyEventImage",
             'description': "provide ready event image data",
         }],
        'ChangeEventImage':
        [[tango.DevLong,
          tango.IMAGE,
          tango.READ, 4096, 4096],
         {
             'label': "ChangeEventImage",
             'description': "provide change event image data",
         }],
    }


def main():
    try:
        py = tango.Util(sys.argv)
        py.add_class(TestImageServerClass, TestImageServer, 'TestImageServer')

        U = tango.Util.instance()
        U.server_init()
        U.server_run()

    except tango.DevFailed as e:
        print('-------> Received a DevFailed exception: %s' % str(e))
    except Exception as e:
        print('-------> An unforeseen exception occured.... %s' % str(e))


if __name__ == '__main__':
    main()
