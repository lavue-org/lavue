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

""" Memory Buffer widget """

import numpy as np
import sys
from .qtuic import uic
from pyqtgraph import QtCore, QtGui
import os


if sys.version_info > (3,):
    unicode = str
else:
    bytes = str

_formclass, _baseclass = uic.loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "ui", "MemoryBufferGroupBox.ui"))


class MemoryBufferGroupBox(QtGui.QGroupBox):

    """
    Set circular memory buffer for images
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) state updated signal
    bufferSizeChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtGui.QGroupBox.__init__(self, parent)

        #: (:class:`Ui_MemoryBufferGroupBox')
        #      ui_groupbox object from qtdesigner
        self.__ui = _formclass()
        self.__ui.setupUi(self)

        #: (:obj:`int`) number of frames in memory buffer
        self.__maxindex = 10
        #: (:obj:`int`) maximal number of frames in memory buffer
        self.__maxbuffersize = 1000
        #: (:obj:`bool`) is on status
        self.__isOn = False
        #: (:obj:`bool`) compute sum flag
        self.__computeSum = False
        #: (:obj:`bool`) is buffer full
        self.__full = False

        #: (:class:`numpy.ndarray`) image stack
        self.__imagestack = None
        #: (:obj:`int`) the current size
        self.__current = 1
        #: (:class:`numpy.ndarray`) the last image
        self.__lastimage = None
        #: (:class:`numpy.ndarray`) the image sum
        self.__imagesum = None
        #: (:obj:`bool`)
        self.__first = True

        self.__ui.sizeSpinBox.setStyleSheet("")
        self.__ui.sizeSpinBox.setEnabled(False)
        self.__ui.resetPushButton.setEnabled(False)
        self.__ui.sizeSpinBox.valueChanged.connect(self._onBufferSizeChanged)
        self.__ui.onoffCheckBox.stateChanged.connect(self.onOff)
        self.__ui.resetPushButton.clicked.connect(self._onBufferSizeChanged)

    def bufferSize(self):
        """ provides buffer size

        :returns: buffer size if buffer is on
        :rtype: int
        """
        size = 0
        if self.__isOn:
            size = self.__maxindex
        return size

    def isOn(self):
        """ is on flag

        :returns: is on flag
        :rtype: bool
        """
        return self.__isOn

    def setBufferSize(self, buffersize):
        """ sets buffer size

        :param buffersize: maximal number of images in the buffer
        :type buffersize: :obj:`int` or :obj:`str`
        """
        try:
            self.__maxindex = int(buffersize)
        except Exception:
            self.__maxindex = 10
        self.__ui.sizeSpinBox.setValue(self.__maxindex)
        self._onBufferSizeChanged(self.__maxindex)

    def setMaxBufferSize(self, maxbuffersize):
        """ sets maximal buffer size

        :param maxbuffersize: maximal number of images in the buffer
        :type maxbuffersize: :obj:`int` or :obj:`str`
        """
        try:
            self.__maxbuffersize = int(maxbuffersize)
        except Exception:
            self.__maxbuffersize = 1000
        if self.__maxbuffersize < self.__maxindex:
            self.__ui.sizeSpinBox.setValue(self.__maxbuffersize)
            self._onBufferSizeChanged(self.__maxbuffersize)

    def setComputeSum(self, computesum):
        """ sets compute sum flag

        :param computesum: compute sum flag
        :type computesum: :obj:`bool`
        """
        self.initialize()
        self.__computeSum = bool(computesum)
        self.initialize()

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot()
    def _onBufferSizeChanged(self, size=None):
        """ set size of image buffer in frame numbers

        :param size: buffer size
        :type size: :obj:`int`
        """
        if size is not None:
            if self.__maxindex != size:
                if self.__maxbuffersize >= size:
                    self.__maxindex = size
                else:
                    self.__maxindex = self.__maxbuffersize
                    self.__ui.sizeSpinBox.setValue(self.__maxbuffersize)
        self.initialize()
        self.bufferSizeChanged.emit(size or 0)

    @QtCore.pyqtSlot(int)
    def onOff(self, status):
        """ switch on/off  the widget

        :param status: flag on/off
        :type status: :obj:`int`
        """
        self.__isOn = True if status else False
        self.__ui.onoffCheckBox.setCheckState(2 if self.__isOn else 0)

        self.initialize()
        self.__ui.sizeSpinBox.setEnabled(status)
        self.__ui.resetPushButton.setEnabled(status)
        self.__ui.sizeSpinBox.setStyleSheet("")
        self.bufferSizeChanged.emit((self.__maxindex or 0) if status else 0)

    def initialize(self):
        """ initialize the filter
        """
        self.__imagestack = None
        self.__lastimage = None
        self.__imagesum = None
        self.__current = 1
        self.__first = True
        self.__full = False
        self.__ui.sizeSpinBox.setStyleSheet("")

    def process(self, image, imagename):
        """ append image to the buffer and returns image buffer and metadata

        :param image: numpy array with an image
        :type image: :class:`numpy.ndarray`
        :param imagename: image name
        :type imagename: :obj:`str`
        :returns: numpy array with an image
        :rtype: (:class:`numpy.ndarray`, :obj`dict`<:obj:`str`, :obj:`str`>)
                 or `None`
        """
        if self.__isOn and image is not None:
            mdata = {}
            ics = int(self.__computeSum)
            if ics:
                mdata["suminthelast"] = True
            while len(image.shape) > 2:
                image = np.nansum(image, 0)
            if self.__lastimage is None \
               or self.__lastimage.shape != image.shape \
               or self.__lastimage.dtype != image.dtype \
               or np.nanmax((self.__lastimage - image)):
                shape = image.shape
                dtype = image.dtype

                if self.__imagestack is not None:
                    if self.__imagestack.shape[1:] != shape or \
                       self.__imagestack.dtype != dtype:
                        self.__imagestack = None
                        self.__imagesum = None
                        self.__first = True
                        self.__current = 1
                if self.__imagestack is None:
                    newshape = np.concatenate(
                        ([self.__maxindex + 1 + ics],
                         list(shape)))
                    self.__imagestack = np.zeros(dtype=dtype, shape=newshape)

                if self.__current > self.__maxindex:
                    self.__current = 1
                if self.__current >= self.__maxindex:
                    self.__full = True
                    self.__ui.sizeSpinBox.setStyleSheet(
                        "color: black;"
                        "background-color: paleGreen;")
                lshape = len(self.__imagestack.shape)
                theoldest = None
                if lshape == 3:
                    if ics:
                        theoldest = np.array(
                            self.__imagestack[self.__current, :, :])
                    self.__imagestack[self.__current, :, :] = image
                    self.__imagestack[0, :, :] = image
                    if ics:
                        if self.__imagesum is None:
                            if self.__full is True:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[1:-1, :, :], 0)
                            else:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[
                                        1:(self.__current + 1), :, :], 0)
                        else:
                            self.__imagesum = self.__imagesum + image
                            if self.__full is True:
                                self.__imagesum = self.__imagesum - theoldest
                        self.__imagestack[-1, :, :] = self.__imagesum
                elif lshape == 2:
                    if ics:
                        theoldest = np.array(
                            self.__imagestack[self.__current, :])
                    self.__imagestack[self.__current, :] = image
                    self.__imagestack[0, :] = image
                    if ics:
                        if self.__imagesum is None:
                            if self.__full is True:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[1:-1, :], 0)
                            else:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[
                                        1:(self.__current + 1), :], 0)
                        else:
                            self.__imagesum = self.__imagesum + image
                            if self.__full is True:
                                self.__imagesum = self.__imagesum - theoldest
                        self.__imagestack[-1, :] = self.__imagesum
                elif lshape == 1:
                    if ics:
                        theoldest = np.array(self.__imagestack[self.__current])
                    self.__imagestack[self.__current] = image
                    self.__imagestack[0] = image
                    if ics:
                        if self.__imagesum is None:
                            if self.__full is True:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[1:-1], 0)
                            else:
                                self.__imagesum = np.nansum(
                                    self.__imagestack[
                                        1:(self.__current + 1)], 0)
                        else:
                            self.__imagesum = self.__imagesum + image
                            if self.__full is True:
                                self.__imagesum = self.__imagesum - theoldest
                        self.__imagestack[-1] = self.__imagesum

                self.__lastimage = np.array(image)
                self.__current += 1
                if self.__first:
                    cblbl = {key: "%s:" % key
                             for key in range(self.__maxindex + 1)}
                else:
                    cblbl = {}
                mdata["channellabels"] = cblbl
                mdata["skipfirst"] = True
                if ics:
                    mdata["suminthelast"] = True
                cblbl[0] = "0: the last image"
                # if imagename:
                #     imagename = imagename.replace("\n", " ")
                cblbl[self.__current - 1] = "%s: %s" % (
                    self.__current - 1, imagename.replace("\n", " "))
                self.__first = False

            if self.__imagestack is not None:
                return (self.__imagestack, mdata)

    def changeView(self, show=False):
        """ shows or hides the histogram widget

        :param show: if histogram should be shown
        :type show: :obj:`bool`
        """
        if show:
            self.show()
        else:
            self.hide()
