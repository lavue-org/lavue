# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
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
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" image display widget """

import pyqtgraph as _pg
import numpy as np
import math
import types
import json
from pyqtgraph.graphicsItems.ROI import ROI, LineROI, Handle
from PyQt4 import QtCore, QtGui

from . import axesDialog
from . import displayParameters

from .external.pyqtgraph_0_10 import (
    viewbox_updateMatrix, viewbox_invertX,
    viewbox_xInverted, axisitem_linkedViewChanged,
    viewbox_linkedViewChanged)

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class HandleWithSignals(Handle):
    """ handle with signals

    """
    #: (:class:`PyQt4.QtCore.pyqtSignal`) hover event emitted
    hovered = QtCore.pyqtSignal()

    def __init__(self, pos, center, parent):
        """ constructor

        :param pos: position of handle
        :type pos: [float, float]
        :param center: center of handle
        :type center: [float, float]
        :param parent: roi object
        :type parent: :class:`pyqtgraph.graphicsItems.ROI.ROI`
        """
        pos = _pg.Point(pos)
        center = _pg.Point(center)
        if pos[0] != center[0] and pos[1] != center[1]:
            raise Exception(
                "Scale/rotate handles must have either the same x or y "
                "coordinate as their center point.")
        Handle.__init__(self, parent.handleSize, typ='sr',
                        pen=parent.handlePen, parent=parent)
        self.setPos(pos * parent.state['size'])

    def hoverEvent(self, ev):
        """ hover event

        :param ev: close event
        :type ev: :class:`PyQt4.QtCore.QEvent`:
        """
        Handle.hoverEvent(self, ev)
        self.hovered.emit()


class SimpleLineROI(LineROI):
    """ simple line roi """

    def __init__(self, pos1, pos2, width=0.00001, **args):
        """ constructor

        :param pos1: start position
        :type pos1: [float, float]
        :param pos2: end position
        :type pos2: [float, float]
        :param args: dictionary with ROI parameters
        :type args: :obj:`dict`<:obj:`str`, :obj:`any`>
        """

        pos1 = _pg.Point(pos1)
        pos2 = _pg.Point(pos2)
        d = pos2 - pos1
        ln = d.length()
        ang = _pg.Point(1, 0).angle(d)

        ROI.__init__(self, pos1, size=_pg.Point(ln, width), angle=ang, **args)
        h1pos = [0, 0.0]
        h1center = [1, 0.0]
        h2pos = [1, 0.0]
        h2center = [0, 0.0]
        vpos = [0.5, 1]
        vcenter = [0.5, 0]
        self.handle1 = HandleWithSignals(h1pos, h1center, self)
        self.handle2 = HandleWithSignals(h2pos, h2center, self)
        self.vhandle = HandleWithSignals(vcenter, vpos, self)
        self.addHandle(
            {'name': 'handle1', 'type': 'sr', 'center': h1center,
             'pos': h1pos, 'item': self.handle1})
        self.addHandle(
            {'name': 'handle2', 'type': 'sr', 'center': h2center,
             'pos': h2pos, 'item': self.handle2})
        self.addHandle(
            {'name': 'vhandle', 'type': 'sr', 'center': vcenter,
             'pos': vpos, 'item': self.vhandle})
        # self.handle1 = self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        # self.handle2 = self.addScaleRotateHandle([1, 0.5], [0, 0.5])

    def getCoordinates(self):
        """ provides the roi coordinates

        :param trans: transposed flag
        :type trans: :obj:`bool`
        :returns: x1, y1, x2, y2 positions of the roi
        :rtype: [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        """
        ang = self.state['angle']
        pos1 = self.state['pos']
        size = self.state['size']
        ra = ang * np.pi / 180.
        pos2 = pos1 + _pg.Point(
            size.x() * math.cos(ra),
            size.x() * math.sin(ra))
        return [pos1.x(), pos1.y(), pos2.x(), pos2.y(), size.y()]


class ImageDisplayWidget(_pg.GraphicsLayoutWidget):

    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) aspect locked toggled signal
    aspectLockedToggled = QtCore.pyqtSignal(bool)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse position changed signal
    mouseImagePositionChanged = QtCore.pyqtSignal()
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse double clicked
    mouseImageDoubleClicked = QtCore.pyqtSignal(float, float)
    #: (:class:`PyQt4.QtCore.pyqtSignal`) mouse single clicked
    mouseImageSingleClicked = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        _pg.GraphicsLayoutWidget.__init__(self, parent)
        #: (:class:`PyQt4.QtGui.QLayout`) the main layout
        self.__layout = self.ci

        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            axes parameters
        self.__lines = displayParameters.CrossLinesParameters()
        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            axes parameters
        self.__axes = displayParameters.AxesParameters()
        #: (:class:`lavuelib.displayParameters.AxesParameters`)
        #:            polar axes parameters
        self.__polaraxes = displayParameters.AxesParameters()
        #: (:class:`lavuelib.displayParameters.ROIsParameters`)
        #:                rois parameters
        self.__rois = displayParameters.ROIsParameters()
        #: (:class:`lavuelib.displayParameters.CutsParameters`)
        #:                 cuts parameters
        self.__cuts = displayParameters.CutsParameters()
        #: (:class:`lavuelib.displayParameters.IntensityParameters`)
        #:                  intensity parameters
        self.__intensity = displayParameters.IntensityParameters()
        #: (:class:`lavuelib.displayParameters.TransformationParameters`)
        #:                  intensity parameters
        self.__transformations = displayParameters.TransformationParameters()

        #: (:class:`numpy.ndarray`) data to displayed in 2d widget
        self.__data = None
        #: (:class:`numpy.ndarray`) raw data to cut plots
        self.__rawdata = None

        #: (:class:`pyqtgraph.ImageItem`) image item
        self.__image = _pg.ImageItem()

        #: (:class:`pyqtgraph.ViewBox`) viewbox item
        self.__viewbox = self.__layout.addViewBox(row=0, col=1)

        #: (:obj:`bool`) crooshair locked flag
        self.__crosshairlocked = False
        #: ([:obj:`float`, :obj:`float`]) center coordinates
        self.__centercoordinates = None
        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__markcoordinates = None
        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__lockercoordinates = None

        self.__viewbox.addItem(self.__image)
        #: (:obj:`float`) current floar x-position
        self.__xfdata = 0
        #: (:obj:`float`) current floar y-position
        self.__yfdata = 0
        #: (:obj:`float`) current x-position
        self.__xdata = 0
        #: (:obj:`float`) current y-position
        self.__ydata = 0
        #: (:obj:`bool`) auto display level flag
        self.__autodisplaylevels = True
        #: (:obj:`bool`) auto down sample
        self.__autodownsample = True
        #: ([:obj:`float`, :obj:`float`]) minimum and maximum intensity levels
        self.__displaylevels = [None, None]

        #: (:class:`PyQt4.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) roi region mapper
        self.__roiregionmapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) current cut mapper
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) cut region mapper
        self.__cutregionmapper = QtCore.QSignalMapper(self)

        #: (:class:`PyQt4.QtGui.QAction`) set aspect ration locked action
        self.__setaspectlocked = QtGui.QAction(
            "Set Aspect Locked", self.__viewbox.menu)
        self.__setaspectlocked.setCheckable(True)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__setaspectlocked)
        self.__viewbox.menu.addAction(self.__setaspectlocked)

        #: (:class:`PyQt4.QtGui.QAction`) view one to one pixel action
        self.__viewonetoone = QtGui.QAction(
            "View 1:1 pixels", self.__viewbox.menu)
        self.__viewonetoone.triggered.connect(self._oneToOneRange)
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            self.__viewbox.menu.axes.insert(0, self.__viewonetoone)
        self.__viewbox.menu.addAction(self.__viewonetoone)

        #: (:class:`pyqtgraph.AxisItem`) left axis
        self.__leftaxis = _pg.AxisItem('left')

        #: (:class:`pyqtgraph.AxisItem`) bottom axis
        self.__bottomaxis = _pg.AxisItem('bottom')

        #: dirty hooks for v0.9.10 to support invertX
        if not hasattr(self.__viewbox, "invertX"):
            self.__viewbox.state["xInverted"] = False
            self.__viewbox.invertX = types.MethodType(
                viewbox_invertX, self.__viewbox)
            self.__viewbox.xInverted = types.MethodType(
                viewbox_xInverted, self.__viewbox)
            self.__viewbox.updateMatrix = types.MethodType(
                viewbox_updateMatrix, self.__viewbox)
            self.__viewbox.linkedViewChanged = types.MethodType(
                viewbox_linkedViewChanged, self.__viewbox)

            self.__bottomaxis.linkedViewChanged = types.MethodType(
                axisitem_linkedViewChanged, self.__bottomaxis)
            self.__leftaxis.linkedViewChanged = types.MethodType(
                axisitem_linkedViewChanged, self.__leftaxis)

        self.__leftaxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__leftaxis, row=0, col=0)
        self.__bottomaxis.linkToView(self.__viewbox)
        self.__layout.addItem(self.__bottomaxis, row=1, col=1)

        self.__layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.__layout.scene().sigMouseClicked.connect(self.mouse_click)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical locker line of the mouse position
        self.__lockerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 0, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal locker line of the mouse position
        self.__lockerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 0, 0))
        self.__viewbox.addItem(self.__lockerVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__lockerHLine, ignoreBounds=True)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical center line of the mouse position
        self.__centerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(0, 255, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal center line of the mouse position
        self.__centerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(0, 255, 0))
        self.__viewbox.addItem(self.__centerVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__centerHLine, ignoreBounds=True)

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical mark line of the mouse position
        self.__markVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(0, 0, 255))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal mark line of the mouse position
        self.__markHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(0, 0, 255))
        self.__viewbox.addItem(self.__markVLine, ignoreBounds=True)
        self.__viewbox.addItem(self.__markHLine, ignoreBounds=True)

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.TextItem`>)
        #:            list of roi widgets
        self.__roitext = []
        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:            list of roi widgets
        self.__roi = []
        self.__roi.append(ROI(0, _pg.Point(50, 50)))
        self.__roi[0].addScaleHandle([1, 1], [0, 0])
        self.__roi[0].addScaleHandle([0, 0], [1, 1])
        text = _pg.TextItem("1.", anchor=(1, 1))
        text.setParentItem(self.__roi[0])
        self.__roitext.append(text)
        self.__viewbox.addItem(self.__roi[0])
        self.__roi[0].hide()
        self.setROIsColors()

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:        list of cut widgets
        self.__cut = []
        self.__cut.append(SimpleLineROI([10, 10], [60, 10], pen='r'))
        self.__viewbox.addItem(self.__cut[0])
        self.__cut[0].hide()

        self.__setaspectlocked.triggered.connect(self.emitAspectLockedToggled)

        self.__roiregionmapper.mapped.connect(self.changeROIRegion)
        self.__currentroimapper.mapped.connect(self._emitROICoordsChanged)
        self._getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self._getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self._getROI(), 0)
        self.__roiregionmapper.setMapping(self._getROI(), 0)

        self.__cutregionmapper.mapped.connect(self.changeCutRegion)
        self.__currentcutmapper.mapped.connect(self._emitCutCoordsChanged)
        self._getCut().sigHoverEvent.connect(
            self.__currentcutmapper.map)
        self._getCut().sigRegionChanged.connect(
            self.__cutregionmapper.map)
        self._getCut().handle1.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().handle2.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().vhandle.hovered.connect(
            self.__currentcutmapper.map)
        self.__currentcutmapper.setMapping(self._getCut().handle1, 0)
        self.__currentcutmapper.setMapping(self._getCut().handle2, 0)
        self.__currentcutmapper.setMapping(self._getCut().vhandle, 0)
        self.__currentcutmapper.setMapping(self._getCut(), 0)
        self.__cutregionmapper.setMapping(self._getCut(), 0)

    def __showLockerLines(self, status):
        """ shows or hides HV locker mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__lockerVLine.show()
            self.__lockerHLine.show()
        else:
            self.__lockerVLine.hide()
            self.__lockerHLine.hide()

    def __showCenterLines(self, status):
        """ shows or hides HV center mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__centerVLine.show()
            self.__centerHLine.show()
        else:
            self.__centerVLine.hide()
            self.__centerHLine.hide()

    def __showMarkLines(self, status):
        """ shows or hides HV mark mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__markVLine.show()
            self.__markHLine.show()
        else:
            self.__markVLine.hide()
            self.__markHLine.hide()

    def setAspectLocked(self, flag):
        """sets aspectLocked

        :param status: state to set
        :type status: :obj:`bool`
        :returns: old state
        :rtype: :obj:`bool`
        """
        if flag != self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(flag)
        oldflag = self.__viewbox.state["aspectLocked"]
        self.__viewbox.setAspectLocked(flag)
        return oldflag

    def __addROI(self, coords=None):
        """ adds ROIs

        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * len(self.__roi)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt + sz]
            spnt = _pg.Point(sz, sz)
        else:
            if not self.__transformations.transpose:
                pnt = _pg.Point(coords[0], coords[1])
                spnt = _pg.Point(coords[2] - coords[0], coords[3] - coords[1])
            else:
                pnt = _pg.Point(coords[1], coords[0])
                spnt = _pg.Point(coords[3] - coords[1], coords[2] - coords[0])
        self.__roi.append(ROI(pnt, spnt))
        self.__roi[-1].addScaleHandle([1, 1], [0, 0])
        self.__roi[-1].addScaleHandle([0, 0], [1, 1])
        text = _pg.TextItem("%s." % len(self.__roi), anchor=(1, 1))
        text.setParentItem(self.__roi[-1])
        self.__roitext.append(text)
        self.__viewbox.addItem(self.__roi[-1])

        self.__rois.coords.append(coords)
        self.setROIsColors()

    def __removeROI(self):
        """ removes the last roi
        """
        roi = self.__roi.pop()
        roi.hide()
        roitext = self.__roitext.pop()
        roitext.hide()
        self.__viewbox.removeItem(roi)
        self.__rois.coords.pop()

    def _getROI(self, rid=-1):
        """ get the given or the last ROI

        :param rid: roi id
        :type rid: :obj:`int`
        """
        if self.__roi and len(self.__roi) > rid:
            return self.__roi[rid]
        else:
            return None

    def __showROIs(self, status):
        """ shows or hides rois

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for roi in self.__roi:
                roi.show()
        else:
            for roi in self.__roi:
                roi.hide()

    def __addROICoords(self, coords):
        """ adds ROI coorinates

        :param coords: roi coordinates
        :type coords: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__roi):
                if i < len(coords):
                    self.__rois.coords[i] = coords[i]
                    if not self.__transformations.transpose:
                        crd.setPos([coords[i][0], coords[i][1]])
                        crd.setSize(
                            [coords[i][2] - coords[i][0],
                             coords[i][3] - coords[i][1]])
                    else:
                        crd.setPos([coords[i][1], coords[i][0]])
                        crd.setSize(
                            [coords[i][3] - coords[i][1],
                             coords[i][2] - coords[i][0]])

    def __addCutCoords(self, coords):
        """ adds Cut coordinates

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__cut):
                if i < len(coords):
                    self.__cuts.coords[i] = coords[i]
                    if not self.__transformations.transpose:
                        crd.setPos([coords[i][0], coords[i][1]])
                        crd.setSize(
                            [coords[i][2] - coords[i][0],
                             coords[i][3] - coords[i][1]])
                    else:
                        crd.setPos([coords[i][1], coords[i][0]])
                        crd.setSize(
                            [coords[i][3] - coords[i][1],
                             coords[i][2] - coords[i][0]])

    def __addCut(self, coords=None):
        """ adds Cuts

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not coords or not isinstance(coords, list) or len(coords) != 5:
            pnt = 10 * (len(self.__cut) + 1)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt, 0.00001]

        if not self.__transformations.transpose:
            self.__cut.append(SimpleLineROI(
                coords[:2], coords[2:4], width=coords[4], pen='r'))
        else:
            self.__cut.append(SimpleLineROI(
                [coords[1], coords[0]],
                [coords[3], coords[2]],
                width=coords[4], pen='r'))
        self.__viewbox.addItem(self.__cut[-1])
        self.__cuts.coords.append(coords)

    def __removeCut(self):
        """ removes the last cut
        """
        cut = self.__cut.pop()
        cut.hide()
        self.__viewbox.removeItem(cut)
        self.__cuts.coords.pop()

    def _getCut(self, cid=-1):
        """ get the given or the last Cut

        :param cid: roi id
        :type cid: :obj:`int`
        """
        if self.__cut and len(self.__cut) > cid:
            return self.__cut[cid]
        else:
            return None

    def __showCuts(self, status):
        """ shows or hides cuts

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for cut in self.__cut:
                cut.show()
        else:
            for cut in self.__cut:
                cut.hide()

    def _oneToOneRange(self):
        """ set one to one range
        """
        ps = self.__image.pixelSize()
        currange = self.__viewbox.viewRange()
        xrg = currange[0][1] - currange[0][0]
        yrg = currange[1][1] - currange[1][0]
        if self.__axes.position is not None and self.__axes.enabled:
            self.__viewbox.setRange(
                QtCore.QRectF(
                    self.__axes.position[0], self.__axes.position[1],
                    xrg * ps[0], yrg * ps[1]),
                padding=0)
        else:
            self.__viewbox.setRange(
                QtCore.QRectF(0, 0, xrg * ps[0], yrg * ps[1]),
                padding=0)
        if self.__setaspectlocked.isChecked():
            self.__setaspectlocked.setChecked(False)
            self.__setaspectlocked.triggered.emit(False)

    def __setScale(self, position=None, scale=None, update=True, polar=False,
                   force=False):
        """ set axes scales

        :param position: start position of axes
        :type position: [:obj:`float`, :obj:`float`]
        :param scale: scale axes
        :type scale: [:obj:`float`, :obj:`float`]
        :param update: update scales on image
        :type update: :obj:`bool`
        :param polar: update polar scale
        :type polar: :obj:`bool`
        :param force: force rescaling
        :type force: :obj:`bool`
        """
        axes = self.__polaraxes if polar else self.__axes

        if update:
            self.__setLabels(axes.xtext, axes.ytext,
                             axes.xunits, axes.yunits)

        if not force:
            if axes.position == position and axes.scale == scale and \
               position is None and scale is None:
                return
        axes.position = position
        axes.scale = scale
        self.__image.resetTransform()
        if axes.scale is not None and update:
            if not self.__transformations.transpose:
                self.__image.scale(*axes.scale)
            else:
                self.__image.scale(
                    axes.scale[1], axes.scale[0])
        else:
            self.__image.scale(1, 1)
        if axes.position is not None and update:
            if not self.__transformations.transpose:
                self.__image.setPos(*axes.position)
            else:
                self.__image.setPos(
                    axes.position[1], axes.position[0])
        else:
            self.__image.setPos(0, 0)
        if self.__rawdata is not None and update:
            self.autoRange()

    def setPolarScale(self, position=None, scale=None):
        """ set axes scales

        :param position: start position of axes
        :type position: [:obj:`float`, :obj:`float`]
        :param scale: scale axes
        :type scale: [:obj:`float`, :obj:`float`]
        :param update: update scales on image
        :type updatescale: :obj:`bool`
        """
        self.__polaraxes.position = position
        self.__polaraxes.scale = scale

    def __resetScale(self, polar=False):
        """ reset axes scales

        :param polar: update polar scale
        :type polar: :obj:`bool`
        """
        axes = self.__polaraxes if polar else self.__axes

        if axes.scale is not None or axes.position is not None:
            self.__image.resetTransform()
        if axes.scale is not None:
            self.__image.scale(1, 1)
        if axes.position is not None:
            self.__image.setPos(0, 0)
        if axes.scale is not None or axes.position is not None:
            if self.__rawdata is not None:
                self.autoRange()
            self.__setLabels()

    def updateImage(self, img=None, rawimg=None):
        """ updates the image to display

        :param img: 2d image array
        :type img: :class:`numpy.ndarray`
        :param rawimg: 2d raw image array
        :type rawimg: :class:`numpy.ndarray`
        """
        if self.__autodisplaylevels:
            self.__image.setImage(
                img, autoLevels=True,
                autoDownsample=self.__autodownsample)
        else:
            self.__image.setImage(
                img, autoLevels=False,
                levels=self.__displaylevels,
                autoDownsample=self.__autodownsample)
        self.__data = img
        self.__rawdata = rawimg
        self.mouse_position()

    def __setLockerLines(self):
        """  sets vLine and hLine positions
        """
        if self.__axes.scale is not None and \
           self.__axes.enabled is True:
            position = [0, 0] \
                if self.__axes.position is None \
                else self.__axes.position

            if not self.__transformations.transpose:
                self.__lockerVLine.setPos(
                    (self.__xfdata + .5) * self.__axes.scale[0]
                    + position[0])
                self.__lockerHLine.setPos(
                    (self.__yfdata + .5) * self.__axes.scale[1]
                    + position[1])
            else:
                self.__lockerVLine.setPos(
                    (self.__yfdata + .5) * self.__axes.scale[1]
                    + position[0])
                self.__lockerHLine.setPos(
                    (self.__xfdata + .5) * self.__axes.scale[0]
                    + position[1])
        else:
            if not self.__transformations.transpose:
                self.__lockerVLine.setPos(self.__xfdata + .5)
                self.__lockerHLine.setPos(self.__yfdata + .5)
            else:
                self.__lockerVLine.setPos(self.__yfdata + .5)
                self.__lockerHLine.setPos(self.__xfdata + .5)

    def __setCenterLines(self):
        """  sets vLine and hLine positions
        """
        if not self.__transformations.transpose:
            self.__centerVLine.setPos(self.__xdata)
            self.__centerHLine.setPos(self.__ydata)
        else:
            self.__centerVLine.setPos(self.__ydata)
            self.__centerHLine.setPos(self.__xdata)

    def __setMarkLines(self):
        """  sets vLine and hLine positions
        """
        if not self.__transformations.transpose:
            self.__markVLine.setPos(self.__xdata)
            self.__markHLine.setPos(self.__ydata)
        else:
            self.__markVLine.setPos(self.__ydata)
            self.__markHLine.setPos(self.__xdata)

    def currentIntensity(self):
        """ provides intensity for current mouse position

        :returns: (x position, y position, pixel intensity,
                   x position, y position)
        :rtype: (float, float, float, float, float)
        """
        if self.__lines.locker and self.__crosshairlocked \
           and self.__lockercoordinates is not None:
            xfdata = math.floor(self.__lockercoordinates[0])
            yfdata = math.floor(self.__lockercoordinates[1])
        else:
            xfdata = self.__xfdata
            yfdata = self.__yfdata
        if self.__rawdata is not None:
            try:
                if not self.__transformations.transpose:
                    xf = int(xfdata)
                    yf = int(yfdata)
                else:
                    yf = int(xfdata)
                    xf = int(yfdata)
                if xf >= 0 and yf >= 0 and xf < self.__rawdata.shape[0] \
                   and yf < self.__rawdata.shape[1]:
                    intensity = self.__rawdata[xf, yf]
                else:
                    intensity = 0.
            except Exception:
                intensity = 0.
        else:
            intensity = 0.
        return (xfdata, yfdata, intensity,
                self.__xdata, self.__ydata)

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: str
        """
        ilabel = "intensity"
        scaling = self.__intensity.scaling \
            if not self.__intensity.statswoscaling else "linear"
        if not self.__rois.enabled:
            if self.__intensity.dobkgsubtraction:
                ilabel = "%s(intensity-background)" % (
                    scaling if scaling != "linear" else "")
            else:
                if scaling == "linear":
                    ilabel = "intensity"
                else:
                    ilabel = "%s(intensity)" % scaling
        return ilabel

    def scaling(self):
        """ provides scaling type

        :returns:  scaling type
        :rtype: str
        """
        return self.__intensity.scaling

    def axesunits(self):
        """ return axes units
        :returns: x,y units
        :rtype: (:obj:`str`, :obj:`str`)
        """
        return (self.__axes.xunits, self.__axes.yunits)

    def scaledxy(self, x, y):
        """ provides scaled x,y positions

        :param x: x pixel coordinate
        :type x: float
        :param y: y pixel coordinate
        :type y: float
        :returns: scaled x,y position
        :rtype: (float, float)
        """
        txdata = None
        tydata = None
        if self.__axes.scale is not None:
            txdata = x * self.__axes.scale[0]
            tydata = y * self.__axes.scale[1]
            if self.__axes.position is not None:
                txdata = txdata + self.__axes.position[0]
                tydata = tydata + self.__axes.position[1]
        elif self.__axes.position is not None:
            txdata = x + self.__axes.position[0]
            tydata = y + self.__axes.position[1]
        return (txdata, tydata)

    @QtCore.pyqtSlot(object)
    def mouse_position(self, event=None):
        """ updates image widget after mouse position change

        :param event: mouse move event
        :type event: :class:`PyQt4.QtCore.QEvent`
        """
        try:
            if event is not None:
                mousePoint = self.__image.mapFromScene(event)
                if not self.__transformations.transpose:
                    self.__xdata = mousePoint.x()
                    self.__ydata = mousePoint.y()
                else:
                    self.__ydata = mousePoint.x()
                    self.__xdata = mousePoint.y()
                self.__xfdata = math.floor(self.__xdata)
                self.__yfdata = math.floor(self.__ydata)
            if self.__lines.locker:
                if not self.__crosshairlocked:
                    self.__setLockerLines()
            if self.__lines.center:
                if not self.__centercoordinates:
                    self.__setCenterLines()
            if self.__lines.positionmark:
                if not self.__markcoordinates:
                    self.__setMarkLines()
            self.mouseImagePositionChanged.emit()
        except Exception:
            # print("Warning: %s" % str(e))
            pass

    def __setLabels(self, xtext=None, ytext=None, xunits=None, yunits=None):
        """ sets labels and units

        :param xtext: x-label text
        :param type: :obj:`str`
        :param ytext: y-label text
        :param type: :obj:`str`
        :param xunits: x-units text
        :param type: :obj:`str`
        :param yunits: y-units text
        :param type: :obj:`str`
        """
        self.__bottomaxis.autoSIPrefix = False
        self.__leftaxis.autoSIPrefix = False
        if not self.__transformations.transpose:
            self.__bottomaxis.setLabel(text=xtext, units=xunits)
            self.__leftaxis.setLabel(text=ytext, units=yunits)
            if xunits is None:
                self.__bottomaxis.labelUnits = ''
            if yunits is None:
                self.__leftaxis.labelUnits = ''
            if xtext is None:
                self.__bottomaxis.label.setVisible(False)
            if ytext is None:
                self.__leftaxis.label.setVisible(False)
        else:
            self.__bottomaxis.setLabel(text=ytext, units=yunits)
            self.__leftaxis.setLabel(text=xtext, units=xunits)
            if yunits is None:
                self.__bottomaxis.labelUnits = ''
            if xunits is None:
                self.__leftaxis.labelUnits = ''
            if ytext is None:
                self.__bottomaxis.label.setVisible(False)
            if xtext is None:
                self.__leftaxis.label.setVisible(False)

    @QtCore.pyqtSlot(object)
    def mouse_click(self, event):
        """ updates image widget after mouse click

        :param event: mouse click event
        :type event: :class:`PyQt4.QtCore.QEvent`
        """

        mousePoint = self.__image.mapFromScene(event.scenePos())

        if not self.__transformations.transpose:
            xdata = mousePoint.x()
            ydata = mousePoint.y()
        else:
            ydata = mousePoint.x()
            xdata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            if self.__lines.locker:
                self.updateLocker(xdata, ydata)
            if self.__lines.center:
                self.updateCenter(xdata, ydata)
            if not self.__lines.doubleclicklock and self.__lines.positionmark:
                self.updatePositionMark(xdata, ydata)
            self.mouseImageDoubleClicked.emit(xdata, ydata)
        else:
            self.mouseImageSingleClicked.emit(xdata, ydata)

    def setAutoLevels(self, autolevels):
        """ sets auto levels

        :param autolevels: auto levels enabled
        :type autolevels: :obj:`bool`
        """
        if autolevels:
            self.__autodisplaylevels = True
        else:
            self.__autodisplaylevels = False

    def setAutoDownSample(self, autodownsample):
        """ sets auto levels

        :param autolevels: auto down sample enabled
        :type autolevels: :obj:`bool`
        """
        if autodownsample:
            self.__autodownsample = True
        else:
            self.__autodownsample = False

    def setDisplayMinLevel(self, level=None):
        """ sets minimum intensity level

        :param level: minimum intensity
        :type level: :obj:`float`
        """
        if level is not None:
            self.__displaylevels[0] = level

    def setDisplayMaxLevel(self, level=None):
        """ sets maximum intensity level

        :param level: maximum intensity
        :type level: :obj:`float`
        """
        if level is not None:
            self.__displaylevels[1] = level

    def setDoubleClickLock(self, status=True):
        """ sets double click lock
        :param status: status flag
        :type status: :obj:`bool`
        """
        self.__lines.doubleclicklock = status

    def setSubWidgets(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        rescale = False
        doreset = False
        if parameters.scale is not None:
            if parameters.scale is False:
                doreset = self.__axes.enabled
            self.__axes.enabled = parameters.scale
        if parameters.polarscale is not None:
            doreset = parameters.polarscale
            if self.__polaraxes.enabled and not parameters.polarscale:
                rescale = True
            self.__polaraxes.enabled = parameters.polarscale

        # if parameters.lines is not None:
        if parameters.crosshairlocker is not None:
            self.__showLockerLines(parameters.crosshairlocker)
            self.__lines.locker = parameters.crosshairlocker
        if parameters.centerlines is not None:
            self.__showCenterLines(parameters.centerlines)
            self.__lines.center = parameters.centerlines
        if parameters.marklines is not None:
            self.__showMarkLines(parameters.marklines)
            self.__lines.positionmark = parameters.marklines
        if parameters.rois is not None:
            self.__showROIs(parameters.rois)
            self.__rois.enabled = parameters.rois
        if parameters.cuts is not None:
            self.__showCuts(parameters.cuts)
            self.__cuts.enabled = parameters.cuts
        if doreset:
            self.__resetScale(polar=parameters.polarscale)
        if parameters.scale is True or rescale:
            self.__setScale(
                self.__axes.position, self.__axes.scale, force=rescale)
        if parameters.polarscale is True:
            self.__setScale(
                self.__polaraxes.position, self.__polaraxes.scale, polar=True)

    @QtCore.pyqtSlot(bool)
    def emitAspectLockedToggled(self, status):
        """ emits aspectLockedToggled

        :param status: aspectLockedToggled status
        :type status: :obj:`bool`
        """
        self.aspectLockedToggled.emit(status)

    def setTicks(self):
        """ launch axes widget

        :returns: apply status
        :rtype: :obj:`bool`
        """
        cnfdlg = axesDialog.AxesDialog()
        if self.__axes.position is None:
            cnfdlg.xposition = None
            cnfdlg.yposition = None
        else:
            cnfdlg.xposition = self.__axes.position[0]
            cnfdlg.yposition = self.__axes.position[1]
        if self.__axes.scale is None:
            cnfdlg.xscale = None
            cnfdlg.yscale = None
        else:
            cnfdlg.xscale = self.__axes.scale[0]
            cnfdlg.yscale = self.__axes.scale[1]

        cnfdlg.xtext = self.__axes.xtext
        cnfdlg.ytext = self.__axes.ytext

        cnfdlg.xunits = self.__axes.xunits
        cnfdlg.yunits = self.__axes.yunits

        cnfdlg.createGUI()
        if cnfdlg.exec_():
            if cnfdlg.xposition is not None and cnfdlg.yposition is not None:
                position = tuple([cnfdlg.xposition, cnfdlg.yposition])
            else:
                position = None
            if cnfdlg.xscale is not None and cnfdlg.yscale is not None:
                scale = tuple([cnfdlg.xscale, cnfdlg.yscale])
            else:
                scale = None
            self.__axes.xtext = cnfdlg.xtext or None
            self.__axes.ytext = cnfdlg.ytext or None

            self.__axes.xunits = cnfdlg.xunits or None
            self.__axes.yunits = cnfdlg.yunits or None
            self.__setScale(position, scale)
            self.updateImage(self.__data, self.__rawdata)

            return True
        return False

    def __calcROIsum(self, rid):
        """ calculates the current roi sum

        :param rid: roi id
        :type rid: :obj:`int`
        :returns: sum roi value, roi id
        :rtype: (float, int)
        """
        if rid >= 0:
            image = self.__rawdata
            if image is not None:
                if self.__rois.enabled:
                    if rid >= 0:
                        roicoords = self.__rois.coords
                        if not self.__transformations.transpose:
                            rcrds = list(roicoords[rid])
                        else:
                            rc = roicoords[rid]
                            rcrds = [rc[1], rc[0], rc[3], rc[2]]
                        for i in [0, 2]:
                            if rcrds[i] > image.shape[0]:
                                rcrds[i] = image.shape[0]
                            elif rcrds[i] < -i // 2:
                                rcrds[i] = -i // 2
                        for i in [1, 3]:
                            if rcrds[i] > image.shape[1]:
                                rcrds[i] = image.shape[1]
                            elif rcrds[i] < - (i - 1) // 2:
                                rcrds[i] = - (i - 1) // 2
                        roival = np.sum(image[
                            int(rcrds[0]):(int(rcrds[2]) + 1),
                            int(rcrds[1]):(int(rcrds[3]) + 1)
                        ])
                    else:
                        roival = 0.
                else:
                    roival = 0.
                return roival, rid
            else:
                return 0., rid
        return None, None

    def calcROIsum(self):
        """ calculates the current roi sum

        :returns: sum roi value, roi id
        :rtype: (float, int)
        """
        if self.__rois.enabled and self._getROI() is not None:
            rid = self.__rois.current
            return self.__calcROIsum(rid)
        return None, None

    def calcROIsums(self):
        """ calculates all roi sums

        :returns: sum roi value, roi id
        :rtype: `obj`list < `obj`<float> >
        """
        if self.__rawdata is None:
            return None
        return [self.__calcROIsum(rid)[0]
                for rid in range(len(self.__rois.coords))]

    def cutData(self, cid=None):
        """ provides the current cut data

        :param cid: cut id
        :type cid: :obj:`int`
        :returns: current cut data
        :rtype: :class:`numpy.ndarray`
        """
        if cid is None:
            cid = self.__cuts.current
        if cid > -1 and len(self.__cut) > cid:
            cut = self._getCut(cid)
            if self.__rawdata is not None:
                dt = cut.getArrayRegion(
                    self.__rawdata, self.__image, axes=(0, 1))
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
                return dt
        return None

    def rawData(self):
        """ provides the raw data

        :returns: current raw data
        :rtype: :class:`numpy.ndarray`
        """
        return self.__rawdata

    def currentData(self):
        """ provides the data

        :returns: current data
        :rtype: :class:`numpy.ndarray`
        """
        return self.__data

    @QtCore.pyqtSlot(int)
    def changeROIRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            rid = self.__rois.current
            roi = self._getROI(rid)
            if roi is not None:
                state = roi.state
                if not self.__transformations.transpose:
                    ptx = int(math.floor(state['pos'].x()))
                    pty = int(math.floor(state['pos'].y()))
                    szx = int(math.floor(state['size'].x()))
                    szy = int(math.floor(state['size'].y()))
                else:
                    pty = int(math.floor(state['pos'].x()))
                    ptx = int(math.floor(state['pos'].y()))
                    szy = int(math.floor(state['size'].x()))
                    szx = int(math.floor(state['size'].y()))
                crd = [ptx, pty, ptx + szx, pty + szy]
                if self.__rois.coords[rid] != crd:
                    self.__rois.coords[rid] = crd
                    self.roiCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitROICoordsChanged(self, rid):
        """ emits roiCoordsChanged signal

        :param rid: roi id
        :type rid: :obj:`int`
        """
        oldrid = self.__rois.current
        if rid != oldrid:
            self.__rois.current = rid
            self.roiCoordsChanged.emit()

    @QtCore.pyqtSlot(int)
    def changeCutRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            cid = self.__cuts.current
            crds = self._getCut(cid).getCoordinates()
            if not self.__transformations.transpose:
                self.__cuts.coords[cid] = crds
            else:
                self.__cuts.coords[cid] = [
                    crds[1], crds[0], crds[3], crds[2], crds[4]]

            self.cutCoordsChanged.emit()
        except Exception as e:
            print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitCutCoordsChanged(self, cid):
        """ emits cutCoordsChanged signal

        :param cid: cut id
        :type cid: :obj:`int`
        """
        oldcid = self.__cuts.current
        if cid != oldcid:
            self.__cuts.current = cid
            self.cutCoordsChanged.emit()

    def updateROIs(self, rid, coords):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__addROICoords(coords)
        while rid > len(self.__roi):
            if coords and len(coords) >= len(self.__roi):
                self.__addROI(coords[len(self.__roi)])
            else:
                self.__addROI()
            self._getROI().sigHoverEvent.connect(self.__currentroimapper.map)
            self._getROI().sigRegionChanged.connect(self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
            self.__roiregionmapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
        if rid <= 0:
            self.__rois.current = -1
        elif self.__rois.current >= rid:
            self.__rois.current = 0
        while self._getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(self._getROI())
            self.__roiregionmapper.removeMappings(self._getROI())
            self.__removeROI()
        self.__showROIs(self.__rois.enabled)

    def updateCuts(self, cid, coords):
        """ update Cuts

        :param cid: cut id
        :type cid: :obj:`int`
        :param coords: cut coordinates
        :type coords: :obj:`list` < [float, float, float, float] >
        """
        self.__addCutCoords(coords)
        while cid > len(self.__cut):
            if coords and len(coords) >= len(self.__cut):
                self.__addCut(coords[len(self.__cut)])
            else:
                self.__addCut()
            self._getCut().sigHoverEvent.connect(self.__currentcutmapper.map)
            self._getCut().sigRegionChanged.connect(self.__cutregionmapper.map)
            self._getCut().handle1.hovered.connect(self.__currentcutmapper.map)
            self._getCut().handle2.hovered.connect(self.__currentcutmapper.map)
            self._getCut().vhandle.hovered.connect(self.__currentcutmapper.map)
            self.__currentcutmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle1, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle2, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().vhandle, len(self.__cut) - 1)
            self.__cutregionmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
        if cid <= 0:
            self.__cuts.current = -1
        elif self.__cuts.current >= cid:
            self.__cuts.current = 0
        while max(cid, 0) < len(self.__cut):
            self.__currentcutmapper.removeMappings(self._getCut())
            self.__currentcutmapper.removeMappings(self._getCut().handle1)
            self.__currentcutmapper.removeMappings(self._getCut().handle2)
            self.__cutregionmapper.removeMappings(self._getCut())
            self.__removeCut()

    def updateMetaData(self, axisscales=None, axislabels=None):
        """ update Metadata informations

        :param axisscales: [xstart, ystart, xscale, yscale]
        :type axisscales:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        :param axislabels: [xtext, ytext, xunits, yunits]
        :type axislabels:
                  [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        """
        if axislabels is not None:
            self.__axes.xtext = str(axislabels[0]) \
                if axislabels[0] is not None else None
            self.__axes.ytext = str(axislabels[1]) \
                if axislabels[0] is not None else None
            self.__axes.xunits = str(axislabels[2]) \
                if axislabels[0] is not None else None
            self.__axes.yunits = str(axislabels[3]) \
                if axislabels[0] is not None else None
        position = None
        scale = None
        if axisscales is not None:
            try:
                position = (float(axisscales[0]), float(axisscales[1]))
            except Exception:
                position = None
            try:
                scale = (float(axisscales[2]), float(axisscales[3]))
            except Exception:
                scale = None
        self.__setScale(position, scale, self.__axes.enabled)

    def setStatsWOScaling(self, status):
        """ sets statistics without scaling flag

        :param status: statistics without scaling flag
        :type status: :obj:`bool`
        :returns: change status
        :rtype: :obj:`bool`
        """
        if self.__intensity.statswoscaling != status:
            self.__intensity.statswoscaling = status
            return True
        return False

    def setROIsColors(self, colors=None):
        """ sets statistics without scaling flag

        :param colors: json list of roi colors
        :type colors: :obj:`str`
        :returns: change status
        :rtype: :obj:`bool`
        """
        force = False
        if colors is not None:
            colors = json.loads(colors)
            if not isinstance(colors, list):
                return False
            for cl in colors:
                if not isinstance(cl, list):
                    return False
                if len(cl) != 3:
                    return False
                for clit in cl:
                    if not isinstance(clit, int):
                        return False
        else:
            colors = self.__rois.colors
            force = True
        if self.__rois.colors != colors or force:
            self.__rois.colors = colors
            defpen = (255, 255, 255)
            for it, roi in enumerate(self.__roi):
                clr = tuple(colors[it % len(colors)]) if colors else defpen
                roi.setPen(clr)
                if hasattr(self.__roitext[it], "setColor"):
                    self.__roitext[it].setColor(clr)
                else:
                    self.__roitext[it].color = fn.mkColor(color)
                    self.__roitext[it].textItem.setDefaultTextColor(self.color)
        return True

    def setScalingType(self, scalingtype):
        """ sets intensity scaling types

        :param scalingtype: intensity scaling type
        :type scalingtype: :obj:`str`
        """
        self.__intensity.scaling = scalingtype

    def setDoBkgSubtraction(self, state):
        """ sets do background subtraction flag

        :param status: do background subtraction flag
        :type status: :obj:`bool`
        """
        self.__intensity.dobkgsubtraction = state

    def isCutsEnabled(self):
        """ provides flag cuts enabled

        :return: cut enabled flag
        :rtype: :obj:`bool`
        """
        return self.__cuts.enabled

    def isROIsEnabled(self):
        """ provides flag rois enabled

        :return: roi enabled flag
        :rtype: :obj:`bool`
        """
        return self.__rois.enabled

    def roiCoords(self):
        """ provides rois coordinates

        :return: rois coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__rois.coords

    def cutCoords(self):
        """ provides cuts coordinates

        :return: cuts coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__cuts.coords

    def currentROI(self):
        """ provides current roi id

        :return: roi id
        :rtype: :obj:`int`
        """
        return self.__rois.current

    def currentCut(self):
        """ provides current cut id

        :return: cut id
        :rtype: :obj:`int`
        """
        return self.__cuts.current

    def image(self):
        """ provides imageItem object

        :returns: image object
        :rtype: :class:`pyqtgraph.imageItem.ImageItem`
        """
        return self.__image

    @QtCore.pyqtSlot(float, float)
    def updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__centercoordinates = [xdata, ydata]
        if not self.__transformations.transpose:
            self.__centerVLine.setPos(xdata)
            self.__centerHLine.setPos(ydata)
        else:
            self.__centerVLine.setPos(ydata)
            self.__centerHLine.setPos(xdata)

    @QtCore.pyqtSlot(float, float)
    def updateLocker(self, xdata, ydata):
        """ updates the locker position

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__crosshairlocked = not self.__crosshairlocked
        if not self.__crosshairlocked:
            if not self.__transformations.transpose:
                self.__lockerVLine.setPos(xdata + 0.5)
                self.__lockerHLine.setPos(ydata + 0.5)
            else:
                self.__lockerVLine.setPos(ydata + 0.5)
                self.__lockerHLine.setPos(xdata + 0.5)
        else:
            self.__lockercoordinates = [xdata, ydata]

    @QtCore.pyqtSlot(float, float)
    def updatePositionMark(self, xdata, ydata):
        """ updates the position mark

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__markcoordinates = [xdata, ydata]
        if not self.__transformations.transpose:
            self.__markVLine.setPos(xdata)
            self.__markHLine.setPos(ydata)
        else:
            self.__markVLine.setPos(ydata)
            self.__markHLine.setPos(xdata)

    def setTransformations(self, transpose, leftrightflip, updownflip):
        """ sets coordinate transformations

        :param transpose: transpose coordinates flag
        :type transpose: :obj:`bool`
        :param leftrightflip: left-right flip coordinates flag
        :type leftrightflip: :obj:`bool`
        :param updownflip: up-down flip coordinates flag
        :type updownflip: :obj:`bool`
        """
        if self.__transformations.transpose != transpose:
            self.__transformations.transpose = transpose
            self.__transposeItems()
        if self.__transformations.leftrightflip != leftrightflip:
            self.__transformations.leftrightflip = leftrightflip
            if hasattr(self.__viewbox, "invertX"):
                self.__viewbox.invertX(leftrightflip)
            else:
                """ version 0.9.10 without invertX """
            # workaround for a bug in old pyqtgraph versions: stretch 0.10
            self.__viewbox.sigXRangeChanged.emit(
                self.__viewbox, tuple(self.__viewbox.state['viewRange'][0]))
            self.__viewbox.sigYRangeChanged.emit(
                self.__viewbox, tuple(self.__viewbox.state['viewRange'][1]))
            self.__viewbox.sigRangeChanged.emit(
                self.__viewbox, self.__viewbox.state['viewRange'])

        if self.__transformations.updownflip != updownflip:
            self.__transformations.updownflip = updownflip
            self.__viewbox.invertY(updownflip)
            # workaround for a bug in old pyqtgraph versions: stretch 0.9.10
            self.__viewbox.sigXRangeChanged.emit(
                self.__viewbox, tuple(self.__viewbox.state['viewRange'][0]))
            self.__viewbox.sigYRangeChanged.emit(
                self.__viewbox, tuple(self.__viewbox.state['viewRange'][1]))
            self.__viewbox.sigRangeChanged.emit(
                self.__viewbox, self.__viewbox.state['viewRange'])

    def transformations(self):
        """ povides coordinates transformations

        :returns: transpose, leftrightflip, updownflip flags
        :rtype: (:obj:`bool`, :obj:`bool`, :obj:`bool`)
        """
        return (
            self.__transformations.transpose,
            self.__transformations.leftrightflip,
            self.__transformations.updownflip)

    def __transposeItems(self):
        """ transposes all image items
        """
        self.__transposeROIs()
        self.__transposeCuts()
        self.__transposeAxes()
        self.__transposeLockerLines()
        self.__transposeCenterLines()
        self.__transposeMarkLines()

    def __transposeROIs(self):
        """ transposes ROIs
        """
        for crd in self.__roi:
            pos = crd.pos()
            size = crd.size()
            crd.setPos([pos[1], pos[0]])
            crd.setSize([size[1], size[0]])

    def __transposeCuts(self):
        """ transposes Cuts
        """
        for crd in self.__cut:
            pos = crd.pos()
            size = crd.size()
            angle = crd.angle()
            ra = angle * np.pi / 180.
            crd.setPos(
                [pos[1] + math.sin(ra) * size[0],
                 pos[0] + math.cos(ra) * size[0]])
            crd.setAngle(270-angle)

    def __transposeLockerLines(self):
        """ transposes locker lines
        """
        v = self.__lockerHLine.getPos()[1]
        h = self.__lockerVLine.getPos()[0]
        self.__lockerVLine.setPos(v)
        self.__lockerHLine.setPos(h)

    def __transposeCenterLines(self):
        """ transposes Center lines
        """
        v = self.__centerHLine.getPos()[1]
        h = self.__centerVLine.getPos()[0]
        self.__centerVLine.setPos(v)
        self.__centerHLine.setPos(h)

    def __transposeMarkLines(self):
        """ transposes Mark Position lines
        """
        v = self.__markHLine.getPos()[1]
        h = self.__markVLine.getPos()[0]
        self.__markVLine.setPos(v)
        self.__markHLine.setPos(h)

    def __transposeAxes(self):
        """ transposes axes
        """
        if self.__axes.enabled is True:
            self.__setScale(self.__axes.position, self.__axes.scale)
        if self.__polaraxes.enabled is True:
            self.__setScale(
                self.__polaraxes.position, self.__polaraxes.scale, polar=True)

    def autoRange(self):
        """ sets auto range
        """
        self.__viewbox.autoRange()
        self.__viewbox.enableAutoRange('xy', True)
