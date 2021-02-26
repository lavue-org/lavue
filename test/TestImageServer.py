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
import struct
import numpy


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
        self.attr_ImageUChar = numpy.array([[2, 5], [3, 4]], dtype='uint8')
        self.attr_ImageEncoded = self.encodeImage()
        self.__images = [
            b'YATD\x02\x00@\x00\x02\x00\x00\x00\x05\x00\x00\x00\x00\x00'
            b'\x02\x00\x06\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
            b'\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05\x00\x06\x00'
            b'\x07\x00\x08\x00\t\x00\n\x00\x0b\x00\x0c\x00\r\x00\x0e\x00'
            b'\x0f\x00\x10\x00\x11\x00\x12\x00\x13\x00\x14\x00\x15\x00\x16'
            b'\x00\x17\x00',
            b'YATD\x02\x00@\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00'
            b'\x03\x00\x02\x00\x03\x00\x04\x00\x00\x00\x00\x00\x00\x00\x04'
            b'\x00\x00\x00\x08\x00\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00'
            b'\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00\x07'
            b'\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00\n\x00\x00\x00\x0b'
            b'\x00\x00\x00\x0c\x00\x00\x00\r\x00\x00\x00\x0e\x00\x00\x00\x0f'
            b'\x00\x00\x00\x10\x00\x00\x00\x11\x00\x00\x00\x12\x00\x00\x00'
            b'\x13\x00\x00\x00\x14\x00\x00\x00\x15\x00\x00\x00\x16\x00\x00'
            b'\x00\x17\x00\x00\x00'
        ]

    def encodeImage(self):
        format = 'VIDEO_IMAGE'
        # uint8 B
        mode = 0
        # uint16 H
#        mode = 1
        height, width = self.attr_ImageUChar.shape
        version = 1
        endian = sys.byteorder == u'big'
        hsize = struct.calcsize('!IHHqiiHHHH')
        header = struct.pack(
            '!IHHqiiHHHH', 0x5644454f, version, mode, -1,
            width, height, endian, hsize, 0, 0)
        fimage = self.attr_ImageUChar.flatten()
        ibuffer = struct.pack('B' * fimage.size, *fimage)
        return [format, bytes(header + ibuffer)]

    # ------------------------------------------------------------------
    #    Read ImageUChar attribute
    # ------------------------------------------------------------------
    def read_ImageUChar(self, attr):
        attr.set_value(self.attr_ImageUChar)

    # ------------------------------------------------------------------
    #    Write ImageUChar attribute
    # ------------------------------------------------------------------
    def write_ImageUChar(self, attr):
        self.attr_ImageUChar = attr.get_write_value()

    def read_ImageEncoded(self, attr):
        attr.set_value(
            self.attr_ImageEncoded[0], self.attr_ImageEncoded[1])

    def write_ImageEncoded(self, attr):
        self.attr_ImageEncoded = attr.get_write_value()

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
        self.attr_ImageEncoded = ("DATA_ARRAY", self.__images[0])

    def ReadyEventAcq(self):
        """ Start the acquisition. """
        self.attr_ReadyEventImage_read = \
            [[random.randint(0, 1000) for i in range(128)] for j in range(256)]
        self.push_data_ready_event("ReadyEventImage", 0)
        self.attr_ImageEncoded = ("DATA_ARRAY", self.__images[1])

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
        'ImageEncoded':
        [[tango.DevEncoded,
          tango.SCALAR,
          tango.READ_WRITE],
         {
             'description': "ImageEncoded attribute",
        }],
        'ImageUChar':
        [[tango.DevUChar,
          tango.IMAGE,
          tango.READ_WRITE, 4096, 4096],
         {
             'description': "ImageUChar attribute",
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
